from __future__ import annotations

from typing import Dict


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
    "optimization": {
        "size_factor": "Fleet size utilization ratio.",
        "position_score": "Agent/fleet ranking position quality.",
        "energy_efficiency": "Output per unit energy pressure.",
        "speed_efficiency": "Speed quality under current load.",
        "yield_efficiency": "Total useful output efficiency.",
        "watch_efficiency": "Quality of monitoring throughput vs overhead.",
    },
}


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


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
    watch_efficiency = clamp01((watch_coverage * 0.35) + (signal_stability * 0.25) + (anomaly_resistance * 0.20) + (drift_control * 0.20))
    energy_efficiency = clamp01(
        (success_signal * 0.32) + (monitor * 0.20) + (maturity * 0.16) + ((1.0 - wrongness_signal) * 0.17) + (watch_efficiency * 0.15)
    )
    speed_efficiency = clamp01((position_score * 0.36) + (success_signal * 0.25) + (size_factor * 0.19) + (monitor * 0.10) + (signal_stability * 0.10))
    yield_efficiency = clamp01((energy_efficiency * 0.40) + (speed_efficiency * 0.30) + (maturity * 0.18) + (watch_efficiency * 0.12))
    return {
        "energy_efficiency": energy_efficiency,
        "speed_efficiency": speed_efficiency,
        "yield_efficiency": yield_efficiency,
        "watch_efficiency": watch_efficiency,
    }
