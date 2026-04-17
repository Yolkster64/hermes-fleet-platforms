using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace HELIOS.Platform.Core.CLI
{
    /// <summary>
    /// Task scheduling configuration
    /// </summary>
    public class ScheduledTask
    {
        public string Id { get; set; } = Guid.NewGuid().ToString();
        public string Name { get; set; }
        public string Description { get; set; }
        public string Command { get; set; }
        public string Schedule { get; set; } // "daily", "weekly", "hourly", cron expression
        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
        public DateTime? LastRun { get; set; }
        public DateTime? NextRun { get; set; }
        public bool Enabled { get; set; } = true;
        public Dictionary<string, string> Parameters { get; set; } = new();
        public int RunCount { get; set; }
        public int FailureCount { get; set; }
    }

    /// <summary>
    /// Manages scheduled task execution
    /// </summary>
    public class TaskScheduler
    {
        private readonly List<ScheduledTask> _tasks;

        public TaskScheduler()
        {
            _tasks = new List<ScheduledTask>();
        }

        /// <summary>
        /// Schedule a new task
        /// </summary>
        public ScheduledTask Schedule(string name, string command, string schedule, Dictionary<string, string> parameters = null)
        {
            var task = new ScheduledTask
            {
                Name = name,
                Command = command,
                Schedule = schedule,
                Parameters = parameters ?? new()
            };

            _tasks.Add(task);
            return task;
        }

        /// <summary>
        /// Get all scheduled tasks
        /// </summary>
        public List<ScheduledTask> GetAllTasks()
        {
            return new List<ScheduledTask>(_tasks);
        }

        /// <summary>
        /// Get enabled tasks that are due to run
        /// </summary>
        public List<ScheduledTask> GetDueTasks()
        {
            var now = DateTime.UtcNow;
            return _tasks.FindAll(t => t.Enabled && t.NextRun.HasValue && t.NextRun <= now);
        }

        /// <summary>
        /// Remove a scheduled task
        /// </summary>
        public bool RemoveTask(string taskId)
        {
            return _tasks.RemoveAll(t => t.Id == taskId) > 0;
        }

        /// <summary>
        /// Enable a task
        /// </summary>
        public bool EnableTask(string taskId)
        {
            var task = _tasks.Find(t => t.Id == taskId);
            if (task != null)
            {
                task.Enabled = true;
                return true;
            }
            return false;
        }

        /// <summary>
        /// Disable a task
        /// </summary>
        public bool DisableTask(string taskId)
        {
            var task = _tasks.Find(t => t.Id == taskId);
            if (task != null)
            {
                task.Enabled = false;
                return true;
            }
            return false;
        }

        /// <summary>
        /// Update task run statistics
        /// </summary>
        public void RecordExecution(string taskId, bool success)
        {
            var task = _tasks.Find(t => t.Id == taskId);
            if (task != null)
            {
                task.LastRun = DateTime.UtcNow;
                task.RunCount++;
                if (!success)
                    task.FailureCount++;
                task.NextRun = CalculateNextRun(task);
            }
        }

        private DateTime? CalculateNextRun(ScheduledTask task)
        {
            var now = DateTime.UtcNow;
            
            return task.Schedule.ToLower() switch
            {
                "hourly" => now.AddHours(1),
                "daily" => now.AddDays(1),
                "weekly" => now.AddDays(7),
                "monthly" => now.AddMonths(1),
                _ => now.AddHours(1) // default
            };
        }
    }
}
