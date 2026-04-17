using System;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace HELIOS.Platform.Core.CLI
{
    /// <summary>
    /// Formats command output in different formats
    /// </summary>
    public class OutputFormatter
    {
        private readonly JsonSerializerOptions _jsonOptions;

        public OutputFormatter()
        {
            _jsonOptions = new JsonSerializerOptions
            {
                WriteIndented = true,
                DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
            };
        }

        /// <summary>
        /// Format output as JSON
        /// </summary>
        public string FormatAsJson(CommandResult result)
        {
            return JsonSerializer.Serialize(result, _jsonOptions) + Environment.NewLine;
        }

        /// <summary>
        /// Format output as verbose text
        /// </summary>
        public string FormatAsVerbose(CommandResult result)
        {
            var output = "";
            output += $"EXIT CODE: {result.ExitCode}\n";
            output += $"MESSAGE: {result.Message}\n";
            output += $"EXECUTED: {result.ExecutedAt:O}\n";
            output += $"DURATION: {result.ExecutionTimeMs}ms\n";
            
            if (result.Data != null)
            {
                output += "\nDATA:\n";
                output += FormatObject(result.Data, 2);
            }

            if (result.Warnings.Count > 0)
            {
                output += "\nWARNINGS:\n";
                foreach (var warning in result.Warnings)
                    output += $"  - {warning}\n";
            }

            if (result.Metadata.Count > 0)
            {
                output += "\nMETADATA:\n";
                foreach (var kvp in result.Metadata)
                    output += $"  {kvp.Key}: {kvp.Value}\n";
            }

            return output + "\n";
        }

        /// <summary>
        /// Format output as default text
        /// </summary>
        public string FormatAsDefault(CommandResult result)
        {
            if (result.ExitCode != 0)
                return $"ERROR: {result.Message}\n";

            var output = "";

            if (!string.IsNullOrWhiteSpace(result.Message))
                output += $"{result.Message}\n";

            if (result.Data != null)
                output += FormatObject(result.Data, 0);

            return output + "\n";
        }

        private string FormatObject(object obj, int indent)
        {
            if (obj == null)
                return "";

            var indentStr = new string(' ', indent);
            var nextIndentStr = new string(' ', indent + 2);

            if (obj is System.Collections.IEnumerable enumerable && !(obj is string))
            {
                var output = "";
                foreach (var item in enumerable)
                {
                    if (item is System.Collections.IDictionary dict)
                    {
                        foreach (System.Collections.DictionaryEntry entry in dict)
                        {
                            output += $"{nextIndentStr}{entry.Key}: ";
                            if (entry.Value is System.Collections.IEnumerable && !(entry.Value is string))
                                output += "\n" + FormatObject(entry.Value, indent + 4);
                            else
                                output += $"{entry.Value}\n";
                        }
                    }
                    else
                    {
                        output += $"{nextIndentStr}{item}\n";
                    }
                }
                return output;
            }

            var json = JsonSerializer.Serialize(obj, _jsonOptions);
            return indentStr + json;
        }
    }
}
