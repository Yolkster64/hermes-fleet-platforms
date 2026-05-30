from typing import Any, Callable, Dict

import streamlit as st


def render_sql_intelligence_panels(
    sql_intel: Dict[str, Any],
    render_xp_bar: Callable[[str, float, str], None],
    run_logged_post_action: Callable[..., Any],
    high_level_learning: float,
) -> None:
    st.caption(
        f"SQL training rows: {int(sql_intel.get('rows', 0))} | "
        f"trend: {float(sql_intel.get('trend', 0.0)):+.4f} | "
        f"signal avg: {float(sql_intel.get('signal_avg', 0.0)):.4f}"
    )
    art_pattern = sql_intel.get("art_pattern", {}) if isinstance(sql_intel, dict) else {}
    if isinstance(art_pattern, dict) and art_pattern:
        ap1, ap2, ap3, ap4, ap5 = st.columns(5)
        ap1.metric("Art Symmetry", f"{float(art_pattern.get('symmetry_index', 0.0)) * 100:.1f}%")
        ap2.metric("Art Contrast", f"{float(art_pattern.get('contrast_index', 0.0)) * 100:.1f}%")
        ap3.metric("Art Fractal Flow", f"{float(art_pattern.get('fractal_flow', 0.0)) * 100:.1f}%")
        ap4.metric("Compression", f"{float(art_pattern.get('compression_ratio', 0.0)) * 100:.1f}%")
        ap5.metric("3D Overlap", f"{float(art_pattern.get('overlap_3d', 0.0)) * 100:.1f}%")
    latest_github = sql_intel.get("latest_github", {}) if isinstance(sql_intel, dict) else {}
    if isinstance(latest_github, dict) and latest_github:
        st.caption(
            f"GitHub->Volume context: {latest_github.get('branch', 'unknown')} "
            f"{latest_github.get('commit_sha', '')} "
            f"({latest_github.get('changed_files', 0)} changed files)"
        )
        with st.expander("GitHub CLI connection"):
            st.code(
                "gh repo view --json name,defaultBranchRef\n"
                "gh pr status\n"
                "gh run list --limit 5"
            )
            st.caption("This feed trains volume SQL context and cross-links Hermes learning with repository reality.")
    super_training = sql_intel.get("super_training", {}) if isinstance(sql_intel, dict) else {}
    if isinstance(super_training, dict) and super_training:
        sp1, sp2, sp3 = st.columns(3)
        sp1.metric("SQL Super Score", f"{float(super_training.get('score', 0.0)) * 100:.1f}%")
        sp2.metric("SQL Health", f"{float(super_training.get('health_score', 0.0)) * 100:.1f}%")
        sp3.metric("Storage Pressure", f"{float(super_training.get('storage_pressure', 0.0)) * 100:.1f}%")
        auto_setup = super_training.get("auto_setup", {})
        if isinstance(auto_setup, dict):
            st.caption(
                f"Auto setup: manifest={'ready' if bool(auto_setup.get('volume_manifest_ready', False)) else 'missing'} | "
                f"checkpoints={'ready' if bool(auto_setup.get('training_checkpoints_ready', False)) else 'missing'}"
            )
        guidance = super_training.get("guidance", [])
        if isinstance(guidance, list) and guidance:
            for note in guidance[:4]:
                st.info(str(note))
    strategy_leaderboard = sql_intel.get("strategy_leaderboard", []) if isinstance(sql_intel, dict) else []
    if isinstance(strategy_leaderboard, list) and strategy_leaderboard:
        st.caption("SQL strategy leaderboard")
        st.dataframe(
            [
                {
                    "strategy": str(row.get("strategy", "")),
                    "blend_score": round(float(row.get("blend_score", 0.0)) * 100.0, 1),
                    "count": int(row.get("count", 0)),
                    "evidence": round(float(row.get("avg_evidence", 0.0)), 4),
                    "reward": round(float(row.get("avg_reward", 0.0)), 4),
                    "truth": round(float(row.get("avg_truth", 0.0)), 4),
                    "shape": round(float(row.get("avg_shape", 0.0)), 4),
                }
                for row in strategy_leaderboard[:8]
                if isinstance(row, dict)
            ],
            use_container_width=True,
            hide_index=True,
        )
    variable_means = sql_intel.get("variable_means", {}) if isinstance(sql_intel, dict) else {}
    if isinstance(variable_means, dict) and variable_means:
        top_vars = sorted(variable_means.items(), key=lambda item: abs(float(item[1]) - 0.5), reverse=True)[:10]
        st.caption("Top SQL pattern variables")
        st.dataframe(
            [{"variable": k, "mean_value": float(v)} for k, v in top_vars],
            use_container_width=True,
            hide_index=True,
        )
    benefits = sql_intel.get("benefits", []) if isinstance(sql_intel, dict) else []
    if isinstance(benefits, list) and benefits:
        st.caption("Automatic SQL benefits")
        for b in benefits[:5]:
            st.success(str(b))
    ideas = sql_intel.get("ideas", []) if isinstance(sql_intel, dict) else []
    if isinstance(ideas, list) and ideas:
        st.caption("Suggested next moves")
        for tip in ideas[:4]:
            st.info(str(tip))
    recent_profiles = sql_intel.get("recent_hermes_profiles", []) if isinstance(sql_intel, dict) else []
    if isinstance(recent_profiles, list) and recent_profiles:
        st.caption("Latest per-Hermes saved variable profiles")
        st.dataframe(
            [
                {
                    "hermes_id": row.get("hermes_id", ""),
                    "specialty": row.get("specialty", ""),
                    "signal_score": round(float(row.get("signal_score", 0.0)), 4),
                    "art_pattern_score": round(float(row.get("art_pattern_score", 0.0)), 4),
                    "level": int(row.get("level", 1)),
                    "xp": int(float(row.get("experience_xp", 0.0))),
                    "size": row.get("size_mode", "mid"),
                    "speed_bonus": round(float(row.get("speed_bonus", 0.0)) * 100.0, 1),
                    "token_power_gain": round(float(row.get("token_power_gain", 0.0)) * 100.0, 1),
                    "tools": ", ".join(row.get("tools", [])) if isinstance(row.get("tools", []), list) else "",
                    "specialties": ", ".join(row.get("specialties", [])) if isinstance(row.get("specialties", []), list) else "",
                }
                for row in recent_profiles[:12]
                if isinstance(row, dict)
            ],
            use_container_width=True,
            hide_index=True,
        )
        st.caption("Hermes XP and bonus bars")
        for row in [r for r in recent_profiles[:6] if isinstance(r, dict)]:
            hid = str(row.get("hermes_id", "hermes"))
            xp_ratio = min(1.0, float(row.get("experience_xp", 0.0)) / 10000.0)
            level_ratio = min(1.0, float(row.get("level", 1.0)) / 120.0)
            speed_ratio = min(1.0, max(0.0, float(row.get("speed_bonus", 0.0))))
            token_ratio = min(1.0, max(0.0, float(row.get("token_power_gain", 0.0))))
            synergy_ratio = min(1.0, (xp_ratio * 0.35) + (level_ratio * 0.35) + (speed_ratio * 0.15) + (token_ratio * 0.15))
            render_xp_bar(f"{hid} XP", xp_ratio, "#52BE80")
            render_xp_bar(f"{hid} Level", level_ratio, "#6FA8FF")
            render_xp_bar(f"{hid} Speed", speed_ratio, "#5DADE2")
            render_xp_bar(f"{hid} Token", token_ratio, "#AF7AC5")
            render_xp_bar(f"{hid} Synergy", synergy_ratio, "#F4D03F")

    lf1, lf2 = st.columns([1, 1])
    st.caption("Deployment controls")
    d1, d2 = st.columns(2)
    with d1:
        if st.button("Deploy SQL Center Upgrade", use_container_width=True):
            run_logged_post_action(
                "deploy-sql-center-upgrade",
                "/learning-pulse",
                {
                    "specialty": "fleet:sql-center-upgrade",
                    "steps": 420,
                    "candidates": 220,
                    "sql_signal": 0.96,
                    "internet_signal": 0.06,
                    "llm_signal": 0.93,
                    "stability_bias": 0.89,
                },
                "SQL center deployment triggered.",
                "SQL center deployment failed",
                timeout=120,
            )
    with d2:
        if st.button("Deploy Hub + Map Sync", use_container_width=True):
            run_logged_post_action(
                "deploy-hub-map-sync",
                "/optimize-fleet",
                {"specialty": "fleet:hub-map-sync", "candidates": 260},
                "Hub + map sync deployment triggered.",
                "Hub + map deployment failed",
                timeout=120,
            )
    with lf1:
        if st.button("Lock Fleet Tough Mode", use_container_width=True):
            run_logged_post_action(
                "fleet-lock-mode",
                "/ingest-signal",
                {
                    "source": "gui_fleet_lock_mode",
                    "signal_score": 0.92,
                    "payload": {
                        "lock_mode": True,
                        "policy": "tough-other-side",
                        "goal": "stability-and-hard-problem-focus",
                        "high_level_learning": high_level_learning,
                    },
                },
                "Fleet lock mode sent.",
                "Failed to lock fleet mode",
                timeout=60,
            )
    with lf2:
        if st.button("Unlock Fleet Mode", use_container_width=True):
            run_logged_post_action(
                "fleet-unlock-mode",
                "/ingest-signal",
                {
                    "source": "gui_fleet_lock_mode",
                    "signal_score": 0.65,
                    "payload": {"lock_mode": False, "policy": "balanced-adaptive"},
                },
                "Fleet lock released.",
                "Failed to unlock fleet mode",
                timeout=60,
            )
