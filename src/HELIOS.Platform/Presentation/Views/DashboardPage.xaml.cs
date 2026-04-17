using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using System;
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

    public DashboardPage()
    {
        this.InitializeComponent();
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
            // CPU Usage
            var cpuUsage = GetCpuUsage();
            CpuPercentText.Text = $"{cpuUsage:F1}%";
            CpuProgressBar.Value = cpuUsage;
            CpuCoresText.Text = $"{Environment.ProcessorCount} cores";

            // Memory Usage
            var (usedMem, totalMem) = GetMemoryUsage();
            var memPercent = (usedMem / (double)totalMem) * 100;
            MemoryPercentText.Text = $"{memPercent:F1}%";
            MemoryProgressBar.Value = memPercent;
            MemoryUsageText.Text = $"{usedMem / 1024:F1} GB / {totalMem / 1024:F1} GB";

            // Disk Usage
            var (usedDisk, totalDisk) = GetDiskUsage();
            var diskPercent = (usedDisk / (double)totalDisk) * 100;
            DiskPercentText.Text = $"{diskPercent:F1}%";
            DiskProgressBar.Value = diskPercent;
            DiskUsageText.Text = $"{usedDisk / 1024:F1} GB / {totalDisk / 1024:F1} GB";

            // Services
            var services = GetRunningServices();
            ServiceCountText.Text = services.ToString();
            ServiceProgressBar.Value = Math.Min(services * 10, 100);
            ServiceStatusText.Text = $"{services} running";

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
            var processes = Process.GetProcesses()
                .Select(p =>
                {
                    try
                    {
                        return new ProcessDisplay
                        {
                            ProcessId = p.Id,
                            Name = p.ProcessName,
                            MemoryUsageMb = p.WorkingSet64 / (1024.0 * 1024.0),
                            CpuUsagePercent = GetProcessCpuUsage(p.Id)
                        };
                    }
                    catch
                    {
                        return null;
                    }
                })
                .Where(p => p != null)
                .OrderByDescending(p => p?.MemoryUsageMb)
                .Take(10)
                .ToList();

            ProcessesListView.ItemsSource = processes;
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
            var infoItems = new[]
            {
                new SystemInfoItem { Label = "OS", Value = GetOsName() },
                new SystemInfoItem { Label = "Computer", Value = Environment.MachineName },
                new SystemInfoItem { Label = "User", Value = Environment.UserName },
                new SystemInfoItem { Label = "Uptime", Value = GetSystemUptime() },
                new SystemInfoItem { Label = "Processes", Value = Process.GetProcesses().Length.ToString() },
                new SystemInfoItem { Label = "Threads", Value = Process.GetCurrentProcess().Threads.Count.ToString() }
            };

            SystemInfoControl.ItemsSource = infoItems;
            await Task.CompletedTask;
        }
        catch (Exception ex)
        {
            Debug.WriteLine($"Error updating system info: {ex.Message}");
        }
    }

    private double GetCpuUsage()
    {
        try
        {
            using var cpuCounter = new PerformanceCounter("Processor", "% Processor Time", "_Total");
            cpuCounter.NextValue(); // First call is always 0
            return cpuCounter.NextValue();
        }
        catch
        {
            return 0;
        }
    }

    private double GetProcessCpuUsage(int processId)
    {
        try
        {
            using var cpuCounter = new PerformanceCounter(
                "Process", "% Processor Time", Process.GetProcessById(processId).ProcessName);
            cpuCounter.NextValue();
            return cpuCounter.NextValue() / Environment.ProcessorCount;
        }
        catch
        {
            return 0;
        }
    }

    private (long Used, long Total) GetMemoryUsage()
    {
        try
        {
            var comp = new Microsoft.VisualBasic.Devices.ComputerInfo();
            var total = (long)(comp.TotalPhysicalMemory / (1024.0 * 1024.0));
            var available = (long)(comp.AvailablePhysicalMemory / (1024.0 * 1024.0));
            return (total - available, total);
        }
        catch
        {
            return (0, 1);
        }
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
        catch
        {
            return 0;
        }
    }

    private string GetOsName()
    {
        var ver = Environment.OSVersion;
        return $"Windows {ver.VersionString}";
    }

    private string GetSystemUptime()
    {
        try
        {
            var uptime = DateTime.Now - new DateTime(new System.Diagnostics.ProcessStartInfo()
                .UseShellExecute = false;
            var result = System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo()
            {
                FileName = "powershell",
                Arguments = "-Command \"(Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime\"",
                UseShellExecute = false,
                RedirectStandardOutput = true,
                CreateNoWindow = true
            });

            if (result?.WaitForExit(5000) == true)
            {
                var output = result.StandardOutput.ReadToEnd().Trim();
                if (TimeSpan.TryParse(output, out var timespan))
                {
                    var days = timespan.Days;
                    var hours = timespan.Hours;
                    return $"{days}d {hours}h";
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
