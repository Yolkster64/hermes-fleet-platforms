using System;
using System.Collections.Generic;
using System.Security;
using System.Security.Permissions;

namespace HELIOS.Platform.Core.Plugins.Security
{
    /// <summary>
    /// Security sandbox for plugin execution
    /// Restricts plugin access to sensitive operations
    /// </summary>
    public class PluginSecuritySandbox
    {
        private readonly PermissionSet _permissionSet;
        private readonly string _pluginName;

        public PluginSecuritySandbox(string pluginName, SecurityLevel level = SecurityLevel.Medium)
        {
            _pluginName = pluginName;
            _permissionSet = CreatePermissionSet(level);
        }

        /// <summary>
        /// Create a permission set based on security level
        /// </summary>
        private PermissionSet CreatePermissionSet(SecurityLevel level)
        {
            var permissions = new PermissionSet(PermissionState.None);

            // Basic permissions (all levels)
            permissions.AddPermission(new SecurityPermission(SecurityPermissionFlag.Execution));

            switch (level)
            {
                case SecurityLevel.Minimal:
                    // Only execution permission
                    break;

                case SecurityLevel.Low:
                    // Add limited file I/O for plugin directory
                    permissions.AddPermission(new FileIOPermission(FileIOPermissionAccess.Read));
                    break;

                case SecurityLevel.Medium:
                    // Add file I/O and environment variables
                    permissions.AddPermission(new FileIOPermission(FileIOPermissionAccess.Read | FileIOPermissionAccess.Write));
                    permissions.AddPermission(new EnvironmentPermission(EnvironmentPermissionAccess.Read));
                    permissions.AddPermission(new ReflectionPermission(ReflectionPermissionFlag.RestrictedMemberAccess));
                    break;

                case SecurityLevel.High:
                    // Most operations allowed (not full trust)
                    permissions.AddPermission(new FileIOPermission(PermissionState.Unrestricted));
                    permissions.AddPermission(new EnvironmentPermission(PermissionState.Unrestricted));
                    permissions.AddPermission(new ReflectionPermission(PermissionState.Unrestricted));
                    permissions.AddPermission(new SecurityPermission(SecurityPermissionFlag.UnmanagedCode));
                    break;
            }

            return permissions;
        }

        /// <summary>
        /// Execute code within the sandbox
        /// </summary>
        public void ExecuteInSandbox(Action action)
        {
            try
            {
                _permissionSet.PermitOnly();
                action?.Invoke();
            }
            finally
            {
                CodeAccessPermission.RevertPermitOnly();
            }
        }

        /// <summary>
        /// Execute code within the sandbox and return result
        /// </summary>
        public T ExecuteInSandbox<T>(Func<T> func)
        {
            try
            {
                _permissionSet.PermitOnly();
                return func?.Invoke();
            }
            finally
            {
                CodeAccessPermission.RevertPermitOnly();
            }
        }

        /// <summary>
        /// Check if plugin has permission
        /// </summary>
        public bool HasPermission(IPermission permission)
        {
            try
            {
                _permissionSet.Demand();
                return true;
            }
            catch (SecurityException)
            {
                return false;
            }
        }

        public string PluginName => _pluginName;
        public SecurityLevel Level { get; }
    }

    /// <summary>
    /// Security levels for plugins
    /// </summary>
    public enum SecurityLevel
    {
        /// <summary>
        /// Only execution permission - most restricted
        /// </summary>
        Minimal = 0,

        /// <summary>
        /// Read-only file access
        /// </summary>
        Low = 1,

        /// <summary>
        /// File I/O and basic environment access
        /// </summary>
        Medium = 2,

        /// <summary>
        /// Most operations allowed except unmanaged code
        /// </summary>
        High = 3,

        /// <summary>
        /// Full trust (use with caution)
        /// </summary>
        Full = 4
    }

    /// <summary>
    /// Plugin security policy
    /// </summary>
    public class PluginSecurityPolicy
    {
        public string PluginId { get; set; }
        public SecurityLevel DefaultLevel { get; set; } = SecurityLevel.Medium;
        public bool AllowNetworkAccess { get; set; } = false;
        public bool AllowFileSystem { get; set; } = true;
        public bool AllowReflection { get; set; } = true;
        public bool AllowUnmanagedCode { get; set; } = false;
        public List<string> AllowedAssemblies { get; set; } = new();
        public List<string> BlockedNamespaces { get; set; } = new();
        public long MaxMemoryMB { get; set; } = 512;
        public long MaxExecutionTimeMs { get; set; } = 30000;
        public Dictionary<string, object> CustomRules { get; set; } = new();

        public static PluginSecurityPolicy CreateDefault(string pluginId)
        {
            return new PluginSecurityPolicy
            {
                PluginId = pluginId,
                DefaultLevel = SecurityLevel.Medium,
                AllowNetworkAccess = false,
                AllowFileSystem = true,
                AllowReflection = true,
                AllowUnmanagedCode = false
            };
        }

        public static PluginSecurityPolicy CreateFullTrust(string pluginId)
        {
            return new PluginSecurityPolicy
            {
                PluginId = pluginId,
                DefaultLevel = SecurityLevel.Full,
                AllowNetworkAccess = true,
                AllowFileSystem = true,
                AllowReflection = true,
                AllowUnmanagedCode = true
            };
        }

        public static PluginSecurityPolicy CreateRestricted(string pluginId)
        {
            return new PluginSecurityPolicy
            {
                PluginId = pluginId,
                DefaultLevel = SecurityLevel.Low,
                AllowNetworkAccess = false,
                AllowFileSystem = false,
                AllowReflection = false,
                AllowUnmanagedCode = false
            };
        }
    }

    /// <summary>
    /// Monitor plugin execution for policy violations
    /// </summary>
    public class PluginExecutionMonitor
    {
        private readonly PluginSecurityPolicy _policy;
        private readonly Dictionary<string, ExecutionMetrics> _metrics = new();

        public PluginExecutionMonitor(PluginSecurityPolicy policy)
        {
            _policy = policy ?? throw new ArgumentNullException(nameof(policy));
        }

        /// <summary>
        /// Record execution metrics
        /// </summary>
        public void RecordExecution(string operationName, long durationMs, long memoryUsedBytes)
        {
            var key = _policy.PluginId;
            if (!_metrics.ContainsKey(key))
            {
                _metrics[key] = new ExecutionMetrics();
            }

            var metrics = _metrics[key];
            metrics.TotalExecutions++;
            metrics.TotalDurationMs += durationMs;
            metrics.PeakMemoryMB = Math.Max(metrics.PeakMemoryMB, memoryUsedBytes / (1024 * 1024));
            metrics.LastExecutionTime = DateTime.UtcNow;

            // Check for violations
            if (durationMs > _policy.MaxExecutionTimeMs)
            {
                metrics.TimeoutViolations++;
            }

            if ((memoryUsedBytes / (1024 * 1024)) > _policy.MaxMemoryMB)
            {
                metrics.MemoryViolations++;
            }
        }

        public ExecutionMetrics GetMetrics()
        {
            return _metrics.TryGetValue(_policy.PluginId, out var m) ? m : new ExecutionMetrics();
        }

        public bool IsCompliant()
        {
            var metrics = GetMetrics();
            return metrics.TimeoutViolations == 0 && metrics.MemoryViolations == 0;
        }
    }

    /// <summary>
    /// Execution metrics for a plugin
    /// </summary>
    public class ExecutionMetrics
    {
        public int TotalExecutions { get; set; }
        public long TotalDurationMs { get; set; }
        public long PeakMemoryMB { get; set; }
        public int TimeoutViolations { get; set; }
        public int MemoryViolations { get; set; }
        public DateTime LastExecutionTime { get; set; }

        public double AverageDurationMs => TotalExecutions > 0 ? (double)TotalDurationMs / TotalExecutions : 0;
    }
}
