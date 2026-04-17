using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Threading.Tasks;

namespace HELIOS.Platform.Core.Performance;

/// <summary>
/// Performance profiling and optimization system.
/// </summary>
public interface IPerformanceProfiler
{
    /// <summary>Starts profiling a named operation.</summary>
    IDisposable Profile(string operationName);

    /// <summary>Records a performance measurement.</summary>
    void RecordMeasurement(string operationName, long milliseconds);

    /// <summary>Gets performance statistics for an operation.</summary>
    PerformanceStatistics? GetStatistics(string operationName);

    /// <summary>Gets all recorded statistics.</summary>
    IEnumerable<PerformanceStatistics> GetAllStatistics();

    /// <summary>Resets all statistics.</summary>
    void Reset();

    /// <summary>Generates a performance report.</summary>
    PerformanceReport GenerateReport();

    /// <summary>Exports statistics to file.</summary>
    Task ExportStatisticsAsync(string filePath);
}

/// <summary>
/// Performance statistics for an operation.
/// </summary>
public class PerformanceStatistics
{
    public required string OperationName { get; init; }
    public long Count { get; set; }
    public long TotalMilliseconds { get; set; }
    public long MinMilliseconds { get; set; } = long.MaxValue;
    public long MaxMilliseconds { get; set; }
    public double AverageMilliseconds => Count > 0 ? TotalMilliseconds / (double)Count : 0;
    public double MedianMilliseconds { get; set; }
    public double PercentileP95 { get; set; }
    public double PercentileP99 { get; set; }
}

/// <summary>
/// Performance report with analysis.
/// </summary>
public class PerformanceReport
{
    public DateTime GeneratedAt { get; init; } = DateTime.UtcNow;
    public List<PerformanceStatistics> Statistics { get; init; } = new();
    public string? Bottleneck { get; set; }
    public List<string> Recommendations { get; init; } = new();

    public override string ToString()
    {
        var sb = new System.Text.StringBuilder();
        sb.AppendLine($"Performance Report - {GeneratedAt:yyyy-MM-dd HH:mm:ss}");
        sb.AppendLine(new string('-', 60));

        foreach (var stat in Statistics.OrderByDescending(s => s.TotalMilliseconds))
        {
            sb.AppendLine($"{stat.OperationName}:");
            sb.AppendLine($"  Count: {stat.Count}");
            sb.AppendLine($"  Average: {stat.AverageMilliseconds:F2}ms");
            sb.AppendLine($"  Min: {stat.MinMilliseconds}ms, Max: {stat.MaxMilliseconds}ms");
            sb.AppendLine($"  P95: {stat.PercentileP95:F2}ms, P99: {stat.PercentileP99:F2}ms");
        }

        if (Recommendations.Count > 0)
        {
            sb.AppendLine("\nRecommendations:");
            foreach (var rec in Recommendations)
                sb.AppendLine($"  • {rec}");
        }

        return sb.ToString();
    }
}

/// <summary>
/// Profiling scope for automatic stopwatch management.
/// </summary>
private class ProfilingScope : IDisposable
{
    private readonly IPerformanceProfiler _profiler;
    private readonly string _operationName;
    private readonly Stopwatch _stopwatch;

    public ProfilingScope(IPerformanceProfiler profiler, string operationName)
    {
        _profiler = profiler;
        _operationName = operationName;
        _stopwatch = Stopwatch.StartNew();
    }

    public void Dispose()
    {
        _stopwatch.Stop();
        _profiler.RecordMeasurement(_operationName, _stopwatch.ElapsedMilliseconds);
    }
}

/// <summary>
/// Default implementation of performance profiler.
/// </summary>
public class PerformanceProfiler : IPerformanceProfiler
{
    private readonly Dictionary<string, List<long>> _measurements = new();
    private readonly object _lockObject = new();

    public IDisposable Profile(string operationName)
    {
        return new ProfilingScope(this, operationName);
    }

    public void RecordMeasurement(string operationName, long milliseconds)
    {
        lock (_lockObject)
        {
            if (!_measurements.ContainsKey(operationName))
                _measurements[operationName] = new List<long>();
            _measurements[operationName].Add(milliseconds);
        }
    }

    public PerformanceStatistics? GetStatistics(string operationName)
    {
        lock (_lockObject)
        {
            if (!_measurements.TryGetValue(operationName, out var measurements) || measurements.Count == 0)
                return null;

            var sorted = measurements.OrderBy(m => m).ToList();
            return new PerformanceStatistics
            {
                OperationName = operationName,
                Count = measurements.Count,
                TotalMilliseconds = measurements.Sum(),
                MinMilliseconds = measurements.Min(),
                MaxMilliseconds = measurements.Max(),
                MedianMilliseconds = CalculatePercentile(sorted, 50),
                PercentileP95 = CalculatePercentile(sorted, 95),
                PercentileP99 = CalculatePercentile(sorted, 99)
            };
        }
    }

    public IEnumerable<PerformanceStatistics> GetAllStatistics()
    {
        lock (_lockObject)
        {
            return _measurements.Keys.Select(k => GetStatistics(k)!).ToList();
        }
    }

    public void Reset()
    {
        lock (_lockObject)
        {
            _measurements.Clear();
        }
    }

    public PerformanceReport GenerateReport()
    {
        lock (_lockObject)
        {
            var stats = GetAllStatistics().ToList();
            var report = new PerformanceReport { Statistics = stats };

            var bottleneck = stats.OrderByDescending(s => s.TotalMilliseconds).FirstOrDefault();
            if (bottleneck != null)
                report.Bottleneck = $"{bottleneck.OperationName} ({bottleneck.TotalMilliseconds}ms)";

            foreach (var stat in stats.Where(s => s.AverageMilliseconds > 1000))
                report.Recommendations.Add($"Optimize {stat.OperationName} - average {stat.AverageMilliseconds:F0}ms");

            return report;
        }
    }

    public async Task ExportStatisticsAsync(string filePath)
    {
        var report = GenerateReport();
        System.IO.File.WriteAllText(filePath, report.ToString());
        await Task.CompletedTask;
    }

    private static double CalculatePercentile(List<long> values, int percentile)
    {
        if (values.Count == 0) return 0;
        var index = (percentile / 100.0) * (values.Count - 1);
        var lower = (int)Math.Floor(index);
        var upper = (int)Math.Ceiling(index);
        var weight = index - lower;
        return lower == upper ? values[lower] : values[lower] * (1 - weight) + values[upper] * weight;
    }
}

/// <summary>
/// CPU usage monitor.
/// </summary>
public class CpuProfiler
{
    public double GetCpuUsage()
    {
        try
        {
            using var cpuCounter = new PerformanceCounter("Processor", "% Processor Time", "_Total");
            cpuCounter.NextValue();
            return cpuCounter.NextValue();
        }
        catch { return 0; }
    }

    public int GetProcessorCount() => Environment.ProcessorCount;
}

/// <summary>
/// Memory usage monitor.
/// </summary>
public class MemoryProfiler
{
    public long GetMemoryUsageMb()
    {
        try
        {
            var comp = new Microsoft.VisualBasic.Devices.ComputerInfo();
            return (long)(comp.TotalPhysicalMemory / (1024.0 * 1024.0)) -
                   (long)(comp.AvailablePhysicalMemory / (1024.0 * 1024.0));
        }
        catch { return 0; }
    }

    public double GetMemoryUsagePercent()
    {
        try
        {
            var comp = new Microsoft.VisualBasic.Devices.ComputerInfo();
            var used = comp.TotalPhysicalMemory - comp.AvailablePhysicalMemory;
            return (used / (double)comp.TotalPhysicalMemory) * 100;
        }
        catch { return 0; }
    }

    public long GetAvailableMemoryMb()
    {
        try
        {
            var comp = new Microsoft.VisualBasic.Devices.ComputerInfo();
            return (long)(comp.AvailablePhysicalMemory / (1024.0 * 1024.0));
        }
        catch { return 0; }
    }
}
