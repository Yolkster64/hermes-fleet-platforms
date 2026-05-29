from typing import Any, Dict, List

import streamlit as st


def render_xp_bar(label: str, value: float, color: str = "#4CAF50") -> None:
    pct = max(0.0, min(1.0, value)) * 100
    st.markdown(
        (
            f"**{label}**  \n"
            f"<div style='background:#1b1f24;border-radius:8px;padding:2px;'>"
            f"<div style='width:{pct:.1f}%;background:{color};height:16px;border-radius:6px;'></div>"
            f"</div>"
            f"<small>{pct:.1f}%</small>"
        ),
        unsafe_allow_html=True,
    )


def render_learning_diagram() -> None:
    st.graphviz_chart(
        """
digraph learning {
  rankdir=LR;
  node [shape=box, style=rounded];
  Prompt -> "Hermes Agents";
  "Hermes Agents" -> "Simulation";
  "Simulation" -> "Learning Pulse";
  "Learning Pulse" -> "Fleet Optimize";
  "Fleet Optimize" -> "Curate + Dedupe";
  "Curate + Dedupe" -> "Bonus + XP";
  "Bonus + XP" -> "Auto Next Cycle";
}
        """
    )


def latest_learned_profile(snapshot_data: Dict[str, Any]) -> Dict[str, Any]:
    signals = snapshot_data.get("external_signals_tail", [])
    for item in signals:
        payload = item.get("payload", {})
        if not isinstance(payload, dict):
            continue
        if "high_level_learning" in payload or "strategy" in payload or "swarm_strategy" in payload:
            return payload
    return {}


def fleet_score_history(snapshot_data: Dict[str, Any]) -> List[float]:
    scores: List[float] = []
    for event in reversed(snapshot_data.get("recent_events", [])):
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            continue
        reward = payload.get("reward_score")
        truth = payload.get("truth_score")
        shape = payload.get("fleet_shape_score")
        if isinstance(reward, (int, float)) and isinstance(truth, (int, float)) and isinstance(shape, (int, float)):
            score = max(0.0, min(100.0, ((float(reward) * 0.35) + (float(truth) * 0.35) + (float(shape) * 0.30)) * 100.0))
            scores.append(score)
    return scores
