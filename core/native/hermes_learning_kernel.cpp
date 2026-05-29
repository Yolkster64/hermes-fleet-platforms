#include <algorithm>
#include <cmath>
#include <cstddef>

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

}
