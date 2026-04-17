using System;
using System.Threading;
using System.Threading.Tasks;
using HELIOS.Platform.Core;
using HELIOS.Platform.BackendServices.ServerManagement;
using HELIOS.Platform.Core.Logging;
using HELIOS.Platform.Core.Diagnostics;
using HELIOS.Platform.Core.Storage;
using HELIOS.Platform.Core.Configuration;
using HELIOS.Platform.Core.Security;
using HELIOS.Platform.Core.Monitoring;
using HELIOS.Platform.Core.Administration;
using HELIOS.Platform.Core.CLI;
using HELIOS.Platform.Core.Plugins;
using HELIOS.Platform.Core.RemoteAccess;
using HELIOS.Platform.Core.GPU;
using HELIOS.Platform.Core.Automation;
using HELIOS.Platform.Core.AI;
using HELIOS.Platform.Core.Backup;
using HELIOS.Platform.Core.Cloud;
using HELIOS.Platform.Core.Sandbox;
using HELIOS.Platform.Core.Hardware;
using HELIOS.Platform.Core.Integration;

namespace HELIOS.Platform
{
    class Program
    {
        static async Task Main(string[] args)
        {
            try
            {
                Console.WriteLine("╔════════════════════════════════════════════════════════════════╗");
                Console.WriteLine("║          HELIOS Platform - Enterprise Management System         ║");
                Console.WriteLine("║                    Version 2.0 Foundation                       ║");
                Console.WriteLine("╚════════════════════════════════════════════════════════════════╝");
                Console.WriteLine();
                
                // Initialize core services
                var logger = new ConsoleLogger();
                var orchestrator = new ServiceOrchestrator();
                var diagnostics = new SystemDiagnostics();
                var storage = new StorageManager();
                var config = new Core.Configuration.ConfigurationManager();
                var encryption = new EncryptionManager();
                var dashboardTracker = new DashboardHistoryTracker();
                var systemManagement = new SystemManagementService();
                var cliExecutor = new CliCommandExecutor(orchestrator, systemManagement);
                
                Console.WriteLine("✓ HELIOS Platform initialized successfully");
                Console.WriteLine("✓ All core services loaded and ready");
                
                // CLI execution
                if (args.Length > 0)
                {
                    var result = await cliExecutor.ExecuteAsync(string.Join(" ", args));
                    Console.WriteLine(result);
                }
                else
                {
                    Console.WriteLine("HELIOS Platform is ready. Use 'help' to see available commands.");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"✗ Error: {ex.Message}");
                Console.WriteLine($"  Details: {ex.InnerException?.Message}");
                Environment.Exit(1);
            }
        }
    }
}
