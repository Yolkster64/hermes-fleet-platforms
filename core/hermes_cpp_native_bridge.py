import ctypes
import os
import platform
from ctypes import c_double, c_size_t
from pathlib import Path
from typing import Optional


class HermesCppNativeBridge:
    def __init__(self, dll_path: Optional[str] = None) -> None:
        self.dll_path = dll_path or self._default_library_path()
        self._dll = None
        self._load()

    def _default_library_path(self) -> str:
        env_path = os.getenv("HERMES_CPP_NATIVE_LIB", "").strip()
        if env_path:
            return env_path
        system = platform.system().lower()
        if system == "windows":
            suffix = ".dll"
        elif system == "darwin":
            suffix = ".dylib"
        else:
            suffix = ".so"
        return str(Path(f"core/native/hermes_learning_kernel{suffix}"))

    def _load(self) -> None:
        dll = Path(self.dll_path)
        if not dll.exists():
            return
        self._dll = ctypes.CDLL(str(dll))
        self._dll.hermes_reward_update.argtypes = [
            c_double,
            c_double,
            c_double,
            c_double,
            c_double,
            ctypes.POINTER(c_double),
            c_size_t,
        ]
        self._dll.hermes_reward_update.restype = c_double
        self._dll.hermes_gaussian_3d_score.argtypes = [
            c_double,
            c_double,
            c_double,
            c_double,
            c_double,
            c_double,
            c_double,
        ]
        self._dll.hermes_gaussian_3d_score.restype = c_double
        try:
            self._dll.hermes_knaa_qnaa_score.argtypes = [
                ctypes.POINTER(c_double),
                c_size_t,
                ctypes.POINTER(c_double),
                c_size_t,
                ctypes.POINTER(c_double),
                c_size_t,
                c_double,
                c_double,
                c_double,
            ]
            self._dll.hermes_knaa_qnaa_score.restype = c_double
        except AttributeError:
            pass
        try:
            self._dll.hermes_fleet_shape_score.argtypes = [
                c_double,
                c_double,
                c_double,
                c_double,
                c_double,
                c_double,
            ]
            self._dll.hermes_fleet_shape_score.restype = c_double
        except AttributeError:
            pass
        try:
            self._dll.hermes_quantized_compression_score.argtypes = [
                ctypes.POINTER(c_double),
                c_size_t,
            ]
            self._dll.hermes_quantized_compression_score.restype = c_double
        except AttributeError:
            pass
        try:
            self._dll.hermes_long_haul_meta_score.argtypes = [
                ctypes.POINTER(c_double),
                c_size_t,
                ctypes.POINTER(c_double),
                c_size_t,
                ctypes.POINTER(c_double),
                c_size_t,
                c_double,
                c_double,
                c_double,
                c_double,
            ]
            self._dll.hermes_long_haul_meta_score.restype = c_double
        except AttributeError:
            pass
        try:
            self._dll.hermes_adaptive_brain_decision.argtypes = [
                ctypes.POINTER(c_double),
                c_size_t,
                ctypes.POINTER(c_double),
                c_size_t,
                c_double,
                c_double,
                c_double,
                c_double,
                c_double,
                ctypes.POINTER(c_double),
                c_size_t,
            ]
            self._dll.hermes_adaptive_brain_decision.restype = None
        except AttributeError:
            pass
        try:
            self._dll.hermes_linear_regression_predict.argtypes = [
                ctypes.POINTER(c_double),
                ctypes.POINTER(c_double),
                c_size_t,
                c_double,
                c_double,
            ]
            self._dll.hermes_linear_regression_predict.restype = c_double
        except AttributeError:
            pass

    @property
    def available(self) -> bool:
        return self._dll is not None

    def reward_update(
        self,
        quality: float,
        speed: float,
        cost_efficiency: float,
        truth_score: float,
        novelty: float,
        weights: list[float],
    ) -> float:
        if not self._dll or not hasattr(self._dll, "hermes_reward_update"):
            score = (
                quality * weights[0]
                + speed * weights[1]
                + cost_efficiency * weights[2]
                + truth_score * weights[3]
                + novelty * weights[4]
            )
            if truth_score < 0.68:
                score -= (0.68 - truth_score) * 1.5
            return score

        arr = (c_double * len(weights))(*weights)
        return float(
            self._dll.hermes_reward_update(
                c_double(quality),
                c_double(speed),
                c_double(cost_efficiency),
                c_double(truth_score),
                c_double(novelty),
                arr,
                c_size_t(len(weights)),
            )
        )

    def gaussian_3d_score(
        self,
        x: float,
        y: float,
        z: float,
        target_x: float,
        target_y: float,
        target_z: float,
        sigma: float = 0.2,
    ) -> float:
        if not self._dll:
            dx = x - target_x
            dy = y - target_y
            dz = z - target_z
            dist2 = dx * dx + dy * dy + dz * dz
            safe_sigma = max(0.000001, sigma)
            return pow(2.718281828, -(dist2 / (2 * safe_sigma * safe_sigma)))

        return float(
            self._dll.hermes_gaussian_3d_score(
                c_double(x),
                c_double(y),
                c_double(z),
                c_double(target_x),
                c_double(target_y),
                c_double(target_z),
                c_double(sigma),
            )
        )

    def knaa_qnaa_score(
        self,
        short_values: list[float],
        mid_values: list[float],
        long_values: list[float],
        truth_score: float,
        reward_score: float,
        exploration_rate: float = 0.1,
    ) -> float:
        if not self._dll:
            short_avg = sum(short_values) / max(1, len(short_values))
            mid_avg = sum(mid_values) / max(1, len(mid_values))
            long_avg = sum(long_values) / max(1, len(long_values))
            knaa = (short_avg * 0.42) + (mid_avg * 0.34) + (long_avg * 0.24)
            qnaa = (
                (1.0 / (1.0 + pow(2.718281828, -((truth_score - 0.5) * 7.0)))) * 0.62
                + (1.0 / (1.0 + pow(2.718281828, -((reward_score - 0.5) * 5.0)))) * 0.38
            )
            explore = max(0.0, min(1.0, exploration_rate)) * 0.14
            return max(0.0, min(1.0, (knaa * 0.64) + (qnaa * 0.36) + explore))

        short_arr = (c_double * len(short_values))(*short_values)
        mid_arr = (c_double * len(mid_values))(*mid_values)
        long_arr = (c_double * len(long_values))(*long_values)
        return float(
            self._dll.hermes_knaa_qnaa_score(
                short_arr,
                c_size_t(len(short_values)),
                mid_arr,
                c_size_t(len(mid_values)),
                long_arr,
                c_size_t(len(long_values)),
                c_double(truth_score),
                c_double(reward_score),
                c_double(exploration_rate),
            )
        )

    def fleet_shape_score(
        self,
        active_agents: float,
        latency_ms: float,
        throughput_rps: float,
        error_rate: float,
        diversity: float,
        memory_retention: float,
    ) -> float:
        if not self._dll or not hasattr(self._dll, "hermes_fleet_shape_score"):
            agent_factor = 1.0 / (1.0 + pow(2.718281828, -((active_agents - 8.0) * 0.28)))
            latency_factor = 1.0 / (1.0 + pow(2.718281828, -((220.0 - latency_ms) / 45.0)))
            throughput_factor = 1.0 / (1.0 + pow(2.718281828, -((throughput_rps - 140.0) / 30.0)))
            reliability = 1.0 - max(0.0, min(1.0, error_rate))
            diversity_factor = max(0.0, min(1.0, diversity))
            retention_factor = max(0.0, min(1.0, memory_retention))
            return max(
                0.0,
                min(
                    1.0,
                    (agent_factor * 0.20)
                    + (latency_factor * 0.22)
                    + (throughput_factor * 0.22)
                    + (reliability * 0.18)
                    + (diversity_factor * 0.08)
                    + (retention_factor * 0.10),
                ),
            )

        return float(
            self._dll.hermes_fleet_shape_score(
                c_double(active_agents),
                c_double(latency_ms),
                c_double(throughput_rps),
                c_double(error_rate),
                c_double(diversity),
                c_double(memory_retention),
            )
        )

    def quantized_compression_score(self, values: list[float]) -> float:
        if not values:
            return 0.0
        if not self._dll or not hasattr(self._dll, "hermes_quantized_compression_score"):
            min_v = min(values)
            max_v = max(values)
            r = max(0.000001, max_v - min_v)
            deq = []
            for v in values:
                norm = max(0.0, min(1.0, (v - min_v) / r))
                q = round(norm * 255.0)
                deq.append(min_v + (q / 255.0) * r)
            mse = sum((a - b) ** 2 for a, b in zip(values, deq)) / len(values)
            fidelity = 1.0 / (1.0 + mse * 200.0)
            compression_ratio = 1.0 - (8.0 / 64.0)
            return max(0.0, min(1.0, (fidelity * 0.72) + (compression_ratio * 0.28)))

        arr = (c_double * len(values))(*values)
        return float(self._dll.hermes_quantized_compression_score(arr, c_size_t(len(values))))

    def long_haul_meta_score(
        self,
        short_values: list[float],
        mid_values: list[float],
        long_values: list[float],
        external_signal_score: float,
        correction_signal: float,
        truth_score: float,
        gaussian_alignment: float,
    ) -> float:
        if not self._dll or not hasattr(self._dll, "hermes_long_haul_meta_score"):
            short_avg = sum(short_values) / max(1, len(short_values))
            mid_avg = sum(mid_values) / max(1, len(mid_values))
            long_avg = sum(long_values) / max(1, len(long_values))
            horizon_stability = (short_avg * 0.20) + (mid_avg * 0.33) + (long_avg * 0.47)
            signal_quality = (
                max(0.0, min(1.0, external_signal_score)) * 0.34
                + max(0.0, min(1.0, truth_score)) * 0.41
                + max(0.0, min(1.0, gaussian_alignment)) * 0.25
            )
            correction = 0.5 + max(-1.0, min(1.0, correction_signal)) * 0.5
            return max(0.0, min(1.0, (horizon_stability * 0.58) + (signal_quality * 0.30) + (correction * 0.12)))

        short_arr = (c_double * len(short_values))(*short_values)
        mid_arr = (c_double * len(mid_values))(*mid_values)
        long_arr = (c_double * len(long_values))(*long_values)
        return float(
            self._dll.hermes_long_haul_meta_score(
                short_arr,
                c_size_t(len(short_values)),
                mid_arr,
                c_size_t(len(mid_values)),
                long_arr,
                c_size_t(len(long_values)),
                c_double(external_signal_score),
                c_double(correction_signal),
                c_double(truth_score),
                c_double(gaussian_alignment),
            )
        )

    def adaptive_brain_decision(
        self,
        variables: list[float],
        variable_weights: list[float],
        truth_score: float,
        stability_signal: float,
        exploration_pressure: float,
        chaos_control: float,
        proactive_bias: float,
    ) -> dict[str, float]:
        if not variables or not variable_weights:
            return {
                "decision_score": 0.0,
                "proactive_score": 0.0,
                "adaptation_rate": 0.0,
                "chaos_intensity": 0.0,
                "confidence": 0.0,
                "llm_boost": 0.0,
                "fleet_boost": 0.0,
                "specialization_shift": 0.0,
            }
        usable = min(len(variables), len(variable_weights))
        vals = [max(0.0, min(1.0, float(v))) for v in variables[:usable]]
        wts = [max(0.000001, float(w)) for w in variable_weights[:usable]]
        w_sum = sum(wts) or 1.0
        wts = [w / w_sum for w in wts]
        truth = max(0.0, min(1.0, float(truth_score)))
        stability = max(0.0, min(1.0, float(stability_signal)))
        exploration = max(0.0, min(1.0, float(exploration_pressure)))
        chaos = max(0.0, min(1.0, float(chaos_control)))
        proactive = max(0.0, min(1.0, float(proactive_bias)))

        if not self._dll or not hasattr(self._dll, "hermes_adaptive_brain_decision"):
            weighted_mean = sum(v * w for v, w in zip(vals, wts))
            variance = sum(((v - weighted_mean) ** 2) * w for v, w in zip(vals, wts))
            volatility = max(0.0, min(1.0, (variance ** 0.5) * 1.6))
            risk = max(0.0, min(1.0, (1.0 - truth) * 0.60 + volatility * 0.30 + exploration * 0.10))
            proactive_score = max(0.0, min(1.0, proactive * 0.52 + weighted_mean * 0.28 + (1.0 - risk) * 0.20))
            adaptation = max(0.0, min(1.0, exploration * 0.34 + volatility * 0.36 + (1.0 - stability) * 0.30))
            chaos_intensity = max(0.0, min(1.0, chaos * (0.25 + adaptation * 0.55) + exploration * 0.12))
            confidence = max(0.0, min(1.0, truth * 0.46 + stability * 0.34 + (1.0 - volatility) * 0.20))
            llm_boost = max(0.0, min(1.0, proactive_score * 0.42 + confidence * 0.40 + (1.0 - risk) * 0.18))
            fleet_boost = max(0.0, min(1.0, confidence * 0.33 + proactive_score * 0.22 + adaptation * 0.25 + (1.0 - risk) * 0.20))
            specialization_shift = max(0.0, min(1.0, adaptation * 0.55 + chaos_intensity * 0.30 + exploration * 0.15))
            decision = max(
                0.0,
                min(
                    1.0,
                    llm_boost * 0.23
                    + fleet_boost * 0.25
                    + confidence * 0.20
                    + proactive_score * 0.16
                    + (1.0 - chaos_intensity) * 0.08
                    + adaptation * 0.08,
                ),
            )
            return {
                "decision_score": decision,
                "proactive_score": proactive_score,
                "adaptation_rate": adaptation,
                "chaos_intensity": chaos_intensity,
                "confidence": confidence,
                "llm_boost": llm_boost,
                "fleet_boost": fleet_boost,
                "specialization_shift": specialization_shift,
            }

        vals_arr = (c_double * len(vals))(*vals)
        wts_arr = (c_double * len(wts))(*wts)
        out_arr = (c_double * 8)(*([0.0] * 8))
        self._dll.hermes_adaptive_brain_decision(
            vals_arr,
            c_size_t(len(vals)),
            wts_arr,
            c_size_t(len(wts)),
            c_double(truth),
            c_double(stability),
            c_double(exploration),
            c_double(chaos),
            c_double(proactive),
            out_arr,
            c_size_t(8),
        )
        return {
            "decision_score": float(out_arr[0]),
            "proactive_score": float(out_arr[1]),
            "adaptation_rate": float(out_arr[2]),
            "chaos_intensity": float(out_arr[3]),
            "confidence": float(out_arr[4]),
            "llm_boost": float(out_arr[5]),
            "fleet_boost": float(out_arr[6]),
            "specialization_shift": float(out_arr[7]),
        }

    def linear_regression_predict(self, y_values: list[float], x_query: float, l2_alpha: float = 0.01) -> float:
        if len(y_values) < 2:
            return float(y_values[-1]) if y_values else 0.0
        ys = [float(v) for v in y_values]
        xs = [float(i + 1) for i in range(len(ys))]
        if not self._dll or not hasattr(self._dll, "hermes_linear_regression_predict"):
            x_mean = sum(xs) / len(xs)
            y_mean = sum(ys) / len(ys)
            num = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
            den = sum((x - x_mean) ** 2 for x in xs) + max(0.0, float(l2_alpha))
            slope = num / max(0.000001, den)
            intercept = y_mean - (slope * x_mean)
            return float(intercept + (slope * float(x_query)))

        xs_arr = (c_double * len(xs))(*xs)
        ys_arr = (c_double * len(ys))(*ys)
        return float(
            self._dll.hermes_linear_regression_predict(
                xs_arr,
                ys_arr,
                c_size_t(len(ys)),
                c_double(float(x_query)),
                c_double(max(0.0, float(l2_alpha))),
            )
        )
