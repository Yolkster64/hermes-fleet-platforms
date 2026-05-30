from __future__ import annotations

import math
from typing import Dict, Iterable, Tuple


VARIABLE_CATALOG: Dict[str, Dict[str, str]] = {
    "short": {
        "success_signal": "Immediate success score from current cycle.",
        "wrongness_signal": "Immediate wrongness/error pressure.",
        "latency_pressure": "Fast response pressure in current cycle.",
        "response_softness": "How smoothly responses adapt this cycle.",
        "micro_recovery": "Short-cycle recovery from small faults.",
    },
    "mid": {
        "group_strength": "Group-level collaboration strength.",
        "solo_strength": "Solo-agent execution quality.",
        "coordination_cohesion": "Mid-window team coordination quality.",
        "reward_adaptation": "Mid-window reward adaptation speed.",
        "monitor_comparison": "Comparison quality of group vs solo monitors.",
    },
    "long": {
        "retention_strength": "Long-term memory retention durability.",
        "knowledge_transfer": "Long-term transfer across tasks/agents.",
        "maturity_signal": "Long-run maturity and stability score.",
        "growth_index": "Growth progression across learning windows.",
        "character_goal_fit": "Fit between behavior and goal profile.",
    },
    "watch": {
        "signal_stability": "Stability of training signals across recent windows.",
        "watch_coverage": "How much of fleet/runtime state is currently observed.",
        "anomaly_resistance": "Resistance to noisy/anomalous signal spikes.",
        "drift_control": "Control strength against long-horizon drift.",
    },
    "conscious": {
        "conscious_clarity": "How clearly the system distinguishes truth from noise in current context.",
        "conscious_alignment": "Alignment between goals, actions, and measured outcomes.",
        "conscious_resilience": "Ability to preserve decision quality during stress/chaos.",
        "conscious_focus": "Sustained focus on high-value trajectories over time.",
    },
    "optimization": {
        "size_factor": "Fleet size utilization ratio.",
        "position_score": "Agent/fleet ranking position quality.",
        "energy_efficiency": "Output per unit energy pressure.",
        "speed_efficiency": "Speed quality under current load.",
        "yield_efficiency": "Total useful output efficiency.",
        "watch_efficiency": "Quality of monitoring throughput vs overhead.",
        "conscious_efficiency": "Quality of conscious signal throughput vs stress.",
        "harmony_index": "Global harmony across watch, conscious, and maturity lanes.",
        "decision_readiness": "How ready the system is to make confident decisions now.",
        "learning_elasticity": "How quickly learning adapts without destabilization.",
        "stability_guard": "Penalty-aware guardrail against watch/conscious divergence.",
        "efficiency_confidence": "Confidence score for the computed efficiency profile.",
        "composite_efficiency": "Balanced top-line efficiency index for orchestration.",
    },
}


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, _safe_float(value, 0.5)))


def _safe_float(value: float | int | str | None, default: float = 0.5) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return float(default)
    if not math.isfinite(parsed):
        return float(default)
    return parsed


def _weighted_score(parts: Iterable[Tuple[float, float]]) -> float:
    numerator = 0.0
    denominator = 0.0
    for value, weight in parts:
        w = max(0.0, float(weight))
        numerator += clamp01(value) * w
        denominator += w
    if denominator <= 0.0:
        return 0.5
    return clamp01(numerator / denominator)


def default_user_entry_profile() -> Dict[str, float | str]:
    return {
        "goal_profile": "balanced",
        "success_priority": 0.72,
        "wrongness_tolerance": 0.22,
        "group_preference": 0.58,
        "solo_preference": 0.42,
        "dynamic_response": 0.62,
        "speed_priority": 0.65,
        "energy_saver": 0.55,
    }


def compute_efficiency_profile(training_variables: Dict[str, float]) -> Dict[str, float]:
    size_factor = clamp01(training_variables.get("size_factor", 0.5))
    position_score = clamp01(training_variables.get("position_score", 0.5))
    success_signal = clamp01(training_variables.get("success_signal", 0.5))
    wrongness_signal = clamp01(training_variables.get("wrongness_signal", 0.5))
    monitor = clamp01(training_variables.get("monitor_comparison", 0.5))
    maturity = clamp01(training_variables.get("maturity_signal", 0.5))
    watch_coverage = clamp01(training_variables.get("watch_coverage", 0.5))
    signal_stability = clamp01(training_variables.get("signal_stability", 0.5))
    anomaly_resistance = clamp01(training_variables.get("anomaly_resistance", 0.5))
    drift_control = clamp01(training_variables.get("drift_control", 0.5))
    conscious_clarity = clamp01(training_variables.get("conscious_clarity", 0.5))
    conscious_alignment = clamp01(training_variables.get("conscious_alignment", 0.5))
    conscious_resilience = clamp01(training_variables.get("conscious_resilience", 0.5))
    conscious_focus = clamp01(training_variables.get("conscious_focus", 0.5))
    retention_strength = clamp01(training_variables.get("retention_strength", 0.5))
    knowledge_transfer = clamp01(training_variables.get("knowledge_transfer", 0.5))
    response_softness = clamp01(training_variables.get("response_softness", 0.5))
    watch_efficiency = _weighted_score(
        (
            (watch_coverage, 0.35),
            (signal_stability, 0.25),
            (anomaly_resistance, 0.20),
            (drift_control, 0.20),
        )
    )
    conscious_efficiency = _weighted_score(
        (
            (conscious_clarity, 0.30),
            (conscious_alignment, 0.30),
            (conscious_resilience, 0.22),
            (conscious_focus, 0.18),
        )
    )
    harmony_index = _weighted_score(
        (
            (watch_efficiency, 0.34),
            (conscious_efficiency, 0.30),
            (maturity, 0.20),
            (monitor, 0.16),
        )
    )
    energy_efficiency = _weighted_score(
        (
            (success_signal, 0.30),
            (monitor, 0.18),
            (maturity, 0.16),
            ((1.0 - wrongness_signal), 0.16),
            (watch_efficiency, 0.12),
            (conscious_efficiency, 0.08),
        )
    )
    speed_efficiency = _weighted_score(
        (
            (position_score, 0.36),
            (success_signal, 0.25),
            (size_factor, 0.19),
            (monitor, 0.10),
            (signal_stability, 0.10),
        )
    )
    yield_efficiency = _weighted_score(
        (
            (energy_efficiency, 0.36),
            (speed_efficiency, 0.30),
            (maturity, 0.16),
            (watch_efficiency, 0.10),
            (conscious_efficiency, 0.08),
        )
    )
    decision_readiness = _weighted_score(
        (
            (harmony_index, 0.34),
            (speed_efficiency, 0.22),
            (signal_stability, 0.20),
            ((1.0 - wrongness_signal), 0.14),
            (conscious_clarity, 0.10),
        )
    )
    learning_elasticity = _weighted_score(
        (
            (retention_strength, 0.28),
            (knowledge_transfer, 0.24),
            (conscious_focus, 0.22),
            (response_softness, 0.16),
            (watch_efficiency, 0.10),
        )
    )
    divergence_penalty = clamp01(abs(watch_efficiency - conscious_efficiency))
    stability_guard = clamp01(
        (signal_stability * 0.30)
        + (anomaly_resistance * 0.20)
        + (drift_control * 0.20)
        + (conscious_resilience * 0.20)
        + ((1.0 - divergence_penalty) * 0.10)
    )
    efficiency_confidence = _weighted_score(
        (
            (signal_stability, 0.24),
            (maturity, 0.18),
            (stability_guard, 0.22),
            (harmony_index, 0.18),
            (decision_readiness, 0.18),
        )
    )
    composite_efficiency = _weighted_score(
        (
            (yield_efficiency, 0.34),
            (decision_readiness, 0.22),
            (learning_elasticity, 0.18),
            (harmony_index, 0.16),
            (stability_guard, 0.10),
        )
    )
    return {
        "energy_efficiency": energy_efficiency,
        "speed_efficiency": speed_efficiency,
        "yield_efficiency": yield_efficiency,
        "watch_efficiency": watch_efficiency,
        "conscious_efficiency": conscious_efficiency,
        "harmony_index": harmony_index,
        "decision_readiness": decision_readiness,
        "learning_elasticity": learning_elasticity,
        "stability_guard": stability_guard,
        "efficiency_confidence": efficiency_confidence,
        "composite_efficiency": composite_efficiency,
    }
