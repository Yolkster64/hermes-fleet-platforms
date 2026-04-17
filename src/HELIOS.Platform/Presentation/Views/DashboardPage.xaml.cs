using HELIOS.Platform.BackendServices.ServerManagement;
using HELIOS.Platform.Core;
using HELIOS.Platform.Core.Performance;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Diagnostics;
using System.Linq;
using System.Threading.Tasks;
using System.Timers;

namespace HELIOS.Platform.Presentation.Views;

public class SystemInfoItem
{
    public string? Label { get; set; }
    public string? Value { get; set; }
}

public class ProcessDisplay
{
    public int ProcessId { get; set; }
    public string? Name { get; set; }
    public double MemoryUsageMb { get; set; }
    public double CpuUsagePercent { get; set; }
}

public sealed partial class DashboardPage : Page
{
    private Timer? _refreshTimer;
    private DateTime _lastUpdate = DateTime.MinValue;
    private readonly IServiceOrchestrator _serviceOrchestrator;
    private readonly CpuProfiler _cpuProfiler;
    private readonly MemoryProfiler _memoryProfiler;
    private readonly IPerformanceProfiler _performanceProfiler;

    public DashboardPage()
    {
        this.InitializeComponent();
        
        _serviceOrchestrator = ServiceContainer.Instance.GetService<IServiceOrchestrator>() ?? new ServiceOrchestrator();
        _cpuProfiler = ServiceContainer.Instance.GetService<CpuProfiler>() ?? new CpuProfiler();
        _memoryProfiler = ServiceContainer.Instance.GetService<MemoryProfiler>() ?? new MemoryProfiler();
        _performanceProfiler = ServiceContainer.Instance.GetService<IPerformanceProfiler>() ?? new PerformanceProfiler();
        
        _ = InitializeAsync();
    }

    private async Task InitializeAsync()
    {
        await RefreshDashboardAsync();
        _refreshTimer = new Timer(5000); // Refresh every 5 seconds
        _refreshTimer.Elapsed += async (s, e) => await RefreshDashboardAsync();
        _refreshTimer.AutoReset = true;
        _refreshTimer.Start();
    }

    private async Task RefreshDashboardAsync()
    {
        try
        {
            await DispatcherQueue.EnqueueAsync(async () =>
            {
                await UpdateSystemMetricsAsync();
                await UpdateProcessesAsync();
                await UpdateSystemInfoAsync();
                LastUpdateText.Text = $"Last updated: {DateTime.Now:HH:mm:ss}";
            });
        }
        catch (Exception ex)
        {
            Debug.WriteLine($"Error refreshing dashboard: {ex.Message}");
        }
    }

    private async Task UpdateSystemMetricsAsync()
    {
        try
        {
            using var _ = _performanceProfiler.Profile("UpdateSystemMetrics");
            
            var systemResources = await _serviceOrchestrator.GetSystemResourcesAsync();

            // CPU Usage
            CpuPercentText.Text = $"{systemResources.CpuUsagePercent:F1}%";
            CpuProgressBar.Value = Math.Min(systemResources.CpuUsagePercent, 100);
            CpuCoresText.Text = $"{_cpuProfiler.GetProcessorCount()} cores";

            // Memory Usage
            MemoryPercentText.Text = $"{systemResources.MemoryUsagePercent:F1}%";
            MemoryProgressBar.Value = Math.Min(systemResources.MemoryUsagePercent, 100);
            MemoryUsageText.Text = $"{systemResources.MemoryUsedMb / 1024:F1} GB / {systemResources.MemoryTotalMb / 1024:F1} GB";

            // Disk Usage (fetch from drive info)
            var (usedDisk, totalDisk) = GetDiskUsage();
            var diskPercent = (usedDisk / (double)totalDisk) * 100;
            DiskPercentText.Text = $"{diskPercent:F1}%";
            DiskProgressBar.Value = Math.Min(diskPercent, 100);
            DiskUsageText.Text = $"{usedDisk / 1024:F1} GB / {totalDisk / 1024:F1} GB";

            // Services
            ServiceCountText.Text = systemResources.ProcessCount.ToString();
            ServiceProgressBar.Value = Math.Min(systemResources.ProcessCount * 10, 100);
            ServiceStatusText.Text = $"{systemResources.ProcessCount} processes running";

            await Task.CompletedTask;
        }
        catch (Exception ex)
        {
            Debug.WriteLine($"Error updating metrics: {ex.Message}");
        }
    }

    private async Task UpdateProcessesAsync()
    {
        try
        {
            using var _ = _performanceProfiler.Profile("UpdateProcesses");
            
            var processes = await _serviceOrchestrator.GetAllProcessesAsync();
            var processDisplays = processes
                .OrderByDescending(p => p.MemoryUsageMb)
                .Take(10)
                .Select(p => new ProcessDisplay
                {
                    ProcessId = p.ProcessId,
                    Name = p.Name,
                    MemoryUsageMb = p.MemoryUsageMb,
                    CpuUsagePercent = p.CpuUsagePercent
                })
                .ToList();

            ProcessesListView.ItemsSource = processDisplays;
            await Task.CompletedTask;
        }
        catch (Exception ex)
        {
            Debug.WriteLine($"Error updating processes: {ex.Message}");
        }
    }

    private async Task UpdateSystemInfoAsync()
    {
        try
        {
            using var _ = _performanceProfiler.Profile("UpdateSystemInfo");
            
            var systemResources = await _serviceOrchestrator.GetSystemResourcesAsync();
            
            var infoItems = new[]
            {
                new SystemInfoItem { Label = "OS", Value = GetOsName() },
                new SystemInfoItem { Label = "Computer", Value = Environment.MachineName },
                new SystemInfoItem { Label = "User", Value = Environment.UserName },
                new SystemInfoItem { Label = "Uptime", Value = GetSystemUptime() },
                new SystemInfoItem { Label = "Processes", Value = systemResources.ProcessCount.ToString() },
                new SystemInfoItem { Label = "Threads", Value = systemResources.ThreadCount.ToString() }
            };

            SystemInfoControl.ItemsSource = infoItems;
            await Task.CompletedTask;
        }
        catch (Exception ex)
        {
            Debug.WriteLine($"Error updating system info: {ex.Message}");
        }
    }

    private double GetCpuUsage() => _cpuProfiler.GetCpuUsage();

    private (long Used, long Total) GetMemoryUsage()
    {
        var usedPercent = _memoryProfiler.GetMemoryUsagePercent();
        var totalMb = (long)(new Microsoft.VisualBasic.Devices.ComputerInfo().TotalPhysicalMemory / (1024.0 * 1024.0));
        var usedMb = (long)((usedPercent / 100.0) * totalMb);
        return (usedMb, totalMb);
    }

    private (long Used, long Total) GetDiskUsage()
    {
        try
        {
            var drive = System.IO.DriveInfo.GetDrives()
                .FirstOrDefault(d => d.IsReady && d.Name.StartsWith("C:"));

            if (drive != null)
            {
                var total = drive.TotalSize / (1024 * 1024);
                var used = (drive.TotalSize - drive.AvailableFreeSpace) / (1024 * 1024);
                return (used, total);
            }
        }
        catch { }

        return (0, 1);
    }

    private int GetRunningServices()
    {
        try
        {
            return System.ServiceProcess.ServiceController.GetServices()
                .Count(s => s.Status == System.ServiceProcess.ServiceControllerStatus.Running);
        }
        catch { return 0; }
    }

    private string GetOsName()
    {
        try
        {
            var winVersion = Environment.OSVersion;
            var productName = Microsoft.Win32.Registry.GetValue(
                @"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion", 
                "ProductName", "Windows");
            var releaseId = Microsoft.Win32.Registry.GetValue(
                @"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion", 
                "DisplayVersion", "");
            return $"{productName} ({releaseId})";
        }
        catch { return Environment.OSVersion.VersionString; }
    }

    private string GetSystemUptime()
    {
        try
        {
            var result = System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo()
            {
                FileName = "powershell",
                Arguments = "-Command \"[math]::Round((Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime | % TotalSeconds)\"",
                UseShellExecute = false,
                RedirectStandardOutput = true,
                CreateNoWindow = true
            });

            if (result?.WaitForExit(5000) == true)
            {
                var output = result.StandardOutput.ReadToEnd().Trim();
                if (long.TryParse(output, out var seconds))
                {
                    var days = seconds / 86400;
                    var hours = (seconds % 86400) / 3600;
                    var minutes = (seconds % 3600) / 60;
                    return $"{days}d {hours}h {minutes}m";
                }
            }
        }
        catch { }

        return "Unknown";
    }

    private void RefreshButton_Click(object sender, RoutedEventArgs e)
    {
        _ = RefreshDashboardAsync();
    }

    private void SettingsButton_Click(object sender, RoutedEventArgs e)
    {
        _ = Windows.System.Launcher.LaunchUriAsync(new Uri("ms-settings:"));
    }

    private void SystemInfoButton_Click(object sender, RoutedEventArgs e)
    {
        _ = Windows.System.Launcher.LaunchUriAsync(new Uri("ms-settings:system-about"));
    }

    private void PerformanceButton_Click(object sender, RoutedEventArgs e)
    {
        // Launch Task Manager
        try
        {
            var psi = new ProcessStartInfo
            {
                FileName = "taskmgr.exe",
                UseShellExecute = true
            };
            Process.Start(psi);
        }
        catch { }
    }
}
