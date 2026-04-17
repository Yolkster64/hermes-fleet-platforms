namespace HELIOS.Platform.BackendServices.ServerManagement;

/// <summary>
/// Core server management and service orchestration.
/// </summary>
public interface IServiceOrchestrator
{
    /// <summary>Starts a service by name.</summary>
    Task<ServiceOperationResult> StartServiceAsync(string serviceName);

    /// <summary>Stops a service by name.</summary>
    Task<ServiceOperationResult> StopServiceAsync(string serviceName);

    /// <summary>Restarts a service by name.</summary>
    Task<ServiceOperationResult> RestartServiceAsync(string serviceName);

    /// <summary>Gets service status.</summary>
    Task<ServiceStatus> GetServiceStatusAsync(string serviceName);

    /// <summary>Gets all service statuses.</summary>
    Task<IEnumerable<ServiceStatus>> GetAllServicesAsync();

    /// <summary>Gets process information.</summary>
    Task<ProcessInfo> GetProcessInfoAsync(int processId);

    /// <summary>Gets all running processes.</summary>
    Task<IEnumerable<ProcessInfo>> GetAllProcessesAsync();

    /// <summary>Kills a process.</summary>
    Task<ServiceOperationResult> KillProcessAsync(int processId);

    /// <summary>Gets system resource usage.</summary>
    Task<SystemResources> GetSystemResourcesAsync();

    /// <summary>Performs health check on all services.</summary>
    Task<IEnumerable<ServiceHealthCheck>> PerformHealthCheckAsync();
}

/// <summary>
/// Result of a service operation.
/// </summary>
public class ServiceOperationResult
{
    public required bool Success { get; init; }
    public string? Message { get; set; }
    public Exception? Exception { get; set; }
    public long ElapsedMilliseconds { get; set; }
}

/// <summary>
/// Status of a service.
/// </summary>
public class ServiceStatus
{
    public required string Name { get; init; }
    public required ServiceState State { get; init; }
    public required bool IsRunning { get; init; }
    public DateTime? StartTime { get; set; }
    public int? ProcessId { get; set; }
    public string? ServiceType { get; set; }
    public double MemoryUsageMb { get; set; }
    public double CpuUsagePercent { get; set; }
    public string? Description { get; set; }
}

/// <summary>
/// Service state enumeration.
/// </summary>
public enum ServiceState
{
    Running,
    Stopped,
    Paused,
    StartPending,
    StopPending,
    ContinuePending,
    PausePending,
    Unknown,
    Disabled
}

/// <summary>
/// Process information.
/// </summary>
public class ProcessInfo
{
    public required int ProcessId { get; init; }
    public required string Name { get; init; }
    public double MemoryUsageMb { get; set; }
    public double CpuUsagePercent { get; set; }
    public DateTime? StartTime { get; set; }
    public int ThreadCount { get; set; }
    public string? State { get; set; }
    public string? ExecutablePath { get; set; }
}

/// <summary>
/// System resource usage.
/// </summary>
public class SystemResources
{
    public double CpuUsagePercent { get; set; }
    public double MemoryUsagePercent { get; set; }
    public long MemoryAvailableMb { get; set; }
    public long MemoryUsedMb { get; set; }
    public long MemoryTotalMb { get; set; }
    public double DiskUsagePercent { get; set; }
    public long DiskAvailableMb { get; set; }
    public long DiskUsedMb { get; set; }
    public long DiskTotalMb { get; set; }
    public int ProcessCount { get; set; }
    public int ThreadCount { get; set; }
    public DateTime MeasuredAt { get; set; }
}

/// <summary>
/// Service health check result.
/// </summary>
public class ServiceHealthCheck
{
    public required string ServiceName { get; init; }
    public required bool IsHealthy { get; init; }
    public required int ResponseTimeMs { get; init; }
    public string? Message { get; set; }
    public DateTime CheckedAt { get; set; }
}

/// <summary>
/// Default implementation of service orchestrator.
/// </summary>
public class ServiceOrchestrator : IServiceOrchestrator
{
    public async Task<ServiceOperationResult> StartServiceAsync(string serviceName)
    {
        var startTime = System.Diagnostics.Stopwatch.StartNew();
        try
        {
            var svc = GetService(serviceName);
            if (svc == null)
                return new ServiceOperationResult { Success = false, Message = $"Service not found: {serviceName}" };

            if (svc.Status != System.ServiceProcess.ServiceControllerStatus.Running)
            {
                svc.Start();
                svc.WaitForStatus(System.ServiceProcess.ServiceControllerStatus.Running, TimeSpan.FromSeconds(10));
            }

            return new ServiceOperationResult
            {
                Success = true,
                Message = $"Service started: {serviceName}",
                ElapsedMilliseconds = startTime.ElapsedMilliseconds
            };
        }
        catch (Exception ex)
        {
            return new ServiceOperationResult
            {
                Success = false,
                Message = ex.Message,
                Exception = ex,
                ElapsedMilliseconds = startTime.ElapsedMilliseconds
            };
        }
    }

    public async Task<ServiceOperationResult> StopServiceAsync(string serviceName)
    {
        var startTime = System.Diagnostics.Stopwatch.StartNew();
        try
        {
            var svc = GetService(serviceName);
            if (svc == null)
                return new ServiceOperationResult { Success = false, Message = $"Service not found: {serviceName}" };

            if (svc.Status != System.ServiceProcess.ServiceControllerStatus.Stopped)
            {
                svc.Stop();
                svc.WaitForStatus(System.ServiceProcess.ServiceControllerStatus.Stopped, TimeSpan.FromSeconds(10));
            }

            return new ServiceOperationResult
            {
                Success = true,
                Message = $"Service stopped: {serviceName}",
                ElapsedMilliseconds = startTime.ElapsedMilliseconds
            };
        }
        catch (Exception ex)
        {
            return new ServiceOperationResult
            {
                Success = false,
                Message = ex.Message,
                Exception = ex,
                ElapsedMilliseconds = startTime.ElapsedMilliseconds
            };
        }
    }

    public async Task<ServiceOperationResult> RestartServiceAsync(string serviceName)
    {
        await StopServiceAsync(serviceName);
        await Task.Delay(1000);
        return await StartServiceAsync(serviceName);
    }

    public async Task<ServiceStatus> GetServiceStatusAsync(string serviceName)
    {
        try
        {
            var svc = GetService(serviceName);
            if (svc == null)
                return new ServiceStatus { Name = serviceName, State = ServiceState.Unknown, IsRunning = false };

            var process = GetProcessForService(svc);
            return new ServiceStatus
            {
                Name = serviceName,
                State = (ServiceState)(int)svc.Status,
                IsRunning = svc.Status == System.ServiceProcess.ServiceControllerStatus.Running,
                ProcessId = process?.Id,
                StartTime = process?.StartTime,
                MemoryUsageMb = process?.WorkingSet64 / (1024.0 * 1024.0) ?? 0,
                Description = svc.DisplayName
            };
        }
        catch
        {
            return new ServiceStatus { Name = serviceName, State = ServiceState.Unknown, IsRunning = false };
        }
    }

    public async Task<IEnumerable<ServiceStatus>> GetAllServicesAsync()
    {
        var results = new List<ServiceStatus>();
        foreach (var service in System.ServiceProcess.ServiceController.GetServices())
        {
            try
            {
                results.Add(await GetServiceStatusAsync(service.ServiceName));
            }
            catch { }
        }
        return results;
    }

    public async Task<ProcessInfo> GetProcessInfoAsync(int processId)
    {
        var proc = System.Diagnostics.Process.GetProcessById(processId);
        return new ProcessInfo
        {
            ProcessId = proc.Id,
            Name = proc.ProcessName,
            MemoryUsageMb = proc.WorkingSet64 / (1024.0 * 1024.0),
            StartTime = proc.StartTime,
            ThreadCount = proc.Threads.Count,
            State = "Running"
        };
    }

    public async Task<IEnumerable<ProcessInfo>> GetAllProcessesAsync()
    {
        var results = new List<ProcessInfo>();
        foreach (var proc in System.Diagnostics.Process.GetProcesses())
        {
            try
            {
                results.Add(new ProcessInfo
                {
                    ProcessId = proc.Id,
                    Name = proc.ProcessName,
                    MemoryUsageMb = proc.WorkingSet64 / (1024.0 * 1024.0),
                    StartTime = proc.StartTime,
                    ThreadCount = proc.Threads.Count
                });
            }
            catch { }
        }
        return results.OrderByDescending(p => p.MemoryUsageMb);
    }

    public async Task<ServiceOperationResult> KillProcessAsync(int processId)
    {
        try
        {
            var proc = System.Diagnostics.Process.GetProcessById(processId);
            proc.Kill();
            return new ServiceOperationResult { Success = true, Message = $"Process killed: {processId}" };
        }
        catch (Exception ex)
        {
            return new ServiceOperationResult { Success = false, Message = ex.Message, Exception = ex };
        }
    }

    public async Task<SystemResources> GetSystemResourcesAsync()
    {
        var totalRam = (long)new Microsoft.VisualBasic.Devices.ComputerInfo().TotalPhysicalMemory / (1024 * 1024);
        var availRam = new Microsoft.VisualBasic.Devices.ComputerInfo().AvailablePhysicalMemory / (1024 * 1024);
        var procs = System.Diagnostics.Process.GetProcesses();

        return new SystemResources
        {
            CpuUsagePercent = GetCpuUsage(),
            MemoryUsagePercent = ((totalRam - availRam) / (double)totalRam) * 100,
            MemoryUsedMb = totalRam - availRam,
            MemoryAvailableMb = availRam,
            MemoryTotalMb = totalRam,
            ProcessCount = procs.Length,
            ThreadCount = procs.Sum(p => p.Threads.Count),
            MeasuredAt = DateTime.UtcNow
        };
    }

    public async Task<IEnumerable<ServiceHealthCheck>> PerformHealthCheckAsync()
    {
        var results = new List<ServiceHealthCheck>();
        foreach (var service in await GetAllServicesAsync())
        {
            results.Add(new ServiceHealthCheck
            {
                ServiceName = service.Name,
                IsHealthy = service.IsRunning,
                ResponseTimeMs = 0,
                Message = service.IsRunning ? "Healthy" : $"Not running",
                CheckedAt = DateTime.UtcNow
            });
        }
        return results;
    }

    private System.ServiceProcess.ServiceController? GetService(string name)
    {
        try { return new System.ServiceProcess.ServiceController(name); }
        catch { return null; }
    }

    private System.Diagnostics.Process? GetProcessForService(System.ServiceProcess.ServiceController svc)
    {
        try { return System.Diagnostics.Process.GetProcessById(svc.ServiceHandle.DangerousGetHandle().ToInt32()); }
        catch { return null; }
    }

    private double GetCpuUsage()
    {
        try
        {
            using var cpuCounter = new System.Diagnostics.PerformanceCounter("Processor", "% Processor Time", "_Total");
            return cpuCounter.NextValue();
        }
        catch { return 0; }
    }
}
