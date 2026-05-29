#include <algorithm>
#include <cmath>
#include <cstddef>

namespace {
double sigmoid(double x) {
    return 1.0 / (1.0 + std::exp(-x));
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
}

extern "C" {

__declspec(dllexport) double hermes_reward_update(
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

__declspec(dllexport) void hermes_quantize_float32(
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

__declspec(dllexport) double hermes_gaussian_3d_score(
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

__declspec(dllexport) double hermes_knaa_qnaa_score(
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

}
