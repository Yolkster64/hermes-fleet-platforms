## GETTING STARTED WITH HELIOS v4.0

Quick start guide for using HELIOS v4.0 in your application.

### 5-Minute Quick Start

```javascript
const { HeliosV4 } = require('helios-v4');

// 1. Create instance
const helios = new HeliosV4({
  environment: 'production',
  enableCache: true,
  enableAI: true,
  enableIntegrations: true,
});

// 2. Initialize
await helios.initialize();

// 3. Use cache
const result = await helios.cache.staleWhileRevalidate(
  'user:123',
  async () => fetchUserProfile(123),
  { ttl: 60, staleTtl: 300 }
);

// 4. Get system status
const status = await helios.getStatus();
console.log(status);

// 5. Shutdown gracefully
await helios.shutdown();
```

### Key Usage Patterns

**Caching:**
```javascript
// Static assets
const css = await helios.cache.cacheFirst('styles.css', () => loadCSS());

// Dynamic data
const data = await helios.cache.staleWhileRevalidate('data:key', () => fetchData());
```

**Database:**
```javascript
const result = await helios.db.executeQuery('SELECT * FROM users', []);
```

**Responses:**
```javascript
const optimized = await helios.gateway.buildOptimizedResponse(data, {
  compress: true,
  paginate: true,
  fields: 'id,name'
});
```

**AI Insights:**
```javascript
helios.ai.anomalyDetector.detectAnomaly('latency', 500);
helios.ai.trafficPredictor.predictTraffic();
helios.ai.scalingAdvisor.analyze({ instances: 5 });
```

### Configuration

```javascript
const helios = new HeliosV4({
  cache: { enableStatistics: true },
  db: { poolSize: 20 },
  gateway: { gzipThreshold: 1024 },
  logging: { level: 'info' },
});
```

See [API Reference](../README.md#api-reference) for complete documentation.
