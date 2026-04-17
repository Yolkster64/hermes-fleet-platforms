using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace HELIOS.Platform.Components.Optimization
{
    /// <summary>
    /// UI component for displaying and selecting optimization profiles.
    /// </summary>
    public class ProfileSelector
    {
        private readonly OptimizationEngine _engine;
        private OptimizationProfile _selectedProfile;

        public ProfileSelector(OptimizationEngine engine)
        {
            _engine = engine ?? throw new ArgumentNullException(nameof(engine));
        }

        /// <summary>
        /// Gets available profiles.
        /// </summary>
        public List<ProfileInfo> GetAvailableProfiles()
        {
            return _engine.Profiles
                .Select(p => new ProfileInfo
                {
                    Id = p.Value.Id,
                    Name = p.Value.Name,
                    Type = p.Value.Type,
                    Description = p.Value.Description,
                    IsActive = p.Value.IsActive,
                    IsReadOnly = p.Value.IsReadOnly,
                    CreatedAt = p.Value.CreatedAt
                })
                .OrderBy(p => p.Name)
                .ToList();
        }

        /// <summary>
        /// Selects a profile for preview.
        /// </summary>
        public ProfileInfo SelectProfile(string profileId)
        {
            if (!_engine.Profiles.TryGetValue(profileId, out var profile))
                return null;

            _selectedProfile = profile;
            
            return new ProfileInfo
            {
                Id = profile.Id,
                Name = profile.Name,
                Type = profile.Type,
                Description = profile.Description,
                IsActive = profile.IsActive,
                IsReadOnly = profile.IsReadOnly,
                CreatedAt = profile.CreatedAt
            };
        }

        /// <summary>
        /// Gets the currently selected profile.
        /// </summary>
        public ProfileInfo GetSelectedProfile()
        {
            if (_selectedProfile == null)
                return null;

            return new ProfileInfo
            {
                Id = _selectedProfile.Id,
                Name = _selectedProfile.Name,
                Type = _selectedProfile.Type,
                Description = _selectedProfile.Description,
                IsActive = _selectedProfile.IsActive,
                IsReadOnly = _selectedProfile.IsReadOnly,
                CreatedAt = _selectedProfile.CreatedAt
            };
        }

        /// <summary>
        /// Gets detailed settings for a profile.
        /// </summary>
        public ProfileSettingsDetail GetProfileDetails(string profileId)
        {
            if (!_engine.Profiles.TryGetValue(profileId, out var profile))
                return null;

            var detail = new ProfileSettingsDetail
            {
                ProfileName = profile.Name,
                ProfileType = profile.Type,
                Description = profile.Description,
                IsReadOnly = profile.IsReadOnly,
                CreatedAt = profile.CreatedAt,
                LastModified = profile.LastModified
            };

            switch (profile.Type)
            {
                case OptimizationProfileType.Gaming:
                    detail.SettingGroups = ExtractGamingSettings((GamingProfileSettings)profile);
                    break;

                case OptimizationProfileType.SysOps:
                    detail.SettingGroups = ExtractSysOpsSettings((SysOpsProfileSettings)profile);
                    break;

                case OptimizationProfileType.Developer:
                    detail.SettingGroups = ExtractDeveloperSettings((DeveloperProfileSettings)profile);
                    break;
            }

            return detail;
        }

        /// <summary>
        /// Extracts Gaming profile settings for display.
        /// </summary>
        private List<SettingGroup> ExtractGamingSettings(GamingProfileSettings profile)
        {
            var groups = new List<SettingGroup>();

            groups.Add(new SettingGroup
            {
                Name = "GPU Optimization",
                Settings = new Dictionary<string, string>
                {
                    { "Driver Updates", profile.GPU.EnableDriverUpdates ? "Enabled" : "Disabled" },
                    { "DirectX Optimization", profile.GPU.OptimizeDirectX ? "Enabled" : "Disabled" },
                    { "Vulkan Optimization", profile.GPU.OptimizeVulkan ? "Enabled" : "Disabled" },
                    { "GPU Priority Boost", profile.GPU.BoostGPUPriority ? "Enabled" : "Disabled" },
                    { "VRAM Allocation", $"{profile.GPU.VRAMAllocationPercent}%" }
                }
            });

            groups.Add(new SettingGroup
            {
                Name = "CPU Optimization",
                Settings = new Dictionary<string, string>
                {
                    { "CPU Affinity", profile.CPU.EnableCPUAffinity ? "Enabled" : "Disabled" },
                    { "Real-Time Priority", profile.CPU.EnableRealTimePriority ? "Enabled" : "Disabled" },
                    { "Frequency Scaling", profile.CPU.OptimizeFrequencyScaling ? "Enabled" : "Disabled" },
                    { "Power Plan", profile.CPU.PowerPlan },
                    { "Max Frequency", $"{profile.CPU.MaxCPUFrequencyPercent}%" }
                }
            });

            groups.Add(new SettingGroup
            {
                Name = "Memory Optimization",
                Settings = new Dictionary<string, string>
                {
                    { "Memory Prioritization", profile.Memory.EnableMemoryPrioritization ? "Enabled" : "Disabled" },
                    { "Page File Optimization", profile.Memory.OptimizePageFile ? "Enabled" : "Disabled" },
                    { "Texture Cache", profile.Memory.OptimizeTextureCache ? "Enabled" : "Disabled" },
                    { "Min Available Memory", $"{profile.Memory.MinimumAvailableMemoryMB}MB" },
                    { "Cache Size", $"{profile.Memory.CacheSizePercent}%" }
                }
            });

            groups.Add(new SettingGroup
            {
                Name = "Network Optimization",
                Settings = new Dictionary<string, string>
                {
                    { "Latency Optimization", profile.Network.OptimizeLatency ? "Enabled" : "Disabled" },
                    { "Packet Prioritization", profile.Network.EnablePacketPrioritization ? "Enabled" : "Disabled" },
                    { "QoS Configuration", profile.Network.ConfigureQoS ? "Enabled" : "Disabled" },
                    { "DNS Optimization", profile.Network.OptimizeDNS ? "Enabled" : "Disabled" },
                    { "Preferred DNS", profile.Network.PreferredDNS }
                }
            });

            groups.Add(new SettingGroup
            {
                Name = "Monitoring",
                Settings = new Dictionary<string, string>
                {
                    { "FPS Counter", profile.Monitoring.EnableFPSCounter ? "Enabled" : "Disabled" },
                    { "Thermal Monitoring", profile.Monitoring.EnableThermalMonitoring ? "Enabled" : "Disabled" },
                    { "Performance Metrics", profile.Monitoring.EnablePerformanceMetrics ? "Enabled" : "Disabled" },
                    { "Fan Curve Profiles", profile.Monitoring.EnableFanCurveProfiles ? "Enabled" : "Disabled" },
                    { "Update Interval", $"{profile.Monitoring.MetricsUpdateIntervalMs}ms" }
                }
            });

            return groups;
        }

        /// <summary>
        /// Extracts SysOps profile settings for display.
        /// </summary>
        private List<SettingGroup> ExtractSysOpsSettings(SysOpsProfileSettings profile)
        {
            var groups = new List<SettingGroup>();

            groups.Add(new SettingGroup
            {
                Name = "Service Optimization",
                Settings = new Dictionary<string, string>
                {
                    { "Critical Services Priority", profile.Service.PrioritizeCriticalServices ? "Enabled" : "Disabled" },
                    { "Background Tasks Scheduling", profile.Service.EnableBackgroundTaskScheduling ? "Enabled" : "Disabled" },
                    { "Resource Reservation", profile.Service.ReserveSystemResources ? "Enabled" : "Disabled" },
                    { "Memory Reservation", $"{profile.Service.MinimumMemoryReservationPercent}%" },
                    { "Critical Services Count", $"{profile.Service.CriticalServices.Count}" }
                }
            });

            groups.Add(new SettingGroup
            {
                Name = "Reliability",
                Settings = new Dictionary<string, string>
                {
                    { "Redundancy Checks", profile.Reliability.EnableRedundancyChecks ? "Enabled" : "Disabled" },
                    { "Auto Backup", profile.Reliability.EnableAutoBackup ? "Enabled" : "Disabled" },
                    { "Health Monitoring", profile.Reliability.EnableHealthMonitoring ? "Enabled" : "Disabled" },
                    { "Backup Schedule", profile.Reliability.BackupSchedule },
                    { "Backup Retention", $"{profile.Reliability.BackupRetentionDays} days" }
                }
            });

            groups.Add(new SettingGroup
            {
                Name = "Uptime",
                Settings = new Dictionary<string, string>
                {
                    { "Auto Recovery", profile.Uptime.EnableAutoRecovery ? "Enabled" : "Disabled" },
                    { "Restart Policies", profile.Uptime.EnableRestartPolicies ? "Enabled" : "Disabled" },
                    { "Failover", profile.Uptime.EnableFailover ? "Enabled" : "Disabled" },
                    { "Max Restart Attempts", $"{profile.Uptime.MaxRestartAttempts}" },
                    { "Heartbeat Monitoring", profile.Uptime.EnableHeartbeatMonitoring ? "Enabled" : "Disabled" }
                }
            });

            groups.Add(new SettingGroup
            {
                Name = "Memory",
                Settings = new Dictionary<string, string>
                {
                    { "Memory Prioritization", profile.Memory.EnableMemoryPrioritization ? "Enabled" : "Disabled" },
                    { "Min Available Memory", $"{profile.Memory.MinimumAvailableMemoryMB}MB" },
                    { "Cache Size", $"{profile.Memory.CacheSizePercent}%" }
                }
            });

            return groups;
        }

        /// <summary>
        /// Extracts Developer profile settings for display.
        /// </summary>
        private List<SettingGroup> ExtractDeveloperSettings(DeveloperProfileSettings profile)
        {
            var groups = new List<SettingGroup>();

            groups.Add(new SettingGroup
            {
                Name = "Build Optimization",
                Settings = new Dictionary<string, string>
                {
                    { "Disk I/O Optimization", profile.Build.OptimizeDiskIO ? "Enabled" : "Disabled" },
                    { "Parallel Threads", $"{profile.Build.ParallelBuildThreads}" },
                    { "Cache Warming", profile.Build.EnableCacheWarming ? "Enabled" : "Disabled" },
                    { "Incremental Builds", profile.Build.EnableIncrementalBuilds ? "Enabled" : "Disabled" },
                    { "Max Cache Size", $"{profile.Build.MaxBuildCacheSize}MB" }
                }
            });

            groups.Add(new SettingGroup
            {
                Name = "IDE Integration",
                Settings = new Dictionary<string, string>
                {
                    { "VS Code Configuration", profile.IDE.ConfigureVSCode ? "Enabled" : "Disabled" },
                    { "Visual Studio Configuration", profile.IDE.ConfigureVisualStudio ? "Enabled" : "Disabled" },
                    { "IntelliSense Optimization", profile.IDE.OptimizeIntelliSense ? "Enabled" : "Disabled" },
                    { "Debug Tools Setup", profile.IDE.SetupDebugTools ? "Enabled" : "Disabled" },
                    { "IntelliSense Delay", $"{profile.IDE.IntelliSenseUpdateDelayMs}ms" }
                }
            });

            groups.Add(new SettingGroup
            {
                Name = "Hot Reload",
                Settings = new Dictionary<string, string>
                {
                    { "XAML Hot Reload", profile.HotReload.EnableXAMLHotReload ? "Enabled" : "Disabled" },
                    { "CSS Auto Refresh", profile.HotReload.EnableCSSAutoRefresh ? "Enabled" : "Disabled" },
                    { "JS Auto Refresh", profile.HotReload.EnableJSAutoRefresh ? "Enabled" : "Disabled" },
                    { "Live Preview", profile.HotReload.EnableLivePreview ? "Enabled" : "Disabled" },
                    { "Hot Reload Delay", $"{profile.HotReload.HotReloadDelayMs}ms" }
                }
            });

            groups.Add(new SettingGroup
            {
                Name = "CPU Optimization",
                Settings = new Dictionary<string, string>
                {
                    { "Power Plan", profile.CPU.PowerPlan },
                    { "Frequency Scaling", profile.CPU.OptimizeFrequencyScaling ? "Enabled" : "Disabled" },
                    { "Max Frequency", $"{profile.CPU.MaxCPUFrequencyPercent}%" }
                }
            });

            return groups;
        }
    }

    /// <summary>
    /// Represents profile information for UI display.
    /// </summary>
    public class ProfileInfo
    {
        public string Id { get; set; }
        public string Name { get; set; }
        public OptimizationProfileType Type { get; set; }
        public string Description { get; set; }
        public bool IsActive { get; set; }
        public bool IsReadOnly { get; set; }
        public DateTime CreatedAt { get; set; }
    }

    /// <summary>
    /// Detailed profile settings for display.
    /// </summary>
    public class ProfileSettingsDetail
    {
        public string ProfileName { get; set; }
        public OptimizationProfileType ProfileType { get; set; }
        public string Description { get; set; }
        public bool IsReadOnly { get; set; }
        public DateTime CreatedAt { get; set; }
        public DateTime LastModified { get; set; }
        public List<SettingGroup> SettingGroups { get; set; } = new();
    }

    /// <summary>
    /// A group of related settings.
    /// </summary>
    public class SettingGroup
    {
        public string Name { get; set; }
        public Dictionary<string, string> Settings { get; set; } = new();
    }

    /// <summary>
    /// Performance metrics dashboard for real-time monitoring.
    /// </summary>
    public class PerformanceDashboard
    {
        private OptimizationMetrics _currentMetrics;
        private List<OptimizationMetrics> _metricsHistory = new();
        private const int MaxHistoryPoints = 60;

        /// <summary>
        /// Updates the current metrics.
        /// </summary>
        public void UpdateMetrics(OptimizationMetrics metrics)
        {
            _currentMetrics = metrics;
            _metricsHistory.Add(metrics);

            if (_metricsHistory.Count > MaxHistoryPoints)
                _metricsHistory.RemoveAt(0);
        }

        /// <summary>
        /// Gets the current metrics.
        /// </summary>
        public OptimizationMetrics GetCurrentMetrics() => _currentMetrics;

        /// <summary>
        /// Gets the metrics history.
        /// </summary>
        public List<OptimizationMetrics> GetMetricsHistory() => new(_metricsHistory);

        /// <summary>
        /// Calculates average metrics from history.
        /// </summary>
        public OptimizationMetrics GetAverageMetrics()
        {
            if (_metricsHistory.Count == 0)
                return new OptimizationMetrics();

            return new OptimizationMetrics
            {
                CPUUsagePercent = _metricsHistory.Average(m => m.CPUUsagePercent),
                MemoryUsagePercent = _metricsHistory.Average(m => m.MemoryUsagePercent),
                GPUUsagePercent = _metricsHistory.Average(m => m.GPUUsagePercent),
                DiskIOPercent = _metricsHistory.Average(m => m.DiskIOPercent),
                NetworkLatencyMs = _metricsHistory.Average(m => m.NetworkLatencyMs),
                CurrentFPS = (int)_metricsHistory.Average(m => m.CurrentFPS),
                CPUTemperatureCelsius = (int)_metricsHistory.Average(m => m.CPUTemperatureCelsius),
                GPUTemperatureCelsius = (int)_metricsHistory.Average(m => m.GPUTemperatureCelsius)
            };
        }

        /// <summary>
        /// Gets the status of the system.
        /// </summary>
        public DashboardStatus GetStatus()
        {
            var status = new DashboardStatus
            {
                Timestamp = DateTime.UtcNow,
                HealthStatus = DetermineDashboardHealth(),
                MetricCount = _metricsHistory.Count
            };

            if (_currentMetrics != null)
            {
                status.CPUStatus = _currentMetrics.CPUUsagePercent > 80 ? "High" :
                                   _currentMetrics.CPUUsagePercent > 50 ? "Normal" : "Low";
                status.MemoryStatus = _currentMetrics.MemoryUsagePercent > 80 ? "High" :
                                      _currentMetrics.MemoryUsagePercent > 50 ? "Normal" : "Low";
                status.GPUStatus = _currentMetrics.GPUUsagePercent > 80 ? "High" :
                                   _currentMetrics.GPUUsagePercent > 50 ? "Normal" : "Low";
            }

            return status;
        }

        /// <summary>
        /// Determines the overall health of the system.
        /// </summary>
        private string DetermineDashboardHealth()
        {
            if (_currentMetrics == null)
                return "Unknown";

            var overallUsage = (_currentMetrics.CPUUsagePercent + 
                              _currentMetrics.MemoryUsagePercent + 
                              _currentMetrics.GPUUsagePercent) / 3;

            return overallUsage > 80 ? "Critical" :
                   overallUsage > 60 ? "Warning" :
                   overallUsage > 40 ? "Normal" : "Excellent";
        }

        /// <summary>
        /// Clears metrics history.
        /// </summary>
        public void ClearHistory() => _metricsHistory.Clear();
    }

    /// <summary>
    /// Dashboard status information.
    /// </summary>
    public class DashboardStatus
    {
        public DateTime Timestamp { get; set; }
        public string HealthStatus { get; set; }
        public string CPUStatus { get; set; }
        public string MemoryStatus { get; set; }
        public string GPUStatus { get; set; }
        public int MetricCount { get; set; }
    }
}
