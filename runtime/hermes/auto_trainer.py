import os
import time
import math
import random
import json

import requests

API_BASE = os.getenv("HERMES_API_BASE_URL", "http://hermes-api:8787")
LEARNING_STATE_PATH = os.getenv("HERMES_LEARNING_STATE_PATH", "runtime/auto/hermes_learning_state.json")
SHARED_MODEL_ID = os.getenv("AIHUB_SHARED_MODEL_ID", "hermes-fleet-latest")
FLEET_MODEL_LABEL = os.getenv("HERMES_FLEET_MODEL_LABEL", "hermes-fleet-newest")
LOW_BANDWIDTH_MODE = os.getenv("HERMES_LOW_BANDWIDTH_MODE", "true").lower() in ("1", "true", "yes", "on")
OFFLINE_ONLY_MODE = os.getenv("HERMES_OFFLINE_ONLY", "false").lower() in ("1", "true", "yes", "on")
USER_ROUTED_INTERNET = os.getenv("HERMES_USER_ROUTED_INTERNET", "true").lower() in ("1", "true", "yes", "on")
SPECIALTY = os.getenv("HERMES_TRAIN_SPECIALTY", "fleet")
STEPS = int(os.getenv("HERMES_TRAIN_STEPS", "400"))
SLEEP_SECONDS = int(os.getenv("HERMES_TRAIN_INTERVAL_SECONDS", "12"))
FLEET_OPTIMIZE_EVERY = int(os.getenv("HERMES_FLEET_OPTIMIZE_EVERY", "6"))
FLEET_CANDIDATES = int(os.getenv("HERMES_FLEET_CANDIDATES", "200"))
MAX_MODE = os.getenv("HERMES_MAX_MODE", "true").lower() in ("1", "true", "yes", "on")
GATEWAY_KEY = os.getenv("HERMES_GATEWAY_KEY", "")
SMART_ACTIONS = os.getenv("HERMES_SMART_ACTIONS", "true").lower() in ("1", "true", "yes", "on")
ALWAYS_DEEP_LEARNING = os.getenv("HERMES_ALWAYS_DEEP_LEARNING", "true").lower() in ("1", "true", "yes", "on")
SWARM_STRATEGY = os.getenv("HERMES_SWARM_STRATEGY", "hybrid")
MICRO_AGENT_COUNT = int(os.getenv("HERMES_MICRO_AGENT_COUNT", "128"))
GAUSSIAN_PRESSURE = float(os.getenv("HERMES_GAUSSIAN_PRESSURE", "0.88"))
PERMANENT_INTELLIGENCE = os.getenv("HERMES_PERMANENT_INTELLIGENCE", "true").lower() in ("1", "true", "yes", "on")
HIGH_LEVEL_LEARNING = max(0.0, min(1.0, float(os.getenv("HERMES_HIGH_LEVEL_LEARNING", "0.70"))))
ENABLE_MOVIE_AIHUB = os.getenv("HERMES_ENABLE_MOVIE_AIHUB", "true").lower() in ("1", "true", "yes", "on")
ENABLE_GITHUB_KNOWLEDGE_SYNC = os.getenv("HERMES_ENABLE_GITHUB_KNOWLEDGE_SYNC", "true").lower() in ("1", "true", "yes", "on")
FIELD_ADAPTATION_WEIGHT = max(0.0, min(1.0, float(os.getenv("HERMES_FIELD_ADAPTATION_WEIGHT", "0.35"))))
SPECIALIST_MODES = [m.strip() for m in os.getenv("HERMES_SPECIALIST_MODES", "swarm,mesh,multipolar,specialist-mix").split(",") if m.strip()]
AGENT_WORK_STYLES = [s.strip() for s in os.getenv("HERMES_AGENT_WORK_STYLES", "fast_micro,deep_specialist,balanced_hybrid").split(",") if s.strip()]
AGENT_SKILLS_25 = [
    "coding",
    "error_checking",
    "testing",
    "gui_design",
    "security_hardening",
    "performance_tuning",
    "data_engineering",
    "ml_modeling",
    "neural_optimization",
    "gaussian_learning",
    "prompt_engineering",
    "llm_routing",
    "communication_mesh",
    "fleet_orchestration",
    "quantization",
    "parallelization",
    "multipolar_reasoning",
    "memory_management",
    "refactoring",
    "observability",
    "cost_optimization",
    "deployment",
    "api_integration",
    "documentation",
    "reliability_engineering",
]
_cycle = 0
_strategy_memory: dict[str, dict[str, float]] = {
    "speed": {k: 0.0 for k in ("nano-swarm", "hybrid", "swarm", "mesh", "multipolar", "specialist-mix")},
    "quality": {k: 0.0 for k in ("nano-swarm", "hybrid", "swarm", "mesh", "multipolar", "specialist-mix")},
    "recovery": {k: 0.0 for k in ("nano-swarm", "hybrid", "swarm", "mesh", "multipolar", "specialist-mix")},
    "exploration": {k: 0.0 for k in ("nano-swarm", "hybrid", "swarm", "mesh", "multipolar", "specialist-mix")},
}
_evidence_matrix: dict[str, dict[str, float]] = {}
_value_brain_history: list[float] = []

STRATEGY_ALGOS: dict[str, dict[str, float]] = {
    "nano-swarm": {"sql_boost": 0.05, "internet_boost": 0.09, "llm_boost": 0.06, "stability_boost": -0.02, "step_mult": 0.82, "candidate_mult": 1.35},
    "hybrid": {"sql_boost": 0.03, "internet_boost": 0.03, "llm_boost": 0.04, "stability_boost": 0.03, "step_mult": 1.00, "candidate_mult": 1.00},
    "swarm": {"sql_boost": 0.02, "internet_boost": 0.07, "llm_boost": 0.02, "stability_boost": -0.01, "step_mult": 0.90, "candidate_mult": 1.12},
    "mesh": {"sql_boost": 0.03, "internet_boost": 0.05, "llm_boost": 0.03, "stability_boost": 0.02, "step_mult": 1.02, "candidate_mult": 1.05},
    "multipolar": {"sql_boost": 0.01, "internet_boost": 0.04, "llm_boost": 0.08, "stability_boost": 0.01, "step_mult": 1.08, "candidate_mult": 0.95},
    "specialist-mix": {"sql_boost": 0.05, "internet_boost": 0.02, "llm_boost": 0.06, "stability_boost": 0.04, "step_mult": 1.10, "candidate_mult": 0.90},
}
_algo_live: dict[str, dict[str, float]] = {k: dict(v) for k, v in STRATEGY_ALGOS.items()}


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _resolved_state_path() -> str:
    if os.path.isabs(LEARNING_STATE_PATH):
        return LEARNING_STATE_PATH
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    return os.path.abspath(os.path.join(repo_root, LEARNING_STATE_PATH))


def _load_learning_state() -> None:
    global _strategy_memory, _evidence_matrix, _value_brain_history, _algo_live
    state_path = _resolved_state_path()
    if not os.path.exists(state_path):
        return
    with open(state_path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    saved_memory = data.get("strategy_memory", {})
    for occasion in _strategy_memory.keys():
        if occasion in saved_memory and isinstance(saved_memory[occasion], dict):
            for strategy in _strategy_memory[occasion].keys():
                if strategy in saved_memory[occasion]:
                    _strategy_memory[occasion][strategy] = float(saved_memory[occasion][strategy])
    saved_evidence = data.get("evidence_matrix", {})
    if isinstance(saved_evidence, dict):
        _evidence_matrix = saved_evidence
    saved_history = data.get("value_brain_history", [])
    if isinstance(saved_history, list):
        _value_brain_history = [float(v) for v in saved_history[-250:]]
    saved_algo = data.get("algo_live", {})
    if isinstance(saved_algo, dict):
        for strategy in _algo_live.keys():
            if strategy in saved_algo and isinstance(saved_algo[strategy], dict):
                for metric in _algo_live[strategy].keys():
                    if metric in saved_algo[strategy]:
                        _algo_live[strategy][metric] = float(saved_algo[strategy][metric])


def _save_learning_state() -> None:
    state_path = _resolved_state_path()
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as fh:
        json.dump(
            {
                "version": 1,
                "fleet_model_label": FLEET_MODEL_LABEL,
                "shared_model_id": SHARED_MODEL_ID,
                "strategy_memory": _strategy_memory,
                "evidence_matrix": _evidence_matrix,
                "value_brain_history": _value_brain_history[-250:],
                "algo_live": _algo_live,
                "updated_unix": time.time(),
            },
            fh,
            indent=2,
            sort_keys=True,
        )


def _headers():
    if GATEWAY_KEY.strip():
        return {"X-Hermes-Key": GATEWAY_KEY.strip()}
    return {}


def _post(path: str, payload: dict, timeout: int = 120) -> dict:
    last_error = None
    for attempt in range(4):
        try:
            response = requests.post(f"{API_BASE}{path}", json=payload, headers=_headers(), timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            last_error = exc
            time.sleep(0.8 + (attempt * 0.6))
    raise last_error


def _get(path: str, timeout: int = 30) -> dict:
    response = requests.get(f"{API_BASE}{path}", headers=_headers(), timeout=timeout)
    response.raise_for_status()
    return response.json()


def _active_specialty(cycle: int) -> str:
    mode = SPECIALIST_MODES[(cycle - 1) % max(1, len(SPECIALIST_MODES))]
    style = AGENT_WORK_STYLES[(cycle - 1) % max(1, len(AGENT_WORK_STYLES))]
    return f"{SPECIALTY}:{SWARM_STRATEGY}:{mode}:{style}"


def _selected_skills(cycle: int) -> list[str]:
    start = ((cycle - 1) * 3) % len(AGENT_SKILLS_25)
    return [AGENT_SKILLS_25[(start + i) % len(AGENT_SKILLS_25)] for i in range(3)]


def _agent_size_profile(cycle: int, data: dict) -> tuple[str, int]:
    load = float(data.get("avg_load", 0.5))
    if cycle % 3 == 1 or load < 0.45:
        return "small-fast", max(48, int(MICRO_AGENT_COUNT * 0.65))
    if cycle % 3 == 2 or load < 0.70:
        return "medium-balanced", max(72, int(MICRO_AGENT_COUNT * 0.85))
    return "large-deep", min(256, int(MICRO_AGENT_COUNT * 1.15))


def _base_signals(data: dict) -> tuple[float, float, float, float]:
    sql_signal = data.get("avg_quantized_compression_score", 0.55)
    internet_signal = data.get("avg_fleet_shape_score", 0.62)
    llm_signal = data.get("avg_long_haul_meta_score", data.get("avg_knaa_qnaa_score", 0.66))
    stability_bias = data.get("avg_truth_score", 0.70)
    if MAX_MODE or ALWAYS_DEEP_LEARNING:
        sql_signal = min(0.99, max(sql_signal, 0.90))
        internet_signal = min(0.99, max(internet_signal, 0.89))
        llm_signal = min(0.99, max(llm_signal, 0.92))
        stability_bias = min(0.99, max(stability_bias, 0.83))
    # HIGH_LEVEL_LEARNING near 1.0 biases retention/learning quality; near 0.0 biases raw speed/perf.
    stability_bias = max(0.55, min(0.99, stability_bias + (GAUSSIAN_PRESSURE * (0.02 + (0.04 * HIGH_LEVEL_LEARNING)))))
    llm_signal = max(0.60, min(0.99, llm_signal + (0.06 * HIGH_LEVEL_LEARNING)))
    internet_signal = max(0.55, min(0.99, internet_signal + (0.05 * (1.0 - HIGH_LEVEL_LEARNING))))
    if LOW_BANDWIDTH_MODE:
        internet_signal = max(0.06, min(0.30, internet_signal * 0.34))
        llm_signal = max(0.70, min(0.99, llm_signal + 0.02))
        stability_bias = max(0.60, min(0.99, stability_bias + 0.03))
    if OFFLINE_ONLY_MODE:
        internet_signal = 0.0
    elif USER_ROUTED_INTERNET:
        internet_signal = min(0.14, max(0.06, internet_signal))
    return sql_signal, internet_signal, llm_signal, stability_bias


def _chaos_vector(cycle: int, data: dict) -> tuple[float, float, float, float]:
    reward = float(data.get("avg_reward_score", 0.5))
    truth = float(data.get("avg_truth_score", 0.6))
    shape = float(data.get("avg_fleet_shape_score", 0.55))
    x = math.sin(cycle * 0.31 + reward * 2.7)
    y = math.cos(cycle * 0.23 + truth * 3.1)
    z = math.sin(cycle * 0.17 + shape * 2.3)
    chaos_rate = max(0.02, min(0.35, abs(x * y * z) * (0.4 + (1.0 - HIGH_LEVEL_LEARNING))))
    return x, y, z, chaos_rate


def _occasion_focus(data: dict) -> str:
    truth = float(data.get("avg_truth_score", 0.7))
    shape = float(data.get("avg_fleet_shape_score", 0.6))
    reward = float(data.get("avg_reward_score", 0.6))
    if truth < 0.63:
        return "truth-recovery"
    if shape < 0.56:
        return "topology-balance"
    if reward < 0.58:
        return "reward-boost"
    return "meta-optimization"


def _occasion_type(focus: str) -> str:
    if focus == "truth-recovery":
        return "recovery"
    if focus == "reward-boost":
        return "speed"
    if focus == "topology-balance":
        return "quality"
    return "exploration"


def _pick_strategy(occasion: str, chaos_rate: float, cycle: int) -> str:
    memory = _strategy_memory.get(occasion, {})
    if not memory:
        return SWARM_STRATEGY
    explore = max(0.12, min(0.40, chaos_rate + (0.05 if cycle % 7 == 0 else 0.0)))
    if random.random() < explore:
        return random.choice(list(memory.keys()))
    return max(memory.items(), key=lambda item: item[1])[0]


def _chaotic_factor_pack(chaos_rate: float) -> dict[str, float]:
    return {
        "ratio_sql": max(0.70, min(1.30, 1.0 + random.uniform(-1.0, 1.0) * chaos_rate)),
        "ratio_internet": max(0.70, min(1.30, 1.0 + random.uniform(-1.0, 1.0) * chaos_rate)),
        "ratio_llm": max(0.70, min(1.30, 1.0 + random.uniform(-1.0, 1.0) * chaos_rate)),
        "ratio_stability": max(0.75, min(1.25, 1.0 + random.uniform(-1.0, 1.0) * (chaos_rate * 0.7))),
        "ratio_steps": max(0.70, min(1.35, 1.0 + random.uniform(-1.0, 1.0) * chaos_rate)),
        "ratio_candidates": max(0.70, min(1.45, 1.0 + random.uniform(-1.0, 1.0) * chaos_rate)),
    }


def _record_evidence(occasion: str, strategy: str, agent_size: str, factors: dict[str, float], reward: float, truth: float, shape: float) -> None:
    ratio_key = f"{factors['ratio_sql']:.2f}/{factors['ratio_internet']:.2f}/{factors['ratio_llm']:.2f}/{factors['ratio_stability']:.2f}"
    key = f"{occasion}|{strategy}|{agent_size}|{ratio_key}"
    score = (reward * 0.45) + (truth * 0.35) + (shape * 0.20)
    prev = _evidence_matrix.get(key, {}).get("score", 0.0)
    _evidence_matrix[key] = {
        "score": max(0.0, min(1.0, (prev * 0.84) + (score * 0.16))),
        "reward": reward,
        "truth": truth,
        "shape": shape,
        "count": _evidence_matrix.get(key, {}).get("count", 0.0) + 1.0,
    }


def _top_evidence(limit: int = 8) -> list[dict]:
    items = sorted(_evidence_matrix.items(), key=lambda item: item[1].get("score", 0.0), reverse=True)[:limit]
    out: list[dict] = []
    for key, val in items:
        occasion, strategy, agent_size, ratio_key = key.split("|", 3)
        out.append(
            {
                "occasion": occasion,
                "strategy": strategy,
                "agent_size": agent_size,
                "ratio_key": ratio_key,
                "score": val.get("score", 0.0),
                "reward": val.get("reward", 0.0),
                "truth": val.get("truth", 0.0),
                "shape": val.get("shape", 0.0),
                "count": val.get("count", 0.0),
            }
        )
    return out


def _value_weight_pack(occasion: str, focus: str) -> dict[str, float]:
    base = {
        "ease": 0.10,
        "correctness": 0.28,
        "opposite_correctness_pressure": 0.08,
        "reward": 0.20,
        "truth": 0.20,
        "shape": 0.14,
        "special_reaction": 0.10,
    }
    if occasion == "speed":
        base["reward"] += 0.06
        base["ease"] += 0.04
    if occasion == "quality":
        base["truth"] += 0.06
        base["shape"] += 0.04
    if occasion == "recovery":
        base["correctness"] += 0.07
        base["opposite_correctness_pressure"] += 0.06
    if focus == "meta-optimization":
        base["special_reaction"] += 0.06
    total = sum(base.values())
    return {k: v / total for k, v in base.items()}


def _composite_value_brain(data: dict, factors: dict[str, float], algo: dict[str, float], occasion: str, focus: str, chaos_rate: float) -> dict[str, float]:
    reward = float(data.get("avg_reward_score", 0.5))
    truth = float(data.get("avg_truth_score", 0.6))
    shape = float(data.get("avg_fleet_shape_score", 0.55))
    ease = max(0.0, min(1.0, 1.0 - (chaos_rate * 0.6)))
    correctness = max(0.0, min(1.0, truth))
    opposite_correctness_pressure = max(0.0, min(1.0, abs(0.92 - correctness)))
    special_reaction = max(
        0.0,
        min(
            1.0,
            (algo["llm_boost"] * 2.4)
            + (algo["internet_boost"] * 1.5)
            + (factors["ratio_llm"] * 0.20)
            + (factors["ratio_internet"] * 0.15),
        ),
    )
    weights = _value_weight_pack(occasion, focus)
    value = (
        (ease * weights["ease"])
        + (correctness * weights["correctness"])
        + ((1.0 - opposite_correctness_pressure) * weights["opposite_correctness_pressure"])
        + (reward * weights["reward"])
        + (truth * weights["truth"])
        + (shape * weights["shape"])
        + (special_reaction * weights["special_reaction"])
    )
    composite = max(0.0, min(1.0, value))
    _value_brain_history.append(composite)
    if len(_value_brain_history) > 250:
        del _value_brain_history[: len(_value_brain_history) - 250]
    return {
        "value": composite,
        "ease": ease,
        "correctness": correctness,
        "opposite_correctness_pressure": opposite_correctness_pressure,
        "special_reaction": special_reaction,
        "reward": reward,
        "truth": truth,
        "shape": shape,
    }


def _horizon_growth_profile(data: dict, brain_value: dict[str, float], signal_score: float) -> dict[str, float]:
    short_horizon = _clamp01((float(data.get("avg_reward_score", 0.5)) * 0.42) + (float(brain_value.get("ease", 0.5)) * 0.33) + (float(data.get("avg_quality", 0.5)) * 0.25))
    mid_horizon = _clamp01((float(data.get("avg_truth_score", 0.5)) * 0.40) + (float(data.get("avg_fleet_shape_score", 0.5)) * 0.35) + (float(brain_value.get("correctness", 0.5)) * 0.25))
    long_horizon = _clamp01((float(data.get("avg_long_haul_meta_score", 0.5)) * 0.45) + (float(data.get("avg_knaa_qnaa_score", 0.5)) * 0.30) + (float(brain_value.get("value", 0.5)) * 0.25))
    growth = _clamp01((short_horizon * 0.30) + (mid_horizon * 0.35) + (long_horizon * 0.35))
    maturity = _clamp01((long_horizon * 0.48) + (growth * 0.32) + (signal_score * 0.20))
    softening = _clamp01((mid_horizon * 0.45) + (maturity * 0.35) + ((1.0 - abs(short_horizon - long_horizon)) * 0.20))
    return {
        "short_horizon": short_horizon,
        "mid_horizon": mid_horizon,
        "long_horizon": long_horizon,
        "growth_index": growth,
        "maturity_index": maturity,
        "softening_factor": softening,
    }


def _training_factor_profile(data: dict, horizon_profile: dict[str, float]) -> dict[str, float]:
    active_agents = float(data.get("active_agents", data.get("agent_count", 120)))
    size_factor = _clamp01(active_agents / 256.0)
    position_score = _clamp01(float(data.get("avg_success_rate", data.get("avg_truth_score", 0.6))))
    success_signal = _clamp01(float(data.get("avg_reward_score", 0.5)))
    wrongness_signal = _clamp01(1.0 - float(data.get("avg_truth_score", 0.6)))
    monitor_comparison = _clamp01(1.0 - abs(float(data.get("avg_knaa_qnaa_score", 0.5)) - float(data.get("avg_fleet_shape_score", 0.5))))
    return {
        "size_factor": size_factor,
        "position_score": position_score,
        "success_signal": success_signal,
        "wrongness_signal": wrongness_signal,
        "monitor_comparison": monitor_comparison,
        "maturity_signal": float(horizon_profile.get("maturity_index", 0.5)),
    }


def _spatial_overlap_map(occasion: str) -> list[dict]:
    local = _strategy_memory.get(occasion, {})
    names = list(local.keys())
    out: list[dict] = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            s1 = names[i]
            s2 = names[j]
            v1 = local.get(s1, 0.0)
            v2 = local.get(s2, 0.0)
            overlap = max(0.0, 1.0 - abs(v1 - v2))
            out.append({"a": s1, "b": s2, "overlap": overlap, "distance": abs(v1 - v2)})
    out.sort(key=lambda item: item["overlap"], reverse=True)
    return out[:12]


def _comparison_upgrade_pass(occasion: str, focus: str, cycle: int, base_steps: int, base_candidates: int) -> None:
    contenders = sorted(_strategy_memory.get(occasion, {}).items(), key=lambda item: item[1], reverse=True)
    top = [s for s, _ in contenders[:3]]
    if "nano-swarm" not in top:
        top = ["nano-swarm"] + top[:2]
    results: list[tuple[str, float]] = []
    for strategy in top:
        algo = _algo_live.get(strategy, STRATEGY_ALGOS["hybrid"])
        try:
            out = _post(
                "/learning-pulse",
                {
                    "specialty": f"{SPECIALTY}:{strategy}:comparison:{focus}",
                    "steps": max(80, min(260, int(base_steps * 0.65 * algo["step_mult"]))),
                    "candidates": max(48, min(220, int(base_candidates * 0.70 * algo["candidate_mult"]))),
                    "sql_signal": max(0.55, min(0.99, 0.82 + algo["sql_boost"])),
                    "internet_signal": (
                        0.0
                        if OFFLINE_ONLY_MODE
                        else (min(0.14, max(0.06, 0.12 + algo["internet_boost"] * 0.15)) if USER_ROUTED_INTERNET else max(0.55, min(0.99, 0.82 + algo["internet_boost"])))
                    ),
                    "llm_signal": max(0.60, min(0.99, 0.86 + algo["llm_boost"])),
                    "stability_bias": max(0.55, min(0.99, 0.84 + algo["stability_boost"])),
                },
                timeout=70,
            )
            try:
                _post(
                    "/ingest-knowledge-mesh",
                    {
                        "source_agent": f"trainer-{chosen_strategy}",
                        "target_agent": "orchestrator-core",
                        "task_family": specialty,
                        "pattern": f"{specialty}|{chosen_strategy}|{focus}",
                        "shape3d": [x, y, z],
                        "weight": max(0.0, min(1.0, pulse.get("pulse_score", 0.5))),
                        "confidence": max(0.0, min(1.0, (stability_bias * 0.6) + (signal_score * 0.4))),
                        "payload": {
                            "algorithm": chosen_strategy,
                            "focus": focus,
                            "evidence_matrix": _evidence_matrix.get(chosen_strategy, {}),
                            "chaotic_factor_pack": factors,
                            "value_brain": brain_value,
                            "cpp_available": cpp_available,
                        },
                    },
                    timeout=90,
                )
            except requests.RequestException:
                pass
            if ENABLE_MOVIE_AIHUB:
                try:
                    _post(
                        "/ingest-signal",
                        {
                            "source": "movie-aihub",
                            "signal_score": max(0.0, min(1.0, (pulse.get("pulse_score", 0.5) * 0.62) + (brain_value * 0.38))),
                            "payload": {
                                "domain": "movies_media",
                                "specialty": specialty,
                                "algorithm": chosen_strategy,
                                "shape3d": [x, y, z],
                                "chaos_rate": chaos_rate,
                                "focus": focus,
                            },
                        },
                        timeout=60,
                    )
                except requests.RequestException:
                    pass
            score = float(out.get("avg_reward", 0.0))
        except requests.RequestException:
            score = -1.0
        results.append((strategy, score))
    winners = sorted(results, key=lambda item: item[1], reverse=True)
    if not winners:
        return
    winner = winners[0][0]
    loser = winners[-1][0]
    tune = 0.008 + (0.006 if focus == "meta-optimization" else 0.0)
    if winner in _algo_live:
        _algo_live[winner]["llm_boost"] = max(0.0, min(0.15, _algo_live[winner]["llm_boost"] + tune))
        _algo_live[winner]["internet_boost"] = max(0.0, min(0.15, _algo_live[winner]["internet_boost"] + (tune * 0.6)))
    if loser in _algo_live:
        _algo_live[loser]["stability_boost"] = max(-0.03, min(0.12, _algo_live[loser]["stability_boost"] + (tune * 0.4)))
        _algo_live[loser]["candidate_mult"] = max(0.75, min(1.50, _algo_live[loser]["candidate_mult"] * 0.995))
    requests.post(
        f"{API_BASE}/ingest-signal",
        json={
            "source": "auto_trainer.comparison_upgrade",
            "signal_score": 0.88,
            "payload": {
                "cycle": cycle,
                "occasion": occasion,
                "focus": focus,
                "comparison_results": [{"strategy": s, "score": sc} for s, sc in winners],
                "winner": winner,
                "loser": loser,
                "algo_live_winner": _algo_live.get(winner, {}),
            },
        },
        headers=_headers(),
        timeout=45,
    ).raise_for_status()


def _update_strategy_memory(occasion: str, strategy: str, reward: float, truth: float, shape: float) -> None:
    if occasion not in _strategy_memory or strategy not in _strategy_memory[occasion]:
        return
    score = (reward * 0.45) + (truth * 0.35) + (shape * 0.20)
    prev = _strategy_memory[occasion][strategy]
    _strategy_memory[occasion][strategy] = max(0.0, min(1.0, (prev * 0.82) + (score * 0.18)))


def _emit_strategy_feedback(
    cycle: int,
    focus: str,
    occasion: str,
    selected_strategy: str,
    algo_profile: dict[str, float],
    dynamic_specialty: str,
    pulse_steps: int,
    pulse_candidates: int,
    sql_signal: float,
    internet_signal: float,
    llm_signal: float,
    stability_bias: float,
    reward: float,
    truth: float,
    shape: float,
    brain_value: dict[str, float],
    horizon_profile: dict[str, float],
    training_variables: dict[str, float],
    chaos: tuple[float, float, float, float],
) -> None:
    leaderboard = sorted(_strategy_memory.get(occasion, {}).items(), key=lambda item: item[1], reverse=True)
    requests.post(
        f"{API_BASE}/ingest-signal",
        json={
            "source": "auto_trainer.strategy_learning",
            "signal_score": max(0.0, min(1.0, (reward * 0.4) + (truth * 0.4) + (shape * 0.2))),
            "payload": {
                "cycle": cycle,
                "focus": focus,
                "occasion": occasion,
                "fleet_model_label": FLEET_MODEL_LABEL,
                "shared_model_id": SHARED_MODEL_ID,
                "selected_strategy": selected_strategy,
                "strategy_algorithm": algo_profile,
                "dynamic_specialty": dynamic_specialty,
                "recommended_learning_pulse": {
                    "steps": pulse_steps,
                    "candidates": pulse_candidates,
                    "sql_signal": sql_signal,
                    "internet_signal": internet_signal,
                    "llm_signal": llm_signal,
                    "stability_bias": stability_bias,
                },
                "score_components": {"reward": reward, "truth": truth, "fleet_shape": shape},
                "value_brain": brain_value,
                "horizon_profile": horizon_profile,
                "training_variables": training_variables,
                "value_brain_history_tail": _value_brain_history[-40:],
                "strategy_leaderboard": [{"strategy": s, "score": sc} for s, sc in leaderboard],
                "evidence_top_combinations": _top_evidence(),
                "spatial_overlap_map": _spatial_overlap_map(occasion),
                "chaos_3d_vector": {"x": chaos[0], "y": chaos[1], "z": chaos[2], "chaos_rate": chaos[3]},
            },
        },
        headers=_headers(),
        timeout=45,
    ).raise_for_status()


def _smart_actions(data: dict, cycle: int, active_specialty: str, skill_pack: list[str], agent_size: str, dynamic_micro_agents: int, chaos: tuple[float, float, float, float]) -> None:
    if not SMART_ACTIONS:
        return
    advisor_prompt = (
        "Generate one concrete optimization action, one communication mesh action, and one cross-LLM boost action "
        "to improve Hermes fleet speed/quality with adaptive specialist switching. Keep actions short and executable."
    )
    advisor = _post(
        "/llm-chat",
        {"prompt": advisor_prompt, "system_prompt": "You are Hermes fleet optimizer.", "temperature": 0.15, "max_tokens": 300},
        timeout=90,
    )
    requests.post(
        f"{API_BASE}/ingest-signal",
        json={
            "source": "auto_trainer.smart_actions",
            "signal_score": max(0.0, min(1.0, data.get("avg_truth_score", 0.7))),
            "payload": {
                "strategy": SWARM_STRATEGY,
                "active_specialty": active_specialty,
                "micro_agents": dynamic_micro_agents,
                "agent_size": agent_size,
                "skill_pack": skill_pack,
                "permanent_intelligence": PERMANENT_INTELLIGENCE,
                "fleet_model_label": FLEET_MODEL_LABEL,
                "shared_model_id": SHARED_MODEL_ID,
                "specialist_modes": SPECIALIST_MODES,
                "agent_work_styles": AGENT_WORK_STYLES,
                "high_level_learning": HIGH_LEVEL_LEARNING,
                "chaos_3d_vector": {"x": chaos[0], "y": chaos[1], "z": chaos[2], "chaos_rate": chaos[3]},
                "advisor_text": advisor.get("response_text", "")[:1200],
            },
        },
        headers=_headers(),
        timeout=60,
    ).raise_for_status()
    requests.post(
        f"{API_BASE}/ingest-signal",
        json={
            "source": "auto_trainer.heartbeat",
            "signal_score": max(0.0, min(1.0, signal_score)),
            "payload": {
                "cycle": _cycle,
                "specialty": dynamic_specialty,
                "mode": "continuous_training",
                "fleet_model_label": FLEET_MODEL_LABEL,
                "shared_model_id": SHARED_MODEL_ID,
                "timestamp_unix": time.time(),
            },
        },
        headers=_headers(),
        timeout=30,
    ).raise_for_status()
    if MAX_MODE or cycle % 2 == 0:
        _post(
            "/optimize-fleet",
            {
                "specialty": active_specialty,
                "candidates": min(500, max(FLEET_CANDIDATES, 240) + int(dynamic_micro_agents * 0.25)),
            },
            timeout=120,
        )


def _emit_knowledge_sync(
    cycle: int,
    dynamic_specialty: str,
    signal_score: float,
    training_variables: dict[str, float],
    chaos: tuple[float, float, float, float],
) -> None:
    if not ENABLE_GITHUB_KNOWLEDGE_SYNC:
        return
    x, y, z, chaos_rate = chaos
    requests.post(
        f"{API_BASE}/ingest-signal",
        json={
            "source": "auto_trainer.github_knowledge_sync",
            "signal_score": max(0.0, min(1.0, signal_score)),
            "payload": {
                "cycle": cycle,
                "specialty": dynamic_specialty,
                "github_training_enabled": True,
                "field_adaptation_weight": FIELD_ADAPTATION_WEIGHT,
                "knowledge_loop": "github_to_field_and_back",
                "training_variables": training_variables,
                "chaos_3d_vector": {"x": x, "y": y, "z": z, "chaos_rate": chaos_rate},
            },
        },
        headers=_headers(),
        timeout=30,
    ).raise_for_status()


def run_cycle() -> None:
    global _cycle
    _cycle += 1
    active_specialty = _active_specialty(_cycle)
    skill_pack = _selected_skills(_cycle)
    perf_bias = 1.0 - HIGH_LEVEL_LEARNING
    sim_steps = min(520, max(120, int((STEPS * (0.20 + (0.30 * perf_bias))) if MAX_MODE else STEPS)))
    data = _post(
        "/simulate",
        {
            "steps": sim_steps,
            "specialty": active_specialty,
        },
        timeout=120,
    )
    signal_score = max(0.0, min(1.0, (data.get("avg_truth_score", 0.5) * 0.6) + (data.get("avg_quality", 0.5) * 0.4)))
    cpp_kernel = {}
    cpp_available = False
    try:
        cpp_kernel = _get("/cpp-kernel-status", timeout=20)
        cpp_available = bool(cpp_kernel.get("available", False))
    except requests.RequestException:
        cpp_kernel = {"available": False}
    focus = _occasion_focus(data)
    occasion = _occasion_type(focus)
    x, y, z, chaos_rate = _chaos_vector(_cycle, data)
    selected_strategy = _pick_strategy(occasion, chaos_rate, _cycle)
    algo_profile = _algo_live.get(selected_strategy, STRATEGY_ALGOS["hybrid"])
    factors = _chaotic_factor_pack(chaos_rate)
    brain_value = _composite_value_brain(data, factors, algo_profile, occasion, focus, chaos_rate)
    horizon_profile = _horizon_growth_profile(data, brain_value, signal_score)
    training_variables = _training_factor_profile(data, horizon_profile)
    dynamic_specialty = f"{SPECIALTY}:{selected_strategy}:{focus}:m{horizon_profile['maturity_index']:.2f}"
    requests.post(
        f"{API_BASE}/ingest-signal",
        json={
            "source": "auto_trainer",
            "signal_score": signal_score,
            "payload": {
                "avg_reward_score": data.get("avg_reward_score"),
                "avg_knaa_qnaa_score": data.get("avg_knaa_qnaa_score"),
                "avg_fleet_shape_score": data.get("avg_fleet_shape_score"),
                "avg_long_haul_meta_score": data.get("avg_long_haul_meta_score"),
                "fleet_model_label": FLEET_MODEL_LABEL,
                "shared_model_id": SHARED_MODEL_ID,
                "high_level_learning": HIGH_LEVEL_LEARNING,
                "focus": focus,
                "occasion": occasion,
                "selected_strategy": selected_strategy,
                "strategy_algorithm": algo_profile,
                "chaotic_factor_pack": factors,
                "value_brain": brain_value,
                "horizon_profile": horizon_profile,
                "chaos_3d_vector": {"x": x, "y": y, "z": z, "chaos_rate": chaos_rate},
                "cpp_kernel": cpp_kernel,
            },
        },
        headers=_headers(),
        timeout=30,
    ).raise_for_status()
    agent_size, dynamic_micro_agents = _agent_size_profile(_cycle, data)
    sql_signal, internet_signal, llm_signal, stability_bias = _base_signals(data)
    if cpp_available:
        sql_signal = min(0.99, sql_signal + 0.04)
        llm_signal = min(0.99, llm_signal + 0.03)
        stability_bias = min(0.99, stability_bias + 0.02)
    sql_signal = max(0.55, min(0.99, (sql_signal + algo_profile["sql_boost"]) * factors["ratio_sql"]))
    internet_signal = max(0.55, min(0.99, (internet_signal + algo_profile["internet_boost"]) * factors["ratio_internet"]))
    if OFFLINE_ONLY_MODE:
        internet_signal = 0.0
    elif USER_ROUTED_INTERNET:
        internet_signal = min(0.14, max(0.06, internet_signal))
    llm_signal = max(0.60, min(0.99, (llm_signal + algo_profile["llm_boost"]) * factors["ratio_llm"]))
    stability_bias = max(0.55, min(0.99, (stability_bias + algo_profile["stability_boost"]) * factors["ratio_stability"]))
    stability_bias = max(0.55, min(0.99, (stability_bias * (0.82 + (horizon_profile["softening_factor"] * 0.18)))))
    pulse_steps = min(620, max(140, int((STEPS * (0.28 + (0.45 * HIGH_LEVEL_LEARNING))) if MAX_MODE else STEPS // 2)))
    pulse_steps = min(680, max(120, int(pulse_steps * algo_profile["step_mult"] * factors["ratio_steps"])))
    pulse_candidates = (
        FLEET_CANDIDATES
        if not MAX_MODE
        else min(500, max(FLEET_CANDIDATES, 240) + int(dynamic_micro_agents * 0.2))
    )
    pulse_candidates = min(520, max(48, int(pulse_candidates * algo_profile["candidate_mult"] * factors["ratio_candidates"])))
    if _cycle % 3 == 0 or MAX_MODE:
        _comparison_upgrade_pass(occasion, focus, _cycle, pulse_steps, pulse_candidates)
    pulse_out = {}
    if _cycle % max(1, FLEET_OPTIMIZE_EVERY) == 0 or ALWAYS_DEEP_LEARNING:
        pulse_out = _post(
            "/learning-pulse",
            {
                "specialty": dynamic_specialty,
                "steps": pulse_steps,
                "candidates": pulse_candidates,
                "sql_signal": sql_signal,
                "internet_signal": internet_signal,
                "llm_signal": llm_signal,
                "stability_bias": max(0.55, min(0.99, stability_bias + chaos_rate * 0.07)),
            },
            timeout=120,
        )
        _post(
            "/curate-learning",
            {
                "sql_signal": sql_signal,
                "internet_signal": internet_signal,
                "llm_signal": llm_signal,
                "stability_bias": stability_bias,
            },
            timeout=90,
        )
        _post("/dedupe-optimize", {"roots": ["imports", "core", "src", "runtime"], "max_file_mb": 8}, timeout=120)
    learned_reward = float(pulse_out.get("avg_reward", data.get("avg_reward_score", 0.5)))
    learned_truth = float(data.get("avg_truth_score", 0.6))
    learned_shape = float(data.get("avg_fleet_shape_score", 0.55))
    weighted_reward = max(0.0, min(1.0, (learned_reward * 0.75) + (brain_value["value"] * 0.25)))
    _update_strategy_memory(occasion, selected_strategy, weighted_reward, learned_truth, learned_shape)
    _record_evidence(occasion, selected_strategy, agent_size, factors, learned_reward, learned_truth, learned_shape)
    _emit_strategy_feedback(
        cycle=_cycle,
        focus=focus,
        occasion=occasion,
        selected_strategy=selected_strategy,
        algo_profile=algo_profile,
        dynamic_specialty=dynamic_specialty,
        pulse_steps=pulse_steps,
        pulse_candidates=pulse_candidates,
        sql_signal=sql_signal,
        internet_signal=internet_signal,
        llm_signal=llm_signal,
        stability_bias=stability_bias,
        reward=learned_reward,
        truth=learned_truth,
        shape=learned_shape,
        brain_value=brain_value,
        horizon_profile=horizon_profile,
        training_variables=training_variables,
        chaos=(x, y, z, chaos_rate),
    )
    _emit_knowledge_sync(_cycle, dynamic_specialty, signal_score, training_variables, (x, y, z, chaos_rate))
    _smart_actions(data, _cycle, dynamic_specialty, skill_pack, agent_size, dynamic_micro_agents, (x, y, z, chaos_rate))
    _save_learning_state()
    print(
        f"[auto-trainer] cycle={_cycle} mode={'MAX' if MAX_MODE else 'BALANCED'} strategy={selected_strategy} "
        f"specialty={dynamic_specialty} size={agent_size} micro_agents={dynamic_micro_agents} "
        f"high_level_learning={HIGH_LEVEL_LEARNING:.2f} chaos={chaos_rate:.3f} "
        f"cpp_native={str(cpp_available).lower()} "
        f"skills={','.join(skill_pack)} steps={data.get('steps')} "
        f"avg_reward={data.get('avg_reward_score'):.4f} "
        f"avg_truth={data.get('avg_truth_score'):.4f} "
        f"avg_knaa_qnaa={data.get('avg_knaa_qnaa_score', 0.0):.4f} "
        f"avg_fleet_shape={data.get('avg_fleet_shape_score', 0.0):.4f} "
        f"avg_long_haul_meta={data.get('avg_long_haul_meta_score', 0.0):.4f}"
    )


if __name__ == "__main__":
    _load_learning_state()
    while True:
        try:
            run_cycle()
        except Exception as exc:
            print(f"[auto-trainer] cycle failed: {exc}")
        finally:
            try:
                _save_learning_state()
            except Exception as state_exc:
                print(f"[auto-trainer] state save failed: {state_exc}")
        time.sleep(SLEEP_SECONDS)
