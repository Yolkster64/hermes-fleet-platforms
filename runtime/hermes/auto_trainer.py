import os
import time

import requests

API_BASE = os.getenv("HERMES_API_BASE_URL", "http://hermes-api:8787")
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
    stability_bias = max(0.55, min(0.99, stability_bias + (GAUSSIAN_PRESSURE * 0.04)))
    return sql_signal, internet_signal, llm_signal, stability_bias


def _smart_actions(data: dict, cycle: int, active_specialty: str, skill_pack: list[str], agent_size: str, dynamic_micro_agents: int) -> None:
    if not SMART_ACTIONS:
        return
    advisor_prompt = (
        "Generate one concrete optimization action, one communication mesh action, and one cross-LLM boost action "
        "to improve Hermes fleet speed/quality. Keep actions short and executable."
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
                "specialist_modes": SPECIALIST_MODES,
                "agent_work_styles": AGENT_WORK_STYLES,
                "advisor_text": advisor.get("response_text", "")[:1200],
            },
        },
        headers=_headers(),
        timeout=60,
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


def run_cycle() -> None:
    global _cycle
    _cycle += 1
    active_specialty = _active_specialty(_cycle)
    skill_pack = _selected_skills(_cycle)
    sim_steps = min(420, max(120, STEPS // 4 if MAX_MODE else STEPS))
    data = _post(
        "/simulate",
        {
            "steps": sim_steps,
            "specialty": active_specialty,
        },
        timeout=120,
    )
    signal_score = max(0.0, min(1.0, (data.get("avg_truth_score", 0.5) * 0.6) + (data.get("avg_quality", 0.5) * 0.4)))
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
            },
        },
        headers=_headers(),
        timeout=30,
    ).raise_for_status()
    agent_size, dynamic_micro_agents = _agent_size_profile(_cycle, data)
    sql_signal, internet_signal, llm_signal, stability_bias = _base_signals(data)
    pulse_steps = min(520, max(140, STEPS // 3 if MAX_MODE else STEPS // 2))
    pulse_candidates = (
        FLEET_CANDIDATES
        if not MAX_MODE
        else min(500, max(FLEET_CANDIDATES, 240) + int(dynamic_micro_agents * 0.2))
    )
    if _cycle % max(1, FLEET_OPTIMIZE_EVERY) == 0 or ALWAYS_DEEP_LEARNING:
        _post(
            "/learning-pulse",
            {
                "specialty": active_specialty,
                "steps": pulse_steps,
                "candidates": pulse_candidates,
                "sql_signal": sql_signal,
                "internet_signal": internet_signal,
                "llm_signal": llm_signal,
                "stability_bias": stability_bias,
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
    _smart_actions(data, _cycle, active_specialty, skill_pack, agent_size, dynamic_micro_agents)
    print(
        f"[auto-trainer] cycle={_cycle} mode={'MAX' if MAX_MODE else 'BALANCED'} strategy={SWARM_STRATEGY} "
        f"specialty={active_specialty} size={agent_size} micro_agents={dynamic_micro_agents} skills={','.join(skill_pack)} steps={data.get('steps')} "
        f"avg_reward={data.get('avg_reward_score'):.4f} "
        f"avg_truth={data.get('avg_truth_score'):.4f} "
        f"avg_knaa_qnaa={data.get('avg_knaa_qnaa_score', 0.0):.4f} "
        f"avg_fleet_shape={data.get('avg_fleet_shape_score', 0.0):.4f} "
        f"avg_long_haul_meta={data.get('avg_long_haul_meta_score', 0.0):.4f}"
    )


if __name__ == "__main__":
    while True:
        try:
            run_cycle()
        except Exception as exc:
            print(f"[auto-trainer] cycle failed: {exc}")
        time.sleep(SLEEP_SECONDS)
