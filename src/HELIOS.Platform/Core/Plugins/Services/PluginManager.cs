using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using HELIOS.Platform.Core.Plugins.Abstractions;
using HELIOS.Platform.Core.Plugins.Services;
using HELIOS.Platform.Core.Plugins.Security;
using HELIOS.Platform.Core.Plugins.Configuration;
using HELIOS.Platform.Core.Plugins.Versioning;

namespace HELIOS.Platform.Core.Plugins.Services
{
    /// <summary>
    /// Main plugin manager coordinating all plugin operations
    /// </summary>
    public class PluginManager : IDisposable
    {
        private readonly PluginLoader _loader;
        private readonly PluginConfigurationManager _configManager;
        private readonly DependencyResolver _dependencyResolver;
        private readonly Dictionary<string, IPlugin> _loadedPlugins = new();
        private readonly Dictionary<string, PluginSecurityPolicy> _securityPolicies = new();
        private readonly Dictionary<string, PluginExecutionMonitor> _executionMonitors = new();
        private readonly Dictionary<string, PluginPluginContext> _contexts = new();
        private readonly List<(string EventName, Func<object, Task> Handler, string PluginId)> _eventSubscriptions = new();

        public event EventHandler<PluginStateChangedEventArgs> PluginStateChanged;
        public event EventHandler<PluginEventArgs> PluginLoaded;
        public event EventHandler<PluginEventArgs> PluginUnloaded;

        public PluginManager(string pluginDirectoryPath, string configDirectoryPath)
        {
            _loader = new PluginLoader(pluginDirectoryPath);
            _configManager = new PluginConfigurationManager(configDirectoryPath);
            _dependencyResolver = new DependencyResolver();
        }

        /// <summary>
        /// Discover and load all plugins from directory
        /// </summary>
        public async Task<LoadResult> DiscoverAndLoadAllPluginsAsync()
        {
            var result = new LoadResult();
            var discovered = await _loader.DiscoverPluginsAsync();

            // Sort by priority
            var sorted = discovered
                .Where(p => p.IsValid)
                .OrderBy(p => p.Manifest.Priority)
                .ToList();

            foreach (var pluginInfo in sorted)
            {
                try
                {
                    var loadResult = await LoadPluginAsync(
                        pluginInfo.PluginTypes.First(),
                        pluginInfo.Manifest.Id,
                        pluginInfo.Manifest);

                    result.SuccessfulLoads.Add(loadResult.PluginId);
                }
                catch (Exception ex)
                {
                    result.FailedLoads[pluginInfo.Manifest.Id] = ex.Message;
                }
            }

            return result;
        }

        /// <summary>
        /// Load a plugin by type
        /// </summary>
        public async Task<LoadedPlugin> LoadPluginAsync(
            Type pluginType,
            string pluginId,
            PluginManifestData manifest = null)
        {
            if (_loadedPlugins.ContainsKey(pluginId))
            {
                throw new InvalidOperationException($"Plugin '{pluginId}' is already loaded");
            }

            try
            {
                // Create plugin instance
                var plugin = _loader.CreateInstance(pluginType) as IPlugin;
                if (plugin == null)
                {
                    throw new InvalidOperationException($"Failed to instantiate plugin {pluginType.Name}");
                }

                // Set security policy
                if (!_securityPolicies.ContainsKey(pluginId))
                {
                    _securityPolicies[pluginId] = PluginSecurityPolicy.CreateDefault(pluginId);
                }

                // Create plugin context
                var config = await _configManager.LoadConfigurationAsync(pluginId);
                var context = new PluginPluginContext(
                    pluginId,
                    config,
                    new ServiceProvider(),
                    new PluginLogger(plugin.Name),
                    this);

                _contexts[pluginId] = context;

                // Initialize plugin
                await plugin.InitializeAsync(context);

                // Subscribe to state changes
                plugin.StateChanged += (s, e) =>
                {
                    PluginStateChanged?.Invoke(this, e);
                };

                // Store monitoring
                _executionMonitors[pluginId] = new PluginExecutionMonitor(_securityPolicies[pluginId]);

                _loadedPlugins[pluginId] = plugin;
                PluginLoaded?.Invoke(this, new PluginEventArgs { PluginId = pluginId, Plugin = plugin });

                return new LoadedPlugin { PluginId = pluginId, Plugin = plugin };
            }
            catch (Exception ex)
            {
                throw new InvalidOperationException($"Failed to load plugin '{pluginId}'", ex);
            }
        }

        /// <summary>
        /// Start a plugin
        /// </summary>
        public async Task StartPluginAsync(string pluginId)
        {
            if (!_loadedPlugins.TryGetValue(pluginId, out var plugin))
            {
                throw new KeyNotFoundException($"Plugin '{pluginId}' not found");
            }

            await plugin.StartAsync();
        }

        /// <summary>
        /// Stop a plugin
        /// </summary>
        public async Task StopPluginAsync(string pluginId)
        {
            if (!_loadedPlugins.TryGetValue(pluginId, out var plugin))
            {
                throw new KeyNotFoundException($"Plugin '{pluginId}' not found");
            }

            await plugin.StopAsync();
        }

        /// <summary>
        /// Unload a plugin
        /// </summary>
        public async Task UnloadPluginAsync(string pluginId)
        {
            if (!_loadedPlugins.TryGetValue(pluginId, out var plugin))
            {
                throw new KeyNotFoundException($"Plugin '{pluginId}' not found");
            }

            try
            {
                if (plugin.State == PluginState.Running)
                {
                    await plugin.StopAsync();
                }

                plugin.Dispose();
                _loadedPlugins.Remove(pluginId);
                _contexts.Remove(pluginId);

                PluginUnloaded?.Invoke(this, new PluginEventArgs { PluginId = pluginId, Plugin = plugin });
            }
            catch (Exception ex)
            {
                throw new InvalidOperationException($"Failed to unload plugin '{pluginId}'", ex);
            }
        }

        /// <summary>
        /// Start all loaded plugins
        /// </summary>
        public async Task StartAllPluginsAsync()
        {
            var tasks = _loadedPlugins.Values
                .Where(p => p.State == PluginState.Initialized)
                .Select(p => p.StartAsync());

            await Task.WhenAll(tasks);
        }

        /// <summary>
        /// Stop all running plugins
        /// </summary>
        public async Task StopAllPluginsAsync()
        {
            var tasks = _loadedPlugins.Values
                .Where(p => p.State == PluginState.Running)
                .Select(p => p.StopAsync());

            await Task.WhenAll(tasks);
        }

        /// <summary>
        /// Reload plugin configuration
        /// </summary>
        public async Task ReloadPluginConfigAsync(string pluginId)
        {
            if (!_loadedPlugins.TryGetValue(pluginId, out var plugin))
            {
                throw new KeyNotFoundException($"Plugin '{pluginId}' not found");
            }

            await plugin.ReloadConfigAsync();
        }

        /// <summary>
        /// Get plugin by ID
        /// </summary>
        public IPlugin GetPlugin(string pluginId)
        {
            _loadedPlugins.TryGetValue(pluginId, out var plugin);
            return plugin;
        }

        /// <summary>
        /// Get all loaded plugins
        /// </summary>
        public IReadOnlyList<IPlugin> GetAllPlugins()
        {
            return _loadedPlugins.Values.ToList();
        }

        /// <summary>
        /// Get plugin health
        /// </summary>
        public async Task<PluginHealth> GetPluginHealthAsync(string pluginId)
        {
            if (!_loadedPlugins.TryGetValue(pluginId, out var plugin))
            {
                throw new KeyNotFoundException($"Plugin '{pluginId}' not found");
            }

            return await plugin.GetHealthAsync();
        }

        /// <summary>
        /// Get health for all plugins
        /// </summary>
        public async Task<Dictionary<string, PluginHealth>> GetAllPluginsHealthAsync()
        {
            var results = new Dictionary<string, PluginHealth>();

            foreach (var plugin in _loadedPlugins)
            {
                results[plugin.Key] = await plugin.Value.GetHealthAsync();
            }

            return results;
        }

        /// <summary>
        /// Execute a plugin command
        /// </summary>
        public async Task<PluginCommandResult> ExecuteCommandAsync(
            string pluginId,
            string commandName,
            Dictionary<string, object> parameters = null)
        {
            if (!_loadedPlugins.TryGetValue(pluginId, out var plugin))
            {
                return PluginCommandResult.Error($"Plugin '{pluginId}' not found");
            }

            try
            {
                var result = await plugin.ExecuteCommandAsync(commandName, parameters ?? new());
                return result;
            }
            catch (Exception ex)
            {
                return PluginCommandResult.Error($"Command execution failed: {ex.Message}");
            }
        }

        /// <summary>
        /// Set security policy for a plugin
        /// </summary>
        public void SetSecurityPolicy(string pluginId, PluginSecurityPolicy policy)
        {
            _securityPolicies[pluginId] = policy ?? throw new ArgumentNullException(nameof(policy));
        }

        /// <summary>
        /// Get execution metrics for a plugin
        /// </summary>
        public ExecutionMetrics GetExecutionMetrics(string pluginId)
        {
            if (_executionMonitors.TryGetValue(pluginId, out var monitor))
            {
                return monitor.GetMetrics();
            }
            return new ExecutionMetrics();
        }

        /// <summary>
        /// Publish an event for plugins to subscribe to
        /// </summary>
        public async Task PublishEventAsync(string pluginId, string eventName, object eventData)
        {
            var handlers = _eventSubscriptions
                .Where(s => s.EventName == eventName && s.PluginId != pluginId)
                .ToList();

            foreach (var (_, handler, _) in handlers)
            {
                try
                {
                    await handler?.Invoke(eventData);
                }
                catch
                {
                    // Log error but continue
                }
            }
        }

        /// <summary>
        /// Subscribe to events from other plugins
        /// </summary>
        public void SubscribeToEvent(string pluginId, string eventName, Func<object, Task> handler)
        {
            _eventSubscriptions.Add((eventName, handler, pluginId));
        }

        /// <summary>
        /// Get platform status
        /// </summary>
        public async Task<PlatformStatus> GetStatusAsync()
        {
            var status = new PlatformStatus
            {
                TotalPluginsLoaded = _loadedPlugins.Count,
                RunningPlugins = _loadedPlugins.Values.Count(p => p.State == PluginState.Running),
                PluginStates = new()
            };

            foreach (var plugin in _loadedPlugins)
            {
                status.PluginStates[plugin.Key] = new PluginStatus
                {
                    Id = plugin.Key,
                    Name = plugin.Value.Name,
                    State = plugin.Value.State,
                    Version = plugin.Value.Version,
                    Health = await plugin.Value.GetHealthAsync()
                };
            }

            return status;
        }

        public void Dispose()
        {
            Task.Run(async () => await StopAllPluginsAsync()).Wait();

            foreach (var plugin in _loadedPlugins.Values)
            {
                plugin?.Dispose();
            }

            _loadedPlugins.Clear();
            _contexts.Clear();
            _securityPolicies.Clear();
            _executionMonitors.Clear();
        }
    }

    /// <summary>
    /// Plugin context implementation
    /// </summary>
    public class PluginPluginContext : IPluginContext
    {
        private readonly PluginManager _pluginManager;

        public string PluginId { get; }
        public IPluginConfiguration Configuration { get; }
        public IServiceProvider ServiceProvider { get; }
        public IPluginLogger Logger { get; }

        public PluginPluginContext(
            string pluginId,
            IPluginConfiguration configuration,
            IServiceProvider serviceProvider,
            IPluginLogger logger,
            PluginManager pluginManager)
        {
            PluginId = pluginId;
            Configuration = configuration;
            ServiceProvider = serviceProvider;
            Logger = logger;
            _pluginManager = pluginManager;
        }

        public IPlugin GetPlugin(string pluginId) => _pluginManager.GetPlugin(pluginId);

        public void RegisterService(string serviceName, object serviceInstance)
        {
            // Implementation would store service in ServiceProvider
        }

        public object GetService(string serviceName)
        {
            // Implementation would retrieve from ServiceProvider
            return null;
        }

        public async Task PublishEventAsync(string eventName, object eventData)
        {
            await _pluginManager.PublishEventAsync(PluginId, eventName, eventData);
        }

        public void SubscribeToEvent(string eventName, Func<object, Task> handler)
        {
            _pluginManager.SubscribeToEvent(PluginId, eventName, handler);
        }
    }

    /// <summary>
    /// Service provider implementation
    /// </summary>
    public class ServiceProvider : IServiceProvider
    {
        private readonly Dictionary<Type, object> _services = new();

        public object GetService(Type serviceType)
        {
            _services.TryGetValue(serviceType, out var service);
            return service;
        }

        public void Register<T>(T instance) where T : class
        {
            _services[typeof(T)] = instance;
        }
    }

    /// <summary>
    /// Load result information
    /// </summary>
    public class LoadResult
    {
        public List<string> SuccessfulLoads { get; } = new();
        public Dictionary<string, string> FailedLoads { get; } = new();

        public bool IsSuccessful => FailedLoads.Count == 0;
    }

    /// <summary>
    /// Loaded plugin information
    /// </summary>
    public class LoadedPlugin
    {
        public string PluginId { get; set; }
        public IPlugin Plugin { get; set; }
    }

    /// <summary>
    /// Plugin event arguments
    /// </summary>
    public class PluginEventArgs : EventArgs
    {
        public string PluginId { get; set; }
        public IPlugin Plugin { get; set; }
    }

    /// <summary>
    /// Platform status
    /// </summary>
    public class PlatformStatus
    {
        public int TotalPluginsLoaded { get; set; }
        public int RunningPlugins { get; set; }
        public Dictionary<string, PluginStatus> PluginStates { get; set; } = new();
    }

    /// <summary>
    /// Individual plugin status
    /// </summary>
    public class PluginStatus
    {
        public string Id { get; set; }
        public string Name { get; set; }
        public string Version { get; set; }
        public PluginState State { get; set; }
        public PluginHealth Health { get; set; }
    }
}
