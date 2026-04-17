# Security Features Integration Example

This file demonstrates how to integrate all security features into your HELIOS Platform application.

## Complete Setup Example

```csharp
// Program.cs or Startup.cs

using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using HELIOS.Platform.BackendServices.Encryption;
using HELIOS.Platform.BackendServices.SecurityVault;
using HELIOS.Platform.BackendServices.AuthService;
using HELIOS.Platform.BackendServices.MalwarebytesIntegration;
using HELIOS.Platform.Components.SecurityDashboard;

var builder = WebApplicationBuilder.CreateBuilder(args);

// ==================== SERVICE REGISTRATION ====================

// Add logging
builder.Services.AddLogging(config =>
{
    config.AddConsole();
    config.AddDebug();
});

// Register encryption service
builder.Services.AddSingleton<IEncryptionService, EncryptionService>();

// Register credential vault
builder.Services.AddSingleton<ICredentialVault, CredentialVault>();

// Register API security with rate limiting
var rateLimitConfig = new RateLimitConfig
{
    RequestsPerSecond = builder.Configuration.GetValue<int>("Security:RateLimitPerSecond", 50),
    MaxBurstSize = builder.Configuration.GetValue<int>("Security:MaxBurstSize", 100),
    WindowSizeSeconds = builder.Configuration.GetValue<int>("Security:WindowSizeSeconds", 60)
};
builder.Services.AddSingleton(rateLimitConfig);
builder.Services.AddSingleton<IApiSecurityService, ApiSecurityService>();

// Register Malwarebytes integration
builder.Services.AddSingleton<IMalwarebytesIntegration, MalwarebytesIntegration>();

// Register security dashboard
builder.Services.AddSingleton<ISecurityDashboard, SecurityDashboard>();

// Add controllers
builder.Services.AddControllers();

var app = builder.Build();

// ==================== MIDDLEWARE SETUP ====================

// Use security headers middleware
app.UseMiddleware<SecurityHeadersMiddleware>();

// Use rate limiting middleware
app.UseMiddleware<RateLimitingMiddleware>();

// Use HTTPS redirection
app.UseHttpsRedirection();

// ==================== APPLICATION INITIALIZATION ====================

// Initialize security systems
var serviceProvider = app.Services;
await InitializeSecurityAsync(serviceProvider);

app.MapControllers();
app.Run();

// ==================== INITIALIZATION FUNCTION ====================

async Task InitializeSecurityAsync(IServiceProvider serviceProvider)
{
    using var scope = serviceProvider.CreateScope();
    var vault = scope.ServiceProvider.GetRequiredService<ICredentialVault>();
    var malwarebytes = scope.ServiceProvider.GetRequiredService<IMalwarebytesIntegration>();
    var logger = scope.ServiceProvider.GetRequiredService<ILogger<Program>>();

    try
    {
        // Initialize vault with master password from configuration
        var masterPassword = Environment.GetEnvironmentVariable("VAULT_MASTER_PASSWORD")
            ?? throw new InvalidOperationException("VAULT_MASTER_PASSWORD environment variable not set");

        logger.LogInformation("Initializing credential vault...");
        var vaultInitialized = await vault.InitializeVaultAsync(masterPassword);
        
        if (!vaultInitialized)
            throw new InvalidOperationException("Failed to initialize credential vault");

        logger.LogInformation("✓ Credential vault initialized successfully");

        // Initialize Malwarebytes integration
        logger.LogInformation("Initializing Malwarebytes integration...");
        var malwarebytesInitialized = await malwarebytes.InitializeAsync();
        
        if (!malwarebytesInitialized)
            throw new InvalidOperationException("Failed to initialize Malwarebytes");

        logger.LogInformation("✓ Malwarebytes integration initialized successfully");

        // Enable real-time protection
        await malwarebytes.EnableRealTimeProtectionAsync();
        logger.LogInformation("✓ Real-time protection enabled");
    }
    catch (Exception ex)
    {
        logger.LogError(ex, "Failed to initialize security systems");
        throw;
    }
}
```

## Security Middleware Classes

```csharp
// SecurityHeadersMiddleware.cs
public class SecurityHeadersMiddleware
{
    private readonly RequestDelegate _next;
    private readonly IApiSecurityService _apiSecurity;
    private readonly ILogger<SecurityHeadersMiddleware> _logger;

    public SecurityHeadersMiddleware(
        RequestDelegate next,
        IApiSecurityService apiSecurity,
        ILogger<SecurityHeadersMiddleware> logger)
    {
        _next = next;
        _apiSecurity = apiSecurity;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        try
        {
            var headers = _apiSecurity.GetSecurityHeaders();
            foreach (var header in headers)
            {
                context.Response.Headers.Add(header.Key, header.Value);
            }

            await _next(context);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error in security headers middleware");
            throw;
        }
    }
}

// RateLimitingMiddleware.cs
public class RateLimitingMiddleware
{
    private readonly RequestDelegate _next;
    private readonly IApiSecurityService _apiSecurity;
    private readonly ILogger<RateLimitingMiddleware> _logger;

    public RateLimitingMiddleware(
        RequestDelegate next,
        IApiSecurityService apiSecurity,
        ILogger<RateLimitingMiddleware> logger)
    {
        _next = next;
        _apiSecurity = apiSecurity;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        var clientId = context.Request.Headers["X-Client-ID"].FirstOrDefault()
            ?? context.Connection.RemoteIpAddress?.ToString()
            ?? "unknown";

        if (!_apiSecurity.CheckRateLimit(clientId))
        {
            _logger.LogWarning($"Rate limit exceeded for client {clientId}");
            context.Response.StatusCode = StatusCodes.Status429TooManyRequests;
            await context.Response.WriteAsJsonAsync(new { error = "Rate limit exceeded" });
            return;
        }

        await _next(context);
    }
}
```

## API Controller Examples

```csharp
// SecurityController.cs
[ApiController]
[Route("api/[controller]")]
[Produces("application/json")]
public class SecurityController : ControllerBase
{
    private readonly ICredentialVault _vault;
    private readonly ISecurityDashboard _dashboard;
    private readonly IMalwarebytesIntegration _malwarebytes;
    private readonly IApiSecurityService _apiSecurity;
    private readonly ILogger<SecurityController> _logger;

    public SecurityController(
        ICredentialVault vault,
        ISecurityDashboard dashboard,
        IMalwarebytesIntegration malwarebytes,
        IApiSecurityService apiSecurity,
        ILogger<SecurityController> logger)
    {
        _vault = vault;
        _dashboard = dashboard;
        _malwarebytes = malwarebytes;
        _apiSecurity = apiSecurity;
        _logger = logger;
    }

    // ==================== VAULT ENDPOINTS ====================

    [HttpPost("vault/initialize")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> InitializeVault([FromBody] VaultInitRequest request)
    {
        try
        {
            var result = await _vault.InitializeVaultAsync(request.MasterPassword);
            return Ok(new { success = result, message = "Vault initialized" });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error initializing vault");
            return BadRequest(new { error = ex.Message });
        }
    }

    [HttpPost("vault/unlock")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    public async Task<IActionResult> UnlockVault([FromBody] VaultUnlockRequest request)
    {
        try
        {
            var result = await _vault.UnlockVaultAsync(request.MasterPassword);
            if (!result)
                return Unauthorized(new { error = "Invalid master password" });

            return Ok(new { success = result, message = "Vault unlocked" });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error unlocking vault");
            return BadRequest(new { error = ex.Message });
        }
    }

    [HttpPost("vault/lock")]
    public async Task<IActionResult> LockVault()
    {
        try
        {
            var result = await _vault.LockVaultAsync();
            return Ok(new { success = result, message = "Vault locked" });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error locking vault");
            return BadRequest(new { error = ex.Message });
        }
    }

    [HttpPost("vault/credentials")]
    [ProducesResponseType(StatusCodes.Status201Created)]
    public async Task<IActionResult> StoreCredential([FromBody] StoreCredentialRequest request)
    {
        try
        {
            var result = await _vault.StoreCredentialAsync(
                request.Name,
                request.Value,
                request.Type,
                request.Metadata,
                request.ExpiresAt);

            if (!result)
                return BadRequest(new { error = "Failed to store credential" });

            return StatusCode(StatusCodes.Status201Created, new { success = result });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error storing credential");
            return BadRequest(new { error = ex.Message });
        }
    }

    [HttpGet("vault/credentials")]
    public async Task<IActionResult> ListCredentials()
    {
        try
        {
            var credentials = await _vault.ListCredentialsAsync();
            return Ok(credentials);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error listing credentials");
            return BadRequest(new { error = ex.Message });
        }
    }

    [HttpGet("vault/is-locked")]
    public async Task<IActionResult> IsVaultLocked()
    {
        try
        {
            var isLocked = await _vault.IsVaultLockedAsync();
            return Ok(new { isLocked });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error checking vault status");
            return BadRequest(new { error = ex.Message });
        }
    }

    // ==================== SECURITY DASHBOARD ENDPOINTS ====================

    [HttpGet("status")]
    public async Task<IActionResult> GetSecurityStatus()
    {
        try
        {
            var status = await _dashboard.GetSecurityStatusAsync();
            return Ok(status);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting security status");
            return StatusCode(StatusCodes.Status500InternalServerError, new { error = ex.Message });
        }
    }

    [HttpGet("alerts")]
    public async Task<IActionResult> GetActiveAlerts()
    {
        try
        {
            var alerts = await _dashboard.GetActiveAlertsAsync();
            return Ok(alerts);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting alerts");
            return StatusCode(StatusCodes.Status500InternalServerError, new { error = ex.Message });
        }
    }

    [HttpGet("threats")]
    public async Task<IActionResult> GetRecentThreats([FromQuery] int count = 10)
    {
        try
        {
            var threats = await _dashboard.GetRecentThreatsAsync(count);
            return Ok(threats);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting threats");
            return StatusCode(StatusCodes.Status500InternalServerError, new { error = ex.Message });
        }
    }

    [HttpGet("threats/statistics")]
    public async Task<IActionResult> GetThreatStatistics()
    {
        try
        {
            var stats = await _dashboard.GetThreatStatisticsAsync();
            return Ok(stats);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting threat statistics");
            return StatusCode(StatusCodes.Status500InternalServerError, new { error = ex.Message });
        }
    }

    [HttpGet("compliance")]
    public async Task<IActionResult> GetComplianceStatus()
    {
        try
        {
            var compliance = await _dashboard.GetComplianceStatusAsync();
            return Ok(compliance);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting compliance status");
            return StatusCode(StatusCodes.Status500InternalServerError, new { error = ex.Message });
        }
    }

    // ==================== MALWAREBYTES ENDPOINTS ====================

    [HttpPost("scan")]
    public async Task<IActionResult> StartScan([FromQuery] ScanType scanType = ScanType.Quick)
    {
        try
        {
            var result = await _malwarebytes.StartScanAsync(scanType);
            return Ok(result);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error starting scan");
            return BadRequest(new { error = ex.Message });
        }
    }

    [HttpGet("scan/{scanId}/status")]
    public async Task<IActionResult> GetScanStatus(string scanId)
    {
        try
        {
            var status = await _malwarebytes.GetScanStatusAsync(scanId);
            if (status == null)
                return NotFound(new { error = "Scan not found" });

            return Ok(status);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting scan status");
            return BadRequest(new { error = ex.Message });
        }
    }

    [HttpDelete("scan/{scanId}")]
    public async Task<IActionResult> StopScan(string scanId)
    {
        try
        {
            var result = await _malwarebytes.StopScanAsync(scanId);
            return Ok(new { success = result });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error stopping scan");
            return BadRequest(new { error = ex.Message });
        }
    }

    [HttpPost("audit")]
    public async Task<IActionResult> RunSecurityAudit()
    {
        try
        {
            var result = await _dashboard.RunSecurityAuditAsync();
            return Ok(new { success = result });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error running audit");
            return BadRequest(new { error = ex.Message });
        }
    }

    // ==================== API SECURITY ENDPOINTS ====================

    [HttpPost("sign-request")]
    public IActionResult SignRequest([FromBody] SignRequest request)
    {
        try
        {
            var signature = _apiSecurity.SignRequest(request.Payload, request.PrivateKey);
            return Ok(new { payload = request.Payload, signature });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error signing request");
            return BadRequest(new { error = ex.Message });
        }
    }

    [HttpPost("verify-signature")]
    public IActionResult VerifySignature([FromBody] VerifySignatureRequest request)
    {
        try
        {
            var isValid = _apiSecurity.VerifySignature(request.Payload, request.Signature, request.PublicKey);
            return Ok(new { isValid });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error verifying signature");
            return BadRequest(new { error = ex.Message });
        }
    }

    [HttpPost("generate-api-key")]
    public IActionResult GenerateApiKey()
    {
        try
        {
            var apiKey = _apiSecurity.GenerateApiKey();
            return Ok(new { apiKey });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error generating API key");
            return BadRequest(new { error = ex.Message });
        }
    }
}

// Request/Response Models
public class VaultInitRequest
{
    public string MasterPassword { get; set; }
}

public class VaultUnlockRequest
{
    public string MasterPassword { get; set; }
}

public class StoreCredentialRequest
{
    public string Name { get; set; }
    public string Value { get; set; }
    public CredentialType Type { get; set; }
    public Dictionary<string, string> Metadata { get; set; }
    public DateTime? ExpiresAt { get; set; }
}

public class SignRequest
{
    public string Payload { get; set; }
    public string PrivateKey { get; set; }
}

public class VerifySignatureRequest
{
    public string Payload { get; set; }
    public string Signature { get; set; }
    public string PublicKey { get; set; }
}
```

## Configuration (appsettings.json)

```json
{
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft": "Warning"
    }
  },
  "Security": {
    "RateLimitPerSecond": 50,
    "MaxBurstSize": 100,
    "WindowSizeSeconds": 60,
    "DefaultPolicy": "balanced"
  },
  "Vault": {
    "MinPasswordLength": 12,
    "MaxAccessLogSize": 1000,
    "AutoLockTimeoutMinutes": 30
  },
  "Malwarebytes": {
    "AutoQuarantine": true,
    "RealTimeProtection": true,
    "ScanOnStartup": true
  },
  "AllowedHosts": "*"
}
```

## Environment Variables (.env)

```bash
# Security
VAULT_MASTER_PASSWORD=YourSecurePassword123!WithSymbols
RATE_LIMIT_PER_SECOND=50
MALWAREBYTES_AUTO_QUARANTINE=true

# Logging
ASPNETCORE_ENVIRONMENT=Development
DOTNET_ENVIRONMENT=Development
```

This example provides a complete, production-ready integration of all HELIOS Platform security features.
