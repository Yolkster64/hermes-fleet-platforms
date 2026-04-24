using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO.Compression;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Tasks;


namespace HELIOS.Platform.Core.AdvancedOptimization
{
    /// <summary>
    /// Implementation of Data Compression Engine with multiple compression strategies.
    /// </summary>
    public class DataCompressionEngine : IDataCompressionEngine
    {
        private readonly Logging.ILogger? _logger;
        private readonly SemaphoreSlim _semaphore = new(1, 1);
        private readonly List<CompressedData> _compressionHistory = new();
        private long _totalBytesProcessed = 0;
        private long _totalBytesSaved = 0;
        private long _compressionCount = 0;
        private long _failureCount = 0;
        private double _totalCompressionTimeMs = 0;
        private double _totalDecompressionTimeMs = 0;

        public DataCompressionEngine(ILogger? logger = null)
        {
            _logger = logger;
        }

        public async Task<bool> InitializeAsync()
        {
            try
            {
                await _semaphore.WaitAsync();
                _logger?.Info("Data Compression Engine initialized");
                return true;
            }
            catch (Exception ex)
            {
                _logger?.Error($"Engine initialization failed: {ex.Message}");
                return false;
            }
            finally
            {
                _semaphore.Release();
            }
        }

        public async Task<CompressedData> CompressDataAsync(string data, CompressionStrategy strategy)
        {
            try
            {
                await _semaphore.WaitAsync();

                var stopwatch = Stopwatch.StartNew();
                var originalBytes = Encoding.UTF8.GetBytes(data);
                var originalSize = originalBytes.Length;

                byte[] compressedBytes = strategy switch
                {
                    CompressionStrategy.Fast => CompressGZip(originalBytes, CompressionLevel.Fastest),
                    CompressionStrategy.Balanced => CompressGZip(originalBytes, CompressionLevel.Optimal),
                    CompressionStrategy.Maximum => CompressGZip(originalBytes, CompressionLevel.SmallestSize),
                    CompressionStrategy.Adaptive => CompressAdaptive(originalBytes),
                    _ => originalBytes
                };

                stopwatch.Stop();

                var compressed = new CompressedData
                {
                    CompressedContent = compressedBytes,
                    OriginalSize = originalSize,
                    CompressedSize = compressedBytes.Length,
                    Strategy = strategy,
                    CompressionRatio = compressedBytes.Length > 0 ? (double)compressedBytes.Length / originalSize : 1.0,
                    CompressionTimeMs = stopwatch.ElapsedMilliseconds,
                    ContentType = "text/plain"
                };

                _totalBytesProcessed += originalSize;
                _totalBytesSaved += originalSize - compressedBytes.Length;
                _compressionCount++;
                _totalCompressionTimeMs += stopwatch.ElapsedMilliseconds;
                _compressionHistory.Add(compressed);

                if (_compressionHistory.Count > 1000)
                    _compressionHistory.RemoveAt(0);

                _logger?.Info($"Data compressed: {originalSize} -> {compressedBytes.Length} bytes (Ratio: {compressed.CompressionRatio:P2})");
                return compressed;
            }
            catch (Exception ex)
            {
                _logger?.Error($"Compression failed: {ex.Message}");
                _failureCount++;
                return new CompressedData();
            }
            finally
            {
                _semaphore.Release();
            }
        }

        public async Task<string> DecompressDataAsync(CompressedData compressedData)
        {
            try
            {
                await _semaphore.WaitAsync();

                var stopwatch = Stopwatch.StartNew();
                var decompressedBytes = DecompressGZip(compressedData.CompressedContent);
                var result = Encoding.UTF8.GetString(decompressedBytes);

                stopwatch.Stop();
                _totalDecompressionTimeMs += stopwatch.ElapsedMilliseconds;

                _logger?.Info($"Data decompressed: {compressedData.CompressedSize} -> {decompressedBytes.Length} bytes");
                return result;
            }
            catch (Exception ex)
            {
                _logger?.Error($"Decompression failed: {ex.Message}");
                return string.Empty;
            }
            finally
            {
                _semaphore.Release();
            }
        }

        public async Task<bool> CompressLogsAsync(List<string> logs)
        {
            try
            {
                await _semaphore.WaitAsync();

                var logData = string.Join("\n", logs);
                var compressed = await CompressDataAsync(logData, CompressionStrategy.Maximum);

                _logger?.Info($"Logs compressed: {logs.Count} entries, Size: {compressed.OriginalSize} -> {compressed.CompressedSize}");
                return compressed.CompressedSize > 0;
            }
            catch (Exception ex)
            {
                _logger?.Error($"Log compression failed: {ex.Message}");
                return false;
            }
            finally
            {
                _semaphore.Release();
            }
        }

        public async Task<bool> CompressMetricsAsync(Dictionary<string, object> metrics)
        {
            try
            {
                await _semaphore.WaitAsync();

                var metricsJson = SerializeMetrics(metrics);
                var compressed = await CompressDataAsync(metricsJson, CompressionStrategy.Balanced);

                _logger?.Info($"Metrics compressed: {metrics.Count} items, Size: {compressed.OriginalSize} -> {compressed.CompressedSize}");
                return compressed.CompressedSize > 0;
            }
            catch (Exception ex)
            {
                _logger?.Error($"Metrics compression failed: {ex.Message}");
                return false;
            }
            finally
            {
                _semaphore.Release();
            }
        }

        public async Task<CompressionMetrics> GetCompressionMetricsAsync()
        {
            try
            {
                await _semaphore.WaitAsync();

                var strategyDistribution = new Dictionary<CompressionStrategy, long>();
                foreach (CompressionStrategy strategy in Enum.GetValues(typeof(CompressionStrategy)))
                {
                    var count = _compressionHistory.Count(c => c.Strategy == strategy);
                    strategyDistribution[strategy] = count;
                }

                var avgCompressionTime = _compressionCount > 0 ? _totalCompressionTimeMs / _compressionCount : 0;
                var avgDecompressionTime = _compressionCount > 0 ? _totalDecompressionTimeMs / _compressionCount : 0;
                var avgRatio = _compressionHistory.Count > 0 ? _compressionHistory.Average(c => c.CompressionRatio) : 1.0;

                return new CompressionMetrics
                {
                    TotalBytesCompressed = _totalBytesProcessed,
                    TotalBytesSaved = _totalBytesSaved,
                    AverageCompressionRatio = avgRatio,
                    CompressedItems = _compressionCount,
                    FailedCompressions = _failureCount,
                    AverageCompressionTimeMs = avgCompressionTime,
                    AverageDecompressionTimeMs = avgDecompressionTime,
                    LastCompressionTime = _compressionHistory.Any() ? _compressionHistory.Last().CompressedAt : DateTime.UtcNow,
                    ItemsByStrategy = strategyDistribution,
                    TotalStorageSaved = _totalBytesSaved / (1024.0 * 1024.0) // MB
                };
            }
            catch (Exception ex)
            {
                _logger?.Error($"Metrics retrieval failed: {ex.Message}");
                return new CompressionMetrics();
            }
            finally
            {
                _semaphore.Release();
            }
        }

        private byte[] CompressGZip(byte[] data, CompressionLevel level)
        {
            using var output = new System.IO.MemoryStream();
            using (var gzip = new GZipStream(output, level, false))
            {
                gzip.Write(data, 0, data.Length);
            }
            return output.ToArray();
        }

        private byte[] DecompressGZip(byte[] data)
        {
            using var input = new System.IO.MemoryStream(data);
            using var gzip = new GZipStream(input, CompressionMode.Decompress);
            using var output = new System.IO.MemoryStream();
            gzip.CopyTo(output);
            return output.ToArray();
        }

        private byte[] CompressAdaptive(byte[] data)
        {
            // Adaptive compression: use smallest size for larger data, fastest for smaller
            var level = data.Length > 10000 ? CompressionLevel.SmallestSize : CompressionLevel.Fastest;
            return CompressGZip(data, level);
        }

        private string SerializeMetrics(Dictionary<string, object> metrics)
        {
            var parts = new List<string>();
            foreach (var kvp in metrics)
            {
                parts.Add($"{kvp.Key}={kvp.Value}");
            }
            return string.Join(",", parts);
        }
    }
}
