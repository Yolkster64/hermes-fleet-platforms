using System;
using System.Collections.Generic;

namespace HELIOS.Platform.Components.Optimization
{
    /// <summary>
    /// Enumeration of available optimization profiles.
    /// </summary>
    public enum OptimizationProfileType
    {
        Gaming,
        SysOps,
        Developer,
        Custom
    }

    /// <summary>
    /// Represents the state of a system optimization profile.
    /// </summary>
    public class OptimizationProfile
    {
        public string Id { get; set; } = Guid.NewGuid().ToString();
        public string Name { get; set; }
        public OptimizationProfileType Type { get; set; }
        public string Description { get; set; }
        public bool IsActive { get; set; }
        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
        public DateTime LastModified { get; set; } = DateTime.UtcNow;
        public Dictionary<string, object> Settings { get; set; } = new();
        public bool IsReadOnly { get; set; }
    }

    /// <summary>
    /// GPU optimization settings.
    /// </summary>
    public class GPUOptimizationSettings
    {
        public bool EnableDriverUpdates { get; set; }
        public bool OptimizeDirectX { get; set; }
        public bool OptimizeVulkan { get; set; }
        public bool BoostGPUPriority { get; set; }
        public int VRAMAllocationPercent { get; set; } = 85;
        public string DriverUpdateMode { get; set; } = "automatic";
    }

    /// <summary>
    /// CPU optimization settings.
    /// </summary>
    public class CPUOptimizationSettings
    {
        public bool EnableCPUAffinity { get; set; }
        public bool EnableRealTimePriority { get; set; }
        public bool OptimizeFrequencyScaling { get; set; }
        public string PowerPlan { get; set; } = "High Performance";
        public int ProcessAffinity { get; set; } = -1;
        public int MaxCPUFrequencyPercent { get; set; } = 100;
    }

    /// <summary>
    /// Memory optimization settings.
    /// </summary>
    public class MemoryOptimizationSettings
    {
        public bool EnableMemoryPrioritization { get; set; }
        public bool OptimizePageFile { get; set; }
        public bool OptimizeTextureCache { get; set; }
        public int MinimumAvailableMemoryMB { get; set; } = 512;
        public int CacheSizePercent { get; set; } = 25;
        public int PageFileMultiplier { get; set; } = 2;
    }

    /// <summary>
    /// Network optimization settings.
    /// </summary>
    public class NetworkOptimizationSettings
    {
        public bool OptimizeLatency { get; set; }
        public bool EnablePacketPrioritization { get; set; }
        public bool ConfigureQoS { get; set; }
        public bool OptimizeDNS { get; set; }
        public string PreferredDNS { get; set; } = "1.1.1.1";
        public int BufferSize { get; set; } = 65536;
        public bool EnableTCPOptimization { get; set; }
    }

    /// <summary>
    /// Monitoring and metrics settings.
    /// </summary>
    public class MonitoringSettings
    {
        public bool EnableFPSCounter { get; set; }
        public bool EnableThermalMonitoring { get; set; }
        public bool EnablePerformanceMetrics { get; set; }
        public bool EnableFanCurveProfiles { get; set; }
        public int MetricsUpdateIntervalMs { get; set; } = 1000;
        public bool LogPerformanceData { get; set; }
    }

    /// <summary>
    /// Gaming profile optimization settings.
    /// </summary>
    public class GamingProfileSettings : OptimizationProfile
    {
        public GPUOptimizationSettings GPU { get; set; } = new();
        public CPUOptimizationSettings CPU { get; set; } = new();
        public MemoryOptimizationSettings Memory { get; set; } = new();
        public NetworkOptimizationSettings Network { get; set; } = new();
        public MonitoringSettings Monitoring { get; set; } = new();
    }

    /// <summary>
    /// Service and reliability settings for SysOps profile.
    /// </summary>
    public class ServiceOptimizationSettings
    {
        public bool PrioritizeCriticalServices { get; set; }
        public bool EnableBackgroundTaskScheduling { get; set; }
        public bool ReserveSystemResources { get; set; }
        public int MinimumMemoryReservationPercent { get; set; } = 20;
        public List<string> CriticalServices { get; set; } = new();
    }

    /// <summary>
    /// Reliability and uptime settings for SysOps profile.
    /// </summary>
    public class ReliabilitySettings
    {
        public bool EnableRedundancyChecks { get; set; }
        public bool EnableAutoBackup { get; set; }
        public bool EnableHealthMonitoring { get; set; }
        public int HealthCheckIntervalSeconds { get; set; } = 300;
        public string BackupSchedule { get; set; } = "daily";
        public int BackupRetentionDays { get; set; } = 30;
    }

    /// <summary>
    /// Uptime and recovery settings for SysOps profile.
    /// </summary>
    public class UptimeSettings
    {
        public bool EnableAutoRecovery { get; set; }
        public bool EnableRestartPolicies { get; set; }
        public bool EnableFailover { get; set; }
        public int MaxRestartAttempts { get; set; } = 3;
        public int RestartDelaySeconds { get; set; } = 30;
        public bool EnableHeartbeatMonitoring { get; set; }
    }

    /// <summary>
    /// SysOps profile optimization settings.
    /// </summary>
    public class SysOpsProfileSettings : OptimizationProfile
    {
        public ServiceOptimizationSettings Service { get; set; } = new();
        public ReliabilitySettings Reliability { get; set; } = new();
        public MemoryOptimizationSettings Memory { get; set; } = new();
        public UptimeSettings Uptime { get; set; } = new();
    }

    /// <summary>
    /// Build optimization settings for Developer profile.
    /// </summary>
    public class BuildOptimizationSettings
    {
        public bool OptimizeDiskIO { get; set; }
        public int ParallelBuildThreads { get; set; } = Environment.ProcessorCount;
        public bool EnableCacheWarming { get; set; }
        public bool EnableIncrementalBuilds { get; set; }
        public int MaxBuildCacheSize { get; set; } = 1024;
    }

    /// <summary>
    /// IDE integration settings for Developer profile.
    /// </summary>
    public class IDEIntegrationSettings
    {
        public bool ConfigureVSCode { get; set; }
        public bool ConfigureVisualStudio { get; set; }
        public bool OptimizeIntelliSense { get; set; }
        public bool SetupDebugTools { get; set; }
        public int IntelliSenseUpdateDelayMs { get; set; } = 500;
        public bool EnableCodeAnalysis { get; set; }
    }

    /// <summary>
    /// Hot reload settings for Developer profile.
    /// </summary>
    public class HotReloadSettings
    {
        public bool EnableXAMLHotReload { get; set; }
        public bool EnableCSSAutoRefresh { get; set; }
        public bool EnableJSAutoRefresh { get; set; }
        public bool EnableLivePreview { get; set; }
        public int HotReloadDelayMs { get; set; } = 200;
    }

    /// <summary>
    /// Developer profile optimization settings.
    /// </summary>
    public class DeveloperProfileSettings : OptimizationProfile
    {
        public BuildOptimizationSettings Build { get; set; } = new();
        public IDEIntegrationSettings IDE { get; set; } = new();
        public HotReloadSettings HotReload { get; set; } = new();
        public CPUOptimizationSettings CPU { get; set; } = new();
    }

    /// <summary>
    /// Result of applying an optimization profile.
    /// </summary>
    public class OptimizationResult
    {
        public bool Success { get; set; }
        public string Message { get; set; }
        public List<string> AppliedSettings { get; set; } = new();
        public List<string> FailedSettings { get; set; } = new();
        public DateTime AppliedAt { get; set; } = DateTime.UtcNow;
        public long ElapsedMilliseconds { get; set; }
    }

    /// <summary>
    /// Workload analysis result for profile detection.
    /// </summary>
    public class WorkloadAnalysis
    {
        public OptimizationProfileType SuggestedProfile { get; set; }
        public double GamingScore { get; set; }
        public double SysOpsScore { get; set; }
        public double DeveloperScore { get; set; }
        public DateTime AnalyzedAt { get; set; }
        public Dictionary<string, double> ProcessMetrics { get; set; } = new();
    }

    /// <summary>
    /// Performance metrics before and after optimization.
    /// </summary>
    public class OptimizationMetrics
    {
        public double CPUUsagePercent { get; set; }
        public double MemoryUsagePercent { get; set; }
        public double GPUUsagePercent { get; set; }
        public double DiskIOPercent { get; set; }
        public double NetworkLatencyMs { get; set; }
        public int CurrentFPS { get; set; }
        public int CPUTemperatureCelsius { get; set; }
        public int GPUTemperatureCelsius { get; set; }
        public DateTime MeasuredAt { get; set; } = DateTime.UtcNow;
    }

    /// <summary>
    /// Profile comparison for performance analysis.
    /// </summary>
    public class ProfileComparison
    {
        public OptimizationProfileType ProfileType { get; set; }
        public OptimizationMetrics BeforeMetrics { get; set; }
        public OptimizationMetrics AfterMetrics { get; set; }
        public double PerformanceImprovement { get; set; }
        public Dictionary<string, double> MetricImprovements { get; set; } = new();
    }
}
