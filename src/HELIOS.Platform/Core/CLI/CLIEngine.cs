using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;

namespace HELIOS.Platform.Core.CLI
{
    /// <summary>
    /// Main CLI Engine that orchestrates command execution and output formatting
    /// </summary>
    public class CLIEngine
    {
        private readonly CommandParser _parser;
        private readonly CommandExecutor _executor;
        private readonly CommandHistory _history;
        private readonly OutputFormatter _formatter;
        private CLIOptions _options;

        public CLIEngine()
        {
            _parser = new CommandParser();
            _executor = new CommandExecutor();
            _history = new CommandHistory();
            _formatter = new OutputFormatter();
            _options = new CLIOptions();
        }

        /// <summary>
        /// Initialize the CLI engine with command-line arguments
        /// </summary>
        public void Initialize(string[] args)
        {
            _options = _parser.ParseArguments(args);
            _history.LoadHistory();
        }

        /// <summary>
        /// Execute a command from command line arguments
        /// </summary>
        public async Task<int> ExecuteAsync(string[] args)
        {
            Initialize(args);

            if (_options.ShowHelp)
            {
                PrintHelp();
                return 0;
            }

            if (_options.ShowVersion)
            {
                PrintVersion();
                return 0;
            }

            if (string.IsNullOrWhiteSpace(_options.Command))
            {
                if (!_options.IsQuiet)
                    Console.WriteLine("No command specified. Use 'helios-cli help' for usage.");
                return 1;
            }

            try
            {
                var result = await _executor.ExecuteAsync(_options);
                
                if (!_options.IsQuiet)
                {
                    var output = _options.OutputFormat switch
                    {
                        OutputFormat.Json => _formatter.FormatAsJson(result),
                        OutputFormat.Verbose => _formatter.FormatAsVerbose(result),
                        _ => _formatter.FormatAsDefault(result)
                    };
                    Console.Write(output);
                }

                _history.RecordCommand(_options);
                
                return result.ExitCode;
            }
            catch (Exception ex)
            {
                if (!_options.IsQuiet)
                {
                    if (_options.IsVerbose)
                        Console.Error.WriteLine($"ERROR: {ex}");
                    else
                        Console.Error.WriteLine($"ERROR: {ex.Message}");
                }
                return 1;
            }
        }

        /// <summary>
        /// Execute from interactive mode
        /// </summary>
        public async Task InteractiveAsync()
        {
            _history.LoadHistory();
            Console.WriteLine("HELIOS CLI Interactive Mode. Type 'exit' to quit, 'help' for commands.");
            
            while (true)
            {
                Console.Write("helios> ");
                var input = Console.ReadLine();

                if (string.IsNullOrWhiteSpace(input))
                    continue;

                if (input.Equals("exit", StringComparison.OrdinalIgnoreCase) ||
                    input.Equals("quit", StringComparison.OrdinalIgnoreCase))
                    break;

                var args = input.Split(' ', StringSplitOptions.RemoveEmptyEntries);
                await ExecuteAsync(args);
            }
        }

        private void PrintHelp()
        {
            Console.WriteLine(@"
HELIOS CLI - Platform Management Tool
=====================================

USAGE:
  helios-cli [OPTIONS] <COMMAND> [ARGS]

COMMANDS:
  deploy      Deploy components or applications
  config      Manage configuration
  status      Show platform status
  health      Check system health
  restart     Restart services
  scale       Scale components
  backup      Create backups
  restore     Restore from backups
  list        List resources
  watch       Watch resource changes
  execute     Execute scripts
  schedule    Schedule tasks
  history     Show command history
  help        Show this help message

OPTIONS:
  -h, --help          Show help message
  -v, --version       Show version
  -q, --quiet         Suppress output
  --verbose           Verbose output
  -j, --json          Output in JSON format
  -o, --output FILE   Write output to file
  --timeout SEC       Command timeout in seconds

EXAMPLES:
  helios-cli status
  helios-cli deploy --config app.json
  helios-cli health --verbose
  helios-cli list --json
  helios-cli scale web --instances 5
  helios-cli backup --path /backups

For more information, visit the documentation.");
        }

        private void PrintVersion()
        {
            Console.WriteLine("HELIOS CLI v1.0.0");
            Console.WriteLine("Platform Version: 7.0.0");
        }
    }

    /// <summary>
    /// Options parsed from command line
    /// </summary>
    public class CLIOptions
    {
        public string Command { get; set; }
        public Dictionary<string, string> Parameters { get; set; } = new();
        public List<string> Arguments { get; set; } = new();
        public bool ShowHelp { get; set; }
        public bool ShowVersion { get; set; }
        public bool IsQuiet { get; set; }
        public bool IsVerbose { get; set; }
        public OutputFormat OutputFormat { get; set; } = OutputFormat.Default;
        public string OutputFile { get; set; }
        public int TimeoutSeconds { get; set; } = 30;
    }

    public enum OutputFormat
    {
        Default,
        Json,
        Verbose
    }
}
