#include <algorithm>
#include <cmath>
#include <cstddef>
#include <vector>

#if defined(_WIN32) || defined(_WIN64)
#define HERMES_EXPORT __declspec(dllexport)
#else
#define HERMES_EXPORT __attribute__((visibility("default")))
#endif

namespace {
double sigmoid(double x) {
    return 1.0 / (1.0 + std::exp(-x));
}

double clamp01(double v) {
    return std::clamp(v, 0.0, 1.0);
}

double sanitize01(double v) {
    if (!std::isfinite(v)) {
        return 0.0;
    }
    return clamp01(v);
}

double safe_weight(double v) {
    if (!std::isfinite(v)) {
        return 0.000001;
    }
    return std::max(0.000001, v);
}

double mean_or_zero(const double* values, std::size_t len) {
    if (values == nullptr || len == 0) {
        return 0.0;
    }
    double sum = 0.0;
    for (std::size_t i = 0; i < len; ++i) {
        sum += values[i];
    }
    return sum / static_cast<double>(len);
}

double triangular_membership(double x, double left, double center, double right) {
    if (x <= left || x >= right) {
        return 0.0;
    }
    if (x == center) {
        return 1.0;
    }
    if (x < center) {
        return (x - left) / std::max(0.000001, center - left);
    }
    return (right - x) / std::max(0.000001, right - center);
}
}

extern "C" {

HERMES_EXPORT double hermes_reward_update(
    double quality,
    double speed,
    double cost_efficiency,
    double truth_score,
    double novelty,
    double* weights,
    std::size_t weight_len) {
    if (weights == nullptr || weight_len < 5) {
        return 0.0;
    }

    const double values[5] = {
        quality,
        speed,
        cost_efficiency,
        truth_score,
        novelty
    };

    double score = 0.0;
    for (std::size_t i = 0; i < 5; ++i) {
        score += values[i] * weights[i];
    }

    // Truth gate penalty: suppress false-positive reward promotion.
    if (truth_score < 0.68) {
        score -= (0.68 - truth_score) * 1.5;
    }

    return score;
}

HERMES_EXPORT void hermes_quantize_float32(
    const float* input,
    std::size_t len,
    float min_value,
    float max_value,
    unsigned char* output) {
    if (input == nullptr || output == nullptr || len == 0) {
        return;
    }

    const float range = std::max(0.000001f, max_value - min_value);
    for (std::size_t i = 0; i < len; ++i) {
        float norm = (input[i] - min_value) / range;
        norm = std::clamp(norm, 0.0f, 1.0f);
        output[i] = static_cast<unsigned char>(std::round(norm * 255.0f));
    }
}

HERMES_EXPORT double hermes_gaussian_3d_score(
    double x,
    double y,
    double z,
    double target_x,
    double target_y,
    double target_z,
    double sigma) {
    const double safe_sigma = std::max(0.000001, sigma);
    const double dx = x - target_x;
    const double dy = y - target_y;
    const double dz = z - target_z;
    const double dist2 = dx * dx + dy * dy + dz * dz;
    return std::exp(-(dist2 / (2.0 * safe_sigma * safe_sigma)));
}

HERMES_EXPORT double hermes_knaa_qnaa_score(
    const double* short_values,
    std::size_t short_len,
    const double* mid_values,
    std::size_t mid_len,
    const double* long_values,
    std::size_t long_len,
    double truth_score,
    double reward_score,
    double exploration_rate) {
    const double short_avg = mean_or_zero(short_values, short_len);
    const double mid_avg = mean_or_zero(mid_values, mid_len);
    const double long_avg = mean_or_zero(long_values, long_len);

    const double knaa = (short_avg * 0.42) + (mid_avg * 0.34) + (long_avg * 0.24);
    const double qnaa = (sigmoid((truth_score - 0.5) * 7.0) * 0.62)
        + (sigmoid((reward_score - 0.5) * 5.0) * 0.38);
    const double explore = std::clamp(exploration_rate, 0.0, 1.0) * 0.14;
    return std::clamp((knaa * 0.64) + (qnaa * 0.36) + explore, 0.0, 1.0);
}

HERMES_EXPORT double hermes_fleet_shape_score(
    double active_agents,
    double latency_ms,
    double throughput_rps,
    double error_rate,
    double diversity,
    double memory_retention) {
    const double agent_factor = sigmoid((active_agents - 8.0) * 0.28);
    const double latency_factor = sigmoid((220.0 - latency_ms) / 45.0);
    const double throughput_factor = sigmoid((throughput_rps - 140.0) / 30.0);
    const double reliability = 1.0 - std::clamp(error_rate, 0.0, 1.0);
    const double diversity_factor = std::clamp(diversity, 0.0, 1.0);
    const double retention_factor = std::clamp(memory_retention, 0.0, 1.0);

    return std::clamp(
        (agent_factor * 0.20)
        + (latency_factor * 0.22)
        + (throughput_factor * 0.22)
        + (reliability * 0.18)
        + (diversity_factor * 0.08)
        + (retention_factor * 0.10),
        0.0,
        1.0
    );
}

HERMES_EXPORT double hermes_quantized_compression_score(
    const double* values,
    std::size_t len) {
    if (values == nullptr || len == 0) {
        return 0.0;
    }

    double min_v = values[0];
    double max_v = values[0];
    for (std::size_t i = 1; i < len; ++i) {
        min_v = std::min(min_v, values[i]);
        max_v = std::max(max_v, values[i]);
    }

    const double range = std::max(0.000001, max_v - min_v);
    std::vector<unsigned char> q(len, 0);
    std::vector<double> deq(len, 0.0);

    for (std::size_t i = 0; i < len; ++i) {
        const double norm = std::clamp((values[i] - min_v) / range, 0.0, 1.0);
        q[i] = static_cast<unsigned char>(std::round(norm * 255.0));
        deq[i] = min_v + (static_cast<double>(q[i]) / 255.0) * range;
    }

    double mse = 0.0;
    for (std::size_t i = 0; i < len; ++i) {
        const double d = values[i] - deq[i];
        mse += d * d;
    }
    mse /= static_cast<double>(len);

    const double fidelity = 1.0 / (1.0 + mse * 200.0);
    const double compression_ratio = 1.0 - (8.0 / 64.0); // 64-bit input to 8-bit
    return std::clamp((fidelity * 0.72) + (compression_ratio * 0.28), 0.0, 1.0);
}

HERMES_EXPORT double hermes_long_haul_meta_score(
    const double* short_values,
    std::size_t short_len,
    const double* mid_values,
    std::size_t mid_len,
    const double* long_values,
    std::size_t long_len,
    double external_signal_score,
    double correction_signal,
    double truth_score,
    double gaussian_alignment) {
    const double short_avg = mean_or_zero(short_values, short_len);
    const double mid_avg = mean_or_zero(mid_values, mid_len);
    const double long_avg = mean_or_zero(long_values, long_len);
    const double horizon_stability = (short_avg * 0.20) + (mid_avg * 0.33) + (long_avg * 0.47);

    const double signal_quality =
        (std::clamp(external_signal_score, 0.0, 1.0) * 0.34) +
        (std::clamp(truth_score, 0.0, 1.0) * 0.41) +
        (std::clamp(gaussian_alignment, 0.0, 1.0) * 0.25);

    const double correction = 0.5 + std::clamp(correction_signal, -1.0, 1.0) * 0.5;
    return std::clamp((horizon_stability * 0.58) + (signal_quality * 0.30) + (correction * 0.12), 0.0, 1.0);
}

HERMES_EXPORT double hermes_linear_regression_predict(
    const double* xs,
    const double* ys,
    std::size_t len,
    double x_query,
    double l2_alpha) {
    if (xs == nullptr || ys == nullptr || len < 2) {
        return 0.0;
    }
    const double alpha = std::max(0.0, l2_alpha);
    double sum_x = 0.0;
    double sum_y = 0.0;
    std::size_t valid = 0;
    for (std::size_t i = 0; i < len; ++i) {
        if (!std::isfinite(xs[i]) || !std::isfinite(ys[i])) {
            continue;
        }
        sum_x += xs[i];
        sum_y += ys[i];
        ++valid;
    }
    if (valid < 2) {
        return 0.0;
    }
    const double mean_x = sum_x / static_cast<double>(valid);
    const double mean_y = sum_y / static_cast<double>(valid);

    double num = 0.0;
    double den = 0.0;
    for (std::size_t i = 0; i < len; ++i) {
        if (!std::isfinite(xs[i]) || !std::isfinite(ys[i])) {
            continue;
        }
        const double dx = xs[i] - mean_x;
        num += dx * (ys[i] - mean_y);
        den += dx * dx;
    }
    const double slope = num / std::max(0.000001, den + alpha);
    const double intercept = mean_y - (slope * mean_x);
    return intercept + (slope * x_query);
}

HERMES_EXPORT void hermes_adaptive_brain_decision(
    const double* variables,
    std::size_t variables_len,
    const double* variable_weights,
    std::size_t weight_len,
    double truth_score,
    double stability_signal,
    double exploration_pressure,
    double chaos_control,
    double proactive_bias,
    double* output_metrics,
    std::size_t output_len) {
    if (output_metrics == nullptr || output_len == 0) {
        return;
    }
    for (std::size_t i = 0; i < output_len; ++i) {
        output_metrics[i] = 0.0;
    }

    const std::size_t n = std::min(variables_len, weight_len);
    if (variables == nullptr || variable_weights == nullptr || n == 0) {
        return;
    }

    double weighted_sum = 0.0;
    double weight_sum = 0.0;
    for (std::size_t i = 0; i < n; ++i) {
        const double w = safe_weight(variable_weights[i]);
        const double v = sanitize01(variables[i]);
        weighted_sum += v * w;
        weight_sum += w;
    }
    const double weighted_mean = weighted_sum / std::max(0.000001, weight_sum);

    double weighted_var = 0.0;
    for (std::size_t i = 0; i < n; ++i) {
        const double w = safe_weight(variable_weights[i]);
        const double d = sanitize01(variables[i]) - weighted_mean;
        weighted_var += w * d * d;
    }
    weighted_var /= std::max(0.000001, weight_sum);
    const double volatility = clamp01(std::sqrt(std::max(0.0, weighted_var)) * 1.6);

    const double low = triangular_membership(weighted_mean, 0.0, 0.20, 0.50);
    const double medium = triangular_membership(weighted_mean, 0.20, 0.50, 0.80);
    const double high = triangular_membership(weighted_mean, 0.50, 0.80, 1.0);

    const double truth = clamp01(truth_score);
    const double stability = clamp01(stability_signal);
    const double exploration = clamp01(exploration_pressure);
    const double chaos = clamp01(chaos_control);
    const double proactive_seed = clamp01(proactive_bias);

    const double risk = clamp01((1.0 - truth) * 0.60 + (volatility * 0.30) + (exploration * 0.10));
    const double proactive = clamp01((proactive_seed * 0.42) + (high * 0.24) + (medium * 0.14) + ((1.0 - risk) * 0.20));
    const double adaptation = clamp01((exploration * 0.34) + (volatility * 0.36) + ((1.0 - stability) * 0.18) + (high * 0.12));
    const double chaos_intensity = clamp01((chaos * (0.25 + adaptation * 0.55)) + (low * 0.20) + (exploration * 0.12));
    const double confidence = clamp01((truth * 0.46) + (stability * 0.34) + ((1.0 - volatility) * 0.20));
    const double llm_boost = clamp01((proactive * 0.42) + (confidence * 0.30) + (high * 0.18) + ((1.0 - risk) * 0.10));
    const double specialization_shift = clamp01((adaptation * 0.48) + (chaos_intensity * 0.24) + (low * 0.18) + (exploration * 0.10));
    const double fleet_boost = clamp01((confidence * 0.30) + (proactive * 0.22) + (adaptation * 0.18) + (high * 0.16) + ((1.0 - risk) * 0.14));
    const double decision_score = clamp01(
        (llm_boost * 0.23)
        + (fleet_boost * 0.25)
        + (confidence * 0.20)
        + (proactive * 0.16)
        + ((1.0 - chaos_intensity) * 0.08)
        + (adaptation * 0.08));

    if (output_len > 0) output_metrics[0] = decision_score;
    if (output_len > 1) output_metrics[1] = proactive;
    if (output_len > 2) output_metrics[2] = adaptation;
    if (output_len > 3) output_metrics[3] = chaos_intensity;
    if (output_len > 4) output_metrics[4] = confidence;
    if (output_len > 5) output_metrics[5] = llm_boost;
    if (output_len > 6) output_metrics[6] = fleet_boost;
    if (output_len > 7) output_metrics[7] = specialization_shift;
}

}
