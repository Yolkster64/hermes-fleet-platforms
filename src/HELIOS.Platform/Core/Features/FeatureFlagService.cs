namespace HELIOS.Platform.Core.Features;

/// <summary>
/// Comprehensive feature flags and toggleables system for HELIOS Platform.
/// </summary>
public interface IFeatureFlagService
{
    /// <summary>Checks if a feature is enabled.</summary>
    bool IsFeatureEnabled(string featureName);

    /// <summary>Checks if a feature is enabled for a specific user.</summary>
    bool IsFeatureEnabled(string featureName, string userId);

    /// <summary>Enables a feature.</summary>
    void EnableFeature(string featureName);

    /// <summary>Disables a feature.</summary>
    void DisableFeature(string featureName);

    /// <summary>Sets feature to beta status.</summary>
    void SetBeta(string featureName);

    /// <summary>Gets all feature states.</summary>
    IEnumerable<FeatureFlag> GetAllFeatures();

    /// <summary>Gets feature details.</summary>
    FeatureFlag? GetFeature(string featureName);

    /// <summary>Resets all features to defaults.</summary>
    void ResetToDefaults();

    /// <summary>Exports feature state.</summary>
    Task ExportFeaturesAsync(string filePath);

    /// <summary>Imports feature state.</summary>
    Task ImportFeaturesAsync(string filePath);
}

/// <summary>
/// Feature flag with comprehensive metadata.
/// </summary>
public class FeatureFlag
{
    public required string Name { get; init; }
    public required string DisplayName { get; init; }
    public required string Description { get; init; }
    public required FeatureStatus Status { get; init; }
    public required string Category { get; init; }
    public bool IsEnabled { get; set; }
    public bool IsExperimental { get; set; }
    public DateTime AddedDate { get; init; }
    public DateTime? DeprecatedDate { get; set; }
    public double? PercentageRolledOut { get; set; }
    public HashSet<string>? EnabledForUsers { get; set; } = new();
    public Dictionary<string, object>? Metadata { get; set; }
}

/// <summary>
/// Feature status enum.
/// </summary>
public enum FeatureStatus
{
    Development,
    Beta,
    GeneralAvailability,
    Experimental,
    Deprecated,
    Maintenance
}

/// <summary>
/// Feature categories.
/// </summary>
public static class FeatureCategories
{
    public const string System = "System";
    public const string UI = "UI";
    public const string Performance = "Performance";
    public const string Security = "Security";
    public const string Cloud = "Cloud";
    public const string AI = "AI";
    public const string Developer = "Developer";
    public const string Experimental = "Experimental";
    public const string Deprecated = "Deprecated";
}

/// <summary>
/// Default implementation of feature flag service.
/// </summary>
public class FeatureFlagService : IFeatureFlagService
{
    private readonly Dictionary<string, FeatureFlag> _features = new();
    private readonly object _lockObject = new();

    public FeatureFlagService()
    {
        InitializeDefaultFeatures();
    }

    public bool IsFeatureEnabled(string featureName)
    {
        if (!_features.TryGetValue(featureName, out var feature))
            return false;

        return feature.IsEnabled;
    }

    public bool IsFeatureEnabled(string featureName, string userId)
    {
        if (!_features.TryGetValue(featureName, out var feature))
            return false;

        if (!feature.IsEnabled)
            return false;

        // Check user-specific enablement
        if (feature.EnabledForUsers?.Contains(userId) == true)
            return true;

        // Check percentage rollout
        if (feature.PercentageRolledOut.HasValue)
        {
            var hash = userId.GetHashCode();
            var percentage = Math.Abs(hash % 100);
            return percentage < feature.PercentageRolledOut.Value;
        }

        return false;
    }

    public void EnableFeature(string featureName)
    {
        lock (_lockObject)
        {
            if (_features.TryGetValue(featureName, out var feature))
                feature.IsEnabled = true;
        }
    }

    public void DisableFeature(string featureName)
    {
        lock (_lockObject)
        {
            if (_features.TryGetValue(featureName, out var feature))
                feature.IsEnabled = false;
        }
    }

    public void SetBeta(string featureName)
    {
        lock (_lockObject)
        {
            if (_features.TryGetValue(featureName, out var feature))
            {
                feature.Status = FeatureStatus.Beta;
                feature.IsExperimental = true;
            }
        }
    }

    public IEnumerable<FeatureFlag> GetAllFeatures()
    {
        lock (_lockObject)
        {
            return _features.Values.ToList();
        }
    }

    public FeatureFlag? GetFeature(string featureName)
    {
        lock (_lockObject)
        {
            return _features.TryGetValue(featureName, out var feature) ? feature : null;
        }
    }

    public void ResetToDefaults()
    {
        lock (_lockObject)
        {
            _features.Clear();
            InitializeDefaultFeatures();
        }
    }

    public async Task ExportFeaturesAsync(string filePath)
    {
        try
        {
            Directory.CreateDirectory(Path.GetDirectoryName(filePath) ?? ".");

            lock (_lockObject)
            {
                var json = System.Text.Json.JsonSerializer.Serialize(_features.Values, new System.Text.Json.JsonSerializerOptions
                {
                    WriteIndented = true
                });

                File.WriteAllText(filePath, json);
            }

            await Task.CompletedTask;
        }
        catch (Exception ex)
        {
            throw new InvalidOperationException($"Failed to export features: {ex.Message}", ex);
        }
    }

    public async Task ImportFeaturesAsync(string filePath)
    {
        try
        {
            if (!File.Exists(filePath))
                throw new FileNotFoundException($"Feature file not found: {filePath}");

            var json = File.ReadAllText(filePath);
            var imported = System.Text.Json.JsonSerializer.Deserialize<List<FeatureFlag>>(json);

            if (imported != null)
            {
                lock (_lockObject)
                {
                    foreach (var feature in imported)
                    {
                        _features[feature.Name] = feature;
                    }
                }
            }

            await Task.CompletedTask;
        }
        catch (Exception ex)
        {
            throw new InvalidOperationException($"Failed to import features: {ex.Message}", ex);
        }
    }

    private void InitializeDefaultFeatures()
    {
        var now = DateTime.UtcNow;

        // System Features
        AddFeature("telemetry-enabled", "Telemetry", "Collect anonymous usage data", FeatureStatus.GeneralAvailability, FeatureCategories.System, true);
        AddFeature("auto-update", "Auto Update", "Automatically update HELIOS Platform", FeatureStatus.GeneralAvailability, FeatureCategories.System, true);
        AddFeature("crash-reporting", "Crash Reporting", "Send crash reports to telemetry", FeatureStatus.GeneralAvailability, FeatureCategories.System, true);
        AddFeature("health-monitoring", "Health Monitoring", "Monitor system health continuously", FeatureStatus.GeneralAvailability, FeatureCategories.System, true);
        AddFeature("background-sync", "Background Sync", "Sync data in background", FeatureStatus.GeneralAvailability, FeatureCategories.System, true);

        // UI Features
        AddFeature("dark-theme", "Dark Theme", "Enable dark theme for UI", FeatureStatus.GeneralAvailability, FeatureCategories.UI, true);
        AddFeature("animations", "Animations", "Enable smooth animations", FeatureStatus.GeneralAvailability, FeatureCategories.UI, true);
        AddFeature("custom-themes", "Custom Themes", "Allow custom theme creation", FeatureStatus.Beta, FeatureCategories.UI, false);
        AddFeature("floating-panels", "Floating Panels", "Experimental floating UI panels", FeatureStatus.Experimental, FeatureCategories.UI, false);

        // Performance Features
        AddFeature("smart-caching", "Smart Caching", "Intelligent caching system", FeatureStatus.GeneralAvailability, FeatureCategories.Performance, true);
        AddFeature("query-optimization", "Query Optimization", "Optimize database queries", FeatureStatus.GeneralAvailability, FeatureCategories.Performance, true);
        AddFeature("lazy-loading", "Lazy Loading", "Load data on demand", FeatureStatus.GeneralAvailability, FeatureCategories.Performance, true);
        AddFeature("connection-pooling", "Connection Pooling", "Reuse database connections", FeatureStatus.GeneralAvailability, FeatureCategories.Performance, true);

        // Security Features
        AddFeature("encryption-at-rest", "Encryption at Rest", "Encrypt data on disk", FeatureStatus.GeneralAvailability, FeatureCategories.Security, true);
        AddFeature("encryption-in-transit", "Encryption in Transit", "Encrypt network data", FeatureStatus.GeneralAvailability, FeatureCategories.Security, true);
        AddFeature("rate-limiting", "Rate Limiting", "Limit API request rates", FeatureStatus.GeneralAvailability, FeatureCategories.Security, true);
        AddFeature("audit-logging", "Audit Logging", "Log all important actions", FeatureStatus.GeneralAvailability, FeatureCategories.Security, true);
        AddFeature("two-factor-auth", "Two-Factor Auth", "Enable 2FA support", FeatureStatus.Beta, FeatureCategories.Security, false);

        // Cloud Features
        AddFeature("azure-integration", "Azure Integration", "Connect to Azure services", FeatureStatus.Beta, FeatureCategories.Cloud, false);
        AddFeature("power-bi-dashboard", "Power BI Dashboard", "Integration with Power BI", FeatureStatus.Beta, FeatureCategories.Cloud, false);
        AddFeature("cloud-sync", "Cloud Sync", "Sync with cloud storage", FeatureStatus.Beta, FeatureCategories.Cloud, false);
        AddFeature("remote-management", "Remote Management", "Manage remotely via web console", FeatureStatus.Experimental, FeatureCategories.Cloud, false);

        // AI Features
        AddFeature("ai-hub", "AI Hub", "AI model management and execution", FeatureStatus.Beta, FeatureCategories.AI, false);
        AddFeature("local-llm", "Local LLM", "Run LLM models locally", FeatureStatus.Experimental, FeatureCategories.AI, false);
        AddFeature("token-optimization", "Token Optimization", "Optimize LLM token usage", FeatureStatus.Beta, FeatureCategories.AI, false);
        AddFeature("agent-framework", "Agent Framework", "AI agents for automation", FeatureStatus.Experimental, FeatureCategories.AI, false);

        // Developer Features
        AddFeature("debug-mode", "Debug Mode", "Enable detailed debugging", FeatureStatus.GeneralAvailability, FeatureCategories.Developer, false);
        AddFeature("dev-tools", "Developer Tools", "Advanced developer tools", FeatureStatus.GeneralAvailability, FeatureCategories.Developer, false);
        AddFeature("plugin-system", "Plugin System", "Load and manage plugins", FeatureStatus.Beta, FeatureCategories.Developer, false);
        AddFeature("api-documentation", "API Documentation", "Built-in API docs", FeatureStatus.GeneralAvailability, FeatureCategories.Developer, true);

        // Experimental Features
        AddFeature("gpu-acceleration", "GPU Acceleration", "Use GPU for computations", FeatureStatus.Experimental, FeatureCategories.Experimental, false);
        AddFeature("wsl2-integration", "WSL2 Integration", "Integrate with WSL2", FeatureStatus.Experimental, FeatureCategories.Experimental, false);
        AddFeature("devdrive-support", "DevDrive Support", "Support Windows DevDrive", FeatureStatus.Experimental, FeatureCategories.Experimental, false);
    }

    private void AddFeature(string name, string displayName, string description, FeatureStatus status, string category, bool enabled)
    {
        _features[name] = new FeatureFlag
        {
            Name = name,
            DisplayName = displayName,
            Description = description,
            Status = status,
            Category = category,
            IsEnabled = enabled,
            IsExperimental = status == FeatureStatus.Experimental || status == FeatureStatus.Beta,
            AddedDate = DateTime.UtcNow
        };
    }
}
