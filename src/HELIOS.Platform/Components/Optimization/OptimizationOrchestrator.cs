using System.Linq;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace HELIOS.Platform.Components.Optimization
{
    /// <summary>
    /// Main orchestrator for the per-user optimization system.
    /// Coordinates profiles, persistence, and UI components.
    /// </summary>
    public class OptimizationOrchestrator
    {
        private readonly OptimizationEngine _engine;
        private readonly ProfilePersistenceManager _persistence;
        private readonly ProfileSelector _selector;
        private readonly PerformanceDashboard _dashboard;
        private bool _isInitialized;

        public OptimizationEngine Engine => _engine;
        public ProfilePersistenceManager Persistence => _persistence;
        public ProfileSelector Selector => _selector;
        public PerformanceDashboard Dashboard => _dashboard;
        public bool IsInitialized => _isInitialized;

        public OptimizationOrchestrator(string profilesDirectory = null)
        {
            _engine = new OptimizationEngine();
            _persistence = new ProfilePersistenceManager(profilesDirectory);
            _selector = new ProfileSelector(_engine);
            _dashboard = new PerformanceDashboard();
        }

        /// <summary>
        /// Initializes the optimization system.
        /// </summary>
        public async Task<bool> InitializeAsync()
        {
            try
            {
                await _engine.InitializeAsync();

                var profiles = await _persistence.LoadAllProfilesAsync();
                foreach (var profile in profiles)
                {
                    _engine.RegisterProfile(profile);
                }

                var activeProfileId = await _persistence.LoadActiveProfileIdAsync();
                if (!string.IsNullOrEmpty(activeProfileId))
                {
                    await ApplyProfileAsync(activeProfileId);
                }

                _isInitialized = true;
                return true;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error initializing optimization system: {ex.Message}");
                return false;
            }
        }

        /// <summary>
        /// Applies an optimization profile.
        /// </summary>
        public async Task<OptimizationResult> ApplyProfileAsync(string profileId)
        {
            if (!_isInitialized)
            {
                return new OptimizationResult
                {
                    Success = false,
                    Message = "System not initialized"
                };
            }

            var result = await _engine.ApplyProfileAsync(profileId);

            if (result.Success)
            {
                await _persistence.SaveActiveProfileAsync(profileId);
            }

            return result;
        }

        /// <summary>
        /// Creates a custom profile.
        /// </summary>
        public async Task<OptimizationProfile> CreateCustomProfileAsync(
            string name,
            string description,
            OptimizationProfileType baseType)
        {
            if (!_isInitialized)
                return null;

            OptimizationProfile profile = baseType switch
            {
                OptimizationProfileType.Gaming => new GamingProfileSettings
                {
                    Name = name,
                    Type = OptimizationProfileType.Custom,
                    Description = description,
                    IsReadOnly = false
                },
                OptimizationProfileType.SysOps => new SysOpsProfileSettings
                {
                    Name = name,
                    Type = OptimizationProfileType.Custom,
                    Description = description,
                    IsReadOnly = false
                },
                OptimizationProfileType.Developer => new DeveloperProfileSettings
                {
                    Name = name,
                    Type = OptimizationProfileType.Custom,
                    Description = description,
                    IsReadOnly = false
                },
                _ => new OptimizationProfile
                {
                    Name = name,
                    Type = OptimizationProfileType.Custom,
                    Description = description,
                    IsReadOnly = false
                }
            };

            _engine.RegisterProfile(profile);
            await _persistence.SaveProfileAsync(profile);

            return profile;
        }

        /// <summary>
        /// Updates a custom profile.
        /// </summary>
        public async Task<bool> UpdateProfileAsync(OptimizationProfile profile)
        {
            if (!_isInitialized || profile.IsReadOnly)
                return false;

            profile.LastModified = DateTime.UtcNow;
            _engine.RegisterProfile(profile);
            return await _persistence.SaveProfileAsync(profile);
        }

        /// <summary>
        /// Deletes a custom profile.
        /// </summary>
        public async Task<bool> DeleteProfileAsync(string profileId)
        {
            if (!_isInitialized)
                return false;

            var removed = _engine.RemoveProfile(profileId);
            if (removed)
            {
                await _persistence.DeleteProfileAsync(profileId);
            }

            return removed;
        }

        /// <summary>
        /// Gets the active profile information.
        /// </summary>
        public ProfileInfo GetActiveProfile()
        {
            var active = _engine.ActiveProfile;
            if (active == null)
                return null;

            return new ProfileInfo
            {
                Id = active.Id,
                Name = active.Name,
                Type = active.Type,
                Description = active.Description,
                IsActive = true,
                IsReadOnly = active.IsReadOnly,
                CreatedAt = active.CreatedAt
            };
        }

        /// <summary>
        /// Detects the optimal profile for current workload.
        /// </summary>
        public WorkloadAnalysis AnalyzeWorkload()
        {
            return _engine.DetectOptimalProfile();
        }

        /// <summary>
        /// Auto-applies the optimal profile.
        /// </summary>
        public async Task<OptimizationResult> AutoOptimizeAsync()
        {
            var analysis = _engine.DetectOptimalProfile();
            
            var suggestedProfileId = _engine.Profiles
                .FirstOrDefault(p => p.Value.Type == analysis.SuggestedProfile).Value?.Id;

            if (string.IsNullOrEmpty(suggestedProfileId))
            {
                return new OptimizationResult
                {
                    Success = false,
                    Message = "Could not find suggested profile"
                };
            }

            return await ApplyProfileAsync(suggestedProfileId);
        }

        /// <summary>
        /// Exports a profile to a file.
        /// </summary>
        public async Task<bool> ExportProfileAsync(string profileId, string exportPath)
        {
            if (!_isInitialized || !_engine.Profiles.TryGetValue(profileId, out var profile))
                return false;

            return await _persistence.ExportProfileAsync(profile, exportPath);
        }

        /// <summary>
        /// Imports a profile from a file.
        /// </summary>
        public async Task<OptimizationProfile> ImportProfileAsync(string importPath)
        {
            if (!_isInitialized)
                return null;

            var profile = await _persistence.ImportProfileAsync(importPath);
            if (profile != null)
            {
                _engine.RegisterProfile(profile);
            }

            return profile;
        }

        /// <summary>
        /// Saves user preferences.
        /// </summary>
        public async Task<bool> SavePreferencesAsync(Dictionary<string, object> preferences)
        {
            return await _persistence.SavePreferencesAsync(preferences);
        }

        /// <summary>
        /// Loads user preferences.
        /// </summary>
        public async Task<Dictionary<string, object>> LoadPreferencesAsync()
        {
            return await _persistence.LoadPreferencesAsync();
        }

        /// <summary>
        /// Gets the result history.
        /// </summary>
        public IReadOnlyCollection<OptimizationResult> GetResultHistory()
        {
            return _engine.GetResultHistory();
        }

        /// <summary>
        /// Gets available profiles.
        /// </summary>
        public List<ProfileInfo> GetAvailableProfiles()
        {
            return _selector.GetAvailableProfiles();
        }

        /// <summary>
        /// Gets detailed profile settings.
        /// </summary>
        public ProfileSettingsDetail GetProfileDetails(string profileId)
        {
            return _selector.GetProfileDetails(profileId);
        }

        /// <summary>
        /// Updates performance metrics on the dashboard.
        /// </summary>
        public void UpdateMetrics(OptimizationMetrics metrics)
        {
            _dashboard.UpdateMetrics(metrics);
        }

        /// <summary>
        /// Gets the dashboard status.
        /// </summary>
        public DashboardStatus GetDashboardStatus()
        {
            return _dashboard.GetStatus();
        }

        /// <summary>
        /// Gets current metrics from the dashboard.
        /// </summary>
        public OptimizationMetrics GetCurrentMetrics()
        {
            return _dashboard.GetCurrentMetrics();
        }

        /// <summary>
        /// Gets average metrics from history.
        /// </summary>
        public OptimizationMetrics GetAverageMetrics()
        {
            return _dashboard.GetAverageMetrics();
        }

        /// <summary>
        /// Gets metrics history.
        /// </summary>
        public List<OptimizationMetrics> GetMetricsHistory()
        {
            return _dashboard.GetMetricsHistory();
        }

        /// <summary>
        /// Gets system status summary.
        /// </summary>
        public SystemStatusSummary GetStatusSummary()
        {
            var activeProfile = _engine.ActiveProfile;
            var currentMetrics = _dashboard.GetCurrentMetrics();
            var dashboardStatus = _dashboard.GetStatus();

            return new SystemStatusSummary
            {
                IsInitialized = _isInitialized,
                ActiveProfile = activeProfile?.Name ?? "None",
                ProfileType = activeProfile?.Type ?? OptimizationProfileType.Custom,
                Timestamp = DateTime.UtcNow,
                DashboardHealth = dashboardStatus?.HealthStatus ?? "Unknown",
                MetricsCount = dashboardStatus?.MetricCount ?? 0,
                CurrentCPUUsage = currentMetrics?.CPUUsagePercent ?? 0,
                CurrentMemoryUsage = currentMetrics?.MemoryUsagePercent ?? 0,
                CurrentGPUUsage = currentMetrics?.GPUUsagePercent ?? 0,
                RegisteredProfileCount = _engine.Profiles.Count
            };
        }
    }

    /// <summary>
    /// System status summary for display.
    /// </summary>
    public class SystemStatusSummary
    {
        public bool IsInitialized { get; set; }
        public string ActiveProfile { get; set; }
        public OptimizationProfileType ProfileType { get; set; }
        public DateTime Timestamp { get; set; }
        public string DashboardHealth { get; set; }
        public int MetricsCount { get; set; }
        public double CurrentCPUUsage { get; set; }
        public double CurrentMemoryUsage { get; set; }
        public double CurrentGPUUsage { get; set; }
        public int RegisteredProfileCount { get; set; }
    }
}
