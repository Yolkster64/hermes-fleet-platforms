import json
import os
import time
from typing import Any, Dict, List, Tuple

import requests
import streamlit as st

API_BASE = os.getenv("HERMES_API_BASE_URL", "http://localhost:8788")
DEFAULT_API_KEY = os.getenv("HERMES_GUI_API_KEY", "local-hermes-ui-key")
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


def headers() -> Dict[str, str]:
    key = st.session_state.get("api_key", "").strip()
    return {"X-Hermes-Key": key} if key else {}


def api_get(path: str, timeout: int = 30) -> Dict[str, Any]:
    r = requests.get(f"{API_BASE}{path}", headers=headers(), timeout=timeout)
    r.raise_for_status()
    return r.json()


def api_post(path: str, payload: Dict[str, Any], timeout: int = 120) -> Dict[str, Any]:
    r = requests.post(f"{API_BASE}{path}", json=payload, headers=headers(), timeout=timeout)
    r.raise_for_status()
    return r.json()


def safe_get(path: str, timeout: int = 30) -> Tuple[Dict[str, Any], str]:
    try:
        return api_get(path, timeout=timeout), ""
    except Exception as exc:  # pragma: no cover
        return {}, str(exc)


def safe_post(path: str, payload: Dict[str, Any], timeout: int = 120) -> Tuple[Dict[str, Any], str]:
    last_error = ""
    for attempt in range(3):
        try:
            return api_post(path, payload=payload, timeout=timeout), ""
        except Exception as exc:  # pragma: no cover
            last_error = str(exc)
            if attempt < 2:
                time.sleep(0.7)
    return {}, last_error


def log_text(label: str, payload: Dict[str, Any]) -> None:
    st.session_state.setdefault("logs", [])
    st.session_state["logs"].insert(0, {"label": label, "payload": payload})
    st.session_state["logs"] = st.session_state["logs"][:25]


def pull_metric(payload: Any, names: Tuple[str, ...], default: float = 0.0) -> float:
    if isinstance(payload, dict):
        for name in names:
            if name in payload and isinstance(payload[name], (int, float)):
                return float(payload[name])
        for value in payload.values():
            found = pull_metric(value, names, default=default)
            if found != default:
                return found
    if isinstance(payload, list):
        for value in payload:
            found = pull_metric(value, names, default=default)
            if found != default:
                return found
    return default


def build_technique_profile(
    techniques: List[str], swarm_strategy: str, micro_agents: int, gaussian_pressure: float, permanent_intelligence: bool, high_level_learning: float
) -> Dict[str, Any]:
    has_knaa = "KNAA/QNAA reasoning" in techniques
    has_quant = "Quantized compression" in techniques
    has_parallel = "Multi-parallel swarm" in techniques
    has_multipolar = "Multipolar ensemble" in techniques
    has_natural = "Natural pressure adaptation" in techniques
    learning_bias = max(0.0, min(1.0, high_level_learning))
    return {
        "techniques": techniques,
        "swarm_strategy": swarm_strategy,
        "micro_agents": micro_agents,
        "gaussian_pressure": gaussian_pressure,
        "permanent_intelligence": permanent_intelligence,
        "high_level_learning": learning_bias,
        "sql_signal": min(0.98, 0.80 + (0.06 if has_knaa else 0.0) + (0.04 if has_natural else 0.0) + (learning_bias * 0.04)),
        "internet_signal": min(0.98, 0.78 + (0.10 if has_parallel else 0.0) + (0.06 if has_multipolar else 0.0) + (learning_bias * 0.06)),
        "llm_signal": min(0.99, 0.82 + (0.07 if has_knaa else 0.0) + (0.05 if has_quant else 0.0) + (learning_bias * 0.05)),
        "stability_bias": min(0.96, 0.72 + (0.10 if permanent_intelligence else 0.0) + (0.06 if has_quant else 0.0) + ((1.0 - learning_bias) * 0.08)),
    }


def run_auto_cycle(max_mode: bool, technique: Dict[str, Any]) -> Dict[str, Any]:
    steps = 520 if max_mode else 220
    candidates = min(500, (320 if max_mode else 140) + int(technique.get("micro_agents", 48) * 0.2))
    sim_steps = 320 if max_mode else 120
    specialty = f"fleet:{technique.get('swarm_strategy', 'hybrid')}"

    simulate, sim_err = safe_post("/simulate", {"specialty": specialty, "steps": sim_steps})
    pulse, pulse_err = safe_post(
        "/learning-pulse",
        {
            "specialty": specialty,
            "steps": steps,
            "candidates": candidates,
            "sql_signal": technique["sql_signal"],
            "internet_signal": technique["internet_signal"],
            "llm_signal": technique["llm_signal"],
            "stability_bias": max(0.60, min(0.98, technique["stability_bias"] + (technique["gaussian_pressure"] * 0.04))),
        },
        timeout=140,
    )
    optimize, opt_err = safe_post("/optimize-fleet", {"specialty": specialty, "candidates": candidates}, timeout=120)
    curate, curate_err = safe_post(
        "/curate-learning",
        {
            "sql_signal": technique["sql_signal"],
            "internet_signal": technique["internet_signal"],
            "llm_signal": technique["llm_signal"],
            "stability_bias": technique["stability_bias"],
        },
        timeout=90,
    )
    dedupe, dedupe_err = safe_post("/dedupe-optimize", {"roots": ["core", "runtime", "src"], "max_file_mb": 8}, timeout=120)
    return {
        "technique_profile": technique,
        "simulate": simulate,
        "learning_pulse": pulse,
        "optimize_fleet": optimize,
        "curate_learning": curate,
        "dedupe_optimize": dedupe,
        "errors": {"simulate": sim_err, "learning_pulse": pulse_err, "optimize_fleet": opt_err, "curate_learning": curate_err, "dedupe_optimize": dedupe_err},
    }


def run_special_fleet_training(max_mode: bool, study_areas: List[str], technique: Dict[str, Any]) -> Dict[str, Any]:
    steps = 760 if max_mode else 300
    candidates = min(500, (360 if max_mode else 180) + int(technique.get("micro_agents", 48) * 0.15))
    areas = "-".join([s.lower().replace(" & ", "-").replace(" ", "-") for s in study_areas[:3]]) if study_areas else "general"
    specialty = f"fleet:{technique.get('swarm_strategy', 'hybrid')}:{areas}"
    pulse, pulse_err = safe_post(
        "/learning-pulse",
        {
            "specialty": specialty,
            "steps": steps,
            "candidates": candidates,
            "sql_signal": technique["sql_signal"],
            "internet_signal": min(0.99, technique["internet_signal"] + 0.03),
            "llm_signal": min(0.99, technique["llm_signal"] + 0.02),
            "stability_bias": technique["stability_bias"],
        },
        timeout=180,
    )
    simulate, sim_err = safe_post("/simulate", {"specialty": specialty, "steps": 360 if max_mode else 140}, timeout=120)
    optimize, opt_err = safe_post("/optimize-fleet", {"specialty": specialty, "candidates": candidates}, timeout=140)
    return {
        "specialty": specialty,
        "technique_profile": technique,
        "learning_pulse": pulse,
        "simulate": simulate,
        "optimize_fleet": optimize,
        "errors": {"learning_pulse": pulse_err, "simulate": sim_err, "optimize_fleet": opt_err},
    }


def zone_for_agent(specialty: str) -> str:
    specialty_l = specialty.lower()
    if "security" in specialty_l:
        return "Security Zone"
    if "research" in specialty_l or "learning" in specialty_l:
        return "Learning Zone"
    if "infra" in specialty_l or "ops" in specialty_l:
        return "Ops Zone"
    if "fleet" in specialty_l:
        return "Fleet Core"
    return "General Zone"


def normalize_agents(snapshot_data: Dict[str, Any], global_bonus: float) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    agents = snapshot_data.get("agents", [])
    symbols = ["🧠", "⚙️", "🛡️", "📡", "🚀", "🔬", "🛰️", "📊"]
    for i, agent in enumerate(agents):
        reward = float(agent.get("reward_score", 0.0))
        success_rate = float(agent.get("success_rate", 0.0))
        load = float(agent.get("load", 0.0))
        bonus = max(0.0, reward * (0.5 + global_bonus))
        progress = max(0.0, min(1.0, (reward * 0.5) + (success_rate * 0.5)))
        size_mode = "small-fast" if progress < 0.45 else ("medium-balanced" if progress < 0.75 else "large-deep")
        interaction = "mesh" if "research" in str(agent.get("specialty", "")).lower() else "hybrid"
        skill_start = (i * 3) % len(AGENT_SKILLS_25)
        skill_pack = [AGENT_SKILLS_25[(skill_start + j) % len(AGENT_SKILLS_25)] for j in range(3)]
        rows.append(
            {
                "symbol": symbols[i % len(symbols)],
                "name": agent.get("name", f"hermes-{i+1}"),
                "specialty": agent.get("specialty", "general"),
                "zone": zone_for_agent(str(agent.get("specialty", "general"))),
                "reward": reward,
                "success_rate": success_rate,
                "load": load,
                "bonus": bonus,
                "progress": progress,
                "active": bool(agent.get("active", True)),
                "size_mode": size_mode,
                "interaction": interaction,
                "skills": skill_pack,
            }
        )
    return rows


def deep_auto_learning_zone(max_mode: bool, study_areas: List[str], rounds: int, technique: Dict[str, Any]) -> Dict[str, Any]:
    candidates = min(500, (300 if max_mode else 160) + int(technique.get("micro_agents", 48) * 0.2))
    steps = 520 if max_mode else 220
    outputs: List[Dict[str, Any]] = []
    for i in range(max(1, rounds)):
        pulse, pulse_err = safe_post(
            "/learning-pulse",
            {
                "specialty": f"fleet:{technique.get('swarm_strategy', 'hybrid')}",
                "steps": steps + (i * 120),
                "candidates": candidates,
                "sql_signal": technique["sql_signal"],
                "internet_signal": technique["internet_signal"],
                "llm_signal": technique["llm_signal"],
                "stability_bias": max(0.60, min(0.98, technique["stability_bias"] + (technique["gaussian_pressure"] * 0.05))),
            },
            timeout=150,
        )
        compare_prompt = (
            "Compare the latest Hermes learning signals and rank improvement opportunities. "
            f"Study areas: {', '.join(study_areas) if study_areas else 'fleet, optimization, safety'}. "
            f"Use techniques: {', '.join(technique.get('techniques', []))}."
        )
        compare, compare_err = safe_post(
            "/llm-chat",
            {"prompt": compare_prompt, "system_prompt": "You are Hermes deep-learning coordinator.", "temperature": 0.2, "max_tokens": 900},
            timeout=120,
        )
        outputs.append({"round": i + 1, "pulse": pulse, "pulse_error": pulse_err, "compare": compare, "compare_error": compare_err})
    return {"rounds": rounds, "study_areas": study_areas, "technique_profile": technique, "results": outputs}


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


st.set_page_config(page_title="Hermes Super Easy", page_icon="🧠", layout="wide")
st.title("Hermes Fleet Command Center")
st.caption("Super simple dashboard: what is happening now, how learning works, and one-click actions.")

if "api_key" not in st.session_state:
    st.session_state["api_key"] = DEFAULT_API_KEY
if "auto_boot_done" not in st.session_state:
    st.session_state["auto_boot_done"] = False
if "last_chat" not in st.session_state:
    st.session_state["last_chat"] = ""
if "ctl_study_areas" not in st.session_state:
    st.session_state["ctl_study_areas"] = ["Optimization", "AIHub", "Truth & Safety", "Fleet Topology"]
if "ctl_techniques" not in st.session_state:
    st.session_state["ctl_techniques"] = ["KNAA/QNAA reasoning", "Quantized compression", "Multi-parallel swarm", "Multipolar ensemble", "Natural pressure adaptation"]
if "ctl_swarm_strategy" not in st.session_state:
    st.session_state["ctl_swarm_strategy"] = "hybrid"
if "ctl_micro_agents" not in st.session_state:
    st.session_state["ctl_micro_agents"] = 128
if "ctl_gaussian_pressure" not in st.session_state:
    st.session_state["ctl_gaussian_pressure"] = 0.88
if "ctl_permanent_intelligence" not in st.session_state:
    st.session_state["ctl_permanent_intelligence"] = True
if "ctl_high_level_learning" not in st.session_state:
    st.session_state["ctl_high_level_learning"] = 0.72

with st.sidebar:
    st.subheader("Easy Connection")
    st.text_input("API Key", key="api_key", type="password")
    st.caption(f"Gateway: {API_BASE}")
    st.caption("Default Docker key is pre-filled.")
    st.markdown("### How it works")
    st.caption("1. Send prompt or click auto action\n2. Hermes fleet simulates + learns\n3. Bonus and XP improve")
    live_refresh = st.checkbox("Live fleet auto-refresh", value=True)
    refresh_seconds = st.slider("Refresh seconds", min_value=10, max_value=90, value=20, step=5)

unified, unified_err = safe_get("/unified-config", timeout=20)
bonus_data, bonus_err = safe_get("/aihub-bonus", timeout=20)
snapshot, snapshot_err = safe_get("/snapshot", timeout=20)
aihub_bonus = float(bonus_data.get("aihub_bonus", 0.0))
agent_rows = normalize_agents(snapshot, aihub_bonus) if not snapshot_err else []
total_hermes = len(agent_rows)
active_hermes = len([a for a in agent_rows if a["active"]])
avg_progress = (sum(a["progress"] for a in agent_rows) / total_hermes) if total_hermes else 0.0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("System", "Online" if not unified_err else "Offline")
c2.metric("Total Hermes", str(total_hermes))
c3.metric("Active Hermes", str(active_hermes))
c4.metric("AIHub Bonus", f"{aihub_bonus * 100:.1f}%")
c5.metric("Model", str(unified.get("aihub_shared_model_id", "aihub-unified-v1")))

if unified_err:
    st.error(f"Gateway not ready: {unified_err}")
if bonus_err:
    st.warning(f"AIHub bonus pending: {bonus_err}")

st.write(
    f"**Unified AI/ML:** provider={unified.get('llm_api_provider', 'temp-api')} | "
    f"entry={unified.get('single_exe_entrypoint', 'hermes-gateway')} | "
    f"profile={unified.get('aihub_shared_ml_profile', 'global-learning')}"
)
render_learning_diagram()

mode = st.radio("Training Level", ["Easy", "Near Max Hermes"], horizontal=True, index=1)
max_mode = mode == "Near Max Hermes"

study_areas = st.multiselect(
    "Study Areas",
    ["Security", "Optimization", "AIHub", "Fleet Topology", "Learning Retention", "Truth & Safety", "Internet Signals", "Cost Efficiency"],
    key="ctl_study_areas",
)
with st.expander("Advanced Intelligence Techniques"):
    techniques = st.multiselect(
        "Techniques",
        [
            "KNAA/QNAA reasoning",
            "Quantized compression",
            "Multi-parallel swarm",
            "Multipolar ensemble",
            "Natural pressure adaptation",
            "Cross-agent communication mesh",
        ],
        key="ctl_techniques",
    )
    swarm_strategy = st.selectbox("Swarm strategy", ["hybrid", "swarm", "mesh", "multipolar", "specialist-mix"], key="ctl_swarm_strategy")
    micro_agents = st.slider("Micro Hermes agents", min_value=16, max_value=256, step=16, key="ctl_micro_agents")
    gaussian_pressure = st.slider("Gaussian learning pressure", min_value=0.40, max_value=1.00, step=0.02, key="ctl_gaussian_pressure")
    permanent_intelligence = st.checkbox("Permanent intelligence memory mode", key="ctl_permanent_intelligence")
    high_level_learning = st.slider(
        "High-level learning focus (performance -> long-term learning)",
        min_value=0.0,
        max_value=1.0,
        step=0.01,
        key="ctl_high_level_learning",
    )

technique_profile = build_technique_profile(
    techniques=techniques,
    swarm_strategy=swarm_strategy,
    micro_agents=micro_agents,
    gaussian_pressure=gaussian_pressure,
    permanent_intelligence=permanent_intelligence,
    high_level_learning=high_level_learning,
)
st.caption(
    "Active upgrades: "
    f"{', '.join(technique_profile['techniques']) if technique_profile['techniques'] else 'standard'} | "
    f"swarm={technique_profile['swarm_strategy']} | micro_agents={technique_profile['micro_agents']} | "
    f"high_level_learning={technique_profile['high_level_learning']:.2f}"
)
st.caption("Agent skill system: 25 total skills, 3 active skills per Hermes unit.")

learned_profile = latest_learned_profile(snapshot)
sync1, sync2, sync3 = st.columns([1.1, 1.1, 2.2])
with sync1:
    if st.button("Send GUI Profile to Fleet", use_container_width=True):
        gui_sync_payload = {
            "source": "gui_profile",
            "signal_score": max(0.0, min(1.0, 0.55 + (technique_profile["high_level_learning"] * 0.25))),
            "payload": {
                "swarm_strategy": technique_profile["swarm_strategy"],
                "micro_agents": technique_profile["micro_agents"],
                "gaussian_pressure": technique_profile["gaussian_pressure"],
                "high_level_learning": technique_profile["high_level_learning"],
                "techniques": technique_profile["techniques"],
                "study_areas": study_areas,
            },
        }
        _, sync_err = safe_post("/ingest-signal", gui_sync_payload, timeout=60)
        if sync_err:
            st.error(f"Sync failed: {sync_err}")
        else:
            st.success("GUI profile synced to fleet memory.")
with sync2:
    if st.button("Apply Fleet Learned Profile", use_container_width=True):
        if learned_profile:
            st.session_state["ctl_swarm_strategy"] = str(learned_profile.get("swarm_strategy", learned_profile.get("strategy", st.session_state["ctl_swarm_strategy"])))
            micro_val = learned_profile.get("micro_agents", st.session_state["ctl_micro_agents"])
            if isinstance(micro_val, (int, float)):
                st.session_state["ctl_micro_agents"] = int(max(16, min(256, micro_val)))
            gp_val = learned_profile.get("gaussian_pressure", learned_profile.get("dynamic_chaos", st.session_state["ctl_gaussian_pressure"]))
            if isinstance(gp_val, (int, float)):
                st.session_state["ctl_gaussian_pressure"] = float(max(0.40, min(1.00, gp_val)))
            hll_val = learned_profile.get("high_level_learning", st.session_state["ctl_high_level_learning"])
            if isinstance(hll_val, (int, float)):
                st.session_state["ctl_high_level_learning"] = float(max(0.0, min(1.0, hll_val)))
            if isinstance(learned_profile.get("techniques"), list) and learned_profile.get("techniques"):
                st.session_state["ctl_techniques"] = [str(t) for t in learned_profile["techniques"][:6]]
            st.success("Fleet learned profile applied to GUI controls.")
            st.rerun()
        else:
            st.warning("No learned profile found in recent fleet signals.")
with sync3:
    if learned_profile:
        st.caption(
            f"Carryover active: strategy={learned_profile.get('swarm_strategy', learned_profile.get('strategy', 'hybrid'))}, "
            f"high_level_learning={float(learned_profile.get('high_level_learning', 0.0)):.2f}"
        )
    else:
        st.caption("Carryover ready: run an auto cycle to generate learned profile signals.")

fleet_reward = pull_metric(snapshot, ("avg_reward_score", "reward_score", "reward"), default=0.0)
fleet_truth = pull_metric(snapshot, ("avg_truth_score", "truth_score", "truth"), default=0.0)
fleet_shape = pull_metric(snapshot, ("avg_fleet_shape_score", "fleet_shape_score"), default=0.0)
learning_depth = pull_metric(snapshot, ("learning_steps", "steps", "total_steps"), default=0.0)
fleet_score = max(0.0, min(100.0, ((fleet_reward * 0.35) + (fleet_truth * 0.35) + (fleet_shape * 0.30)) * 100.0))
st.progress(float(max(0.0, min(1.0, avg_progress))), text=f"Fleet Progress: {avg_progress * 100:.1f}%")
st.metric("Fleet Score", f"{fleet_score:.1f}/100")
xp1, xp2, xp3, xp4 = st.columns(4)
with xp1:
    render_xp_bar("Learning XP", min(1.0, learning_depth / 1000.0), "#48C9B0")
with xp2:
    render_xp_bar("Reward XP", fleet_reward, "#58D68D")
with xp3:
    render_xp_bar("Truth XP", fleet_truth, "#5DADE2")
with xp4:
    render_xp_bar("Fleet Shape XP", fleet_shape, "#AF7AC5")

trend1, trend2 = st.columns(2)
with trend1:
    st.caption("AIHub bonus memory (recent)")
    bonus_tail = snapshot.get("aihub_bonus_memory_tail", [])[-20:]
    if bonus_tail:
        st.line_chart(bonus_tail)
with trend2:
    st.caption("Fleet score trend (recent)")
    score_tail = fleet_score_history(snapshot)
    if score_tail:
        st.line_chart(score_tail[-20:])

summary_left, summary_right = st.columns([2, 1])
with summary_left:
    st.subheader("Fleet Summary")
    st.write(
        f"- Reward quality: **{fleet_reward:.3f}**\n"
        f"- Truth and safety: **{fleet_truth:.3f}**\n"
        f"- Fleet shape signal: **{fleet_shape:.3f}**\n"
        f"- Learning depth: **{int(learning_depth)} steps**"
    )
with summary_right:
    st.subheader("Quick Actions")
    st.caption("These buttons run full actions immediately.")
    if st.button("Generate Fleet Health Report", use_container_width=True):
        report_prompt = (
            "Create a short fleet health report from current Hermes data with "
            "strengths, risks, and next optimization action."
        )
        chat, chat_err = safe_post(
            "/llm-chat",
            {"prompt": report_prompt, "system_prompt": "You are Hermes AIHub fleet analyst.", "temperature": 0.2, "max_tokens": 800},
        )
        if chat_err:
            st.error(f"Report generation failed: {chat_err}")
        else:
            st.session_state["last_chat"] = chat.get("response_text", "")
            log_text("fleet-health-report", chat)
            st.success("Fleet health report generated.")
    if st.button("🚀 Deploy All Hermes", use_container_width=True):
        deploy = run_auto_cycle(max_mode=True, technique=technique_profile)
        log_text("deploy-all-hermes", deploy)
        st.success("All Hermes units deployed and synced.")
    if st.button("⚡ Permanent Bonus Boost", use_container_width=True):
        boost1, e1 = safe_post(
            "/curate-learning",
            {
                "sql_signal": min(0.99, technique_profile["sql_signal"] + 0.04),
                "internet_signal": min(0.99, technique_profile["internet_signal"] + 0.04),
                "llm_signal": min(0.99, technique_profile["llm_signal"] + 0.04),
                "stability_bias": min(0.99, technique_profile["stability_bias"] + 0.03),
            },
            timeout=90,
        )
        boost2, e2 = safe_post("/dedupe-optimize", {"roots": ["core", "runtime", "src"], "max_file_mb": 8}, timeout=120)
        log_text("permanent-bonus-boost", {"curate_learning": boost1, "dedupe": boost2, "errors": [e1, e2]})
        st.success("Permanent bonus boost tools applied.")

act1, act2, act3, act4, act5 = st.columns([1.1, 1, 1, 1.1, 1.3])
with act1:
    if st.button("Run Full Auto Learning + Fleet Upgrade", use_container_width=True):
        result = run_auto_cycle(max_mode=max_mode, technique=technique_profile)
        log_text("full-auto-cycle", result)
        st.success("Auto cycle finished.")
        st.text_area("Auto Cycle Result", value=json.dumps(result, indent=2), height=260)
with act2:
    if st.button("Refresh Fleet Data", use_container_width=True):
        snapshot, snapshot_err = safe_get("/snapshot", timeout=20)
        if snapshot_err:
            st.error(f"Fleet data refresh failed: {snapshot_err}")
        else:
            agent_rows = normalize_agents(snapshot, aihub_bonus)
            log_text("fleet-refresh", snapshot)
            st.success("Fleet data refreshed.")
with act3:
    if st.button("Quick Optimize Now", use_container_width=True):
        optimize, opt_err = safe_post(
            "/optimize-fleet",
            {"specialty": f"fleet:{technique_profile['swarm_strategy']}", "candidates": min(500, (480 if max_mode else 160) + int(technique_profile["micro_agents"] * 0.2))},
            timeout=120,
        )
        if opt_err:
            st.error(f"Optimize failed: {opt_err}")
        else:
            log_text("quick-optimize", optimize)
            st.success("Fleet optimization complete.")
with act4:
    if st.button("♾️ Deep Auto Learning Zone", use_container_width=True):
        deep = deep_auto_learning_zone(max_mode=max_mode, study_areas=study_areas, rounds=3 if max_mode else 2, technique=technique_profile)
        log_text("deep-auto-learning-zone", deep)
        st.success("Deep auto-learning completed.")
        st.text_area("Deep Learning Summary", value=json.dumps(deep, indent=2), height=260)
with act5:
    if st.button("🛰️ Special Fleet Training", use_container_width=True):
        special = run_special_fleet_training(max_mode=max_mode, study_areas=study_areas, technique=technique_profile)
        log_text("special-fleet-training", special)
        st.success("Special fleet training completed.")
        st.text_area("Special Training Result", value=json.dumps(special, indent=2), height=260)

st.subheader("Automatic Learning Zone")
auto_enabled = st.checkbox("Always run automatic smart learning", value=True)
auto_interval = st.slider("Auto interval (seconds)", min_value=20, max_value=300, value=45, step=5)
intelligent_shuffle = st.checkbox("Intelligent shuffle + adaptive profile each cycle", value=True)
if "last_auto_run_ts" not in st.session_state:
    st.session_state["last_auto_run_ts"] = 0.0
now_ts = time.time()
if auto_enabled and (now_ts - float(st.session_state.get("last_auto_run_ts", 0.0))) >= auto_interval:
    auto_profile = dict(technique_profile)
    if intelligent_shuffle and learned_profile:
        learned_hll = float(learned_profile.get("high_level_learning", auto_profile["high_level_learning"]))
        auto_profile["high_level_learning"] = max(0.0, min(1.0, (auto_profile["high_level_learning"] * 0.65) + (learned_hll * 0.35)))
        if isinstance(learned_profile.get("swarm_strategy"), str):
            auto_profile["swarm_strategy"] = learned_profile["swarm_strategy"]
        if isinstance(learned_profile.get("micro_agents"), (int, float)):
            auto_profile["micro_agents"] = int(max(16, min(256, learned_profile["micro_agents"])))
    auto_result = run_auto_cycle(max_mode=max_mode, technique=auto_profile)
    safe_post(
        "/ingest-signal",
        {
            "source": "gui_auto_sync",
            "signal_score": max(0.0, min(1.0, 0.52 + (auto_profile["high_level_learning"] * 0.28))),
            "payload": {
                "swarm_strategy": auto_profile["swarm_strategy"],
                "micro_agents": auto_profile["micro_agents"],
                "gaussian_pressure": auto_profile["gaussian_pressure"],
                "high_level_learning": auto_profile["high_level_learning"],
                "techniques": auto_profile["techniques"],
                "mode": "auto_cycle",
            },
        },
        timeout=60,
    )
    log_text("automatic-learning-zone", auto_result)
    st.session_state["last_auto_run_ts"] = now_ts
    st.info("Automatic smart learning cycle executed.")
else:
    remaining = max(0, auto_interval - int(now_ts - float(st.session_state.get("last_auto_run_ts", 0.0))))
    st.caption(f"Next automatic cycle in ~{remaining}s")

st.subheader("Learning Space (text)")
prompt = st.text_area(
    "Ask Hermes AIHub",
    value="Summarize current fleet state and tell me the next best learning and optimization action.",
    height=120,
)
if st.button("Send to Hermes", use_container_width=True):
    chat, chat_err = safe_post(
        "/llm-chat",
        {"prompt": prompt, "system_prompt": "You are Hermes AIHub fleet learning assistant.", "temperature": 0.25, "max_tokens": 700},
    )
    if chat_err:
        st.error(f"Hermes text request failed: {chat_err}")
    else:
        st.session_state["last_chat"] = chat.get("response_text", "")
        log_text("learning-space-chat", chat)
        st.success("Hermes response ready.")
if st.session_state.get("last_chat", ""):
    st.text_area("Hermes Learning Response", value=st.session_state["last_chat"], height=220)
st.caption("Prompt path: Prompt -> Hermes fleet agents -> learning pulse -> optimization -> bonus + XP")

st.subheader("Hermes Fleet Units")
if snapshot_err:
    st.warning(f"Fleet snapshot unavailable: {snapshot_err}")
else:
    d1, d2, d3, d4 = st.columns(4)
    d1.metric("Reward", f"{fleet_reward:.3f}")
    d2.metric("Truth", f"{fleet_truth:.3f}")
    d3.metric("Fleet Shape", f"{fleet_shape:.3f}")
    d4.metric("Learning Depth", str(int(learning_depth)))
    st.dataframe(
        [
            {
                "Unit": a["symbol"],
                "Hermes": a["name"],
                "Bonus": round(a["bonus"], 4),
                "Progress": f"{a['progress'] * 100:.1f}%",
                "Size": a["size_mode"],
                "Interaction": a["interaction"],
                "Zone": a["zone"],
                "Specialty": a["specialty"],
                "Skills(3)": ", ".join(a["skills"]),
                "Active": "Yes" if a["active"] else "No",
            }
            for a in agent_rows
        ],
        use_container_width=True,
        hide_index=True,
    )
    st.caption("Raw runtime data is hidden by default.")
    with st.expander("Show Raw Data (advanced)"):
        st.json(snapshot)

    st.subheader("Live Fleet Feed")
    recent_events = snapshot.get("recent_events", [])
    if recent_events:
        for event in recent_events[:8]:
            event_type = str(event.get("event_type", "event"))
            ts = float(event.get("ts", 0.0))
            payload = event.get("payload", {})
            st.markdown(f"**{event_type}**  \n`{ts:.0f}`")
            st.code(str(payload)[:900])
    else:
        st.caption("No recent events yet.")

st.subheader("Tips + Tools")
t1, t2, t3 = st.columns(3)
t1.info("Tip: Keep Near Max mode on for stronger fleet adaptation.")
t2.info("Tip: Use Study Areas to steer what Hermes learns next.")
t3.info("Tip: Run Permanent Bonus Boost after major changes.")

if not st.session_state["auto_boot_done"]:
    warm, warm_err = safe_post("/learning-pulse", {"specialty": "fleet", "steps": 260, "candidates": 180}, timeout=90)
    if not warm_err:
        log_text("auto-boot-warmstart", warm)
        st.session_state["auto_boot_done"] = True
        st.info("Automatic warm-start completed.")
    else:
        st.warning("Automatic warm-start pending.")

with st.expander("Text Log"):
    for item in st.session_state.get("logs", []):
        st.code(f"{item['label']}: {item['payload']}")

if live_refresh:
    st.caption(f"Live refresh active: updating every {refresh_seconds}s")
    time.sleep(refresh_seconds)
    st.rerun()
