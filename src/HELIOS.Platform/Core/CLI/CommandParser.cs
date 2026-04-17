using System;
using System.Collections.Generic;
using System.Linq;

namespace HELIOS.Platform.Core.CLI
{
    /// <summary>
    /// Parses command-line arguments into CLIOptions
    /// </summary>
    public class CommandParser
    {
        private const char ParameterPrefix = '-';
        private const string LongParameterPrefix = "--";

        public CLIOptions ParseArguments(string[] args)
        {
            if (args == null || args.Length == 0)
                return new CLIOptions();

            var options = new CLIOptions();
            var positionalArgs = new List<string>();

            for (int i = 0; i < args.Length; i++)
            {
                var arg = args[i];

                if (arg.StartsWith(LongParameterPrefix))
                {
                    var parameterName = arg.Substring(2);
                    HandleLongParameter(parameterName, args, ref i, options, positionalArgs);
                }
                else if (arg.StartsWith(ParameterPrefix.ToString()) && arg.Length > 1)
                {
                    var shortParams = arg.Substring(1);
                    HandleShortParameters(shortParams, args, ref i, options, positionalArgs);
                }
                else
                {
                    positionalArgs.Add(arg);
                }
            }

            // First positional argument is the command
            if (positionalArgs.Count > 0)
            {
                options.Command = positionalArgs[0];
                options.Arguments = positionalArgs.Skip(1).ToList();
            }

            return options;
        }

        private void HandleLongParameter(string parameter, string[] args, ref int index, CLIOptions options, List<string> positionalArgs)
        {
            var parts = parameter.Split('=', 2);
            var name = parts[0].ToLower();
            var value = parts.Length > 1 ? parts[1] : null;

            switch (name)
            {
                case "help":
                    options.ShowHelp = true;
                    break;
                case "version":
                    options.ShowVersion = true;
                    break;
                case "quiet":
                    options.IsQuiet = true;
                    break;
                case "verbose":
                    options.IsVerbose = true;
                    break;
                case "json":
                    options.OutputFormat = OutputFormat.Json;
                    break;
                case "output":
                    if (value == null && index + 1 < args.Length)
                        options.OutputFile = args[++index];
                    else
                        options.OutputFile = value;
                    break;
                case "timeout":
                    if (value == null && index + 1 < args.Length)
                        value = args[++index];
                    if (int.TryParse(value, out var timeout))
                        options.TimeoutSeconds = timeout;
                    break;
                default:
                    // Store as parameter
                    if (value == null && index + 1 < args.Length && !args[index + 1].StartsWith("-"))
                        value = args[++index];
                    options.Parameters[name] = value ?? "true";
                    break;
            }
        }

        private void HandleShortParameters(string shortParams, string[] args, ref int index, CLIOptions options, List<string> positionalArgs)
        {
            foreach (var c in shortParams)
            {
                switch (c)
                {
                    case 'h':
                        options.ShowHelp = true;
                        break;
                    case 'v':
                        options.ShowVersion = true;
                        break;
                    case 'q':
                        options.IsQuiet = true;
                        break;
                    case 'j':
                        options.OutputFormat = OutputFormat.Json;
                        break;
                    case 'o':
                        if (index + 1 < args.Length)
                            options.OutputFile = args[++index];
                        break;
                    default:
                        break;
                }
            }
        }

        /// <summary>
        /// Parse parameters from a dictionary format
        /// </summary>
        public Dictionary<string, object> ParseParameters(Dictionary<string, string> parameters)
        {
            var result = new Dictionary<string, object>();
            
            foreach (var kvp in parameters)
            {
                // Try to parse as different types
                if (kvp.Value.Equals("true", StringComparison.OrdinalIgnoreCase))
                    result[kvp.Key] = true;
                else if (kvp.Value.Equals("false", StringComparison.OrdinalIgnoreCase))
                    result[kvp.Key] = false;
                else if (int.TryParse(kvp.Value, out var intVal))
                    result[kvp.Key] = intVal;
                else if (double.TryParse(kvp.Value, out var doubleVal))
                    result[kvp.Key] = doubleVal;
                else if (kvp.Value.StartsWith("[") && kvp.Value.EndsWith("]"))
                    result[kvp.Key] = ParseArray(kvp.Value);
                else
                    result[kvp.Key] = kvp.Value;
            }

            return result;
        }

        private List<string> ParseArray(string arrayStr)
        {
            var content = arrayStr.Substring(1, arrayStr.Length - 2);
            return content.Split(',').Select(s => s.Trim().Trim('"')).ToList();
        }
    }
}
