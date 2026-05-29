using System.Net.Http.Json;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddHttpClient("hermes");
var app = builder.Build();

var backendUrl = Environment.GetEnvironmentVariable("HERMES_BACKEND_URL") ?? "http://hermes-api:8787";
var backendApiKey = Environment.GetEnvironmentVariable("HERMES_API_KEY") ?? "";
var gatewayKey = Environment.GetEnvironmentVariable("HERMES_GATEWAY_KEY") ?? "";
var unifiedEnabled = Environment.GetEnvironmentVariable("AIHUB_UNIFIED_ENABLED") ?? "true";
var sharedModelId = Environment.GetEnvironmentVariable("AIHUB_SHARED_MODEL_ID") ?? "aihub-unified-v1";
var sharedMlProfile = Environment.GetEnvironmentVariable("AIHUB_SHARED_ML_PROFILE") ?? "global-learning";

bool Authorized(HttpContext context)
{
    if (string.IsNullOrWhiteSpace(gatewayKey))
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

app.MapGet("/health", async (IHttpClientFactory factory, HttpContext context) =>
{
    if (!Authorized(context))
        return Results.Unauthorized();
    using var client = factory.CreateClient("hermes");
    AttachBackendKey(client);
    using var response = await client.GetAsync($"{backendUrl}/health");
    var body = await response.Content.ReadAsStringAsync();
    return Results.Content(body, "application/json", statusCode: (int)response.StatusCode);
});

app.MapGet("/snapshot", async (IHttpClientFactory factory, HttpContext context) =>
{
    if (!Authorized(context))
        return Results.Unauthorized();
    using var client = factory.CreateClient("hermes");
    AttachBackendKey(client);
    using var response = await client.GetAsync($"{backendUrl}/snapshot");
    var body = await response.Content.ReadAsStringAsync();
    return Results.Content(body, "application/json", statusCode: (int)response.StatusCode);
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
        security = new
        {
            gateway_key_enabled = !string.IsNullOrWhiteSpace(gatewayKey),
            backend_api_key_enabled = !string.IsNullOrWhiteSpace(backendApiKey)
        }
    });
});

app.MapPost("/simulate", async (IHttpClientFactory factory, SimulateRequest request, HttpContext context) =>
{
    if (!Authorized(context))
        return Results.Unauthorized();
    using var client = factory.CreateClient("hermes");
    AttachBackendKey(client);
    using var response = await client.PostAsJsonAsync(
        $"{backendUrl}/simulate",
        new { steps = request.Steps, specialty = request.Specialty });
    var body = await response.Content.ReadAsStringAsync();
    return Results.Content(body, "application/json", statusCode: (int)response.StatusCode);
});

app.MapPost("/learning-pulse", async (IHttpClientFactory factory, LearningPulseRequest request, HttpContext context) =>
{
    if (!Authorized(context))
        return Results.Unauthorized();
    using var client = factory.CreateClient("hermes");
    AttachBackendKey(client);
    using var response = await client.PostAsJsonAsync(
        $"{backendUrl}/learning-pulse",
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
    var body = await response.Content.ReadAsStringAsync();
    return Results.Content(body, "application/json", statusCode: (int)response.StatusCode);
});

app.MapPost("/optimize-fleet", async (IHttpClientFactory factory, OptimizeFleetRequest request, HttpContext context) =>
{
    if (!Authorized(context))
        return Results.Unauthorized();
    using var client = factory.CreateClient("hermes");
    AttachBackendKey(client);
    using var response = await client.PostAsJsonAsync(
        $"{backendUrl}/optimize-fleet",
        new { specialty = request.Specialty, candidates = request.Candidates });
    var body = await response.Content.ReadAsStringAsync();
    return Results.Content(body, "application/json", statusCode: (int)response.StatusCode);
});

app.MapPost("/curate-learning", async (IHttpClientFactory factory, CurateLearningRequest request, HttpContext context) =>
{
    if (!Authorized(context))
        return Results.Unauthorized();
    using var client = factory.CreateClient("hermes");
    AttachBackendKey(client);
    using var response = await client.PostAsJsonAsync(
        $"{backendUrl}/curate-learning",
        new
        {
            sql_signal = request.SqlSignal,
            internet_signal = request.InternetSignal,
            llm_signal = request.LlmSignal,
            stability_bias = request.StabilityBias,
        });
    var body = await response.Content.ReadAsStringAsync();
    return Results.Content(body, "application/json", statusCode: (int)response.StatusCode);
});

app.MapPost("/dedupe-optimize", async (IHttpClientFactory factory, DedupeRequest request, HttpContext context) =>
{
    if (!Authorized(context))
        return Results.Unauthorized();
    using var client = factory.CreateClient("hermes");
    AttachBackendKey(client);
    using var response = await client.PostAsJsonAsync(
        $"{backendUrl}/dedupe-optimize",
        new { roots = request.Roots, max_file_mb = request.MaxFileMb });
    var body = await response.Content.ReadAsStringAsync();
    return Results.Content(body, "application/json", statusCode: (int)response.StatusCode);
});

app.MapGet("/aihub-bonus", async (IHttpClientFactory factory, HttpContext context) =>
{
    if (!Authorized(context))
        return Results.Unauthorized();
    using var client = factory.CreateClient("hermes");
    AttachBackendKey(client);
    using var response = await client.GetAsync($"{backendUrl}/aihub-bonus");
    var body = await response.Content.ReadAsStringAsync();
    return Results.Content(body, "application/json", statusCode: (int)response.StatusCode);
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
public sealed record DedupeRequest(string[] Roots, int MaxFileMb = 8);
