using System.Net.Http.Json;
using System.Security.Cryptography;
using System.Text.Json;
using System.Collections.Concurrent;
using System.Diagnostics;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddHttpClient("hermes", client =>
{
    client.Timeout = TimeSpan.FromMinutes(10);
});
var app = builder.Build();

bool ReadBoolEnv(string key, bool defaultValue)
{
    var raw = Environment.GetEnvironmentVariable(key);
    if (string.IsNullOrWhiteSpace(raw))
        return defaultValue;
    return raw.Trim().ToLowerInvariant() is "1" or "true" or "yes" or "on";
}

var backendUrl = Environment.GetEnvironmentVariable("HERMES_BACKEND_URL") ?? "http://hermes-api:8787";
var backendApiKey = Environment.GetEnvironmentVariable("HERMES_API_KEY") ?? "";
var gatewayKey = Environment.GetEnvironmentVariable("HERMES_GATEWAY_KEY") ?? "";
var allowInsecureNoKey = ReadBoolEnv("HERMES_ALLOW_INSECURE_NO_KEY", false);
var unifiedEnabled = Environment.GetEnvironmentVariable("AIHUB_UNIFIED_ENABLED") ?? "true";
var sharedModelId = Environment.GetEnvironmentVariable("AIHUB_SHARED_MODEL_ID") ?? "hermes-fleet-latest";
var sharedMlProfile = Environment.GetEnvironmentVariable("AIHUB_SHARED_ML_PROFILE") ?? "global-learning";
var fleetModelLabel = Environment.GetEnvironmentVariable("HERMES_FLEET_MODEL_LABEL") ?? "hermes-fleet-newest";
var mcpServer = Environment.GetEnvironmentVariable("HERMES_MCP_SERVER") ?? "github";
var lowBandwidthMode = ReadBoolEnv("HERMES_LOW_BANDWIDTH_MODE", true);
var offlineOnlyMode = ReadBoolEnv("HERMES_OFFLINE_ONLY", false);
var userRoutedInternet = ReadBoolEnv("HERMES_USER_ROUTED_INTERNET", true);
var sessionTtlHours = Math.Max(1, int.TryParse(Environment.GetEnvironmentVariable("HERMES_SESSION_TTL_HOURS"), out var ttl) ? ttl : 12);
var authSessions = new ConcurrentDictionary<string, DateTimeOffset>();
var gatewayStats = new ConcurrentDictionary<string, GatewayRouteStats>();

string NewSessionToken()
{
    var bytes = RandomNumberGenerator.GetBytes(32);
    return Convert.ToBase64String(bytes).Replace("+", "-").Replace("/", "_").TrimEnd('=');
}

void CleanupExpiredSessions()
{
    var now = DateTimeOffset.UtcNow;
    foreach (var session in authSessions)
    {
        if (session.Value <= now)
            authSessions.TryRemove(session.Key, out _);
    }
}

bool HasValidToken(HttpContext context)
{
    CleanupExpiredSessions();
    string? token = null;
    if (context.Request.Headers.TryGetValue("X-Hermes-Session", out var sessionHeader))
        token = sessionHeader.ToString();
    if (string.IsNullOrWhiteSpace(token) &&
        context.Request.Headers.TryGetValue("Authorization", out var authHeader) &&
        authHeader.ToString().StartsWith("Bearer ", StringComparison.OrdinalIgnoreCase))
        token = authHeader.ToString()["Bearer ".Length..].Trim();
    if (string.IsNullOrWhiteSpace(token))
        return false;
    return authSessions.TryGetValue(token, out var expiresAt) && expiresAt > DateTimeOffset.UtcNow;
}

bool Authorized(HttpContext context)
{
    if (string.IsNullOrWhiteSpace(gatewayKey))
        return allowInsecureNoKey || HasValidToken(context);
    if (HasValidToken(context))
        return true;
    return context.Request.Headers.TryGetValue("X-Hermes-Key", out var incoming) && incoming.ToString() == gatewayKey;
}

void AttachBackendKey(HttpClient client)
{
    if (string.IsNullOrWhiteSpace(backendApiKey))
        return;
    client.DefaultRequestHeaders.Remove("X-Hermes-Key");
    client.DefaultRequestHeaders.Add("X-Hermes-Key", backendApiKey);
}

async Task<IResult> ProxyGetStreamed(
    IHttpClientFactory factory,
    HttpContext context,
    string path)
{
    if (!Authorized(context))
        return Results.Unauthorized();
    using var client = factory.CreateClient("hermes");
    AttachBackendKey(client);
    using var request = new HttpRequestMessage(HttpMethod.Get, $"{backendUrl}{path}");
    using var response = await client.SendAsync(request, HttpCompletionOption.ResponseHeadersRead, context.RequestAborted);
    var contentType = response.Content.Headers.ContentType?.ToString() ?? "application/json";
    context.Response.StatusCode = (int)response.StatusCode;
    context.Response.ContentType = contentType;
    await response.Content.CopyToAsync(context.Response.Body, context.RequestAborted);
    return Results.Empty;
}

async Task<IResult> ProxyGetJson(
    IHttpClientFactory factory,
    HttpContext context,
    string path)
{
    if (!Authorized(context))
        return Results.Unauthorized();
    using var client = factory.CreateClient("hermes");
    AttachBackendKey(client);
    using var response = await client.GetAsync($"{backendUrl}{path}", context.RequestAborted);
    var body = await response.Content.ReadAsStringAsync(context.RequestAborted);
    return Results.Content(body, "application/json", statusCode: (int)response.StatusCode);
}

async Task<IResult> ProxyPostJson(
    IHttpClientFactory factory,
    HttpContext context,
    string path,
    object payload)
{
    if (!Authorized(context))
        return Results.Unauthorized();
    using var client = factory.CreateClient("hermes");
    AttachBackendKey(client);
    using var response = await client.PostAsJsonAsync($"{backendUrl}{path}", payload, context.RequestAborted);
    var body = await response.Content.ReadAsStringAsync(context.RequestAborted);
    return Results.Content(body, "application/json", statusCode: (int)response.StatusCode);
}

app.Use(async (context, next) =>
{
    var sw = Stopwatch.StartNew();
    await next();
    sw.Stop();
    var key = $"{context.Request.Method} {context.Request.Path.Value ?? "/"}";
    var stat = gatewayStats.GetOrAdd(key, _ => new GatewayRouteStats());
    stat.Record(sw.Elapsed.TotalMilliseconds, context.Response.StatusCode >= 400);
});

app.MapGet("/", () =>
    Results.Json(new
    {
        service = "hermes-gateway",
        ok = true,
        endpoints = new[]
        {
            "/auth/login",
            "/health",
            "/system-watch",
            "/gateway-max-status",
            "/aihub-max-upgrade",
            "/snapshot",
            "/learning-growth",
            "/training-status",
            "/learning-state",
            "/cpp-kernel-status",
            "/knowledge-mesh",
            "/unified-config",
            "/runtime-orchestrate/deploy",
            "/runtime-orchestrate/return",
            "/runtime-orchestrate/restore",
            "/runtime-bridge/transfer"
        },
        auth_header = "X-Hermes-Key",
        auth_session_header = "X-Hermes-Session",
        note = "Most endpoints require X-Hermes-Key."
    })
);

app.MapPost("/auth/login", async (HttpContext context) =>
{
    var payload = await context.Request.ReadFromJsonAsync<JsonElement>();
    var providedKey = payload.TryGetProperty("gateway_key", out var keyNode) ? (keyNode.GetString() ?? "") : "";
    var valid = (!string.IsNullOrWhiteSpace(gatewayKey) && providedKey == gatewayKey)
        || (string.IsNullOrWhiteSpace(gatewayKey) && allowInsecureNoKey);
    if (!valid)
        return Results.Unauthorized();
    var token = NewSessionToken();
    var expiresAt = DateTimeOffset.UtcNow.AddHours(sessionTtlHours);
    authSessions[token] = expiresAt;
    return Results.Json(new
    {
        token,
        expires_at = expiresAt,
        auth_header = "X-Hermes-Session",
        bearer_supported = true
    });
});

app.MapGet("/health", async (IHttpClientFactory factory, HttpContext context) =>
{
    return await ProxyGetJson(factory, context, "/health");
});

app.MapGet("/snapshot", async (IHttpClientFactory factory, HttpContext context) =>
{
    return await ProxyGetStreamed(factory, context, "/snapshot");
});

app.MapGet("/learning-growth", async (IHttpClientFactory factory, HttpContext context) =>
{
    return await ProxyGetJson(factory, context, "/learning-growth");
});

app.MapGet("/training-status", async (IHttpClientFactory factory, HttpContext context) =>
{
    return await ProxyGetJson(factory, context, "/training-status");
});

app.MapGet("/learning-state", async (IHttpClientFactory factory, HttpContext context) =>
{
    return await ProxyGetStreamed(factory, context, "/learning-state");
});

app.MapGet("/cpp-kernel-status", async (IHttpClientFactory factory, HttpContext context) =>
{
    return await ProxyGetJson(factory, context, "/cpp-kernel-status");
});

app.MapGet("/knowledge-mesh", async (IHttpClientFactory factory, HttpContext context) =>
{
    return await ProxyGetJson(factory, context, "/knowledge-mesh");
});

app.MapGet("/system-watch", async (IHttpClientFactory factory, HttpContext context) =>
{
    if (!Authorized(context))
        return Results.Unauthorized();
    using var client = factory.CreateClient("hermes");
    AttachBackendKey(client);

    async Task<object> FetchJsonOrError(string path)
    {
        try
        {
            using var response = await client.GetAsync($"{backendUrl}{path}", context.RequestAborted);
            var body = await response.Content.ReadAsStringAsync(context.RequestAborted);
            if (!response.IsSuccessStatusCode)
            {
                return new { ok = false, status = (int)response.StatusCode, error = $"backend returned {(int)response.StatusCode}" };
            }
            using var doc = JsonDocument.Parse(body);
            return doc.RootElement.Clone();
        }
        catch (HttpRequestException ex)
        {
            return new { ok = false, error = ex.Message };
        }
        catch (TaskCanceledException ex)
        {
            return new { ok = false, error = ex.Message };
        }
        catch (JsonException ex)
        {
            return new { ok = false, error = ex.Message };
        }
    }

    var healthTask = FetchJsonOrError("/health");
    var snapshotTask = FetchJsonOrError("/snapshot");
    var growthTask = FetchJsonOrError("/learning-growth");
    var trainingTask = FetchJsonOrError("/training-status");
    var cppTask = FetchJsonOrError("/cpp-kernel-status");
    var bonusTask = FetchJsonOrError("/aihub-bonus");
    var meshTask = FetchJsonOrError("/knowledge-mesh");
    await Task.WhenAll(healthTask, snapshotTask, growthTask, trainingTask, cppTask, bonusTask, meshTask);

    return Results.Json(new
    {
        watch_timestamp_utc = DateTimeOffset.UtcNow,
        gateway = new
        {
            ok = true,
            low_bandwidth_mode = lowBandwidthMode,
            offline_only_mode = offlineOnlyMode,
            user_routed_internet = userRoutedInternet
        },
        unified_config = new
        {
            single_exe_entrypoint = "hermes-gateway",
            aihub_unified_enabled = unifiedEnabled,
            aihub_shared_model_id = sharedModelId,
            aihub_shared_ml_profile = sharedMlProfile,
            fleet_model_label = fleetModelLabel,
            mcp_server = mcpServer
        },
        health = healthTask.Result,
        snapshot = snapshotTask.Result,
        learning_growth = growthTask.Result,
        training_status = trainingTask.Result,
        cpp_kernel_status = cppTask.Result,
        aihub_bonus = bonusTask.Result,
        knowledge_mesh = meshTask.Result
    });
});

app.MapGet("/gateway-max-status", (HttpContext context) =>
{
    if (!Authorized(context))
        return Results.Unauthorized();
    var topRoutes = gatewayStats
        .OrderByDescending(kvp => kvp.Value.Requests)
        .Take(24)
        .Select(kvp => new
        {
            route = kvp.Key,
            requests = kvp.Value.Requests,
            errors = kvp.Value.Errors,
            avg_ms = kvp.Value.AverageMs,
            max_ms = kvp.Value.MaxMs
        })
        .ToArray();
    return Results.Json(new
    {
        timestamp_utc = DateTimeOffset.UtcNow,
        gateway = new
        {
            service = "hermes-gateway",
            routes_tracked = gatewayStats.Count,
            low_bandwidth_mode = lowBandwidthMode,
            offline_only_mode = offlineOnlyMode,
            user_routed_internet = userRoutedInternet
        },
        routes = topRoutes
    });
});

app.MapPost("/aihub-max-upgrade", async (IHttpClientFactory factory, GatewayMaxUpgradeRequest request, HttpContext context) =>
{
    if (!Authorized(context))
        return Results.Unauthorized();
    using var client = factory.CreateClient("hermes");
    AttachBackendKey(client);
    var specialty = string.IsNullOrWhiteSpace(request.Specialty) ? "fleet:max-upgrade" : request.Specialty;
    using var curateResp = await client.PostAsJsonAsync(
        $"{backendUrl}/curate-learning",
        new
        {
            sql_signal = Math.Clamp(request.SqlSignal, 0.55, 0.99),
            internet_signal = Math.Clamp(request.InternetSignal, 0.0, 0.30),
            llm_signal = Math.Clamp(request.LlmSignal, 0.60, 0.99),
            stability_bias = Math.Clamp(request.StabilityBias, 0.60, 0.99)
        },
        context.RequestAborted
    );
    using var pulseResp = await client.PostAsJsonAsync(
        $"{backendUrl}/learning-pulse",
        new
        {
            specialty,
            steps = Math.Clamp(request.Steps, 120, 1400),
            candidates = Math.Clamp(request.Candidates, 80, 500),
            sql_signal = Math.Clamp(request.SqlSignal, 0.55, 0.99),
            internet_signal = Math.Clamp(request.InternetSignal, 0.0, 0.30),
            llm_signal = Math.Clamp(request.LlmSignal, 0.60, 0.99),
            stability_bias = Math.Clamp(request.StabilityBias, 0.60, 0.99)
        },
        context.RequestAborted
    );
    var curateBody = await curateResp.Content.ReadAsStringAsync(context.RequestAborted);
    var pulseBody = await pulseResp.Content.ReadAsStringAsync(context.RequestAborted);
    return Results.Json(new
    {
        ok = curateResp.IsSuccessStatusCode && pulseResp.IsSuccessStatusCode,
        mode = "aihub-max-upgrade",
        request = new
        {
            specialty,
            steps = Math.Clamp(request.Steps, 120, 1400),
            candidates = Math.Clamp(request.Candidates, 80, 500),
            sql_signal = Math.Clamp(request.SqlSignal, 0.55, 0.99),
            internet_signal = Math.Clamp(request.InternetSignal, 0.0, 0.30),
            llm_signal = Math.Clamp(request.LlmSignal, 0.60, 0.99),
            stability_bias = Math.Clamp(request.StabilityBias, 0.60, 0.99)
        },
        curate = new { status = (int)curateResp.StatusCode, body = curateBody },
        learning_pulse = new { status = (int)pulseResp.StatusCode, body = pulseBody }
    });
});

app.MapGet("/unified-config", (HttpContext context) =>
{
    if (!Authorized(context))
        return Results.Unauthorized();
    return Results.Json(new
    {
        single_exe_entrypoint = "hermes-gateway",
        aihub_unified_enabled = unifiedEnabled,
        aihub_shared_model_id = sharedModelId,
        aihub_shared_ml_profile = sharedMlProfile,
        fleet_model_label = fleetModelLabel,
        mcp_server = mcpServer,
        low_bandwidth_mode = lowBandwidthMode,
        offline_only_mode = offlineOnlyMode,
        user_routed_internet = userRoutedInternet,
        security = new
        {
            gateway_key_enabled = !string.IsNullOrWhiteSpace(gatewayKey),
            backend_api_key_enabled = !string.IsNullOrWhiteSpace(backendApiKey),
            allow_insecure_no_key = allowInsecureNoKey
        }
    });
});

app.MapPost("/simulate", async (IHttpClientFactory factory, SimulateRequest request, HttpContext context) =>
{
    return await ProxyPostJson(factory, context, "/simulate", new { steps = request.Steps, specialty = request.Specialty });
});

app.MapPost("/learning-pulse", async (IHttpClientFactory factory, LearningPulseRequest request, HttpContext context) =>
{
    return await ProxyPostJson(
        factory,
        context,
        "/learning-pulse",
        new
        {
            specialty = request.Specialty,
            steps = request.Steps,
            candidates = request.Candidates,
            sql_signal = request.SqlSignal,
            internet_signal = request.InternetSignal,
            llm_signal = request.LlmSignal,
            stability_bias = request.StabilityBias,
        });
});

app.MapPost("/optimize-fleet", async (IHttpClientFactory factory, OptimizeFleetRequest request, HttpContext context) =>
{
    return await ProxyPostJson(
        factory,
        context,
        "/optimize-fleet",
        new { specialty = request.Specialty, candidates = request.Candidates });
});

app.MapPost("/runtime-orchestrate/deploy", async (IHttpClientFactory factory, RuntimeDeployRequest request, HttpContext context) =>
{
    if (!Authorized(context))
        return Results.Unauthorized();
    var specialty = string.IsNullOrWhiteSpace(request.Specialty) ? "fleet" : request.Specialty;
    var normalizedBatch = Math.Max(1, Math.Min(256, request.BatchSize));
    var isBatchScope = request.Scope.Equals("batch", StringComparison.OrdinalIgnoreCase);
    var candidates = isBatchScope
        ? Math.Max(40, Math.Min(request.Candidates, normalizedBatch * 6))
        : request.Scope.Equals("all", StringComparison.OrdinalIgnoreCase)
            ? Math.Max(120, request.Candidates)
            : request.Candidates;
    using var client = factory.CreateClient("hermes");
    AttachBackendKey(client);
    using var pulseResponse = await client.PostAsJsonAsync(
        $"{backendUrl}/learning-pulse",
        new
        {
            specialty,
            steps = request.Steps,
            candidates,
            sql_signal = request.SqlSignal,
            internet_signal = request.InternetSignal,
            llm_signal = request.LlmSignal,
            stability_bias = request.StabilityBias,
        },
        context.RequestAborted);
    var pulseBody = await pulseResponse.Content.ReadAsStringAsync(context.RequestAborted);
    if (!pulseResponse.IsSuccessStatusCode)
        return Results.Content(pulseBody, "application/json", statusCode: (int)pulseResponse.StatusCode);

    using var optimizeResponse = await client.PostAsJsonAsync(
        $"{backendUrl}/optimize-fleet",
        new { specialty, candidates },
        context.RequestAborted);
    var optimizeBody = await optimizeResponse.Content.ReadAsStringAsync(context.RequestAborted);
    if (!optimizeResponse.IsSuccessStatusCode)
        return Results.Content(optimizeBody, "application/json", statusCode: (int)optimizeResponse.StatusCode);

    using var pulseJson = JsonDocument.Parse(pulseBody);
    using var optimizeJson = JsonDocument.Parse(optimizeBody);
    return Results.Json(new
    {
        ok = true,
        mode = request.Mode,
        scope = request.Scope,
        batch_size = normalizedBatch,
        dispatch = "csharp-gateway-control-plane",
        learning_pulse = pulseJson.RootElement.Clone(),
        optimized = optimizeJson.RootElement.Clone()
    });
});

app.MapPost("/runtime-orchestrate/return", async (IHttpClientFactory factory, RuntimeReturnRequest request, HttpContext context) =>
{
    var specialty = string.IsNullOrWhiteSpace(request.Specialty) ? "fleet" : request.Specialty;
    var payload = new
    {
        source = "csharp-gateway-return",
        score = Math.Max(0.0, Math.Min(1.0, request.Confidence)),
        payload = new
        {
            action = "return_hermes",
            specialty,
            units = request.Units,
            mode = request.Mode,
            reason = request.Reason
        }
    };
    return await ProxyPostJson(factory, context, "/ingest-signal", payload);
});

app.MapPost("/runtime-orchestrate/restore", async (IHttpClientFactory factory, RuntimeRestoreRequest request, HttpContext context) =>
{
    var specialty = string.IsNullOrWhiteSpace(request.Specialty) ? "fleet" : request.Specialty;
    var payload = new
    {
        source = "csharp-gateway-restore",
        score = Math.Max(0.0, Math.Min(1.0, request.Confidence)),
        payload = new
        {
            action = "restore",
            specialty,
            units = request.Units,
            mode = request.Mode
        }
    };
    return await ProxyPostJson(factory, context, "/ingest-signal", payload);
});

app.MapPost("/runtime-bridge/transfer", async (IHttpClientFactory factory, RuntimeBridgeTransferRequest request, HttpContext context) =>
{
    var payload = new
    {
        source = "csharp-runtime-bridge",
        score = Math.Max(0.0, Math.Min(1.0, request.Reliability)),
        payload = new
        {
            source_runtime = request.SourceRuntime,
            target_runtime = request.TargetRuntime,
            transfer_kind = request.TransferKind,
            route = request.Route,
            data_shape = request.DataShape,
            deployment_scope = request.DeploymentScope
        }
    };
    return await ProxyPostJson(factory, context, "/ingest-signal", payload);
});

app.MapPost("/curate-learning", async (IHttpClientFactory factory, CurateLearningRequest request, HttpContext context) =>
{
    return await ProxyPostJson(
        factory,
        context,
        "/curate-learning",
        new
        {
            sql_signal = request.SqlSignal,
            internet_signal = request.InternetSignal,
            llm_signal = request.LlmSignal,
            stability_bias = request.StabilityBias,
        });
});

app.MapPost("/dedupe-optimize", async (IHttpClientFactory factory, DedupeRequest request, HttpContext context) =>
{
    return await ProxyPostJson(
        factory,
        context,
        "/dedupe-optimize",
        new { roots = request.Roots, max_file_mb = request.MaxFileMb });
});

app.MapPost("/llm-chat", async (IHttpClientFactory factory, HttpContext context) =>
{
    if (!Authorized(context))
        return Results.Unauthorized();
    var payload = await context.Request.ReadFromJsonAsync<JsonElement>();
    var prompt = payload.TryGetProperty("prompt", out var promptNode) ? (promptNode.GetString() ?? "") : "";
    var systemPrompt = payload.TryGetProperty("system_prompt", out var systemNode)
        ? (systemNode.GetString() ?? "You are Hermes AIHub assistant.")
        : "You are Hermes AIHub assistant.";
    var model = payload.TryGetProperty("model", out var modelNode) ? modelNode.GetString() : null;
    var temperature = payload.TryGetProperty("temperature", out var tempNode) && tempNode.TryGetDouble(out var t) ? t : 0.3;
    var maxTokens = payload.TryGetProperty("max_tokens", out var tokNode) && tokNode.TryGetInt32(out var mt) ? mt : 512;
    return await ProxyPostJson(
        factory,
        context,
        "/llm-chat",
        new
        {
            prompt,
            system_prompt = systemPrompt,
            model,
            temperature,
            max_tokens = maxTokens,
        });
});

app.MapPost("/learning-state/import", async (IHttpClientFactory factory, HttpContext context) =>
{
    var payload = await context.Request.ReadFromJsonAsync<JsonElement>();
    return await ProxyPostJson(factory, context, "/learning-state/import", payload);
});

app.MapPost("/ingest-knowledge-mesh", async (IHttpClientFactory factory, HttpContext context) =>
{
    var payload = await context.Request.ReadFromJsonAsync<JsonElement>();
    return await ProxyPostJson(factory, context, "/ingest-knowledge-mesh", payload);
});

app.MapGet("/aihub-bonus", async (IHttpClientFactory factory, HttpContext context) =>
{
    return await ProxyGetJson(factory, context, "/aihub-bonus");
});

app.Run("http://0.0.0.0:8788");

public sealed record SimulateRequest(int Steps = 200, string Specialty = "fleet");
public sealed record OptimizeFleetRequest(int Candidates = 120, string Specialty = "fleet");
public sealed record CurateLearningRequest(double SqlSignal = 0.75, double InternetSignal = 0.55, double LlmSignal = 0.7, double StabilityBias = 0.72);
public sealed record LearningPulseRequest(
    string Specialty = "fleet",
    int Steps = 180,
    int Candidates = 120,
    double SqlSignal = 0.75,
    double InternetSignal = 0.55,
    double LlmSignal = 0.7,
    double StabilityBias = 0.72);
public sealed record RuntimeDeployRequest(
    string Mode = "deploy",
    string Scope = "all",
    string Specialty = "fleet",
    int BatchSize = 10,
    int Steps = 220,
    int Candidates = 140,
    double SqlSignal = 0.8,
    double InternetSignal = 0.58,
    double LlmSignal = 0.78,
    double StabilityBias = 0.74);
public sealed record RuntimeReturnRequest(
    string Mode = "return",
    string Specialty = "fleet",
    int Units = 10,
    string Reason = "gui-return-action",
    double Confidence = 0.8);
public sealed record RuntimeRestoreRequest(
    string Mode = "restore",
    string Specialty = "fleet",
    int Units = 64,
    double Confidence = 0.8);
public sealed record RuntimeBridgeTransferRequest(
    string SourceRuntime = "csharp",
    string TargetRuntime = "cpp",
    string TransferKind = "learning-data",
    string Route = "gateway-dispatch",
    string DataShape = "mesh+sql+signals",
    string DeploymentScope = "all",
    double Reliability = 0.8);
public sealed record DedupeRequest(string[] Roots, int MaxFileMb = 8);
public sealed record GatewayMaxUpgradeRequest(
    string Specialty = "fleet:max-upgrade",
    int Steps = 520,
    int Candidates = 240,
    double SqlSignal = 0.90,
    double InternetSignal = 0.12,
    double LlmSignal = 0.94,
    double StabilityBias = 0.84);

public sealed class GatewayRouteStats
{
    private long _requests;
    private long _errors;
    private double _totalMs;
    private double _maxMs;
    private readonly object _sync = new();

    public long Requests => Interlocked.Read(ref _requests);
    public long Errors => Interlocked.Read(ref _errors);
    public double AverageMs => Requests <= 0 ? 0.0 : (_totalMs / Requests);
    public double MaxMs => _maxMs;

    public void Record(double elapsedMs, bool isError)
    {
        Interlocked.Increment(ref _requests);
        if (isError)
            Interlocked.Increment(ref _errors);
        lock (_sync)
        {
            _totalMs += elapsedMs;
            if (elapsedMs > _maxMs)
                _maxMs = elapsedMs;
        }
    }
}
