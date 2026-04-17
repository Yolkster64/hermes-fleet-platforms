using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;

namespace HELIOS.Platform.Core.CLI
{
    /// <summary>
    /// Tracks and manages command history
    /// </summary>
    public class CommandHistory
    {
        private readonly string _historyPath;
        private List<CommandHistoryEntry> _entries;
        private const int MaxHistorySize = 500;

        public CommandHistory()
        {
            _historyPath = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                "HELIOS", 
                "history.json"
            );
            _entries = new List<CommandHistoryEntry>();
        }

        /// <summary>
        /// Load history from disk
        /// </summary>
        public void LoadHistory()
        {
            try
            {
                if (File.Exists(_historyPath))
                {
                    var json = File.ReadAllText(_historyPath);
                    _entries = JsonSerializer.Deserialize<List<CommandHistoryEntry>>(json) ?? new();
                }
            }
            catch
            {
                _entries = new List<CommandHistoryEntry>();
            }
        }

        /// <summary>
        /// Record a command in history
        /// </summary>
        public void RecordCommand(CLIOptions options)
        {
            var entry = new CommandHistoryEntry
            {
                Command = options.Command,
                Arguments = string.Join(" ", options.Arguments),
                Parameters = options.Parameters,
                ExecutedAt = DateTime.UtcNow,
                WorkingDirectory = Environment.CurrentDirectory
            };

            _entries.Add(entry);

            // Keep history manageable
            if (_entries.Count > MaxHistorySize)
                _entries = _entries.TakeLast(MaxHistorySize).ToList();

            SaveHistory();
        }

        /// <summary>
        /// Save history to disk
        /// </summary>
        private void SaveHistory()
        {
            try
            {
                var dir = Path.GetDirectoryName(_historyPath);
                if (!Directory.Exists(dir))
                    Directory.CreateDirectory(dir);

                var json = JsonSerializer.Serialize(_entries, new JsonSerializerOptions { WriteIndented = true });
                File.WriteAllText(_historyPath, json);
            }
            catch
            {
                // Silently fail if history can't be saved
            }
        }

        /// <summary>
        /// Get history entries
        /// </summary>
        public List<CommandHistoryEntry> GetHistory(int count = 50)
        {
            return _entries.TakeLast(count).Reverse().ToList();
        }

        /// <summary>
        /// Search history
        /// </summary>
        public List<CommandHistoryEntry> Search(string query)
        {
            return _entries
                .Where(e => e.Command.Contains(query, StringComparison.OrdinalIgnoreCase) ||
                           e.Arguments.Contains(query, StringComparison.OrdinalIgnoreCase))
                .ToList();
        }

        /// <summary>
        /// Clear history
        /// </summary>
        public void Clear()
        {
            _entries.Clear();
            try { File.Delete(_historyPath); } catch { }
        }
    }

    public class CommandHistoryEntry
    {
        public string Command { get; set; }
        public string Arguments { get; set; }
        public Dictionary<string, string> Parameters { get; set; }
        public DateTime ExecutedAt { get; set; }
        public string WorkingDirectory { get; set; }
    }
}
