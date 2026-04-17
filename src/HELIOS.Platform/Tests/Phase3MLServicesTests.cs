using Microsoft.Extensions.Logging;
using Xunit;

namespace HELIOS.Platform.Tests.Phase3;

public class Phase3MLServicesTests
{
    private readonly ILogger<DataCollector> _dataCollectorLogger;
    private readonly ILogger<InMemoryTimeSeriesDB> _timeSeriesLogger;

    public Phase3MLServicesTests()
    {
        _dataCollectorLogger = new NullLogger<DataCollector>();
        _timeSeriesLogger = new NullLogger<InMemoryTimeSeriesDB>();
    }

    [Fact]
    public async Task DataCollector_RegisterMetricProvider_SuccessfullyRegisters()
    {
        // Arrange
        var db = new InMemoryTimeSeriesDB(_timeSeriesLogger);
        var collector = new DataCollector(_dataCollectorLogger, db);

        Func<Task<IDictionary<string, object>>> provider = async () =>
        {
            await Task.Delay(1);
            return new Dictionary<string, object> { { "cpu", 45.5 }, { "memory", 2048 } };
        };

        // Act
        collector.RegisterMetricProvider("TestService", provider);
        var providers = collector.GetRegisteredProviders().ToList();

        // Assert
        Assert.Contains("TestService", providers);
    }

    [Fact]
    public async Task DataCollector_CollectMetricsAsync_AggregatesFromMultipleProviders()
    {
        // Arrange
        var db = new InMemoryTimeSeriesDB(_timeSeriesLogger);
        var collector = new DataCollector(_dataCollectorLogger, db);

        collector.RegisterMetricProvider("Service1", async () =>
        {
            await Task.Delay(1);
            return new Dictionary<string, object> { { "cpu", 50 } };
        });

        collector.RegisterMetricProvider("Service2", async () =>
        {
            await Task.Delay(1);
            return new Dictionary<string, object> { { "memory", 2000 } };
        });

        // Act
        var metrics = await collector.CollectMetricsAsync();

        // Assert
        Assert.NotEmpty(metrics);
        Assert.Contains("Service1_metrics", metrics.Keys);
        Assert.Contains("Service2_metrics", metrics.Keys);
    }

    [Fact]
    public async Task TimeSeriesDB_WritePoint_Successfully()
    {
        // Arrange
        var db = new InMemoryTimeSeriesDB(_timeSeriesLogger);

        // Act
        await db.WritePointAsync("TestService", "cpu_usage", 45.5);
        var stats = await db.GetStatsAsync();

        // Assert
        Assert.Equal(1, stats.TotalPoints);
    }

    [Fact]
    public async Task TimeSeriesDB_WriteBatch_Successfully()
    {
        // Arrange
        var db = new InMemoryTimeSeriesDB(_timeSeriesLogger);
        var points = new List<MetricPoint>
        {
            new() { ServiceName = "S1", MetricName = "cpu", Value = 50, Timestamp = DateTime.UtcNow },
            new() { ServiceName = "S1", MetricName = "memory", Value = 2048, Timestamp = DateTime.UtcNow },
            new() { ServiceName = "S2", MetricName = "cpu", Value = 30, Timestamp = DateTime.UtcNow }
        };

        // Act
        await db.WriteBatchAsync(points);
        var stats = await db.GetStatsAsync();

        // Assert
        Assert.Equal(3, stats.TotalPoints);
        Assert.Equal(2, stats.ServiceCount);
    }

    [Fact]
    public async Task TimeSeriesDB_QueryAsync_ReturnsCorrectPoints()
    {
        // Arrange
        var db = new InMemoryTimeSeriesDB(_timeSeriesLogger);
        var now = DateTime.UtcNow;
        
        await db.WritePointAsync("Service1", "metric1", 10, null);
        await Task.Delay(10);
        await db.WritePointAsync("Service1", "metric1", 20, null);

        // Act
        var results = await db.QueryAsync("Service1", "metric1", now.AddMinutes(-5), now.AddMinutes(5));

        // Assert
        Assert.Equal(2, results.Count);
    }

    [Fact]
    public async Task TimeSeriesDB_QueryAggregatedAsync_CalculatesAggregations()
    {
        // Arrange
        var db = new InMemoryTimeSeriesDB(_timeSeriesLogger);
        var now = DateTime.UtcNow;

        for (int i = 0; i < 10; i++)
        {
            await db.WritePointAsync("Service1", "metric1", i * 10);
        }

        // Act
        var aggregated = await db.QueryAggregatedAsync("Service1", "metric1", 
            now.AddHours(-1), now.AddHours(1), TimeSpan.FromMinutes(10), AggregationType.Average);

        // Assert
        Assert.NotEmpty(aggregated);
    }

    [Fact]
    public async Task TimeSeriesDB_PruneOldData_RemovesExpiredPoints()
    {
        // Arrange
        var db = new InMemoryTimeSeriesDB(_timeSeriesLogger);
        var oldTime = DateTime.UtcNow.AddDays(-60);
        
        // Manually add an old point (simulate old data)
        var points = new List<MetricPoint>
        {
            new() { ServiceName = "S1", MetricName = "m1", Value = 10, Timestamp = oldTime }
        };
        await db.WriteBatchAsync(points);

        var statsBefore = await db.GetStatsAsync();
        Assert.Equal(1, statsBefore.TotalPoints);

        // Act
        await db.PruneOldDataAsync(TimeSpan.FromDays(30));

        // Assert
        var statsAfter = await db.GetStatsAsync();
        Assert.Equal(0, statsAfter.TotalPoints);
    }
}

/// <summary>
/// Null logger for testing.
/// </summary>
public class NullLogger<T> : ILogger<T>
{
    public IDisposable BeginScope<TState>(TState state) => null!;
    public bool IsEnabled(LogLevel logLevel) => false;
    public void Log<TState>(LogLevel logLevel, EventId eventId, TState state, Exception? exception, Func<TState, Exception?, string> formatter) { }
}
