namespace MonadoBlade.Core.Services;

using System.Runtime.InteropServices;

/// <summary>
/// Native bridge to high-performance C++ Hermes learning kernels.
/// Falls back to managed scoring if native binary is unavailable.
/// </summary>
public sealed class NativeHermesLearningBridge
{
    private const string NativeDll = "hermes_learning_kernel";

    [DllImport(NativeDll, EntryPoint = "hermes_reward_update", CallingConvention = CallingConvention.Cdecl)]
    private static extern double HermesRewardUpdateNative(
        double quality,
        double speed,
        double costEfficiency,
        double truthScore,
        double novelty,
        double[] weights,
        nuint weightLen);

    /// <summary>
    /// Computes reward using native C++ kernels when available.
    /// </summary>
    public double ComputeReward(
        double quality,
        double speed,
        double costEfficiency,
        double truthScore,
        double novelty,
        double[] weights)
    {
        if (weights is null || weights.Length < 5)
            throw new ArgumentException("At least 5 weights are required", nameof(weights));

        try
        {
            return HermesRewardUpdateNative(
                quality,
                speed,
                costEfficiency,
                truthScore,
                novelty,
                weights,
                (nuint)weights.Length);
        }
        catch (DllNotFoundException)
        {
            return ComputeManagedFallback(quality, speed, costEfficiency, truthScore, novelty, weights);
        }
        catch (EntryPointNotFoundException)
        {
            return ComputeManagedFallback(quality, speed, costEfficiency, truthScore, novelty, weights);
        }
    }

    private static double ComputeManagedFallback(
        double quality,
        double speed,
        double costEfficiency,
        double truthScore,
        double novelty,
        double[] weights)
    {
        var score =
            quality * weights[0] +
            speed * weights[1] +
            costEfficiency * weights[2] +
            truthScore * weights[3] +
            novelty * weights[4];

        if (truthScore < 0.68d)
            score -= (0.68d - truthScore) * 1.5d;

        return score;
    }
}
