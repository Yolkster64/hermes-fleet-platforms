# HELIOS Platform Cloud & AI Integration - Quick Reference

## Setup in 3 Steps

### Step 1: Add Services to DI Container
```csharp
var services = new ServiceCollection();
services.AddHeliosCloudAndAIServices();
var provider = services.BuildServiceProvider();
```

### Step 2: Initialize Cloud Services
```csharp
var initialized = await provider.InitializeCloudServicesAsync();
```

### Step 3: Use the Services
```csharp
// Get any service
var aiHub = provider.GetRequiredService<IAIHubService>();
var wsl2 = provider.GetRequiredService<IWSL2Service>();
var docker = provider.GetRequiredService<IDockerService>();
```

---

## Common Tasks

### Azure Blob Storage

**Upload file:**
```csharp
var blob = provider.GetRequiredService<IAzureBlobStorageClient>();
await blob.CreateContainerAsync("my-container");
await blob.UploadBlobAsync("my-container", "file.txt", fileStream);
```

**Download file:**
```csharp
var content = await blob.DownloadBlobAsync("my-container", "file.txt");
```

**List files:**
```csharp
var files = await blob.ListBlobsAsync("my-container");
```

### Azure SQL Database

**Execute query:**
```csharp
var sql = provider.GetRequiredService<IAzureSqlDatabaseClient>();
var result = await sql.ExecuteQueryAsync("SELECT * FROM Users");
```

**Execute command:**
```csharp
await sql.ExecuteCommandAsync(
    "UPDATE Users SET Active = 1 WHERE Id = @id",
    new SqlParameter("@id", 123)
);
```

### Azure Key Vault

**Get secret:**
```csharp
var vault = provider.GetRequiredService<IAzureKeyVaultClient>();
var connectionString = await vault.GetSecretAsync("ConnectionString");
```

**Set secret:**
```csharp
await vault.SetSecretAsync("MySecret", "secret-value");
```

### AI Hub

**Discover models:**
```csharp
var aiHub = provider.GetRequiredService<IAIHubService>();
var models = await aiHub.DiscoverModelsAsync();
```

**Run inference:**
```csharp
var result = await aiHub.RunInferenceAsync("model-id", "Your prompt");
Console.WriteLine(result.Output);
```

**Get metrics:**
```csharp
var metrics = await aiHub.GetPerformanceMetricsAsync("model-id");
```

### WSL2

**List distributions:**
```csharp
var wsl2 = provider.GetRequiredService<IWSL2Service>();
var distros = await wsl2.ListDistrosAsync();
```

**Run command:**
```csharp
var output = await wsl2.RunCommandAsync("Ubuntu", "ls -la");
```

### Docker

**Check if installed:**
```csharp
var docker = provider.GetRequiredService<IDockerService>();
bool installed = await docker.IsDockerInstalledAsync();
```

**Run container:**
```csharp
var containerId = await docker.RunContainerAsync(
    "nginx:latest", 
    "web-server",
    new[] { "80:80" }
);
```

**Stop container:**
```csharp
await docker.StopContainerAsync(containerId);
```

**Get logs:**
```csharp
var logs = await docker.GetLogsAsync(containerId, 50);
```

---

## Configuration

### Using appsettings.json

```json
{
  "Azure": {
    "TenantId": "your-tenant-id",
    "SubscriptionId": "your-subscription-id",
    "StorageAccountName": "yourstorage",
    "KeyVaultUri": "https://keyvault.vault.azure.net/"
  }
}
```

### Programmatic Configuration

```csharp
var config = new CloudConfigurationBuilder()
    .WithTenantId("tenant-id")
    .WithSubscriptionId("sub-id")
    .WithStorageAccount("account", "key")
    .WithKeyVault("https://vault.vault.azure.net/")
    .Build();
```

---

## Error Handling

All services return `null` or `false` on error and log the issue:

```csharp
var result = await aiHub.RunInferenceAsync("model-id", "prompt");
if (result == null)
{
    // Check logs for error details
}

bool success = await docker.IsDockerInstalledAsync();
if (!success)
{
    // Check logs for error details
}
```

---

## Health Checks

Get service health status:

```csharp
var factory = provider.GetRequiredService<IAzureServiceFactory>();
var health = await factory.GetHealthStatusAsync();

foreach (var (service, status) in health)
{
    Console.WriteLine($"{service}: {(status.IsHealthy ? "✓" : "✗")}");
    Console.WriteLine($"  Response Time: {status.ResponseTimeMs}ms");
}
```

---

## Logging

Enable logging to see detailed operation traces:

```csharp
services.AddLogging(builder =>
{
    builder.AddConsole();
    builder.SetMinimumLevel(LogLevel.Information);
});
```

Log output example:
```
Azure Identity Provider: Device flow authentication successful
Azure Credential Manager: Credential stored: default (expires at ...)
Azure Service Factory: Service created and cached: AzureBlobStorageClient
Docker Service: Docker detected
WSL2 Service: WSL2 detected
AI Hub Service: Discovered 3 AI models
```

---

## Common Issues

### Azure Authentication Fails
- Ensure you have Azure credentials set up
- Check tenant ID and subscription ID
- Verify Azure SDK version compatibility

### Docker Not Found
- Docker might not be installed
- Docker Desktop might not be running
- Check that docker.exe is in PATH

### WSL2 Not Detected
- WSL2 might not be installed
- Windows Home edition might not support it
- Hyper-V might not be enabled

---

## API Reference

### IAzureIdentityProvider
- `GetDeviceFlowCredentialAsync()` - Interactive user auth
- `GetInteractiveCredentialAsync()` - Browser-based auth
- `GetServicePrincipalCredentialAsync(tenantId, clientId, secret)` - Automation
- `GetDefaultCredentialAsync()` - Auto-detect best method
- `GetCurrentIdentityAsync()` - Get current user/app

### IAzureCredentialManager
- `StoreCredentialAsync(key, credential, expiry)` - Cache credential
- `GetCredentialAsync(key)` - Get cached credential
- `RemoveCredentialAsync(key)` - Remove credential
- `ClearAllAsync()` - Clear all cache
- `GetCredentialInfoAsync(key)` - Get cache entry info

### IAzureServiceFactory
- `GetServiceAsync<T>(name)` - Get or create service
- `RegisterService<T>(factory)` - Register service
- `InitializeAllServicesAsync(credential)` - Init all
- `GetRegisteredServices()` - List services
- `GetHealthStatusAsync()` - Health check

### IAzureBlobStorageClient
- `UploadBlobAsync(container, name, content, overwrite)` - Upload
- `DownloadBlobAsync(container, name)` - Download
- `DeleteBlobAsync(container, name)` - Delete
- `ListBlobsAsync(container, prefix)` - List
- `CreateContainerAsync(name)` - Create container
- `DeleteContainerAsync(name)` - Delete container
- `BlobExistsAsync(container, name)` - Check existence
- `GetBlobPropertiesAsync(container, name)` - Get properties

### IAIHubService
- `IsAIHubInstalledAsync()` - Check installation
- `DiscoverModelsAsync()` - Find models
- `RegisterModelAsync(model)` - Register model
- `DeployModelAsync(modelId)` - Deploy model
- `RunInferenceAsync(modelId, prompt)` - Run inference
- `GetPerformanceMetricsAsync(modelId)` - Get metrics
- `CacheModelAsync(modelId, path)` - Cache model

### IWSL2Service
- `IsWSL2InstalledAsync()` - Check installation
- `ListDistrosAsync()` - List distributions
- `GetDistroAsync(name)` - Get distro info
- `InstallDistroAsync(name, imagePath)` - Install
- `RemoveDistroAsync(name)` - Remove
- `StartDistroAsync(name)` - Start
- `StopDistroAsync(name)` - Stop
- `RunCommandAsync(distroName, command)` - Execute
- `GetConfigAsync()` - Get configuration
- `SetConfigAsync(options)` - Set configuration

### IDockerService
- `IsDockerInstalledAsync()` - Check installation
- `GetVersionAsync()` - Get version
- `ListContainersAsync(all)` - List containers
- `GetContainerAsync(id)` - Get container info
- `RunContainerAsync(image, name, ports)` - Run
- `StopContainerAsync(id)` - Stop
- `RemoveContainerAsync(id)` - Remove
- `ListImagesAsync()` - List images
- `PullImageAsync(repo, tag)` - Pull image
- `RemoveImageAsync(imageId)` - Remove image
- `ExecCommandAsync(id, command)` - Execute
- `GetLogsAsync(id, lines)` - Get logs

---

## Performance Tips

1. **Cache Services**: Services are singletons, reuse instances
2. **Batch Operations**: Group multiple operations in loops
3. **Async**: Use async/await to prevent blocking
4. **Health Checks**: Use sparingly, don't call in tight loops
5. **Connection Strings**: Cache connection strings, not credentials

---

## Support & Troubleshooting

Check logs for detailed error information:
- Service initialization failures
- Authentication issues
- Connection problems
- Operation details

All operations log at minimum INFO level.

