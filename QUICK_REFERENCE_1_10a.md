# Per-User Optimization System - Quick Reference Guide

## 📋 Quick Start

### Initialize System
```csharp
var orchestrator = new OptimizationOrchestrator();
await orchestrator.InitializeAsync();
```

### List Available Profiles
```csharp
var profiles = orchestrator.GetAvailableProfiles();
foreach (var p in profiles)
    Console.WriteLine($"{p.Name} - {p.Description}");
```

### Apply Profile
```csharp
var profileId = profiles[0].Id;
var result = await orchestrator.ApplyProfileAsync(profileId);
if (result.Success)
    Console.WriteLine("Profile applied!");
```

## 🎮 Gaming Profile
**When to use:** Playing games, GPU-intensive workloads
```csharp
// Automatically optimizes for:
// - GPU at 90% VRAM utilization
// - High Performance power plan
// - Maximum CPU frequency
// - Low-latency networking
// - FPS monitoring enabled
```

## 🔧 SysOps Profile
**When to use:** Server operations, background services, system stability
```csharp
// Automatically optimizes for:
// - 25% memory reservation
// - Critical service prioritization
// - Daily backups
// - Auto-recovery enabled
// - Health monitoring every 5 minutes
```

## 💻 Developer Profile
**When to use:** Software development, building, coding
```csharp
// Automatically optimizes for:
// - Parallel builds (CPU count - 1 threads)
// - IntelliSense optimization
// - XAML/CSS/JS hot reload
// - Balanced power plan
// - Debug tools configured
```

## 🔍 Auto-Optimize
```csharp
// Detect and apply optimal profile
var result = await orchestrator.AutoOptimizeAsync();
Console.WriteLine($"Applied: {orchestrator.GetActiveProfile().Name}");
```

## 📊 Monitor Performance
```csharp
// Update metrics
orchestrator.UpdateMetrics(new OptimizationMetrics
{
    CPUUsagePercent = 45,
    MemoryUsagePercent = 60,
    GPUUsagePercent = 80
});

// Get dashboard status
var status = orchestrator.GetDashboardStatus();
Console.WriteLine($"Health: {status.HealthStatus}");
Console.WriteLine($"CPU: {status.CPUStatus}");

// Get history
var average = orchestrator.GetAverageMetrics();
Console.WriteLine($"Avg CPU: {average.CPUUsagePercent}%");
```

## 🔨 Create Custom Profile
```csharp
// Create from template
var custom = await orchestrator.CreateCustomProfileAsync(
    name: "My Gaming Config",
    description: "RTX 4090 optimized",
    baseType: OptimizationProfileType.Gaming);

// Customize
if (custom is GamingProfileSettings gaming)
{
    gaming.GPU.VRAMAllocationPercent = 95;
    gaming.Network.PreferredDNS = "8.8.8.8";
    await orchestrator.UpdateProfileAsync(gaming);
}
```

## 💾 Save & Load
```csharp
// Save preferences
await orchestrator.SavePreferencesAsync(new Dictionary<string, object>
{
    { "EnableAutoOptimize", true },
    { "UpdateIntervalSeconds", 300 }
});

// Load preferences
var prefs = await orchestrator.LoadPreferencesAsync();
```

## 📤 Export & Import
```csharp
// Export profile
await orchestrator.ExportProfileAsync(profileId, "my_profile.json");

// Import profile
var imported = await orchestrator.ImportProfileAsync("my_profile.json");
```

## ℹ️ Get Profile Details
```csharp
var details = orchestrator.GetProfileDetails(profileId);
Console.WriteLine($"Profile: {details.ProfileName}");

foreach (var group in details.SettingGroups)
{
    Console.WriteLine($"\n{group.Name}:");
    foreach (var setting in group.Settings)
        Console.WriteLine($"  {setting.Key}: {setting.Value}");
}
```

## 📈 Get System Status
```csharp
var summary = orchestrator.GetStatusSummary();
Console.WriteLine($"Status: {summary.IsInitialized}");
Console.WriteLine($"Active: {summary.ActiveProfile}");
Console.WriteLine($"Health: {summary.DashboardHealth}");
Console.WriteLine($"Profiles: {summary.RegisteredProfileCount}");
Console.WriteLine($"CPU: {summary.CurrentCPUUsage}%");
Console.WriteLine($"Memory: {summary.CurrentMemoryUsage}%");
```

## 🎯 Workload Analysis
```csharp
var analysis = orchestrator.AnalyzeWorkload();
Console.WriteLine($"Suggested: {analysis.SuggestedProfile}");
Console.WriteLine($"Gaming: {analysis.GamingScore}");
Console.WriteLine($"SysOps: {analysis.SysOpsScore}");
Console.WriteLine($"Developer: {analysis.DeveloperScore}");
```

## 📂 File Locations

**Profile Storage:**
```
%APPDATA%\HELIOS\Profiles\
├── Gaming_uuid.json
├── SysOps_uuid.json
├── Developer_uuid.json
├── active_profile.json
└── preferences.json
```

## ⚙️ Common Tasks

### Switch to Gaming Profile
```csharp
var profiles = orchestrator.GetAvailableProfiles();
var gaming = profiles.First(p => p.Type == OptimizationProfileType.Gaming);
await orchestrator.ApplyProfileAsync(gaming.Id);
```

### Delete Custom Profile
```csharp
await orchestrator.DeleteProfileAsync(profileId);
```

### Get Result History
```csharp
var history = orchestrator.GetResultHistory();
foreach (var result in history)
{
    Console.WriteLine($"{result.AppliedAt}: {result.Message}");
}
```

### Get Active Profile Info
```csharp
var active = orchestrator.GetActiveProfile();
if (active != null)
    Console.WriteLine($"Active: {active.Name} ({active.Type})");
```

## 🔑 Key Classes

| Class | Purpose |
|-------|---------|
| `OptimizationOrchestrator` | Main system coordinator |
| `OptimizationEngine` | Profile management and application |
| `ProfilePersistenceManager` | File-based persistence |
| `ProfileSelector` | UI profile selection |
| `PerformanceDashboard` | Metrics tracking |

## 📊 Profile Types

| Type | Best For | Key Feature |
|------|----------|-------------|
| Gaming | Games, GPU work | GPU optimization |
| SysOps | Servers, services | Reliability |
| Developer | Development, builds | Build speed |
| Custom | Specialized needs | Full customization |

## 🎯 Health Status Levels

- **Excellent:** < 40% avg resource usage
- **Normal:** 40-60% avg resource usage
- **Warning:** 60-80% avg resource usage
- **Critical:** > 80% avg resource usage

## ⏱️ Default Intervals

- Health Checks: 300 seconds (5 minutes)
- Metrics Update: 1000ms (1 second)
- IntelliSense Update: 300ms
- Hot Reload: 200ms
- Backup Schedule: Daily
- Backup Retention: 30 days

## 🚀 Performance Tips

1. **Use Auto-Optimize:** Let the system detect the best profile
2. **Monitor Metrics:** Track performance trends
3. **Custom Profiles:** Create profiles for your specific hardware
4. **Regular Exports:** Backup custom profiles regularly
5. **Preference Tuning:** Adjust intervals for your needs

## ❓ Troubleshooting

**Profile won't apply?**
- Check system permissions
- Verify profile ID is valid
- Confirm profile exists

**Auto-optimize wrong profile?**
- Run workload analysis manually
- Check suggested scores
- Verify current processes

**Metrics not updating?**
- Call UpdateMetrics() with fresh data
- Check dashboard status
- Verify metrics values are reasonable

## 📞 Integration

**With MonadoEngine:**
```csharp
var monado = new MonadoEngine();
await monado.InitializeAsync();
var optimizer = monado.OptimizationSystem;
```

## 📝 Code Size

- Total: 85.54 KB
- OptimizationModels: 9.62 KB
- OptimizationEngine: 20.16 KB
- ProfileUI: 18.97 KB
- OptimizationOrchestrator: 11.98 KB
- ProfilePersistence: 9.96 KB
- Tests: 14.85 KB

---

**Version:** 1.0.0  
**Status:** Production Ready  
**Test Coverage:** 20+ comprehensive tests  
**Documentation:** Complete
