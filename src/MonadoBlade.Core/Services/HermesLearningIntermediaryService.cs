namespace MonadoBlade.Core.Services;

using System.Net.Http.Json;

/// <summary>
/// Intermediary layer between native C++ Hermes kernels and Python orchestration APIs.
/// Uses native scoring locally, then pushes curated learning signals to orchestrator endpoints.
/// </summary>
public sealed class HermesLearningIntermediaryService
{
    private readonly NativeHermesLearningBridge _nativeBridge;
    private readonly HttpClient _httpClient;

    public HermesLearningIntermediaryService(NativeHermesLearningBridge nativeBridge, HttpClient? httpClient = null)
    {
        _nativeBridge = nativeBridge ?? throw new ArgumentNullException(nameof(nativeBridge));
        _httpClient = httpClient ?? new HttpClient();
    }

    public HermesIntermediaryScore ComputeIntermediaryScore(
        double[] shortValues,
        double[] midValues,
        double[] longValues,
        double truthScore,
        double rewardScore,
        double activeAgents,
        double latencyMs,
        double throughputRps,
        double errorRate,
        double diversity,
        double memoryRetention)
    {
        var knaaQnaa = _nativeBridge.ComputeKnaaQnaaScore(shortValues, midValues, longValues, truthScore, rewardScore);
        var fleetShape = _nativeBridge.ComputeFleetShapeScore(activeAgents, latencyMs, throughputRps, errorRate, diversity, memoryRetention);
        var quantizedCompression = _nativeBridge.ComputeQuantizedCompressionScore(
            shortValues.Concat(midValues).Concat(longValues).ToArray());
        var composite = Math.Clamp((knaaQnaa * 0.46d) + (fleetShape * 0.34d) + (quantizedCompression * 0.20d), 0.0d, 1.0d);
        return new HermesIntermediaryScore(knaaQnaa, fleetShape, quantizedCompression, composite);
    }

    public async Task<HermesCuratedLearningPlan> CurateLearningAsync(
        Uri orchestratorBaseUri,
        double sqlSignal,
        double internetSignal,
        double llmSignal,
        double stabilityBias,
        CancellationToken cancellationToken = default)
    {
        var request = new
        {
            sql_signal = sqlSignal,
            internet_signal = internetSignal,
            llm_signal = llmSignal,
            stability_bias = stabilityBias,
        };

        using var response = await _httpClient.PostAsJsonAsync(
            new Uri(orchestratorBaseUri, "/curate-learning"),
            request,
            cancellationToken);
        response.EnsureSuccessStatusCode();
        var curated = await response.Content.ReadFromJsonAsync<HermesCuratedLearningPlan>(cancellationToken: cancellationToken);
        return curated ?? new HermesCuratedLearningPlan("sql", new Dictionary<string, double>(), stabilityBias, "focus-truth-and-retention");
    }

    public async Task IngestCompositeSignalAsync(
        Uri orchestratorBaseUri,
        HermesIntermediaryScore score,
        string source = "csharp_intermediary",
        CancellationToken cancellationToken = default)
    {
        var payload = new
        {
            source,
            signal_score = score.Composite,
            payload = new
            {
                knaa_qnaa = score.KnaaQnaa,
                fleet_shape = score.FleetShape,
                quantized_compression = score.QuantizedCompression,
                composite = score.Composite,
            },
        };

        using var response = await _httpClient.PostAsJsonAsync(
            new Uri(orchestratorBaseUri, "/ingest-signal"),
            payload,
            cancellationToken);
        response.EnsureSuccessStatusCode();
    }
}

public sealed record HermesIntermediaryScore(
    double KnaaQnaa,
    double FleetShape,
    double QuantizedCompression,
    double Composite);

public sealed record HermesCuratedLearningPlan(
    string PrimarySource,
    Dictionary<string, double> SourceWeights,
    double StabilityBias,
    string Recommendation);
