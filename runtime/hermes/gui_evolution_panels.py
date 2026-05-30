from typing import Any, Dict, List

import streamlit as st


def _agent_icon(size_mode: str) -> str:
    if size_mode == "mini":
        return "⚡"
    if size_mode == "full":
        return "🛡️"
    return "🧠"


def _evolution_reason(row: Dict[str, Any]) -> str:
    vars_payload = row.get("variables", {})
    if not isinstance(vars_payload, dict):
        vars_payload = {}
    parts = []
    if float(vars_payload.get("retention_strength", 0.5)) >= 0.60:
        parts.append("strong memory retention")
    if float(vars_payload.get("knowledge_transfer", 0.5)) >= 0.58:
        parts.append("high knowledge transfer")
    if float(vars_payload.get("watch_efficiency", 0.5)) >= 0.56:
        parts.append("watch-efficient learning")
    if float(vars_payload.get("coordination_cohesion", 0.5)) >= 0.58:
        parts.append("fleet coordination gains")
    if not parts:
        parts.append("steady balanced training")
    return ", ".join(parts[:2])


def render_evolution_centerpiece(
    agent_rows: List[Dict[str, Any]],
    sql_intel: Dict[str, Any],
    growth_data: Dict[str, Any],
    training_status: Dict[str, Any],
) -> None:
    st.subheader("Hermes Evolution Centerpiece")
    recent_profiles = sql_intel.get("recent_hermes_profiles", []) if isinstance(sql_intel, dict) else []
    if not isinstance(recent_profiles, list):
        recent_profiles = []

    total_hermes = max(len(agent_rows), len(recent_profiles), 1)
    fleet_xp = sum(float(p.get("experience_xp", 0.0)) for p in recent_profiles if isinstance(p, dict))
    avg_level = (
        sum(float(p.get("level", 1)) for p in recent_profiles if isinstance(p, dict)) / max(1, len(recent_profiles))
        if recent_profiles
        else 1.0
    )
    fleet_evolution = min(1.0, fleet_xp / float(total_hermes * 10000.0))
    trend = float(sql_intel.get("trend", 0.0)) if isinstance(sql_intel, dict) else 0.0
    training_active = bool(training_status.get("training_active", False)) if isinstance(training_status, dict) else False

    h1, h2, h3, h4 = st.columns(4)
    h1.metric("Fleet Evolution", f"{fleet_evolution * 100:.1f}%")
    h2.metric("Average Hermes Level", f"{avg_level:.1f}")
    h3.metric("Learning Trend", f"{trend:+.4f}")
    h4.metric("Training State", "Active" if training_active else "Idle")
    st.progress(fleet_evolution, text=f"Fleet XP core: {int(fleet_xp)} / {int(total_hermes * 10000)}")

    if isinstance(growth_data, dict):
        g1, g2, g3 = st.columns(3)
        g1.metric("Growth Maturity", f"{float(growth_data.get('maturity_index', 0.0)) * 100:.1f}%")
        g2.metric("Growth Signal", f"{float(growth_data.get('growth_index', 0.0)) * 100:.1f}%")
        g3.metric("Character Fit", f"{float(growth_data.get('character_goal_fit', 0.0)) * 100:.1f}%")

    st.caption("How and why Hermes evolve: retention + transfer + watch efficiency + coordination signals compound into XP and level.")
    cards = [p for p in recent_profiles if isinstance(p, dict)][:8]
    if cards:
        st.markdown("#### Hermes Evolution Cards")
        for i in range(0, len(cards), 4):
            cols = st.columns(4)
            for col, row in zip(cols, cards[i : i + 4]):
                with col:
                    icon = _agent_icon(str(row.get("size_mode", "mid")))
                    st.markdown(f"**{icon} {row.get('hermes_id', 'hermes')}**")
                    st.caption(f"{row.get('specialty', 'fleet')} | level {int(row.get('level', 1))}")
                    st.progress(min(1.0, float(row.get("experience_xp", 0.0)) / 10000.0), text=f"XP {int(float(row.get('experience_xp', 0.0)))}")
                    st.caption(f"Speed +{float(row.get('speed_bonus', 0.0)) * 100:.1f}% | Token +{float(row.get('token_power_gain', 0.0)) * 100:.1f}%")
                    st.caption(f"Evolving by: {_evolution_reason(row)}")


def render_learning_graphs(sql_intel: Dict[str, Any]) -> None:
    st.markdown("#### Learning Graph Theater")
    signal_series = sql_intel.get("signal_series", []) if isinstance(sql_intel, dict) else []
    reward_series = sql_intel.get("reward_series", []) if isinstance(sql_intel, dict) else []
    truth_series = sql_intel.get("truth_series", []) if isinstance(sql_intel, dict) else []
    shape_series = sql_intel.get("shape_series", []) if isinstance(sql_intel, dict) else []

    if all(isinstance(s, list) and s for s in (signal_series, reward_series, truth_series, shape_series)):
        st.line_chart(
            {
                "signal": [float(v) for v in signal_series],
                "reward": [float(v) for v in reward_series],
                "truth": [float(v) for v in truth_series],
                "shape": [float(v) for v in shape_series],
            },
            use_container_width=True,
        )

    art_pattern = sql_intel.get("art_pattern", {}) if isinstance(sql_intel, dict) else {}
    if isinstance(art_pattern, dict) and art_pattern:
        st.bar_chart(
            {
                "art_pattern": {
                    "symmetry": float(art_pattern.get("symmetry_index", 0.0)),
                    "contrast": float(art_pattern.get("contrast_index", 0.0)),
                    "fractal": float(art_pattern.get("fractal_flow", 0.0)),
                    "compression": float(art_pattern.get("compression_ratio", 0.0)),
                    "overlap_3d": float(art_pattern.get("overlap_3d", 0.0)),
                }
            },
            use_container_width=True,
        )
