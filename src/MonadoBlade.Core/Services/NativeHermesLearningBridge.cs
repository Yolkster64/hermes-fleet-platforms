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

    [DllImport(NativeDll, EntryPoint = "hermes_gaussian_3d_score", CallingConvention = CallingConvention.Cdecl)]
    private static extern double HermesGaussian3DScoreNative(
        double x,
        double y,
        double z,
        double targetX,
        double targetY,
        double targetZ,
        double sigma);

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

    public double ComputeGaussian3DScore(
        double x,
        double y,
        double z,
        double targetX,
        double targetY,
        double targetZ,
        double sigma = 0.2d)
    {
        try
        {
            return HermesGaussian3DScoreNative(x, y, z, targetX, targetY, targetZ, sigma);
        }
        catch (DllNotFoundException)
        {
            return ComputeGaussianManagedFallback(x, y, z, targetX, targetY, targetZ, sigma);
        }
        catch (EntryPointNotFoundException)
        {
            return ComputeGaussianManagedFallback(x, y, z, targetX, targetY, targetZ, sigma);
        }
    }

    private static double ComputeGaussianManagedFallback(
        double x,
        double y,
        double z,
        double targetX,
        double targetY,
        double targetZ,
        double sigma)
    {
        var safeSigma = Math.Max(0.000001d, sigma);
        var dx = x - targetX;
        var dy = y - targetY;
        var dz = z - targetZ;
        var dist2 = (dx * dx) + (dy * dy) + (dz * dz);
        return Math.Exp(-(dist2 / (2.0d * safeSigma * safeSigma)));
    }
}
