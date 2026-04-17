using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;

namespace HELIOS.Platform.Core.CLI
{
    /// <summary>
    /// Batch processor for executing multiple commands
    /// </summary>
    public class BatchProcessor
    {
        private readonly CLIEngine _engine;
        private List<BatchCommand> _commands;

        public BatchProcessor()
        {
            _engine = new CLIEngine();
            _commands = new List<BatchCommand>();
        }

        /// <summary>
        /// Load batch commands from JSON file
        /// </summary>
        public void LoadBatch(string filePath)
        {
            try
            {
                var json = File.ReadAllText(filePath);
                var batch = JsonSerializer.Deserialize<BatchFile>(json);
                _commands = batch?.Commands ?? new();
            }
            catch (Exception ex)
            {
                throw new Exception($"Failed to load batch file: {ex.Message}");
            }
        }

        /// <summary>
        /// Load batch commands from JSON string
        /// </summary>
        public void LoadBatchJson(string json)
        {
            try
            {
                var batch = JsonSerializer.Deserialize<BatchFile>(json);
                _commands = batch?.Commands ?? new();
            }
            catch (Exception ex)
            {
                throw new Exception($"Failed to parse batch JSON: {ex.Message}");
            }
        }

        /// <summary>
        /// Execute batch commands
        /// </summary>
        public async Task<BatchResult> ExecuteAsync(bool stopOnError = true)
        {
            var result = new BatchResult
            {
                StartedAt = DateTime.UtcNow,
                Commands = new List<BatchCommandResult>()
            };

            foreach (var cmd in _commands)
            {
                try
                {
                    var args = BuildArgs(cmd);
                    var cmdResult = await _engine.ExecuteAsync(args);

                    result.Commands.Add(new BatchCommandResult
                    {
                        CommandName = cmd.Name,
                        ExitCode = cmdResult,
                        Message = "Executed",
                        ExecutionTimeMs = 0
                    });

                    if (cmdResult != 0 && stopOnError)
                    {
                        result.Status = "Failed";
                        break;
                    }
                }
                catch (Exception ex)
                {
                    result.Commands.Add(new BatchCommandResult
                    {
                        CommandName = cmd.Name,
                        ExitCode = 1,
                        Message = ex.Message,
                        ExecutionTimeMs = 0
                    });

                    if (stopOnError)
                    {
                        result.Status = "Failed";
                        break;
                    }
                }
            }

            result.CompletedAt = DateTime.UtcNow;
            if (result.Status != "Failed")
                result.Status = "Completed";

            return result;
        }

        private string[] BuildArgs(BatchCommand cmd)
        {
            var args = new List<string> { cmd.Command };
            
            if (cmd.Arguments != null)
                args.AddRange(cmd.Arguments);

            if (cmd.Options != null)
            {
                foreach (var opt in cmd.Options)
                {
                    args.Add($"--{opt.Key}");
                    if (!string.IsNullOrEmpty(opt.Value))
                        args.Add(opt.Value);
                }
            }

            return args.ToArray();
        }
    }

    public class BatchFile
    {
        public string Name { get; set; }
        public string Description { get; set; }
        public List<BatchCommand> Commands { get; set; } = new();
    }

    public class BatchCommand
    {
        public string Name { get; set; }
        public string Command { get; set; }
        public List<string> Arguments { get; set; } = new();
        public Dictionary<string, string> Options { get; set; } = new();
        public int? TimeoutSeconds { get; set; }
    }

    public class BatchResult
    {
        public string Status { get; set; } = "Pending";
        public DateTime StartedAt { get; set; }
        public DateTime CompletedAt { get; set; }
        public List<BatchCommandResult> Commands { get; set; } = new();
        
        public long TotalExecutionTimeMs 
        { 
            get { return (long)(CompletedAt - StartedAt).TotalMilliseconds; }
        }

        public int SuccessCount
        {
            get { return Commands.Count(c => c.ExitCode == 0); }
        }

        public int FailureCount
        {
            get { return Commands.Count(c => c.ExitCode != 0); }
        }
    }

    public class BatchCommandResult
    {
        public string CommandName { get; set; }
        public int ExitCode { get; set; }
        public string Message { get; set; }
        public long ExecutionTimeMs { get; set; }
    }
}
