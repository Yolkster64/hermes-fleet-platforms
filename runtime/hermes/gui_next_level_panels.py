import html
import json
import os
import time
from typing import Any, Callable, Dict, List

import streamlit as st

from training_sql_intel import export_hermes_profiles_snapshot


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _inject_next_level_theme() -> None:
    st.markdown(
        """
<style>
.stApp, .stApp * {font-family: "Segoe UI Variable Text", "Segoe UI", Inter, Arial, sans-serif;}
.hermes-glow {border: 1px solid rgba(0, 230, 255, 0.45); border-radius: 14px; padding: 12px; background: linear-gradient(120deg, rgba(10,20,40,0.8), rgba(25,25,45,0.65)); box-shadow: 0 0 16px rgba(0, 210, 255, 0.25);}
.recommended-pill {display: inline-block; padding: 3px 8px; border-radius: 999px; font-size: 12px; color: #00101a; background: linear-gradient(90deg, #00f0ff, #7dffb3); font-weight: 700; box-shadow: 0 0 12px rgba(0, 240, 255, 0.45);}
.cool-title {font-size: 1.1rem; font-weight: 700; letter-spacing: 0.3px;}
.monado-orbit {position: relative; height: 44px; margin: 6px 0 10px 0;}
.monado-orbit span {position: absolute; border-radius: 999px; border: 1px solid rgba(130, 205, 255, 0.35);}
.monado-orbit span:nth-child(1) {inset: 8px 36%; animation: monadoPulse 3.2s ease-in-out infinite;}
.monado-orbit span:nth-child(2) {inset: 3px 29%; animation: monadoPulse 4.1s ease-in-out infinite reverse;}
.monado-orbit span:nth-child(3) {inset: 0px 22%; opacity: 0.58; animation: monadoSpinLite 12s linear infinite;}
.holo-kanji-mini {text-align:right; font-size:0.92rem; letter-spacing:0.16rem; color: rgba(164, 216, 255, 0.50); font-family:'Yu Gothic UI','MS Gothic','Segoe UI',sans-serif;}
.holo-scan {height: 4px; border-radius: 999px; background: linear-gradient(90deg, rgba(0,0,0,0), rgba(117,246,255,0.9), rgba(186,120,255,0.8), rgba(0,0,0,0)); opacity: 0.66; animation: scanSweep 6.6s linear infinite;}
.clock-wrap {display:flex; justify-content:center; align-items:center; height:96px; border-radius:12px; border:1px solid rgba(255,255,255,0.15); background: radial-gradient(circle at 50% 20%, rgba(0,255,220,0.15), rgba(20,20,40,0.65));}
.clock-glow {animation: pulseGlow 1.8s ease-in-out infinite; font-family: 'Segoe UI', Inter, Arial;}
div.stButton > button {border-radius: 12px; border: 1px solid rgba(117, 216, 255, 0.45); background: linear-gradient(135deg, rgba(31,50,86,0.9), rgba(18,26,48,0.95)); color: #eaf7ff; box-shadow: 0 0 10px rgba(112, 198, 255, 0.28);}
div.stButton > button:hover {border-color: rgba(145, 233, 255, 0.82); box-shadow: 0 0 14px rgba(112, 198, 255, 0.42);}
@keyframes pulseGlow {0% {transform: scale(1.0); text-shadow: 0 0 8px rgba(120,220,255,0.35);} 50% {transform: scale(1.03); text-shadow: 0 0 16px rgba(120,220,255,0.75);} 100% {transform: scale(1.0); text-shadow: 0 0 8px rgba(120,220,255,0.35);}}
@keyframes monadoPulse {0% {transform: scaleX(0.94); opacity: 0.30;} 50% {transform: scaleX(1.06); opacity: 0.85;} 100% {transform: scaleX(0.94); opacity: 0.30;}}
@keyframes monadoSpinLite {from {transform: rotate(0deg);} to {transform: rotate(360deg);}}
@keyframes scanSweep {0% {transform: translateX(-20%) scaleX(0.78);} 50% {transform: translateX(18%) scaleX(1.04);} 100% {transform: translateX(-20%) scaleX(0.78);}}
</style>
""",
        unsafe_allow_html=True,
    )


def _role_area_for_specialty(specialty: str) -> str:
    s = str(specialty).lower()
    if "security" in s:
        return "Security Ring"
    if "sql" in s or "data" in s:
        return "SQL Core"
    if "gui" in s or "ux" in s:
        return "Design Deck"
    if "fleet" in s or "orchestration" in s:
        return "Fleet Nexus"
    if "training" in s or "learning" in s:
        return "Learning Grid"
    return "General Bay"


def _sort_map_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    area_rank = {
        "Fleet Nexus": 0,
        "SQL Core": 1,
        "Learning Grid": 2,
        "Design Deck": 3,
        "Security Ring": 4,
        "General Bay": 5,
    }
    return sorted(
        rows,
        key=lambda row: (
            area_rank.get(str(row.get("area", "General Bay")), 99),
            -int(row.get("level", 0)),
            -int(row.get("xp", 0)),
            str(row.get("bot", "")),
        ),
    )


def _render_center_nexus(
    *,
    sql_health: Dict[str, Any],
    growth_data: Dict[str, Any],
    training_status: Dict[str, Any],
    unified: Dict[str, Any],
    cpp_kernel: Dict[str, Any],
) -> None:
    db_mb = float(sql_health.get("db_mb", 0.0))
    wal_mb = float(sql_health.get("wal_mb", 0.0))
    growth = float(growth_data.get("growth_index", 0.0)) if isinstance(growth_data, dict) else 0.0
    maturity = float(growth_data.get("maturity_index", 0.0)) if isinstance(growth_data, dict) else 0.0
    active = int(training_status.get("active_agents", 0)) if isinstance(training_status, dict) else 0
    total = max(1, int(training_status.get("agent_count", 1))) if isinstance(training_status, dict) else 1
    collab = _clamp01((active / total) * 0.45 + (growth * 0.30) + (maturity * 0.25))
    cpp_ready = bool(cpp_kernel.get("available", cpp_kernel.get("cpp_ready", False))) if isinstance(cpp_kernel, dict) else False
    speed_band = "C++ Safe Path ON" if cpp_ready else "Python Fallback Path"
    model_name = html.escape(str(unified.get("aihub_shared_model_id", "aihub-unified-v1")))
    entry_name = html.escape(str(unified.get("single_exe_entrypoint", "hermes-gateway")))
    center_score = _clamp01((growth * 0.30) + (maturity * 0.24) + ((1.0 - _clamp01((db_mb / 1024.0) + (wal_mb / 256.0))) * 0.20) + (collab * 0.26))
    st.markdown(
        f"""
<div style="border:1px solid rgba(0,230,255,0.35); border-radius:16px; padding:14px; background:radial-gradient(circle at 50% 20%, rgba(74,148,255,0.22), rgba(13,19,36,0.84));">
  <div style="font-weight:800; color:#e9f5ff; margin-bottom:6px;">AIHub / SQL / Fleet Nexus</div>
  <div style="display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:8px;">
    <div style="background:rgba(255,255,255,0.06); padding:8px; border-radius:10px;"><div style="font-size:0.72rem; color:#a7d6ff;">Nexus Score</div><div style="font-size:1.08rem; color:#ecf7ff;">{center_score * 100:.1f}%</div></div>
    <div style="background:rgba(255,255,255,0.06); padding:8px; border-radius:10px;"><div style="font-size:0.72rem; color:#a7d6ff;">Fleet Collaboration</div><div style="font-size:1.08rem; color:#ecf7ff;">{collab * 100:.1f}%</div></div>
    <div style="background:rgba(255,255,255,0.06); padding:8px; border-radius:10px;"><div style="font-size:0.72rem; color:#a7d6ff;">SQL Load</div><div style="font-size:1.08rem; color:#ecf7ff;">DB {db_mb:.1f}MB / WAL {wal_mb:.1f}MB</div></div>
    <div style="background:rgba(255,255,255,0.06); padding:8px; border-radius:10px;"><div style="font-size:0.72rem; color:#a7d6ff;">Speed Path</div><div style="font-size:1.08rem; color:#ecf7ff;">{speed_band}</div></div>
  </div>
  <div style="margin-top:8px; font-size:0.78rem; color:#cfe6ff;">Model: {model_name} • Entry: {entry_name}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def _render_center_sql_visual(sql_health: Dict[str, Any], evidence: Dict[str, Any]) -> None:
    db_mb = float(sql_health.get("db_mb", 0.0))
    wal_mb = float(sql_health.get("wal_mb", 0.0))
    rows = float(sql_health.get("total_evidence_rows", 0.0))
    evidence_score = float(evidence.get("score", 0.0)) if isinstance(evidence, dict) else 0.0
    db_ratio = _clamp01(db_mb / 1024.0)
    wal_ratio = _clamp01(wal_mb / 256.0)
    row_ratio = _clamp01(rows / 200000.0)
    st.markdown("#### Center SQL Visual")
    st.markdown(
        """
<div style="border:1px solid rgba(0,230,255,0.35); border-radius:16px; padding:14px; background:radial-gradient(circle at 50% 20%, rgba(40,90,170,0.22), rgba(13,19,36,0.84));">
  <div style="font-weight:800; color:#e9f5ff; margin-bottom:6px;">SQL Core Pulse</div>
  <div style="font-size:0.80rem; color:#d2e7ff;">Simple center view for SQL deployment + training readiness.</div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.progress(db_ratio, text=f"DB Utilization {db_ratio * 100:.1f}% ({db_mb:.1f} MB)")
    st.progress(wal_ratio, text=f"WAL Utilization {wal_ratio * 100:.1f}% ({wal_mb:.1f} MB)")
    st.progress(row_ratio, text=f"Evidence Rows {int(rows)}")
    st.progress(_clamp01(evidence_score), text=f"Evidence Confidence {evidence_score * 100:.1f}%")


def render_next_level_control_center(
    *,
    sql_intel: Dict[str, Any],
    growth_data: Dict[str, Any],
    training_status: Dict[str, Any],
    watch_payload: Dict[str, Any],
    unified: Dict[str, Any],
    cpp_kernel: Dict[str, Any],
    ultimate_entrance: Dict[str, Any],
    volume_root: str,
    run_logged_post_action: Callable[..., None],
    show_center_nexus: bool = False,
) -> None:
    _inject_next_level_theme()
    st.markdown("### Level 5 AIHub + SQL Command Center")
    st.markdown('<div class="hermes-glow"><span class="recommended-pill">LEVEL 5</span> <span class="cool-title">Enhanced visuals, center SQL design, richer bars/animations, fleet styling, and guided deployment</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="monado-orbit"><span></span><span></span><span></span></div>', unsafe_allow_html=True)
    st.markdown('<div class="holo-scan"></div>', unsafe_allow_html=True)
    st.markdown('<div class="holo-kanji-mini">光 斬 学 翼</div>', unsafe_allow_html=True)
    smart_tools = [str(x) for x in st.session_state.get("ctl_smart_tools", []) if isinstance(x, str)]
    both_sides_training = bool(st.session_state.get("ctl_both_sides_training", True))
    x5_brain_pack = bool(st.session_state.get("ctl_x5_brain_pack", False))
    x6_learning_pack = bool(st.session_state.get("ctl_x6_learning_pack", True))

    tabs = st.tabs(["SQL Center", "AIHub Lab", "Fleet Table", "Evidence Advisor", "Security + Benchmark", "Clock + Style"])
    sql_health = sql_intel.get("sql_health", {}) if isinstance(sql_intel, dict) else {}
    if not isinstance(sql_health, dict):
        sql_health = {}
    evidence = sql_intel.get("evidence", {}) if isinstance(sql_intel, dict) else {}
    if not isinstance(evidence, dict):
        evidence = {}

    with tabs[0]:
        _render_center_sql_visual(sql_health=sql_health, evidence=evidence)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("SQL DB MB", f"{float(sql_health.get('db_mb', 0.0)):.2f}")
        c2.metric("Training Dir MB", f"{float(sql_health.get('training_dir_mb', 0.0)):.2f}")
        c3.metric("Evidence Rows", str(int(sql_health.get("total_evidence_rows", 0))))
        c4.metric("Snapshot Age (min)", f"{float(sql_health.get('snapshot_age_minutes', -1.0)):.1f}")
        st.progress(_clamp01(float(sql_health.get("db_mb", 0.0)) / 1024.0), text="SQL Design Bar • Storage")
        st.progress(_clamp01(float(sql_health.get("wal_mb", 0.0)) / 256.0), text="SQL Design Bar • Write Flow")
        st.progress(_clamp01(float(evidence.get("score", 0.0))), text="SQL Design Bar • Pattern Confidence")
        st.markdown("#### Center Data Shape Studio")
        shape = st.selectbox("Shape style", ["Monado Ring", "Hex Grid", "Pulse Sphere"], key="ctl_center_shape_style")
        shape_intensity = st.slider("Shape intensity", min_value=0.10, max_value=1.00, value=0.68, step=0.01, key="ctl_center_shape_intensity")
        shape_glow = int(10 + (shape_intensity * 26))
        shape_symbol = "(O)" if shape == "Monado Ring" else ("[#]" if shape == "Hex Grid" else "(*)")
        st.markdown(
            f"<div style='text-align:center; font-size:2.2rem; color:rgba(182,233,255,0.9); text-shadow:0 0 {shape_glow}px rgba(117,228,255,0.75);'>{shape_symbol} {shape_symbol} {shape_symbol}</div>",
            unsafe_allow_html=True,
        )
        st.progress(_clamp01(shape_intensity * 0.92), text=f"{shape} energy")

        report_scope = st.selectbox("Instant report scope", ["overview", "sql-health", "evidence", "github-context", "aihub"])
        report_payload = {
            "scope": report_scope,
            "timestamp": time.time(),
            "sql_health": sql_health,
            "evidence": evidence,
            "github": sql_intel.get("latest_github", {}),
            "growth": growth_data,
            "training": training_status,
            "aihub": unified,
        }
        st.code(json.dumps(report_payload, indent=2)[:4000], language="json")
        st.download_button("Download Instant Report", data=json.dumps(report_payload, indent=2), file_name=f"hermes_{report_scope}_report.json", mime="application/json", use_container_width=True)
        st.markdown("#### Easy Setup + Deploy")
        s1, s2, s3 = st.columns(3)
        with s1:
            if st.button("One-Click SQL + Training Setup", use_container_width=True):
                run_logged_post_action(
                    label="one-click-sql-training-setup",
                    path="/learning-pulse",
                    payload={
                        "specialty": "fleet:sql-training-easy-setup",
                        "steps": 460,
                        "candidates": 260,
                        "both_sides_training": both_sides_training,
                        "x5_brain_pack": x5_brain_pack,
                        "x6_learning_pack": x6_learning_pack,
                        "smart_tools": smart_tools,
                        "sql_signal": 0.97,
                        "internet_signal": 0.05,
                        "llm_signal": 0.94,
                        "stability_bias": 0.90,
                    },
                    success_message="SQL + training setup deployed.",
                    error_prefix="SQL + training setup failed",
                    timeout=150,
                )
        with s2:
            if st.button("Ultimate Hermes + AIHub Upgrade", use_container_width=True):
                run_logged_post_action(
                    label="ultimate-hermes-aihub-upgrade",
                    path="/aihub-max-upgrade",
                    payload={
                        "specialty": "fleet:ultimate-hermes-aihub",
                        "steps": 980,
                        "candidates": 420,
                        "both_sides_training": both_sides_training,
                        "x5_brain_pack": x5_brain_pack,
                        "x6_learning_pack": x6_learning_pack,
                        "smart_tools": smart_tools,
                        "sql_signal": 0.98,
                        "internet_signal": 0.08,
                        "llm_signal": 0.97,
                        "stability_bias": 0.92,
                    },
                    success_message="Ultimate Hermes + AIHub upgrade triggered.",
                    error_prefix="Ultimate Hermes + AIHub upgrade failed",
                    timeout=200,
                )
        with s3:
            if st.button("Ultimate ML X5 Brain Setup", use_container_width=True):
                run_logged_post_action(
                    label="ultimate-ml-x5-brain-setup",
                    path="/learning-pulse",
                    payload={
                        "specialty": "fleet:ultimate-ml-x5-brain",
                        "steps": 1400,
                        "candidates": 900,
                        "both_sides_training": both_sides_training,
                        "x5_brain_pack": True,
                        "x6_learning_pack": x6_learning_pack,
                        "smart_tools": smart_tools,
                        "sql_signal": 0.99,
                        "internet_signal": 0.08,
                        "llm_signal": 0.98,
                        "stability_bias": 0.93,
                    },
                    success_message="Ultimate ML X5 brain setup triggered.",
                    error_prefix="Ultimate ML X5 setup failed",
                    timeout=220,
                )
        st.caption("Use One-Click setup first, then run Ultimate upgrade, then Ultimate ML X5 for max complexity and brain depth.")
        st.dataframe(
            [
                {"Layer": "Ultimate X5 brain", "Status": "ON" if x5_brain_pack else "Standby", "Why": "Deep horizon training and stronger retention"},
                {"Layer": "X6 learning plus", "Status": "ON" if x6_learning_pack else "Off", "Why": "Extends learning pressure over longer cycles"},
                {"Layer": "C++ path", "Status": "Ready" if bool(cpp_kernel.get("available", False)) else "Fallback", "Why": "Higher compile/runtime efficiency for intensive workloads"},
                {"Layer": "Smart tools", "Status": f"{len(smart_tools)} enabled", "Why": "Operational automation + split routing quality"},
                {"Layer": "Both-sides training", "Status": "ON" if both_sides_training else "Off", "Why": "Combines defensive and offensive learning signals"},
            ],
            use_container_width=True,
            hide_index=True,
        )
        if st.button("Save Hermes Snapshot Now", use_container_width=True):
            info = export_hermes_profiles_snapshot(volume_root, max_rows=600)
            st.success(f"Hermes snapshot saved: {info.get('path', 'unknown')} ({info.get('rows', 0)} rows)")

    with tabs[1]:
        st.caption("AIBox calculator for AIHub planning and power/cost balance.")
        token_batch = st.slider("Token batch", min_value=500, max_value=200000, value=18000, step=500)
        model_speed = st.slider("Model speed (tokens/sec)", min_value=10, max_value=600, value=130, step=5)
        cost_per_1k = st.slider("Cost per 1k tokens (USD)", min_value=0.0001, max_value=0.0500, value=0.0045, step=0.0001, format="%.4f")
        quality = st.slider("Quality factor", min_value=0.10, max_value=1.00, value=0.82, step=0.01)
        calc_seconds = token_batch / max(1, model_speed)
        calc_cost = (token_batch / 1000.0) * cost_per_1k
        aibox = (quality * 0.55) + ((1.0 - _clamp01(calc_cost / 2.0)) * 0.20) + ((1.0 - _clamp01(calc_seconds / 300.0)) * 0.25)
        p1, p2, p3 = st.columns(3)
        p1.metric("ETA seconds", f"{calc_seconds:.1f}")
        p2.metric("Estimated cost", f"${calc_cost:.4f}")
        p3.metric("AIBox score", f"{_clamp01(aibox) * 100:.1f}%")
        growth = float(growth_data.get("growth_index", 0.0)) if isinstance(growth_data, dict) else 0.0
        maturity = float(growth_data.get("maturity_index", 0.0)) if isinstance(growth_data, dict) else 0.0
        teamwork = _clamp01((growth * 0.40) + (maturity * 0.35) + (float(training_status.get("active_agents", 0.0)) / max(1.0, float(training_status.get("agent_count", 1.0))) * 0.25))
        growth_gain = _clamp01((_clamp01(aibox) * 0.44) + (teamwork * 0.38) + (float(evidence.get("score", 0.0)) * 0.18))
        g1, g2, g3 = st.columns(3)
        g1.metric("Teamwork multiplier", f"x{1.0 + (teamwork * 0.45):.3f}")
        g2.metric("Projected growth gain", f"+{growth_gain * 100:.1f}%")
        g3.metric("Collab readiness", f"{teamwork * 100:.1f}%")
        st.markdown("#### AIHub Idea Engine")
        st.dataframe(
            [
                {"Idea": "C++ Turbo Loop", "Use when": "heavy compile + optimization", "Expected gain": "higher throughput + lower decision lag"},
                {"Idea": "Visual Harmony Loop", "Use when": "UI/UX polish and readability", "Expected gain": "cleaner UX + faster iteration"},
                {"Idea": "Security Fortress Loop", "Use when": "hardening and trust controls", "Expected gain": "safer autonomous actions"},
            ],
            use_container_width=True,
            hide_index=True,
        )
        st.markdown("#### Multi-LLM Blend Guide")
        st.dataframe(
            [
                {"Lane": "Reasoning LLM", "Primary role": "deep planning and C++ logic", "Best for": "intensive coding + architecture"},
                {"Lane": "UI/UX LLM", "Primary role": "layout readability and interaction polishing", "Best for": "clear dashboard flows"},
                {"Lane": "Security LLM", "Primary role": "guardrails and anomaly checks", "Best for": "safe autonomous behavior"},
            ],
            use_container_width=True,
            hide_index=True,
        )
        st.caption("Blend rule: route complex logic to Reasoning, visual clarity to UI/UX, and risk decisions to Security lane.")
        if st.button("Run AIHub Next-Level Upgrade", use_container_width=True):
            run_logged_post_action(
                label="aihub-next-level-upgrade",
                path="/aihub-max-upgrade",
                payload={
                    "specialty": "fleet:next-level-aihub",
                    "steps": int(720 + (_clamp01(aibox) * 240)),
                    "candidates": int(280 + (_clamp01(aibox) * 120)),
                    "both_sides_training": both_sides_training,
                    "x5_brain_pack": x5_brain_pack,
                    "x6_learning_pack": x6_learning_pack,
                    "smart_tools": smart_tools,
                    "sql_signal": min(0.99, 0.86 + (_clamp01(aibox) * 0.10)),
                    "internet_signal": 0.08,
                    "llm_signal": min(0.99, 0.90 + (_clamp01(aibox) * 0.08)),
                    "stability_bias": min(0.97, 0.82 + (_clamp01(aibox) * 0.10)),
                },
                success_message="Next-level AIHub upgrade triggered.",
                error_prefix="AIHub next-level upgrade failed",
                timeout=180,
            )

    with tabs[2]:
        st.markdown("#### Hermes Army Settings")
        if show_center_nexus:
            _render_center_nexus(
                sql_health=sql_health,
                growth_data=growth_data,
                training_status=training_status,
                unified=unified,
                cpp_kernel=cpp_kernel,
            )
        profiles = sql_intel.get("recent_hermes_profiles", []) if isinstance(sql_intel, dict) else []
        if not isinstance(profiles, list):
            profiles = []
        map_rows: List[Dict[str, Any]] = []
        for i, item in enumerate([p for p in profiles if isinstance(p, dict)][:40]):
            map_rows.append(
                {
                    "bot": item.get("hermes_id", f"hermes-{i+1}"),
                    "specialty": item.get("specialty", "fleet"),
                    "area": _role_area_for_specialty(str(item.get("specialty", "fleet"))),
                    "level": int(float(item.get("level", 1.0))),
                    "xp": int(float(item.get("experience_xp", 0.0))),
                    "size_mode": item.get("size_mode", "mid"),
                    "thinking": "Pattern synthesis + role optimization" if "sql" in str(item.get("specialty", "")).lower() else "Task execution + adaptive planning",
                    "good_at": "Data reasoning" if "sql" in str(item.get("specialty", "")).lower() else ("Security hardening" if "security" in str(item.get("specialty", "")).lower() else "Fleet coordination"),
                }
            )
        map_rows = _sort_map_rows(map_rows)
        if map_rows:
            st.dataframe(map_rows, use_container_width=True, hide_index=True)
        else:
            st.info("No Hermes profile map data yet. Run training and SQL snapshots for instant map population.")
        github_ctx = sql_intel.get("latest_github", {}) if isinstance(sql_intel, dict) else {}
        if isinstance(github_ctx, dict):
            st.markdown("#### GitHub CLI/Data Snapshot")
            st.json(github_ctx, expanded=False)
        st.markdown("#### Entrance + Army Nexus")
        entrance = ultimate_entrance if isinstance(ultimate_entrance, dict) else {}
        b1, b2, b3, b4 = st.columns(4)
        b1.metric("Entrance Integration", f"{float(entrance.get('integration_score', 0.0)) * 100:.1f}%")
        b2.metric("Gateway Reliability", f"{float(entrance.get('reliability', 0.0)) * 100:.1f}%")
        b3.metric("Gateway Responsiveness", f"{float(entrance.get('responsiveness', 0.0)) * 100:.1f}%")
        b4.metric("Route Diversity", f"{float(entrance.get('route_diversity', 0.0)) * 100:.1f}%")
        volume_ok = os.path.isdir(volume_root)
        file_count = 0
        if volume_ok:
            try:
                file_count = sum(len(files) for _, _, files in os.walk(volume_root))
            except OSError:
                file_count = 0
        st.caption(f"Volume setup: {'ready' if volume_ok else 'missing'} | root={volume_root} | files={file_count}")

    with tabs[3]:
        st.markdown("#### Evidence Advisor + Pattern Guide")
        evidence_score = float(evidence.get("score", 0.0))
        evidence_rows = int(evidence.get("rows", sql_health.get("total_evidence_rows", 0)))
        trend = float(sql_intel.get("trend", 0.0)) if isinstance(sql_intel, dict) else 0.0
        watch_eff = float(sql_intel.get("variable_means", {}).get("watch_efficiency", 0.5)) if isinstance(sql_intel, dict) else 0.5
        e1, e2, e3, e4 = st.columns(4)
        e1.metric("Evidence confidence", f"{evidence_score * 100:.1f}%")
        e2.metric("Evidence rows", str(evidence_rows))
        e3.metric("Pattern trend", f"{trend:+.4f}")
        e4.metric("Watch efficiency", f"{watch_eff * 100:.1f}%")
        guide_rows = [
            {"Pattern": "Growth Lane", "Condition": "trend >= 0.03 and evidence >= 0.60", "Guide": "Push AIHub max-upgrade and increase steps."},
            {"Pattern": "Stability Lane", "Condition": "watch_eff >= 0.58 and trend around 0", "Guide": "Keep balanced blend; focus on consistency."},
            {"Pattern": "Recovery Lane", "Condition": "trend < 0 or evidence < 0.45", "Guide": "Run evidence-heavy learning pulse + SQL optimize."},
        ]
        st.dataframe(guide_rows, use_container_width=True, hide_index=True)
        advice: List[str] = []
        if trend < 0:
            advice.append("Trend is negative: increase stability_bias and run optimizer first.")
        if evidence_score < 0.50:
            advice.append("Evidence confidence is low: prioritize SQL/evidence ingestion before aggressive upgrades.")
        if watch_eff < 0.55:
            advice.append("Watch efficiency is low: tune monitor coverage and reduce noisy candidate bursts.")
        if not advice:
            advice.append("Signals look healthy: run full AIHub next-level plan with higher candidates.")
        st.markdown("**Advice for you**")
        for line in advice:
            st.markdown(f"- {line}")

    with tabs[4]:
        st.markdown("#### Security Area")
        s1, s2, s3 = st.columns(3)
        block_remote = s1.toggle("Block remote control", value=True)
        disable_hidden_hv = s2.toggle("Disable hidden Hyper-V paths", value=True)
        lock_remote_cli = s3.toggle("Lock remote CLI execution", value=True)
        shield = 0.0
        shield += 0.34 if block_remote else 0.0
        shield += 0.33 if disable_hidden_hv else 0.0
        shield += 0.33 if lock_remote_cli else 0.0
        st.progress(_clamp01(shield), text=f"Security shield score: {_clamp01(shield) * 100:.1f}%")
        st.caption("This panel enforces dashboard policy guidance and hardening checks for safe operation.")
        st.markdown("#### Web Security Profile")
        w1, w2, w3, w4 = st.columns(4)
        strict_headers = w1.toggle("Strict security headers", value=True, key="ctl_web_strict_headers")
        csrf_guard = w2.toggle("CSRF guard policy", value=True, key="ctl_web_csrf_guard")
        secure_cookie = w3.toggle("Secure cookie mode", value=True, key="ctl_web_secure_cookie")
        rate_guard = w4.toggle("Rate-limit guard", value=True, key="ctl_web_rate_guard")
        web_security_score = (
            (0.26 if strict_headers else 0.0)
            + (0.24 if csrf_guard else 0.0)
            + (0.24 if secure_cookie else 0.0)
            + (0.26 if rate_guard else 0.0)
        )
        st.progress(_clamp01(web_security_score), text=f"Web security profile: {_clamp01(web_security_score) * 100:.1f}%")
        if st.button("Apply Web Security Shield", use_container_width=True):
            run_logged_post_action(
                label="web-security-shield",
                path="/ingest-signal",
                payload={
                    "source": "gui_web_security_profile",
                    "signal_score": _clamp01(0.52 + (web_security_score * 0.48)),
                    "payload": {
                        "strict_headers": strict_headers,
                        "csrf_guard": csrf_guard,
                        "secure_cookie": secure_cookie,
                        "rate_guard": rate_guard,
                        "both_sides_training": both_sides_training,
                        "smart_tools": smart_tools,
                    },
                },
                success_message="Web security profile applied.",
                error_prefix="Web security profile failed",
                timeout=60,
            )

        st.markdown("#### Optimization Profile")
        o1, o2, o3 = st.columns(3)
        web_cache = o1.slider("Web cache level", min_value=0.0, max_value=1.0, value=0.74, step=0.01, key="ctl_web_cache_level")
        render_parallel = o2.slider("Parallel rendering", min_value=0.0, max_value=1.0, value=0.78, step=0.01, key="ctl_render_parallel")
        query_opt = o3.slider("SQL query optimization", min_value=0.0, max_value=1.0, value=0.82, step=0.01, key="ctl_query_opt_level")
        opt_score = _clamp01((web_cache * 0.34) + (render_parallel * 0.33) + (query_opt * 0.33))
        st.progress(opt_score, text=f"Optimization profile: {opt_score * 100:.1f}%")
        if st.button("Apply Web + Fleet Optimization", use_container_width=True):
            run_logged_post_action(
                label="web-fleet-optimization",
                path="/optimize-fleet",
                payload={
                    "specialty": "fleet:web-optimization",
                    "candidates": int(240 + (opt_score * 260)),
                    "web_cache_level": web_cache,
                    "render_parallel": render_parallel,
                    "query_opt_level": query_opt,
                    "x6_learning_pack": x6_learning_pack,
                    "smart_tools": smart_tools,
                },
                success_message="Web + fleet optimization triggered.",
                error_prefix="Web + fleet optimization failed",
                timeout=90,
            )
        st.markdown("#### Runtime Lockdown + Max Power")
        p1, p2, p3 = st.columns(3)
        cpu_target = p1.slider("CPU target utilization", min_value=0.50, max_value=1.00, value=1.00, step=0.01, key="ctl_cpu_target_util")
        memory_target = p2.slider("Memory target utilization", min_value=0.50, max_value=1.00, value=0.96, step=0.01, key="ctl_memory_target_util")
        gpu_target = p3.slider("GPU target utilization", min_value=0.50, max_value=1.00, value=1.00, step=0.01, key="ctl_gpu_target_util")
        st.caption("Use Lockdown first to shut remote/hidden paths, then Max Power to push CPU/RAM/GPU profile.")
        if st.button("Apply Remote/Hidden Machine Lockdown", use_container_width=True):
            run_logged_post_action(
                label="runtime-lockdown-hard",
                path="/runtime-orchestrate/lock-mode",
                payload={
                    "specialty": "fleet:lockdown-hard",
                    "mode": "lockdown-hard",
                    "block_remote": bool(block_remote),
                    "disable_hidden_hyperv": bool(disable_hidden_hv),
                    "lock_remote_cli": bool(lock_remote_cli),
                    "strict_headers": bool(strict_headers),
                    "csrf_guard": bool(csrf_guard),
                    "secure_cookie": bool(secure_cookie),
                    "rate_guard": bool(rate_guard),
                },
                success_message="Remote/hidden-machine lockdown applied.",
                error_prefix="Lockdown apply failed",
                timeout=90,
            )
        if st.button("Apply Max Power CPU/RAM/GPU", use_container_width=True):
            run_logged_post_action(
                label="runtime-max-power-profile",
                path="/runtime-orchestrate/deploy",
                payload={
                    "specialty": "fleet:max-power",
                    "mode": "deploy-max-power",
                    "cpu_target_utilization": cpu_target,
                    "memory_target_utilization": memory_target,
                    "gpu_target_utilization": gpu_target,
                    "x5_brain_pack": x5_brain_pack,
                    "x6_learning_pack": x6_learning_pack,
                    "smart_tools": smart_tools,
                },
                success_message="Max power profile applied.",
                error_prefix="Max power profile failed",
                timeout=90,
            )

        st.markdown("#### Benchmark")
        if st.button("Run Benchmark", use_container_width=True):
            growth = float(growth_data.get("growth_index", 0.0)) if isinstance(growth_data, dict) else 0.0
            integration = float(growth_data.get("integration_index", 0.0)) if isinstance(growth_data, dict) else 0.0
            evidence_score = float(evidence.get("score", 0.0))
            sql_pressure = _clamp01((float(sql_health.get("db_mb", 0.0)) / 1024.0) + (float(sql_health.get("wal_mb", 0.0)) / 256.0))
            cpp_boost = 0.12 if bool(cpp_kernel.get("available", False)) else 0.0
            bench_score = _clamp01((growth * 0.30) + (integration * 0.24) + (evidence_score * 0.22) + ((1.0 - sql_pressure) * 0.14) + (0.10 + cpp_boost))
            st.success(f"Benchmark score: {bench_score * 100:.1f}%")
            st.caption("Higher score means stronger quality+stability with lower SQL pressure.")

        st.markdown("#### Power Growth Recommendations")
        recs = [
            "Use C++ kernel acceleration for heavy loops and leave Python for orchestration/UI.",
            "Increase model speed tiers before increasing raw token volume to keep quality-per-watt high.",
            "Use evidence+SQL pressure loops to optimize retention without reducing decision power.",
        ]
        for r in recs:
            st.markdown(f"- {r}")

    with tabs[5]:
        now_struct = time.localtime()
        hhmmss = time.strftime("%H:%M:%S", now_struct)
        st.markdown('<div class="clock-wrap"><h2 class="clock-glow" style="margin:0;">⏱️ ' + hhmmss + "</h2></div>", unsafe_allow_html=True)
        st.caption("Animated Level 5 clock pulse tracks live training watch mode.")

    st.markdown("---")
    st.markdown("### AIHub Scroll Zone (standalone)")
    st.caption("Independent AIHub section below the tabs for scrolling workflow.")
    ah1, ah2, ah3 = st.columns(3)
    aihub_depth = ah1.slider("Top-level mind depth", min_value=0.10, max_value=1.00, value=0.86, step=0.01, key="ctl_aihub_scroll_depth")
    aihub_speed = ah2.slider("AIHub response speed", min_value=0.10, max_value=1.00, value=0.74, step=0.01, key="ctl_aihub_scroll_speed")
    aihub_safe = ah3.slider("AIHub safety bias", min_value=0.10, max_value=1.00, value=0.90, step=0.01, key="ctl_aihub_scroll_safety")
    top_mind = st.selectbox("Top-level mind selector", ["Optimal Balanced Mind", "C++ Performance Mind", "Security Fortress Mind", "Learning Hyper Mind"], key="ctl_top_mind_selector")
    st.dataframe(
        [
            {"Suggestion": "For C++ + throughput projects", "Best mind": "C++ Performance Mind", "Why": "Higher speed + compile loop efficiency"},
            {"Suggestion": "For stable production", "Best mind": "Security Fortress Mind", "Why": "Stronger guardrails + safer actions"},
            {"Suggestion": "For long training cycles", "Best mind": "Learning Hyper Mind", "Why": "Deeper retention + adaptation quality"},
            {"Suggestion": "For mixed workloads", "Best mind": "Optimal Balanced Mind", "Why": "Best all-around blend"},
        ],
        use_container_width=True,
        hide_index=True,
    )
    if st.button("Apply Top-Level Mind Optimally", use_container_width=True):
        run_logged_post_action(
            label="top-level-mind-apply",
            path="/ingest-signal",
            payload={
                "source": "gui_top_level_mind",
                "signal_score": _clamp01((aihub_depth * 0.42) + (aihub_speed * 0.24) + (aihub_safe * 0.34)),
                "payload": {
                    "top_mind": top_mind,
                    "aihub_depth": aihub_depth,
                    "aihub_speed": aihub_speed,
                    "aihub_safety": aihub_safe,
                    "x5_brain_pack": x5_brain_pack,
                    "x6_learning_pack": x6_learning_pack,
                    "smart_tools": smart_tools,
                },
            },
            success_message="Top-level mind profile applied.",
            error_prefix="Top-level mind apply failed",
            timeout=60,
        )
    if st.button("Run AIHub Scroll Upgrade", use_container_width=True):
        run_logged_post_action(
            label="aihub-scroll-upgrade",
            path="/aihub-max-upgrade",
            payload={
                "specialty": "fleet:aihub-scroll-zone",
                "steps": int(740 + (aihub_depth * 260)),
                "candidates": int(280 + (aihub_speed * 200)),
                "stability_bias": min(0.99, 0.80 + (aihub_safe * 0.16)),
                "x5_brain_pack": x5_brain_pack,
                "x6_learning_pack": x6_learning_pack,
            },
            success_message="AIHub scroll-zone upgrade started.",
            error_prefix="AIHub scroll-zone upgrade failed",
            timeout=180,
        )
