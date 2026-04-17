# Per-User Optimization System (HELIOS Phase 1 Task 1.10a)

## Overview

The Per-User Optimization System is a comprehensive framework for optimizing Windows systems based on user workload profiles. It provides three built-in profiles (Gaming, SysOps, Developer) with one-click switching, auto-detection, custom profile creation, and persistent settings management.

## Architecture

### Core Components

```
OptimizationSystem/
├── OptimizationModels.cs          # Data models and settings structures
├── OptimizationEngine.cs          # Core optimization logic and profile management
├── ProfilePersistenceManager.cs   # File-based profile persistence
├── ProfileUI.cs                   # UI components and dashboard
├── OptimizationOrchestrator.cs    # High-level orchestration
└── OptimizationSystemTests.cs     # Comprehensive test suite
```

## Profiles

### 1. Gaming Profile
Optimized for maximum gaming performance with GPU acceleration and low-latency networking.

**Features:**
- GPU driver updates and optimization (DirectX, Vulkan)
- CPU affinity and frequency scaling
- Memory prioritization with texture caching
- Network latency optimization with packet prioritization
- FPS counter, thermal monitoring, and fan curve profiles

**Key Settings:**
```csharp
GPU:
  - VRAM Allocation: 90%
  - GPU Priority: Maximum
  - Driver Updates: Automatic

CPU:
  - Power Plan: High Performance
  - Max Frequency: 100%
  - Frequency Scaling: Optimized

Network:
  - Latency Optimization: Enabled
  - DNS: 1.1.1.1
  - Buffer Size: 131KB
```

### 2. SysOps Profile
Focused on system reliability, uptime, and operational stability.

**Features:**
- Critical service prioritization
- Automatic backup scheduling
- Health monitoring with configurable intervals
- Auto-recovery with failover
- Memory persistence and paging optimization

**Key Settings:**
```csharp
Service:
  - Critical Service Priority: Enabled
  - Memory Reservation: 25%
  - Background Task Scheduling: Enabled

Reliability:
  - Auto Backup: Daily
  - Retention: 30 days
  - Health Checks: Every 5 minutes

Uptime:
  - Auto Recovery: Enabled
  - Max Restart Attempts: 5
  - Heartbeat Monitoring: Enabled
```

### 3. Developer Profile
Optimized for rapid development, compilation, and IDE performance.

**Features:**
- Parallel build optimization
- IDE integration (VS Code, Visual Studio)
- IntelliSense optimization
- Hot reload support (XAML, CSS, JS)
- Incremental builds and cache warming

**Key Settings:**
```csharp
Build:
  - Parallel Threads: CPU count - 1
  - Cache Warming: Enabled
  - Incremental Builds: Enabled

IDE:
  - IntelliSense Update: 300ms
  - Code Analysis: Enabled
  - Debug Tools: Configured

HotReload:
  - XAML Hot Reload: Enabled
  - CSS/JS Auto Refresh: Enabled
  - Live Preview: Enabled
```

## Usage

### Basic Initialization

```csharp
// Create orchestrator
var orchestrator = new OptimizationOrchestrator();

// Initialize system
await orchestrator.InitializeAsync();

// Get available profiles
var profiles = orchestrator.GetAvailableProfiles();
foreach (var profile in profiles)
{
    Console.WriteLine($"{profile.Name}: {profile.Description}");
}
```

### Applying Profiles

```csharp
// Apply a specific profile
var profileId = profiles[0].Id;
var result = await orchestrator.ApplyProfileAsync(profileId);

if (result.Success)
{
    Console.WriteLine($"Profile applied successfully");
    foreach (var setting in result.AppliedSettings)
    {
        Console.WriteLine($"  ✓ {setting}");
    }
}
```

### Auto-Optimization

```csharp
// Detect optimal profile for current workload
var analysis = orchestrator.AnalyzeWorkload();
Console.WriteLine($"Suggested Profile: {analysis.SuggestedProfile}");
Console.WriteLine($"Gaming Score: {analysis.GamingScore}");
Console.WriteLine($"SysOps Score: {analysis.SysOpsScore}");
Console.WriteLine($"Developer Score: {analysis.DeveloperScore}");

// Automatically apply optimal profile
var result = await orchestrator.AutoOptimizeAsync();
```

### Creating Custom Profiles

```csharp
// Create a custom profile based on Gaming profile
var customProfile = await orchestrator.CreateCustomProfileAsync(
    name: "My Gaming Config",
    description: "Custom gaming profile for RTX 4090",
    baseType: OptimizationProfileType.Gaming);

// Customize settings
if (customProfile is GamingProfileSettings gaming)
{
    gaming.GPU.VRAMAllocationPercent = 95;
    gaming.Network.PreferredDNS = "8.8.8.8";
    
    // Update profile
    await orchestrator.UpdateProfileAsync(gaming);
}
```

### Profile Persistence

```csharp
// Save preferences
var preferences = new Dictionary<string, object>
{
    { "EnableAutoOptimize", true },
    { "UpdateIntervalSeconds", 300 },
    { "LogPerformanceData", true }
};
await orchestrator.SavePreferencesAsync(preferences);

// Load preferences
var loaded = await orchestrator.LoadPreferencesAsync();

// Export profile for sharing
await orchestrator.ExportProfileAsync(profileId, "C:\\my_gaming_profile.json");

// Import profile from file
var imported = await orchestrator.ImportProfileAsync("C:\\my_gaming_profile.json");
```

### Performance Monitoring

```csharp
// Update metrics on dashboard
var metrics = new OptimizationMetrics
{
    CPUUsagePercent = GetCPUUsage(),
    MemoryUsagePercent = GetMemoryUsage(),
    GPUUsagePercent = GetGPUUsage(),
    CurrentFPS = GetFPS()
};
orchestrator.UpdateMetrics(metrics);

// Get dashboard status
var status = orchestrator.GetDashboardStatus();
Console.WriteLine($"Health: {status.HealthStatus}");
Console.WriteLine($"CPU Status: {status.CPUStatus}");
Console.WriteLine($"Memory Status: {status.MemoryStatus}");

// Get metrics history
var history = orchestrator.GetMetricsHistory();
var average = orchestrator.GetAverageMetrics();
Console.WriteLine($"Average CPU Usage: {average.CPUUsagePercent}%");
```

### Profile Details

```csharp
// Get detailed profile information
var details = orchestrator.GetProfileDetails(profileId);
Console.WriteLine($"Profile: {details.ProfileName}");
Console.WriteLine($"Type: {details.ProfileType}");

foreach (var group in details.SettingGroups)
{
    Console.WriteLine($"\n{group.Name}:");
    foreach (var setting in group.Settings)
    {
        Console.WriteLine($"  {setting.Key}: {setting.Value}");
    }
}
```

### System Status

```csharp
// Get complete system status
var summary = orchestrator.GetStatusSummary();
Console.WriteLine($"Initialized: {summary.IsInitialized}");
Console.WriteLine($"Active Profile: {summary.ActiveProfile}");
Console.WriteLine($"Health: {summary.DashboardHealth}");
Console.WriteLine($"Profiles Available: {summary.RegisteredProfileCount}");
Console.WriteLine($"CPU Usage: {summary.CurrentCPUUsage}%");
Console.WriteLine($"Memory Usage: {summary.CurrentMemoryUsage}%");
```

## Profile Persistence

Profiles are stored in JSON format in the user's AppData directory:
- **Windows**: `%APPDATA%\HELIOS\Profiles\`
- **Profiles**: `{ProfileName}_{Id}.json`
- **Active Profile**: `active_profile.json`
- **Preferences**: `preferences.json`

## Settings Engine

### Registry Modifications (Safe)
- Power plan management
- Performance settings
- Network optimization values

### Process Management
- CPU affinity configuration
- Priority level adjustment
- Process throttling

### Service Management
- Critical service prioritization
- Background task scheduling
- Auto-recovery setup

### System Configuration
- Power settings
- DNS configuration
- Network QoS settings

## Test Coverage

Comprehensive test suite with 20+ test cases covering:
- Profile initialization and application
- Settings configuration and validation
- Profile persistence (save/load/export/import)
- Workload detection and auto-optimization
- Dashboard metrics and health status
- Custom profile creation and management
- Profile details extraction and display
- Multi-profile handling

Run tests:
```bash
dotnet test src/HELIOS.Platform/Components/Optimization/OptimizationSystemTests.cs
```

## Integration with Monado Engine

The optimization system is integrated into the MonadoEngine component:

```csharp
var monado = new MonadoEngine();
await monado.InitializeAsync();

// Access optimization system
var optimizer = monado.OptimizationSystem;
await optimizer.AutoOptimizeAsync();
```

## Data Files

### Profile File Format
```json
{
  "id": "uuid",
  "name": "Gaming",
  "type": 0,
  "description": "Gaming profile",
  "isActive": true,
  "createdAt": "2024-01-01T00:00:00Z",
  "lastModified": "2024-01-01T00:00:00Z",
  "settings": {}
}
```

### Active Profile File
```json
{
  "ProfileId": "uuid",
  "Timestamp": "2024-01-01T00:00:00Z"
}
```

### Preferences File
```json
{
  "EnableAutoOptimize": true,
  "UpdateIntervalSeconds": 300,
  "LogPerformanceData": true
}
```

## Performance Metrics

### Tracked Metrics
- CPU Usage (%)
- Memory Usage (%)
- GPU Usage (%)
- Disk I/O (%)
- Network Latency (ms)
- Current FPS
- CPU Temperature (°C)
- GPU Temperature (°C)

### Dashboard Features
- Real-time metrics display
- 60-point history tracking
- Average calculations
- Health determination
- Status categorization (Excellent/Normal/Warning/Critical)

## Best Practices

1. **Profile Selection**: Choose profiles based on primary workload
   - Gaming: For games and GPU-intensive applications
   - SysOps: For servers and background services
   - Developer: For IDE and build-heavy development

2. **Custom Profiles**: Create custom profiles for specific hardware
   - Export and import for easy sharing
   - Clone from default profiles as templates

3. **Monitoring**: Enable metrics tracking for:
   - Performance validation
   - Temperature monitoring
   - Identifying optimization opportunities

4. **Preferences**: Set auto-optimization preferences
   - Enable auto-apply for recommended profiles
   - Configure update intervals
   - Control logging verbosity

5. **Backups**: Export profiles regularly
   - Share across machines
   - Maintain version control
   - Create recovery backups

## Troubleshooting

### Profile Won't Apply
- Check system permissions (may require admin rights)
- Verify profile exists and is not read-only
- Check for conflicts with other system optimizations

### Auto-Optimize Selecting Wrong Profile
- Manually run workload analysis
- Check suggested scores for each profile
- Verify current processes are representative

### Performance Not Improving
- Check applied settings in result history
- Monitor metrics before/after
- Adjust custom profile settings
- Enable detailed logging

### File Permission Errors
- Ensure AppData directory is writable
- Check disk space availability
- Verify user has profile directory permissions

## Future Enhancements

- Machine learning for profile suggestions
- Per-application optimization rules
- Remote profile synchronization
- Web-based dashboard
- REST API for profile management
- Profile versioning and rollback
- A/B testing framework for settings
- Hardware-specific preset profiles
