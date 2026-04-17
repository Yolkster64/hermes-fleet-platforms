using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace HELIOS.Platform.Core.Performance;

/// <summary>
/// Advanced caching layer for frequently accessed data
/// Supports TTL, capacity management, and eviction policies
/// </summary>
public interface IAdvancedCacheService
{
    /// <summary>Get or set a cached value</summary>
    Task<T> GetAsync<T>(string key, Func<Task<T>> factory, TimeSpan? ttl = null) where T : class;
    
    /// <summary>Set a value in cache</summary>
    Task SetAsync<T>(string key, T value, TimeSpan? ttl = null) where T : class;
    
    /// <summary>Remove a value from cache</summary>
    Task RemoveAsync(string key);
    
    /// <summary>Clear all cache entries</summary>
    Task ClearAsync();
    
    /// <summary>Get cache statistics</summary>
    Task<CacheStatistics> GetStatisticsAsync();
    
    /// <summary>Configure cache policy</summary>
    void ConfigurePolicy(CachePolicy policy);
}

public class AdvancedCacheService : IAdvancedCacheService
{
    private readonly Dictionary<string, CacheEntry> _cache = new();
    private CachePolicy _policy = new();
    private int _hits = 0;
    private int _misses = 0;

    public async Task<T> GetAsync<T>(string key, Func<Task<T>> factory, TimeSpan? ttl = null) where T : class
    {
        lock (_cache)
        {
            if (_cache.TryGetValue(key, out var entry))
            {
                if (entry.ExpiresAt == null || DateTime.UtcNow < entry.ExpiresAt)
                {
                    entry.LastAccessedAt = DateTime.UtcNow;
                    entry.AccessCount++;
                    _hits++;
                    return entry.Value as T;
                }
                else
                {
                    _cache.Remove(key);
                }
            }
        }

        _misses++;
        var value = await factory();

        if (value != null)
        {
            await SetAsync(key, value, ttl);
        }

        return value;
    }

    public async Task SetAsync<T>(string key, T value, TimeSpan? ttl = null) where T : class
    {
        lock (_cache)
        {
            // Check capacity
            if (_cache.Count >= _policy.MaxCapacity && !_cache.ContainsKey(key))
            {
                EvictLRU();
            }

            _cache[key] = new CacheEntry
            {
                Key = key,
                Value = value,
                CreatedAt = DateTime.UtcNow,
                LastAccessedAt = DateTime.UtcNow,
                ExpiresAt = ttl.HasValue ? DateTime.UtcNow.Add(ttl.Value) : null
            };
        }

        await Task.CompletedTask;
    }

    public async Task RemoveAsync(string key)
    {
        lock (_cache)
        {
            _cache.Remove(key);
        }
        await Task.CompletedTask;
    }

    public async Task ClearAsync()
    {
        lock (_cache)
        {
            _cache.Clear();
        }
        _hits = 0;
        _misses = 0;
        await Task.CompletedTask;
    }

    public async Task<CacheStatistics> GetStatisticsAsync()
    {
        CacheStatistics stats;
        lock (_cache)
        {
            stats = new CacheStatistics
            {
                Hits = _hits,
                Misses = _misses,
                HitRate = _hits + _misses > 0 ? (double)_hits / (_hits + _misses) : 0,
                EntriesCount = _cache.Count,
                CapacityUsage = (double)_cache.Count / _policy.MaxCapacity * 100
            };
        }

        await Task.CompletedTask;
        return stats;
    }

    public void ConfigurePolicy(CachePolicy policy)
    {
        _policy = policy ?? new CachePolicy();
    }

    private void EvictLRU()
    {
        if (_cache.Count == 0) return;

        var lruEntry = _cache.Values
            .OrderBy(e => e.LastAccessedAt)
            .First();

        _cache.Remove(lruEntry.Key);
    }
}

public class CacheEntry
{
    public string Key { get; set; }
    public object Value { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime LastAccessedAt { get; set; }
    public DateTime? ExpiresAt { get; set; }
    public int AccessCount { get; set; }
}

public class CachePolicy
{
    public int MaxCapacity { get; set; } = 10000;
    public TimeSpan DefaultTTL { get; set; } = TimeSpan.FromHours(1);
    public EvictionPolicy EvictionPolicy { get; set; } = EvictionPolicy.LRU;
}

public enum EvictionPolicy
{
    LRU, // Least Recently Used
    LFU, // Least Frequently Used
    FIFO // First In First Out
}

public class CacheStatistics
{
    public int Hits { get; set; }
    public int Misses { get; set; }
    public double HitRate { get; set; }
    public int EntriesCount { get; set; }
    public double CapacityUsage { get; set; }
}
