import html
from typing import Any, Dict, List

import streamlit as st


def _tiny_avatar(index: int, size_mode: str) -> str:
    avatars = ["🤖", "🛰️", "🧠", "⚙️", "🚀", "🔬", "🛡️", "📡", "🧩", "🎯"]
    if size_mode == "mini":
        return "⚡"
    if size_mode == "full":
        return "🛡️"
    return avatars[index % len(avatars)]


def _design_pack(size_mode: str, specialty: str) -> str:
    s = specialty.lower()
    if size_mode == "mini":
        return "Neon Scout • ultra-light shell"
    if size_mode == "full":
        return "Titan Core • reinforced reasoning"
    if "security" in s:
        return "Aegis Shade • hardened defensive shell"
    if "gui" in s or "ux" in s:
        return "Prism Shade • creative visual shell"
    if "sql" in s or "data" in s:
        return "Obsidian Shade • data-signal shell"
    if "training" in s or "learning" in s:
        return "Aurora Shade • memory-growth shell"
    return "Balanced Prism • adaptive shell"


def _shade_for_specialty(specialty: str) -> str:
    s = specialty.lower()
    if "security" in s:
        return "linear-gradient(145deg, rgba(32,25,46,0.92), rgba(15,18,35,0.92))"
    if "gui" in s or "ux" in s:
        return "linear-gradient(145deg, rgba(18,38,62,0.92), rgba(20,26,40,0.92))"
    if "sql" in s or "data" in s:
        return "linear-gradient(145deg, rgba(19,42,46,0.92), rgba(16,22,34,0.92))"
    if "training" in s or "learning" in s:
        return "linear-gradient(145deg, rgba(42,33,56,0.92), rgba(16,20,33,0.92))"
    return "linear-gradient(145deg, rgba(18,22,34,0.90), rgba(16,18,28,0.90))"


def _role_for_specialty(specialty: str) -> str:
    name = specialty.lower()
    if "security" in name or "hardening" in name:
        return "Guardian"
    if "gui" in name or "ux" in name:
        return "Designer"
    if "data" in name or "sql" in name:
        return "Data Pilot"
    if "orchestration" in name or "fleet" in name:
        return "Coordinator"
    return "Builder"


def _accessories_for_role(role: str) -> str:
    mapping = {
        "Guardian": "Aegis visor • shield mesh • audit pin",
        "Designer": "Prism brush • UX lens • palette chip",
        "Data Pilot": "SQL lens • index ring • insight relay",
        "Coordinator": "Nexus pin • route compass • swarm relay",
        "Builder": "Forge grip • patch kit • deploy anchor",
    }
    return mapping.get(role, "Core badge • utility belt • comm node")


def _stable_bot_name(index: int, row: Dict[str, Any]) -> str:
    existing = str(row.get("hermes_id", "")).strip()
    if existing:
        return existing
    seeds = [
        "Hermes Nova",
        "Hermes Aegis",
        "Hermes Prism",
        "Hermes Oracle",
        "Hermes Atlas",
        "Hermes Chrono",
        "Hermes Pulse",
        "Hermes Vector",
        "Hermes Ether",
        "Hermes Zenith",
    ]
    return f"{seeds[index % len(seeds)]}-{index + 1:02d}"


def _sort_cards(cards: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    role_rank = {"Coordinator": 0, "Data Pilot": 1, "Designer": 2, "Guardian": 3, "Builder": 4}
    return sorted(
        cards,
        key=lambda row: (
            role_rank.get(_role_for_specialty(str(row.get("specialty", "fleet"))), 99),
            -float(row.get("level", 0.0)),
            -float(row.get("experience_xp", 0.0)),
            str(row.get("specialty", "")),
        ),
    )


def _profile_style_name(specialty: str, level: int) -> str:
    s = specialty.lower()
    if "security" in s:
        base = "Guardian"
    elif "data" in s or "sql" in s:
        base = "Data Pilot"
    elif "gui" in s or "ux" in s:
        base = "Designer"
    elif "training" in s or "learning" in s:
        base = "Trainer"
    elif "fleet" in s or "orchestration" in s:
        base = "Coordinator"
    else:
        base = "Builder"
    tier = "T1" if level < 20 else ("T2" if level < 45 else ("T3" if level < 80 else "T4"))
    return f"{base} {tier}"


def _tool_subset(row: Dict[str, Any], fallback_index: int) -> str:
    skills = row.get("skills", [])
    if isinstance(skills, list) and skills:
        return ", ".join(str(s) for s in skills[:3])
    presets = [
        "orchestrator, reasoner, router",
        "guardian, audit, hardening",
        "trainer, evidence, memory",
        "designer, ui, map",
    ]
    return presets[fallback_index % len(presets)]


def _thinking_for_row(row: Dict[str, Any]) -> str:
    specialty = str(row.get("specialty", "fleet")).lower()
    interaction = str(row.get("interaction", "hybrid")).lower()
    if "security" in specialty:
        return "Threat checks + policy guard"
    if "sql" in specialty or "data" in specialty:
        return "Pattern mining + SQL signal merge"
    if "gui" in specialty or "ux" in specialty:
        return "Visual clarity + interaction smoothness"
    if "training" in specialty or "learning" in specialty:
        return "Retention growth + adaptive memory"
    if interaction in ("mesh", "swarm"):
        return "Parallel coordination + fleet sync"
    return "Balanced optimization + task execution"


def _render_cosmic_scroll(cards: List[Dict[str, Any]]) -> None:
    rows: List[str] = []
    for i, row in enumerate(cards):
        size_mode = str(row.get("size_mode", "mid"))
        specialty = str(row.get("specialty", "fleet"))
        level = int(float(row.get("level", 1.0)))
        xp = int(float(row.get("experience_xp", 0.0)))
        avatar = _tiny_avatar(i, size_mode)
        role = _role_for_specialty(specialty)
        profile_name = _profile_style_name(specialty, level)
        tools = _tool_subset(row, i)
        speed = float(row.get("speed_bonus", 0.0)) * 100.0
        token = float(row.get("token_power_gain", 0.0)) * 100.0
        xp_pct = max(0.0, min(100.0, (xp / 10000.0) * 100.0))
        lvl_pct = max(0.0, min(100.0, (level / 120.0) * 100.0))
        bot_name = _stable_bot_name(i, row)
        accessory = _accessories_for_role(role)
        rows.append(
            (
                f"<div class='hf-card' style='background:{_shade_for_specialty(specialty)};'>"
                f"<div class='hf-head'><span class='hf-avatar'>{html.escape(avatar)}</span><span>{html.escape(bot_name)}</span></div>"
                f"<div class='hf-god'>{html.escape(profile_name)}</div>"
                f"<div class='hf-meta'>{html.escape(role)} • {html.escape(specialty)}</div>"
                f"<div class='hf-meta'>Tools: {html.escape(tools)}</div>"
                f"<div class='hf-bar'><span style='width:{xp_pct:.1f}%'></span></div><div class='hf-txt'>XP {xp}</div>"
                f"<div class='hf-bar'><span style='width:{lvl_pct:.1f}%'></span></div><div class='hf-txt'>Level {level}</div>"
                f"<div class='hf-meta'>Boosts: speed +{speed:.1f}% • token +{token:.1f}%</div>"
                f"<div class='hf-meta'>Accessories: {html.escape(accessory)}</div>"
                f"</div>"
            )
        )
    st.markdown(
        """
<style>
.hf-scroll {display:flex; gap:14px; overflow-x:auto; padding-bottom:10px;}
.hf-card {min-width:260px; max-width:260px; border:1px solid rgba(145,160,190,0.35); border-radius:12px; padding:12px; background:linear-gradient(145deg, rgba(18,22,34,0.90), rgba(16,18,28,0.90)); box-shadow:none;}
.hf-head {display:flex; align-items:center; gap:8px; font-weight:700; color:#e6f5ff; margin-bottom:2px;}
.hf-avatar {font-size:1rem;}
.hf-god {font-size:0.82rem; color:#b9d5ff; margin-bottom:2px;}
.hf-meta {font-size:0.76rem; color:#c9d8ee; margin-top:2px;}
.hf-bar {height:7px; border-radius:8px; background:rgba(255,255,255,0.12); margin-top:6px; overflow:hidden;}
.hf-bar span {display:block; height:100%; border-radius:8px; background:linear-gradient(90deg, #5ac7ff, #7f9bff);}
.hf-txt {font-size:0.72rem; color:#b8cff0;}
</style>
""",
        unsafe_allow_html=True,
    )
    st.markdown("<div class='hf-scroll'>" + "".join(rows) + "</div>", unsafe_allow_html=True)


def _progress_variant(label: str, value: float, tone: str) -> None:
    palette = {
        "xp": ("#45c0ff", "#79d2ff"),
        "level": ("#7a86ff", "#9d8fff"),
        "synergy": ("#44d3a2", "#7ce4bc"),
    }
    left, right = palette.get(tone, ("#45c0ff", "#79d2ff"))
    pct = max(0.0, min(1.0, value)) * 100.0
    st.markdown(
        (
            "<div style='margin-top:0.18rem;'>"
            f"<div style='display:flex;justify-content:space-between;font-size:0.76rem;color:#cfdef5;'><span>{html.escape(label)}</span><span>{pct:.1f}%</span></div>"
            "<div style='height:8px;background:rgba(255,255,255,0.12);border-radius:999px;overflow:hidden;'>"
            f"<div style='width:{pct:.1f}%;height:100%;background:linear-gradient(90deg,{left},{right});'></div>"
            "</div></div>"
        ),
        unsafe_allow_html=True,
    )


def _sub_agent_summary(cards: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    buckets = {
        "Coordinator Mesh": {"match": ("fleet", "orchestration"), "tips": "Keep routing weights balanced and reduce overloaded routes."},
        "SQL Intelligence": {"match": ("sql", "data"), "tips": "Improve SQL health first, then raise candidate counts."},
        "UX + Hub": {"match": ("gui", "ux"), "tips": "Deploy small UI iterations and monitor response stability."},
        "Security Guard": {"match": ("security", "hardening"), "tips": "Prioritize hardening toggles before aggressive upgrades."},
    }
    results: List[Dict[str, Any]] = []
    for name, cfg in buckets.items():
        picked = [
            c
            for c in cards
            if any(token in str(c.get("specialty", "")).lower() for token in cfg["match"])
        ]
        if not picked:
            continue
        avg_xp = sum(float(c.get("experience_xp", 0.0)) for c in picked) / max(1, len(picked))
        avg_lvl = sum(float(c.get("level", 1.0)) for c in picked) / max(1, len(picked))
        avg_speed = sum(float(c.get("speed_bonus", 0.0)) for c in picked) / max(1, len(picked))
        readiness = min(1.0, (avg_xp / 10000.0) * 0.45 + (avg_lvl / 120.0) * 0.35 + avg_speed * 0.20)
        results.append(
            {
                "name": name,
                "readiness": readiness,
                "members": len(picked),
                "tips": str(cfg["tips"]),
                "profile": "Tight sub-agent collaboration with guided optimization loops.",
            }
        )
    return results


def render_fleet_showcase_panels(
    sql_intel: Dict[str, Any],
    growth_data: Dict[str, Any],
    training_status: Dict[str, Any],
    cpp_kernel: Dict[str, Any],
) -> None:
    st.subheader("Hermes Fleet Overview")
    profiles = sql_intel.get("recent_hermes_profiles", []) if isinstance(sql_intel, dict) else []
    if not isinstance(profiles, list):
        profiles = []
    cards = _sort_cards([p for p in profiles if isinstance(p, dict)])[:16]

    growth = float(growth_data.get("growth_index", 0.0)) if isinstance(growth_data, dict) else 0.0
    maturity = float(growth_data.get("maturity_index", 0.0)) if isinstance(growth_data, dict) else 0.0
    integration = float(growth_data.get("integration_index", 0.0)) if isinstance(growth_data, dict) else 0.0
    active = bool(training_status.get("training_active", False)) if isinstance(training_status, dict) else False
    recent_events = int(training_status.get("recent_learning_events", 0)) if isinstance(training_status, dict) else 0
    cpp_ready = bool(cpp_kernel.get("cpp_ready", False)) if isinstance(cpp_kernel, dict) else False
    cpp_boost = 1.35 if cpp_ready else 1.0
    eta_hours = max(0.5, (8.0 * (1.0 - ((growth * 0.50) + (maturity * 0.30) + (integration * 0.20)))) / cpp_boost)

    a1, a2, a3, a4, a5 = st.columns(5)
    a1.metric("Fleet Stats", f"{len(cards)} bots")
    a2.metric("Estimated Upgrade ETA", f"{eta_hours:.1f}h")
    a3.metric("Learning Pulses", str(recent_events))
    a4.metric("C++ Speed Boost", "ON" if cpp_ready else "OFF")
    a5.metric("Training", "Active" if active else "Idle")

    st.progress(min(1.0, growth), text=f"Fleet growth {growth * 100:.1f}%")
    st.progress(min(1.0, maturity), text=f"Fleet maturity {maturity * 100:.1f}%")
    st.progress(min(1.0, integration), text=f"Fleet integration {integration * 100:.1f}%")

    st.markdown("#### Setup Guide (Who / What / Area)")
    guide = {
        "Who": "Guardian, Builder, Designer, Data Pilot, Coordinator bots collaborate in parallel.",
        "What": "Focus upgrades on watch efficiency, SQL pattern quality, action/adaptive decision stability, and AIHub routing quality.",
        "Big Area": "Control plane (gateway), AIHub brain, learning trainer, and runtime fleet telemetry all in one loop.",
    }
    st.json(guide, expanded=False)
    eta_rows = []
    for i, row in enumerate(cards[:10]):
        specialty = str(row.get("specialty", "fleet"))
        role = _role_for_specialty(specialty)
        level = float(row.get("level", 1.0))
        xp = float(row.get("experience_xp", 0.0))
        speed = float(row.get("speed_bonus", 0.0))
        role_weight = {"Coordinator": 0.88, "Data Pilot": 0.92, "Designer": 1.00, "Guardian": 1.08, "Builder": 1.03}.get(role, 1.0)
        role_eta = max(0.2, (eta_hours * role_weight) * (1.0 - min(0.55, (level / 160.0) + (speed * 0.35) + (xp / 30000.0))))
        eta_rows.append(
            {
                "bot": _stable_bot_name(i, row),
                "role": role,
                "area": specialty,
                "eta_h": round(role_eta, 2),
                "level": int(level),
                "xp": int(xp),
            }
        )
    if eta_rows:
        st.caption("Detailed ETA by role / area")
        st.dataframe(eta_rows, use_container_width=True, hide_index=True)
    thought_rows = []
    for i, row in enumerate(cards[:20]):
        specialty = str(row.get("specialty", "fleet"))
        role = _role_for_specialty(specialty)
        thought_rows.append(
            {
                "Robot": _stable_bot_name(i, row),
                "Where": str(row.get("zone", "Fleet Area")),
                "Specialized In": specialty,
                "Good At": role,
                "Thinking": _thinking_for_row(row),
            }
        )
    if thought_rows:
        st.caption("Robot thinking/specialization table")
        st.dataframe(thought_rows, use_container_width=True, hide_index=True)

    if not cards:
        st.caption("No saved Hermes profiles yet — run training to populate the fleet arena cards.")
        return

    st.markdown("#### Hermes Row")
    _render_cosmic_scroll(cards)
    st.markdown("#### Bot Cards")
    for chunk_start in range(0, len(cards), 4):
        cols = st.columns(4)
        for idx, (col, row) in enumerate(zip(cols, cards[chunk_start : chunk_start + 4])):
            with col:
                size_mode = str(row.get("size_mode", "mid"))
                specialty = str(row.get("specialty", "fleet"))
                level = int(float(row.get("level", 1.0)))
                xp = float(row.get("experience_xp", 0.0))
                speed = float(row.get("speed_bonus", 0.0))
                token = float(row.get("token_power_gain", 0.0))
                bot_name = _stable_bot_name(chunk_start + idx, row)
                tiny = _tiny_avatar(chunk_start + idx, size_mode)
                role = _role_for_specialty(specialty)
                st.markdown(f"**{tiny} {bot_name}**")
                st.caption(f"{role} • {specialty}")
                st.caption(f"Design: {_design_pack(size_mode, specialty)}")
                xp_ratio = min(1.0, xp / 10000.0)
                level_ratio = min(1.0, level / 120.0)
                synergy_ratio = min(1.0, (xp_ratio * 0.45) + (level_ratio * 0.35) + (speed * 0.20))
                _progress_variant("XP", xp_ratio, "xp")
                _progress_variant("Level", level_ratio, "level")
                _progress_variant("Synergy", synergy_ratio, "synergy")
                st.caption(f"Accessories: {_accessories_for_role(role)}")
                st.caption(f"Boosts: speed +{speed * 100:.1f}% • token +{token * 100:.1f}%")

    st.markdown("#### Sub-Agent Bars + Optimization Guide")
    sub_agents = _sub_agent_summary(cards)
    if sub_agents:
        for item in sub_agents:
            _progress_variant(f"{item['name']} readiness", float(item["readiness"]), "synergy")
            st.caption(f"{item['name']}: {item['profile']}")
            st.caption(f"Tip: {item['tips']} • members: {int(item['members'])}")
    else:
        st.caption("Sub-agent readiness appears after profile snapshots include specialty coverage.")
