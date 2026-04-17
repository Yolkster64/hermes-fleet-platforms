using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;

namespace HELIOS.Platform.Core.Plugins.Configuration
{
    /// <summary>
    /// Plugin configuration manager
    /// </summary>
    public class PluginConfigurationManager
    {
        private readonly string _configDirectoryPath;
        private readonly Dictionary<string, IPluginConfiguration> _configurations = new();

        public PluginConfigurationManager(string configDirectoryPath)
        {
            _configDirectoryPath = configDirectoryPath;
            if (!Directory.Exists(_configDirectoryPath))
            {
                Directory.CreateDirectory(_configDirectoryPath);
            }
        }

        /// <summary>
        /// Load configuration for a plugin
        /// </summary>
        public async Task<IPluginConfiguration> LoadConfigurationAsync(string pluginId)
        {
            var configPath = Path.Combine(_configDirectoryPath, $"{pluginId}.json");

            if (File.Exists(configPath))
            {
                try
                {
                    var json = await File.ReadAllTextAsync(configPath);
                    var dict = JsonSerializer.Deserialize<Dictionary<string, object>>(json) ?? new();
                    var config = new PluginConfiguration(dict);
                    _configurations[pluginId] = config;
                    return config;
                }
                catch
                {
                    return new PluginConfiguration();
                }
            }

            var defaultConfig = new PluginConfiguration();
            _configurations[pluginId] = defaultConfig;
            return defaultConfig;
        }

        /// <summary>
        /// Save configuration for a plugin
        /// </summary>
        public async Task SaveConfigurationAsync(string pluginId, IPluginConfiguration configuration)
        {
            var configPath = Path.Combine(_configDirectoryPath, $"{pluginId}.json");
            var dict = configuration.GetAll();
            var json = JsonSerializer.Serialize(dict, new JsonSerializerOptions { WriteIndented = true });
            await File.WriteAllTextAsync(configPath, json);
            _configurations[pluginId] = configuration;
        }

        /// <summary>
        /// Create default configuration file if not exists
        /// </summary>
        public async Task CreateDefaultConfigAsync(string pluginId, Dictionary<string, object> defaultValues)
        {
            var configPath = Path.Combine(_configDirectoryPath, $"{pluginId}.json");
            if (!File.Exists(configPath))
            {
                var json = JsonSerializer.Serialize(defaultValues, new JsonSerializerOptions { WriteIndented = true });
                await File.WriteAllTextAsync(configPath, json);
            }
        }

        /// <summary>
        /// Get configuration for a plugin (cached)
        /// </summary>
        public IPluginConfiguration GetConfiguration(string pluginId)
        {
            if (_configurations.TryGetValue(pluginId, out var config))
            {
                return config;
            }
            return new PluginConfiguration();
        }

        /// <summary>
        /// Watch configuration file for changes
        /// </summary>
        public void WatchConfiguration(string pluginId, Action<IPluginConfiguration> onChanged)
        {
            var configPath = Path.Combine(_configDirectoryPath, $"{pluginId}.json");
            var directory = Path.GetDirectoryName(configPath);
            var filename = Path.GetFileName(configPath);

            var watcher = new FileSystemWatcher(directory);
            watcher.Filter = filename;
            watcher.Changed += async (s, e) =>
            {
                await Task.Delay(100); // Wait for file to be fully written
                var config = await LoadConfigurationAsync(pluginId);
                onChanged?.Invoke(config);
            };
            watcher.EnableRaisingEvents = true;
        }
    }

    /// <summary>
    /// Plugin configuration implementation
    /// </summary>
    public class PluginConfiguration : IPluginConfiguration
    {
        private readonly Dictionary<string, object> _config;
        private readonly object _lockObject = new();

        public PluginConfiguration(Dictionary<string, object> initialConfig = null)
        {
            _config = new(initialConfig ?? new());
        }

        public T Get<T>(string key, T defaultValue = default)
        {
            lock (_lockObject)
            {
                if (_config.TryGetValue(key, out var value))
                {
                    try
                    {
                        return (T)Convert.ChangeType(value, typeof(T));
                    }
                    catch
                    {
                        return defaultValue;
                    }
                }
                return defaultValue;
            }
        }

        public void Set<T>(string key, T value)
        {
            lock (_lockObject)
            {
                _config[key] = value;
            }
        }

        public Dictionary<string, object> GetAll()
        {
            lock (_lockObject)
            {
                return new Dictionary<string, object>(_config);
            }
        }

        public async Task ReloadAsync()
        {
            await Task.CompletedTask;
        }
    }

    /// <summary>
    /// Configuration schema validator
    /// </summary>
    public class ConfigurationSchemaValidator
    {
        private readonly Dictionary<string, ConfigurationSchema> _schemas = new();

        /// <summary>
        /// Register a configuration schema for a plugin
        /// </summary>
        public void RegisterSchema(string pluginId, ConfigurationSchema schema)
        {
            _schemas[pluginId] = schema;
        }

        /// <summary>
        /// Validate configuration against schema
        /// </summary>
        public ValidationResult Validate(string pluginId, IPluginConfiguration config)
        {
            if (!_schemas.TryGetValue(pluginId, out var schema))
            {
                return ValidationResult.Valid();
            }

            var errors = new List<string>();
            var configDict = config.GetAll();

            foreach (var property in schema.Properties)
            {
                if (property.Value.Required && !configDict.ContainsKey(property.Key))
                {
                    errors.Add($"Required property '{property.Key}' is missing");
                }

                if (configDict.TryGetValue(property.Key, out var value))
                {
                    if (value != null && !property.Value.Type.IsAssignableFrom(value.GetType()))
                    {
                        errors.Add($"Property '{property.Key}' has invalid type. Expected {property.Value.Type.Name}, got {value.GetType().Name}");
                    }

                    if (property.Value.MinValue != null && (IComparable)value < (IComparable)property.Value.MinValue)
                    {
                        errors.Add($"Property '{property.Key}' is below minimum value {property.Value.MinValue}");
                    }

                    if (property.Value.MaxValue != null && (IComparable)value > (IComparable)property.Value.MaxValue)
                    {
                        errors.Add($"Property '{property.Key}' exceeds maximum value {property.Value.MaxValue}");
                    }

                    if (property.Value.AllowedValues != null && property.Value.AllowedValues.Count > 0)
                    {
                        if (!property.Value.AllowedValues.Contains(value))
                        {
                            errors.Add($"Property '{property.Key}' has invalid value. Allowed: {string.Join(", ", property.Value.AllowedValues)}");
                        }
                    }
                }
            }

            return errors.Count > 0 ? ValidationResult.Invalid(errors) : ValidationResult.Valid();
        }
    }

    /// <summary>
    /// Configuration property schema
    /// </summary>
    public class ConfigurationProperty
    {
        public Type Type { get; set; }
        public bool Required { get; set; }
        public object DefaultValue { get; set; }
        public string Description { get; set; }
        public IComparable MinValue { get; set; }
        public IComparable MaxValue { get; set; }
        public List<object> AllowedValues { get; set; }
    }

    /// <summary>
    /// Configuration schema
    /// </summary>
    public class ConfigurationSchema
    {
        public string PluginId { get; set; }
        public Dictionary<string, ConfigurationProperty> Properties { get; set; } = new();
        public string Version { get; set; } = "1.0";
    }

    /// <summary>
    /// Validation result
    /// </summary>
    public class ValidationResult
    {
        public bool IsValid { get; }
        public List<string> Errors { get; }

        public ValidationResult(bool isValid, List<string> errors = null)
        {
            IsValid = isValid;
            Errors = errors ?? new();
        }

        public static ValidationResult Valid() => new ValidationResult(true);
        public static ValidationResult Invalid(List<string> errors) => new ValidationResult(false, errors);
    }
}
