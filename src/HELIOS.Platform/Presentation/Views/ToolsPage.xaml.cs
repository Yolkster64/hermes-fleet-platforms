using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Input;
using System.Collections.ObjectModel;
using System.Diagnostics;

namespace HELIOS.Platform.Presentation.Views;

public class ToolItem
{
    public string? Name { get; set; }
    public string? Description { get; set; }
    public string? Icon { get; set; }
    public string? Command { get; set; }
}

public sealed partial class ToolsPage : Page
{
    public ObservableCollection<ToolItem> DiagnosticTools { get; } = new();
    public ObservableCollection<ToolItem> MaintenanceTools { get; } = new();
    public ObservableCollection<ToolItem> OptimizationTools { get; } = new();

    public ToolsPage()
    {
        this.InitializeComponent();
        InitializeTools();
    }

    private void InitializeTools()
    {
        // System Diagnostics
        DiagnosticTools.Add(new ToolItem
        {
            Name = "System Health",
            Description = "Check system status and health metrics",
            Icon = "❤️",
            Command = "systeminfo"
        });
        DiagnosticTools.Add(new ToolItem
        {
            Name = "Event Viewer",
            Description = "View system event logs and errors",
            Icon = "📋",
            Command = "eventvwr"
        });
        DiagnosticTools.Add(new ToolItem
        {
            Name = "Device Manager",
            Description = "Manage hardware devices and drivers",
            Icon = "🖥️",
            Command = "devmgmt.msc"
        });
        DiagnosticTools.Add(new ToolItem
        {
            Name = "Resource Monitor",
            Description = "Monitor system resource usage",
            Icon = "📊",
            Command = "resmon"
        });
        DiagnosticTools.Add(new ToolItem
        {
            Name = "Task Manager",
            Description = "View and manage running processes",
            Icon = "⚙️",
            Command = "taskmgr"
        });
        DiagnosticTools.Add(new ToolItem
        {
            Name = "Performance Monitor",
            Description = "Monitor system performance metrics",
            Icon = "📈",
            Command = "perfmon"
        });

        // Maintenance Tools
        MaintenanceTools.Add(new ToolItem
        {
            Name = "Disk Cleanup",
            Description = "Free up disk space by removing temporary files",
            Icon = "🧹",
            Command = "cleanmgr"
        });
        MaintenanceTools.Add(new ToolItem
        {
            Name = "Disk Defragmentation",
            Description = "Optimize disk performance",
            Icon = "💽",
            Command = "dfrgui"
        });
        MaintenanceTools.Add(new ToolItem
        {
            Name = "Backup & Restore",
            Description = "Create system backups and recovery points",
            Icon = "💾",
            Command = "sdclt"
        });
        MaintenanceTools.Add(new ToolItem
        {
            Name = "System Restore",
            Description = "Restore system to previous state",
            Icon = "↩️",
            Command = "rstrui"
        });
        MaintenanceTools.Add(new ToolItem
        {
            Name = "Windows Update",
            Description = "Check for and install updates",
            Icon = "🔄",
            Command = "ms-settings:update"
        });
        MaintenanceTools.Add(new ToolItem
        {
            Name = "Network Troubleshooting",
            Description = "Diagnose network connection issues",
            Icon = "🌐",
            Command = "msdt"
        });

        // Optimization Tools
        OptimizationTools.Add(new ToolItem
        {
            Name = "Startup Manager",
            Description = "Manage startup programs and services",
            Icon = "🚀",
            Command = "msconfig"
        });
        OptimizationTools.Add(new ToolItem
        {
            Name = "Service Manager",
            Description = "Control Windows services",
            Icon = "🔧",
            Command = "services.msc"
        });
        OptimizationTools.Add(new ToolItem
        {
            Name = "Power Settings",
            Description = "Configure power management options",
            Icon = "⚡",
            Command = "powercfg.cpl"
        });
        OptimizationTools.Add(new ToolItem
        {
            Name = "Memory Optimizer",
            Description = "Optimize system memory usage",
            Icon = "💾",
            Command = "optimize-memory"
        });
        OptimizationTools.Add(new ToolItem
        {
            Name = "Network Optimizer",
            Description = "Optimize network performance",
            Icon = "🚄",
            Command = "optimize-network"
        });
        OptimizationTools.Add(new ToolItem
        {
            Name = "GPU Optimization",
            Description = "Configure GPU settings and drivers",
            Icon = "🎮",
            Command = "nvidia-smi"
        });
    }

    private void Tool_Click(object sender, ItemClickEventArgs e)
    {
        if (e.ClickedItem is ToolItem tool)
        {
            ExecuteTool(tool);
        }
    }

    private void ExecuteTool(ToolItem tool)
    {
        try
        {
            if (tool.Command?.StartsWith("ms-settings:") == true)
            {
                _ = Windows.System.Launcher.LaunchUriAsync(new System.Uri(tool.Command));
            }
            else if (tool.Command?.StartsWith("optimize-") == true)
            {
                System.Diagnostics.Debug.WriteLine($"Executing optimization: {tool.Command}");
                // TODO: Execute optimization command
            }
            else if (!string.IsNullOrEmpty(tool.Command))
            {
                var psi = new ProcessStartInfo
                {
                    FileName = tool.Command,
                    UseShellExecute = true
                };
                Process.Start(psi);
            }
        }
        catch (System.Exception ex)
        {
            System.Diagnostics.Debug.WriteLine($"Error executing tool {tool.Name}: {ex.Message}");
        }
    }

    private void ToolCard_PointerEntered(object sender, PointerRoutedEventArgs e)
    {
        // Add hover effects
        if (sender is StackPanel panel)
        {
            panel.Opacity = 0.9;
        }
    }

    private void ToolCard_PointerExited(object sender, PointerRoutedEventArgs e)
    {
        if (sender is StackPanel panel)
        {
            panel.Opacity = 1.0;
        }
    }
}
