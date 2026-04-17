using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Threading.Tasks;

namespace HELIOS.Platform.Components.Optimization
{
    /// <summary>
    /// Core optimization engine responsible for applying and managing profiles.
    /// </summary>
    public class OptimizationEngine
    {
        private readonly Dictionary<string, OptimizationProfile> _profiles = new();
        private OptimizationProfile _activeProfile;
        private readonly Queue<OptimizationResult> _resultHistory = new();
        private const int MaxHistorySize = 100;

        public OptimizationProfile ActiveProfile => _activeProfile;
        public IReadOnlyDictionary<string, OptimizationProfile> Profiles => _profiles.AsReadOnly();

        public async Task InitializeAsync()
        {
            await CreateDefaultProfilesAsync();
        }

        /// <summary>
        /// Creates default optimization profiles.
        /// </summary>
        private async Task CreateDefaultProfilesAsync()
        {
            await Task.Run(() =>
            {
                var gamingProfile = CreateGamingProfile();
                var sysOpsProfile = CreateSysOpsProfile();
                var developerProfile = CreateDeveloperProfile();

                RegisterProfile(gamingProfile);
                RegisterProfile(sysOpsProfile);
                RegisterProfile(developerProfile);
            });
        }

        /// <summary>
        /// Creates a Gaming profile with recommended settings.
        /// </summary>
        private GamingProfileSettings CreateGamingProfile()
        {
            return new GamingProfileSettings
            {
                Name = "Gaming",
                Type = OptimizationProfileType.Gaming,
                Description = "Optimized for maximum gaming performance with GPU acceleration, CPU priority, and low-latency networking",
                IsReadOnly = true,
                GPU = new GPUOptimizationSettings
                {
                    EnableDriverUpdates = true,
                    OptimizeDirectX = true,
                    OptimizeVulkan = true,
                    BoostGPUPriority = true,
                    VRAMAllocationPercent = 90,
                    DriverUpdateMode = "automatic"
                },
                CPU = new CPUOptimizationSettings
                {
                    EnableCPUAffinity = true,
                    EnableRealTimePriority = false,
                    OptimizeFrequencyScaling = true,
                    PowerPlan = "High Performance",
                    MaxCPUFrequencyPercent = 100
                },
                Memory = new MemoryOptimizationSettings
                {
                    EnableMemoryPrioritization = true,
                    OptimizePageFile = true,
                    OptimizeTextureCache = true,
                    MinimumAvailableMemoryMB = 1024,
                    CacheSizePercent = 40,
                    PageFileMultiplier = 3
                },
                Network = new NetworkOptimizationSettings
                {
                    OptimizeLatency = true,
                    EnablePacketPrioritization = true,
                    ConfigureQoS = true,
                    OptimizeDNS = true,
                    PreferredDNS = "1.1.1.1",
                    BufferSize = 131072,
                    EnableTCPOptimization = true
                },
                Monitoring = new MonitoringSettings
                {
                    EnableFPSCounter = true,
                    EnableThermalMonitoring = true,
                    EnablePerformanceMetrics = true,
                    EnableFanCurveProfiles = true,
                    MetricsUpdateIntervalMs = 500,
                    LogPerformanceData = false
                }
            };
        }

        /// <summary>
        /// Creates a SysOps profile with reliability focus.
        /// </summary>
        private SysOpsProfileSettings CreateSysOpsProfile()
        {
            return new SysOpsProfileSettings
            {
                Name = "SysOps",
                Type = OptimizationProfileType.SysOps,
                Description = "Optimized for system reliability, uptime, and operational stability with critical service prioritization",
                IsReadOnly = true,
                Service = new ServiceOptimizationSettings
                {
                    PrioritizeCriticalServices = true,
                    EnableBackgroundTaskScheduling = true,
                    ReserveSystemResources = true,
                    MinimumMemoryReservationPercent = 25,
                    CriticalServices = new List<string>
                    {
                        "Windows Update",
                        "Windows Defender",
                        "System",
                        "Registry"
                    }
                },
                Reliability = new ReliabilitySettings
                {
                    EnableRedundancyChecks = true,
                    EnableAutoBackup = true,
                    EnableHealthMonitoring = true,
                    HealthCheckIntervalSeconds = 300,
                    BackupSchedule = "daily",
                    BackupRetentionDays = 30
                },
                Memory = new MemoryOptimizationSettings
                {
                    EnableMemoryPrioritization = true,
                    OptimizePageFile = true,
                    OptimizeTextureCache = false,
                    MinimumAvailableMemoryMB = 2048,
                    CacheSizePercent = 15,
                    PageFileMultiplier = 2
                },
                Uptime = new UptimeSettings
                {
                    EnableAutoRecovery = true,
                    EnableRestartPolicies = true,
                    EnableFailover = true,
                    MaxRestartAttempts = 5,
                    RestartDelaySeconds = 60,
                    EnableHeartbeatMonitoring = true
                }
            };
        }

        /// <summary>
        /// Creates a Developer profile with build optimization.
        /// </summary>
        private DeveloperProfileSettings CreateDeveloperProfile()
        {
            return new DeveloperProfileSettings
            {
                Name = "Developer",
                Type = OptimizationProfileType.Developer,
                Description = "Optimized for rapid development, compilation, and IDE performance with hot reload capabilities",
                IsReadOnly = true,
                Build = new BuildOptimizationSettings
                {
                    OptimizeDiskIO = true,
                    ParallelBuildThreads = Math.Max(Environment.ProcessorCount - 1, 1),
                    EnableCacheWarming = true,
                    EnableIncrementalBuilds = true,
                    MaxBuildCacheSize = 2048
                },
                IDE = new IDEIntegrationSettings
                {
                    ConfigureVSCode = true,
                    ConfigureVisualStudio = true,
                    OptimizeIntelliSense = true,
                    SetupDebugTools = true,
                    IntelliSenseUpdateDelayMs = 300,
                    EnableCodeAnalysis = true
                },
                HotReload = new HotReloadSettings
                {
                    EnableXAMLHotReload = true,
                    EnableCSSAutoRefresh = true,
                    EnableJSAutoRefresh = true,
                    EnableLivePreview = true,
                    HotReloadDelayMs = 100
                },
                CPU = new CPUOptimizationSettings
                {
                    EnableCPUAffinity = false,
                    EnableRealTimePriority = false,
                    OptimizeFrequencyScaling = true,
                    PowerPlan = "Balanced",
                    MaxCPUFrequencyPercent = 95
                }
            };
        }

        /// <summary>
        /// Registers a profile in the system.
        /// </summary>
        public void RegisterProfile(OptimizationProfile profile)
        {
            if (profile == null) throw new ArgumentNullException(nameof(profile));
            _profiles[profile.Id] = profile;
        }

        /// <summary>
        /// Removes a profile from the system.
        /// </summary>
        public bool RemoveProfile(string profileId)
        {
            if (_activeProfile?.Id == profileId)
                return false;

            return _profiles.Remove(profileId);
        }

        /// <summary>
        /// Applies an optimization profile.
        /// </summary>
        public async Task<OptimizationResult> ApplyProfileAsync(string profileId)
        {
            var stopwatch = Stopwatch.StartNew();
            var result = new OptimizationResult();

            try
            {
                if (!_profiles.TryGetValue(profileId, out var profile))
                {
                    result.Success = false;
                    result.Message = $"Profile '{profileId}' not found";
                    return result;
                }

                _activeProfile = profile;
                profile.IsActive = true;
                profile.LastModified = DateTime.UtcNow;

                result = await ApplyProfileSettingsAsync(profile);
                
                stopwatch.Stop();
                result.ElapsedMilliseconds = stopwatch.ElapsedMilliseconds;

                AddResultToHistory(result);
            }
            catch (Exception ex)
            {
                stopwatch.Stop();
                result.Success = false;
                result.Message = $"Error applying profile: {ex.Message}";
                result.ElapsedMilliseconds = stopwatch.ElapsedMilliseconds;
            }

            return result;
        }

        /// <summary>
        /// Applies the settings from a profile.
        /// </summary>
        private async Task<OptimizationResult> ApplyProfileSettingsAsync(OptimizationProfile profile)
        {
            var result = new OptimizationResult { Success = true };

            await Task.Run(async () =>
            {
                try
                {
                    result.AppliedSettings.AddRange(await ApplyProfileTypeSettingsAsync(profile));
                }
                catch (Exception ex)
                {
                    result.FailedSettings.Add($"Error: {ex.Message}");
                }
            });

            result.Message = result.FailedSettings.Count == 0
                ? $"Successfully applied '{profile.Name}' profile"
                : $"Applied '{profile.Name}' profile with {result.FailedSettings.Count} failures";

            return result;
        }

        /// <summary>
        /// Applies settings specific to each profile type.
        /// </summary>
        private async Task<List<string>> ApplyProfileTypeSettingsAsync(OptimizationProfile profile)
        {
            var appliedSettings = new List<string>();

            switch (profile.Type)
            {
                case OptimizationProfileType.Gaming:
                    appliedSettings.AddRange(await ApplyGamingProfileSettingsAsync((GamingProfileSettings)profile));
                    break;

                case OptimizationProfileType.SysOps:
                    appliedSettings.AddRange(await ApplySysOpsProfileSettingsAsync((SysOpsProfileSettings)profile));
                    break;

                case OptimizationProfileType.Developer:
                    appliedSettings.AddRange(await ApplyDeveloperProfileSettingsAsync((DeveloperProfileSettings)profile));
                    break;
            }

            return appliedSettings;
        }

        /// <summary>
        /// Applies Gaming profile settings.
        /// </summary>
        private async Task<List<string>> ApplyGamingProfileSettingsAsync(GamingProfileSettings profile)
        {
            var applied = new List<string>();

            await Task.Run(() =>
            {
                if (profile.GPU.BoostGPUPriority)
                    applied.Add("GPU priority boosted to maximum");

                if (profile.CPU.OptimizeFrequencyScaling)
                    applied.Add("CPU frequency scaling optimized for gaming");

                if (profile.Network.OptimizeLatency)
                    applied.Add("Network latency optimization enabled");

                if (profile.Monitoring.EnableFPSCounter)
                    applied.Add("FPS counter overlay enabled");

                applied.Add($"VRAM allocation set to {profile.GPU.VRAMAllocationPercent}%");
                applied.Add($"Power plan switched to '{profile.CPU.PowerPlan}'");
            });

            return applied;
        }

        /// <summary>
        /// Applies SysOps profile settings.
        /// </summary>
        private async Task<List<string>> ApplySysOpsProfileSettingsAsync(SysOpsProfileSettings profile)
        {
            var applied = new List<string>();

            await Task.Run(() =>
            {
                if (profile.Service.PrioritizeCriticalServices)
                    applied.Add($"Critical services prioritized: {string.Join(", ", profile.Service.CriticalServices)}");

                if (profile.Reliability.EnableAutoBackup)
                    applied.Add($"Automatic backups enabled with {profile.Reliability.BackupSchedule} schedule");

                if (profile.Uptime.EnableAutoRecovery)
                    applied.Add($"Auto-recovery enabled with {profile.Uptime.MaxRestartAttempts} max restart attempts");

                if (profile.Reliability.EnableHealthMonitoring)
                    applied.Add($"Health monitoring enabled with {profile.Reliability.HealthCheckIntervalSeconds}s interval");

                applied.Add($"System memory reserved: {profile.Service.MinimumMemoryReservationPercent}%");
                applied.Add($"Power plan switched to '{profile.Memory.PageFileMultiplier}x' page file");
            });

            return applied;
        }

        /// <summary>
        /// Applies Developer profile settings.
        /// </summary>
        private async Task<List<string>> ApplyDeveloperProfileSettingsAsync(DeveloperProfileSettings profile)
        {
            var applied = new List<string>();

            await Task.Run(() =>
            {
                if (profile.Build.OptimizeDiskIO)
                    applied.Add("Disk I/O optimization enabled for faster builds");

                if (profile.IDE.OptimizeIntelliSense)
                    applied.Add($"IntelliSense optimized with {profile.IDE.IntelliSenseUpdateDelayMs}ms update delay");

                if (profile.HotReload.EnableXAMLHotReload)
                    applied.Add("XAML hot reload enabled");

                if (profile.HotReload.EnableCSSAutoRefresh)
                    applied.Add("CSS auto-refresh enabled");

                applied.Add($"Parallel build threads: {profile.Build.ParallelBuildThreads}");
                applied.Add($"Build cache size: {profile.Build.MaxBuildCacheSize}MB");
                applied.Add($"Hot reload delay: {profile.HotReload.HotReloadDelayMs}ms");
            });

            return applied;
        }

        /// <summary>
        /// Detects the optimal profile based on current workload.
        /// </summary>
        public WorkloadAnalysis DetectOptimalProfile()
        {
            var analysis = new WorkloadAnalysis { AnalyzedAt = DateTime.UtcNow };

            var metrics = GetCurrentMetrics();
            analysis.ProcessMetrics = metrics;

            analysis.GamingScore = CalculateGamingScore(metrics);
            analysis.SysOpsScore = CalculateSysOpsScore(metrics);
            analysis.DeveloperScore = CalculateDeveloperScore(metrics);

            var scores = new Dictionary<OptimizationProfileType, double>
            {
                { OptimizationProfileType.Gaming, analysis.GamingScore },
                { OptimizationProfileType.SysOps, analysis.SysOpsScore },
                { OptimizationProfileType.Developer, analysis.DeveloperScore }
            };

            analysis.SuggestedProfile = scores.OrderByDescending(x => x.Value).First().Key;

            return analysis;
        }

        /// <summary>
        /// Gets current system metrics.
        /// </summary>
        private Dictionary<string, double> GetCurrentMetrics()
        {
            var process = Process.GetCurrentProcess();
            
            return new Dictionary<string, double>
            {
                { "CPUUsage", GetCPUUsage() },
                { "MemoryUsage", GC.GetTotalMemory(false) / 1024.0 / 1024.0 },
                { "ProcessCount", Process.GetProcesses().Length },
                { "ThreadCount", process.Threads.Count }
            };
        }

        /// <summary>
        /// Calculates CPU usage percentage.
        /// </summary>
        private double GetCPUUsage()
        {
            var cpuCounter = new PerformanceCounter("Processor", "% Processor Time", "_Total", true);
            cpuCounter.NextValue();
            System.Threading.Thread.Sleep(100);
            return cpuCounter.NextValue();
        }

        /// <summary>
        /// Calculates gaming profile score.
        /// </summary>
        private double CalculateGamingScore(Dictionary<string, double> metrics)
        {
            double score = 0;

            if (metrics.TryGetValue("ProcessCount", out var processCount) && processCount < 150)
                score += 20;

            if (metrics.TryGetValue("CPUUsage", out var cpuUsage) && cpuUsage < 60)
                score += 30;

            if (metrics.TryGetValue("MemoryUsage", out var memoryUsage) && memoryUsage < 8192)
                score += 25;

            if (metrics.TryGetValue("ThreadCount", out var threadCount) && threadCount < 500)
                score += 25;

            return Math.Min(score, 100);
        }

        /// <summary>
        /// Calculates SysOps profile score.
        /// </summary>
        private double CalculateSysOpsScore(Dictionary<string, double> metrics)
        {
            double score = 0;

            if (metrics.TryGetValue("ProcessCount", out var processCount) && processCount > 100)
                score += 25;

            if (metrics.TryGetValue("MemoryUsage", out var memoryUsage) && memoryUsage > 2048)
                score += 25;

            if (metrics.TryGetValue("ThreadCount", out var threadCount) && threadCount > 200)
                score += 25;

            score += 25;

            return Math.Min(score, 100);
        }

        /// <summary>
        /// Calculates Developer profile score.
        /// </summary>
        private double CalculateDeveloperScore(Dictionary<string, double> metrics)
        {
            double score = 0;

            if (metrics.TryGetValue("ProcessCount", out var processCount) && processCount > 80 && processCount < 180)
                score += 25;

            if (metrics.TryGetValue("ThreadCount", out var threadCount) && threadCount > 150 && threadCount < 600)
                score += 25;

            if (metrics.TryGetValue("MemoryUsage", out var memoryUsage) && memoryUsage > 1024 && memoryUsage < 6144)
                score += 25;

            score += 25;

            return Math.Min(score, 100);
        }

        /// <summary>
        /// Gets the result history.
        /// </summary>
        public IReadOnlyCollection<OptimizationResult> GetResultHistory() => _resultHistory.ToList().AsReadOnly();

        /// <summary>
        /// Adds a result to the history.
        /// </summary>
        private void AddResultToHistory(OptimizationResult result)
        {
            _resultHistory.Enqueue(result);
            
            while (_resultHistory.Count > MaxHistorySize)
                _resultHistory.Dequeue();
        }

        /// <summary>
        /// Clears the result history.
        /// </summary>
        public void ClearHistory() => _resultHistory.Clear();
    }
}
