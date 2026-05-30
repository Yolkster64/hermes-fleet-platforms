from typing import Any, Dict, List

import streamlit as st


def _fallback_candidates() -> List[Dict[str, Any]]:
    return [
        {"model": "hermes-mini-fast", "speed_tokens_per_sec": 125.0, "cost_per_1k_tokens": 0.0018, "quality_score": 0.68, "blend_score": 0.70},
        {"model": "hermes-balanced-plus", "speed_tokens_per_sec": 72.0, "cost_per_1k_tokens": 0.0055, "quality_score": 0.82, "blend_score": 0.80},
        {"model": "hermes-reasoning-max", "speed_tokens_per_sec": 36.0, "cost_per_1k_tokens": 0.0120, "quality_score": 0.94, "blend_score": 0.92},
        {"model": "hermes-guard-safe", "speed_tokens_per_sec": 48.0, "cost_per_1k_tokens": 0.0088, "quality_score": 0.90, "blend_score": 0.86},
    ]


def _model_zone(name: str) -> str:
    model = name.lower()
    if "mini" in model:
        return "Fast Lane"
    if "guard" in model or "safe" in model:
        return "Safety Orbit"
    if "reasoning" in model or "max" in model:
        return "Deep Core"
    return "Balanced Ring"


def render_aihub_watch_panels(
    unified: Dict[str, Any],
    watch_payload: Dict[str, Any],
    gateway_status: Dict[str, Any],
    sql_intel: Dict[str, Any],
    training_status: Dict[str, Any],
    growth_data: Dict[str, Any],
    optimizer_state: Dict[str, Any],
) -> Dict[str, Any]:
    st.subheader("AIHub Watch Map + Fleet Forecast")
    routes = gateway_status.get("routes", []) if isinstance(gateway_status, dict) else []
    if not isinstance(routes, list):
        routes = []
    avg_latency = 0.0
    if routes:
        avg_latency = sum(float(r.get("avg_ms", 0.0)) for r in routes[:12]) / max(1, min(12, len(routes)))

    active_agents = float(training_status.get("active_agents", 0.0)) if isinstance(training_status, dict) else 0.0
    training_active = bool(training_status.get("training_active", False)) if isinstance(training_status, dict) else False
    growth_index = float(growth_data.get("growth_index", 0.0)) if isinstance(growth_data, dict) else 0.0
    maturity = float(growth_data.get("maturity_index", 0.0)) if isinstance(growth_data, dict) else 0.0
    trend = float(sql_intel.get("trend", 0.0)) if isinstance(sql_intel, dict) else 0.0
    watch_eff = float(sql_intel.get("variable_means", {}).get("watch_efficiency", 0.5)) if isinstance(sql_intel, dict) else 0.5
    sql_health = sql_intel.get("sql_health", {}) if isinstance(sql_intel, dict) else {}
    if not isinstance(sql_health, dict):
        sql_health = {}
    db_mb = float(sql_health.get("db_mb", 0.0))
    total_cycles = int(sql_health.get("total_cycles", 0))
    action_brain = float(growth_data.get("avg_action_brain", 0.0)) if isinstance(growth_data, dict) else 0.0
    adaptive_brain = float(growth_data.get("avg_adaptive_brain", 0.0)) if isinstance(growth_data, dict) else 0.0

    fleet_growth_hour = max(0.0, ((growth_index * 0.55) + (maturity * 0.25) + max(0.0, trend) * 0.20) * 100.0)
    fleet_growth_day = fleet_growth_hour * 9.5
    practice_index = max(0.0, min(100.0, ((growth_index * 0.45) + (watch_eff * 0.35) + (maturity * 0.20)) * 100.0))
    power_draw_w = max(0.0, (active_agents * 2.6) + (practice_index * 1.8) + (35.0 if training_active else 12.0))

    f1, f2, f3, f4 = st.columns(4)
    f1.metric("Fleet Growth Forecast (1h)", f"+{fleet_growth_hour:.1f}%")
    f2.metric("Fleet Growth Forecast (24h)", f"+{fleet_growth_day:.1f}%")
    f3.metric("Practice Intensity", f"{practice_index:.1f}/100")
    f4.metric("Estimated Power Draw", f"{power_draw_w:.1f} W")
    st.caption(f"Latency watch: ~{avg_latency:.1f} ms avg | profile={unified.get('aihub_shared_ml_profile', 'global-learning')}")

    candidates = optimizer_state.get("candidates", []) if isinstance(optimizer_state, dict) else []
    if not isinstance(candidates, list) or not candidates:
        candidates = _fallback_candidates()

    model_rows = []
    for item in candidates[:8]:
        name = str(item.get("model", "unknown"))
        speed = float(item.get("speed_tokens_per_sec", item.get("speed_tps", 0.0)))
        cost = float(item.get("cost_per_1k_tokens", item.get("cost_per_1k", 0.0)))
        blend = float(item.get("blend_score", 0.0))
        quality = float(item.get("quality_score", item.get("quality", 0.0)))
        zone = _model_zone(name)
        latency_est = max(12.0, (135.0 - min(130.0, speed)) + (cost * 2400.0))
        power_est = max(8.0, (quality * 44.0) + (blend * 21.0) + (cost * 1800.0))
        bonus_mult = 1.0 + (blend * 0.35) + (watch_eff * 0.20)
        specialty = "complex reasoning" if "max" in name else ("safe governance" if "guard" in name else ("rapid iteration" if "mini" in name else "balanced planning"))
        model_rows.append(
            {
                "Model": name,
                "Zone": zone,
                "Specialty": specialty,
                "Latency ms(est)": round(latency_est, 1),
                "Power W(est)": round(power_est, 1),
                "Bonus x": round(bonus_mult, 3),
                "Speed tok/s": round(speed, 1),
            }
        )

    st.markdown("#### Multi-LLM AIHub Map")
    st.dataframe(model_rows, use_container_width=True, hide_index=True)
    st.bar_chart(
        {
            "bonus": {row["Model"]: row["Bonus x"] for row in model_rows},
            "power": {row["Model"]: row["Power W(est)"] for row in model_rows},
        },
        use_container_width=True,
    )

    complexity = min(1.0, (avg_latency / 220.0) * 0.35 + (1.0 - watch_eff) * 0.35 + (max(0.0, -trend) * 0.30))
    complicated = complexity >= 0.42
    if complicated:
        st.warning("Complicated situation detected: auto-design upgrade path is recommended.")
    else:
        st.success("System complexity looks manageable. Continue balanced scaling.")

    st.markdown("#### Ultimate Ops Center (Brain + SQL + Power)")
    u1, u2, u3, u4, u5 = st.columns(5)
    u1.metric("Action Brain", f"{action_brain * 100:.1f}%")
    u2.metric("Adaptive Brain", f"{adaptive_brain * 100:.1f}%")
    u3.metric("SQL Size", f"{db_mb:.2f} MB")
    u4.metric("SQL Cycles", str(total_cycles))
    u5.metric("Complexity", f"{complexity * 100:.1f}%")
    stability_index = max(0.0, min(1.0, (watch_eff * 0.35) + ((1.0 - complexity) * 0.30) + (adaptive_brain * 0.20) + (action_brain * 0.15)))
    escalation_index = max(0.0, min(1.0, (complexity * 0.45) + (max(0.0, -trend) * 0.30) + ((1.0 - watch_eff) * 0.25)))
    st.progress(stability_index, text=f"Stability Index: {stability_index * 100:.1f}%")
    st.progress(escalation_index, text=f"Escalation Pressure: {escalation_index * 100:.1f}%")

    return {
        "complexity": complexity,
        "complicated": complicated,
        "stability_index": stability_index,
        "escalation_index": escalation_index,
        "recommended_payload": {
            "specialty": "fleet:aihub:auto-design",
            "steps": int(700 if complicated else 500),
            "candidates": int(320 if complicated else 220),
            "sql_signal": 0.94 if complicated else 0.86,
            "internet_signal": 0.10 if complicated else 0.08,
            "llm_signal": 0.96 if complicated else 0.91,
            "stability_bias": max(0.78, min(0.96, (0.84 if complicated else 0.80) + (stability_index * 0.08))),
        },
    }
