# Security Features Configuration Guide

## Quick Start

### 1. Register Services in DependencyInjection

```csharp
// In Program.cs or Startup.cs
using HELIOS.Platform.BackendServices.Encryption;
using HELIOS.Platform.BackendServices.SecurityVault;
using HELIOS.Platform.BackendServices.AuthService;
using HELIOS.Platform.BackendServices.MalwarebytesIntegration;
using HELIOS.Platform.Components.SecurityDashboard;

public void ConfigureServices(IServiceCollection services)
{
    // Encryption
    services.AddSingleton<IEncryptionService, EncryptionService>();
    
    // Vault
    services.AddSingleton<ICredentialVault, CredentialVault>();
    
    // API Security
    var rateLimitConfig = new RateLimitConfig 
    { 
        RequestsPerSecond = 50,
        MaxBurstSize = 100,
        WindowSizeSeconds = 60
    };
    services.AddSingleton(rateLimitConfig);
    services.AddSingleton<IApiSecurityService, ApiSecurityService>();
    
    // Malwarebytes Integration
    services.AddSingleton<IMalwarebytesIntegration, MalwarebytesIntegration>();
    
    // Security Dashboard
    services.AddSingleton<ISecurityDashboard, SecurityDashboard>();
}
```

### 2. Initialize Vault on Application Startup

```csharp
// In application initialization
public async Task InitializeSecurityAsync(IServiceProvider serviceProvider)
{
    var vault = serviceProvider.GetRequiredService<ICredentialVault>();
    var masterPassword = Environment.GetEnvironmentVariable("VAULT_MASTER_PASSWORD");
    
    if (string.IsNullOrEmpty(masterPassword))
    {
        throw new InvalidOperationException("VAULT_MASTER_PASSWORD environment variable not set");
    }
    
    var initialized = await vault.InitializeVaultAsync(masterPassword);
    if (!initialized)
    {
        throw new InvalidOperationException("Failed to initialize credential vault");
    }
}
```

### 3. Configure Environment Variables

```bash
# .env or environment configuration
VAULT_MASTER_PASSWORD=YourSecurePassword123!_With_Symbols

# API Security (optional)
RATE_LIMIT_PER_SECOND=50
RATE_LIMIT_BURST_SIZE=100

# Malwarebytes (optional)
MALWAREBYTES_AUTO_QUARANTINE=true
MALWAREBYTES_REAL_TIME_PROTECTION=true
```

## Credential Vault Usage

### Store API Credentials

```csharp
public class ApiClientService
{
    private readonly ICredentialVault _vault;
    
    public ApiClientService(ICredentialVault vault)
    {
        _vault = vault;
    }
    
    public async Task<string> GetApiKeyAsync(string serviceName)
    {
        var credentials = await _vault.ListCredentialsAsync(CredentialType.ApiKey);
        var apiCredential = credentials.FirstOrDefault(c => c.Name == serviceName);
        
        if (apiCredential == null)
        {
            throw new KeyNotFoundException($"API key for {serviceName} not found");
        }
        
        return await _vault.RetrieveCredentialAsync(apiCredential.Id);
    }
    
    public async Task StoreApiKeyAsync(string serviceName, string apiKey, DateTime? expiresAt = null)
    {
        await _vault.StoreCredentialAsync(
            serviceName,
            apiKey,
            CredentialType.ApiKey,
            new Dictionary<string, string> { { "Service", serviceName } },
            expiresAt);
    }
}
```

### Store Database Passwords

```csharp
public class DatabaseConnectionService
{
    private readonly ICredentialVault _vault;
    
    public DatabaseConnectionService(ICredentialVault vault)
    {
        _vault = vault;
    }
    
    public async Task<string> GetConnectionStringAsync(string database)
    {
        var credential = await GetDatabasePasswordAsync(database);
        return $"Server=db-server;Database={database};User Id=sa;Password={credential};";
    }
    
    private async Task<string> GetDatabasePasswordAsync(string database)
    {
        var credentials = await _vault.ListCredentialsAsync(CredentialType.DatabasePassword);
        var dbCredential = credentials.FirstOrDefault(c => c.Name == database);
        
        if (dbCredential == null)
        {
            throw new KeyNotFoundException($"Database password for {database} not found");
        }
        
        return await _vault.RetrieveCredentialAsync(dbCredential.Id);
    }
}
```

## API Security Configuration

### Implement Rate Limiting Middleware

```csharp
public class RateLimitingMiddleware
{
    private readonly RequestDelegate _next;
    private readonly IApiSecurityService _apiSecurity;
    
    public RateLimitingMiddleware(RequestDelegate next, IApiSecurityService apiSecurity)
    {
        _next = next;
        _apiSecurity = apiSecurity;
    }
    
    public async Task InvokeAsync(HttpContext context)
    {
        var clientId = context.Request.Headers["X-Client-ID"].FirstOrDefault() 
            ?? context.Connection.RemoteIpAddress?.ToString() 
            ?? "unknown";
        
        if (!_apiSecurity.CheckRateLimit(clientId))
        {
            context.Response.StatusCode = StatusCodes.Status429TooManyRequests;
            await context.Response.WriteAsJsonAsync(new { error = "Rate limit exceeded" });
            return;
        }
        
        await _next(context);
    }
}

// Register in Startup
public void Configure(IApplicationBuilder app)
{
    app.UseMiddleware<RateLimitingMiddleware>();
    // ... other middleware
}
```

### Add Security Headers

```csharp
public class SecurityHeadersMiddleware
{
    private readonly RequestDelegate _next;
    private readonly IApiSecurityService _apiSecurity;
    
    public SecurityHeadersMiddleware(RequestDelegate next, IApiSecurityService apiSecurity)
    {
        _next = next;
        _apiSecurity = apiSecurity;
    }
    
    public async Task InvokeAsync(HttpContext context)
    {
        var headers = _apiSecurity.GetSecurityHeaders();
        foreach (var header in headers)
        {
            context.Response.Headers.Add(header.Key, header.Value);
        }
        
        await _next(context);
    }
}
```

### Implement Request Signing

```csharp
[ApiController]
[Route("api/[controller]")]
public class SecureApiController : ControllerBase
{
    private readonly IApiSecurityService _apiSecurity;
    private readonly string _apiSecret = "your-api-secret-key"; // From config
    
    public SecureApiController(IApiSecurityService apiSecurity)
    {
        _apiSecurity = apiSecurity;
    }
    
    [HttpPost("validate-signature")]
    public IActionResult ValidateSignature([FromBody] SignedRequest request)
    {
        var isValid = _apiSecurity.VerifySignature(
            request.Payload, 
            request.Signature, 
            _apiSecret);
        
        if (!isValid)
        {
            return Unauthorized(new { error = "Invalid signature" });
        }
        
        return Ok(new { message = "Signature verified" });
    }
    
    [HttpPost("sign-request")]
    public IActionResult SignRequest([FromBody] string payload)
    {
        var signature = _apiSecurity.SignRequest(payload, _apiSecret);
        return Ok(new { payload, signature });
    }
}

public class SignedRequest
{
    public string Payload { get; set; }
    public string Signature { get; set; }
}
```

## Malwarebytes Integration

### Scheduled Scans

```csharp
public class ScanSchedulerService : BackgroundService
{
    private readonly IMalwarebytesIntegration _malwarebytes;
    private readonly ILogger<ScanSchedulerService> _logger;
    
    public ScanSchedulerService(IMalwarebytesIntegration malwarebytes, 
        ILogger<ScanSchedulerService> logger)
    {
        _malwarebytes = malwarebytes;
        _logger = logger;
    }
    
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        // Schedule quick scan every night at 2 AM
        await _malwarebytes.ScheduleScanAsync("0 2 * * *", ScanType.Quick);
        
        // Schedule full scan every Sunday at 3 AM
        await _malwarebytes.ScheduleScanAsync("0 3 * * 0", ScanType.Full);
        
        _logger.LogInformation("Scan schedules configured");
        
        await Task.Delay(Timeout.Infinite, stoppingToken);
    }
}

// Register in Startup
public void ConfigureServices(IServiceCollection services)
{
    services.AddHostedService<ScanSchedulerService>();
}
```

### Threat Monitoring

```csharp
[ApiController]
[Route("api/[controller]")]
public class ThreatMonitoringController : ControllerBase
{
    private readonly ISecurityDashboard _dashboard;
    private readonly IMalwarebytesIntegration _malwarebytes;
    
    public ThreatMonitoringController(ISecurityDashboard dashboard, 
        IMalwarebytesIntegration malwarebytes)
    {
        _dashboard = dashboard;
        _malwarebytes = malwarebytes;
    }
    
    [HttpGet("status")]
    public async Task<IActionResult> GetSecurityStatus()
    {
        var status = await _dashboard.GetSecurityStatusAsync();
        return Ok(status);
    }
    
    [HttpGet("threats")]
    public async Task<IActionResult> GetRecentThreats([FromQuery] int count = 10)
    {
        var threats = await _dashboard.GetRecentThreatsAsync(count);
        return Ok(threats);
    }
    
    [HttpGet("alerts")]
    public async Task<IActionResult> GetActiveAlerts()
    {
        var alerts = await _dashboard.GetActiveAlertsAsync();
        return Ok(alerts);
    }
    
    [HttpPost("scan")]
    public async Task<IActionResult> StartScan([FromQuery] ScanType scanType = ScanType.Quick)
    {
        var result = await _malwarebytes.StartScanAsync(scanType);
        return Ok(result);
    }
    
    [HttpGet("scan/{scanId}/status")]
    public async Task<IActionResult> GetScanStatus(string scanId)
    {
        var status = await _malwarebytes.GetScanStatusAsync(scanId);
        return Ok(status);
    }
    
    [HttpPost("audit")]
    public async Task<IActionResult> RunSecurityAudit()
    {
        var result = await _dashboard.RunSecurityAuditAsync();
        return Ok(new { success = result });
    }
    
    [HttpGet("compliance")]
    public async Task<IActionResult> GetComplianceStatus()
    {
        var compliance = await _dashboard.GetComplianceStatusAsync();
        return Ok(compliance);
    }
}
```

## Security Policy Implementation

```csharp
public class SecurityPolicyService
{
    private readonly ISecurityDashboard _dashboard;
    private readonly IConfiguration _configuration;
    
    public SecurityPolicyService(ISecurityDashboard dashboard, IConfiguration configuration)
    {
        _dashboard = dashboard;
        _configuration = configuration;
    }
    
    public async Task ApplyDefaultPolicyAsync()
    {
        var policy = _configuration["Security:DefaultPolicy"] ?? "balanced";
        await _dashboard.ApplySecurityPolicyAsync(policy);
    }
    
    public async Task<bool> VerifyComplianceAsync()
    {
        var compliance = await _dashboard.GetComplianceStatusAsync();
        return compliance.Values.All(v => v); // All checks pass
    }
}

// Register in Startup
public void ConfigureServices(IServiceCollection services)
{
    services.AddSingleton<SecurityPolicyService>();
}
```

## Configuration File Example

```json
{
  "Security": {
    "Vault": {
      "MinPasswordLength": 12,
      "MaxAccessLogSize": 1000,
      "AutoLockTimeoutMinutes": 30
    },
    "ApiSecurity": {
      "RateLimitPerSecond": 50,
      "MaxBurstSize": 100,
      "WindowSizeSeconds": 60
    },
    "Malwarebytes": {
      "AutoQuarantine": true,
      "RealTimeProtection": true,
      "ScanOnStartup": true,
      "QuickScanSchedule": "0 2 * * *",
      "FullScanSchedule": "0 3 * * 0"
    },
    "DefaultPolicy": "balanced"
  }
}
```

## Error Handling

```csharp
public static class SecurityExceptionHandler
{
    public static IActionResult HandleSecurityException(Exception ex, ILogger logger)
    {
        logger.LogError(ex, "Security operation failed");
        
        return ex switch
        {
            ArgumentNullException => new BadRequestObjectResult(
                new { error = "Required security parameter missing" }),
            InvalidOperationException => new BadRequestObjectResult(
                new { error = "Security operation invalid in current state" }),
            KeyNotFoundException => new NotFoundObjectResult(
                new { error = "Credential or resource not found" }),
            UnauthorizedAccessException => new UnauthorizedObjectResult(
                new { error = "Unauthorized access" }),
            _ => new ObjectResult(new { error = "Security operation failed" })
            {
                StatusCode = StatusCodes.Status500InternalServerError
            }
        };
    }
}
```

## Testing Configuration

```csharp
public static class SecurityTestConfiguration
{
    public static IServiceCollection AddTestSecurityServices(this IServiceCollection services)
    {
        services.AddSingleton<IEncryptionService, EncryptionService>();
        services.AddSingleton<ICredentialVault, CredentialVault>();
        
        var testConfig = new RateLimitConfig 
        { 
            RequestsPerSecond = 1000,
            MaxBurstSize = 10000
        };
        
        services.AddSingleton(testConfig);
        services.AddSingleton<IApiSecurityService, ApiSecurityService>();
        services.AddSingleton<IMalwarebytesIntegration, MalwarebytesIntegration>();
        services.AddSingleton<ISecurityDashboard, SecurityDashboard>();
        
        return services;
    }
}
```

## Performance Optimization

### Connection Pooling for Vault
```csharp
// For high-throughput scenarios, consider implementing connection pooling
public class VaultConnectionPool
{
    private readonly Stack<ICredentialVault> _pool;
    private readonly int _maxSize;
    
    public VaultConnectionPool(int maxSize = 10)
    {
        _maxSize = maxSize;
        _pool = new Stack<ICredentialVault>(maxSize);
    }
}
```

### Caching Security Headers
```csharp
public class CachedSecurityHeadersMiddleware
{
    private readonly Dictionary<string, string> _cachedHeaders;
    private readonly IApiSecurityService _apiSecurity;
    
    public CachedSecurityHeadersMiddleware(IApiSecurityService apiSecurity)
    {
        _apiSecurity = apiSecurity;
        _cachedHeaders = _apiSecurity.GetSecurityHeaders();
    }
}
```
