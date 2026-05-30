import os
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
import streamlit as st


def _gateway_base() -> str:
    return os.getenv("HERMES_API_BASE_URL", "http://hermes-gateway:8788").strip()


def _key_path() -> Path:
    volume_root = os.getenv("HERMES_VOLUME_DATA_PATH", "/workspace/runtime/hermes_persist").strip()
    return Path(volume_root) / "auth" / "gui_api_key.txt"


def _agents_path() -> Path:
    volume_root = os.getenv("HERMES_VOLUME_DATA_PATH", "/workspace/runtime/hermes_persist").strip()
    return Path(volume_root) / "agents" / "simple_agents.json"


def _backbones_path() -> Path:
    volume_root = os.getenv("HERMES_VOLUME_DATA_PATH", "/workspace/runtime/hermes_persist").strip()
    return Path(volume_root) / "agents" / "backbone_profiles.json"


def _load_agents() -> list[dict]:
    path = _agents_path()
    try:
        if path.exists():
            data = path.read_text(encoding="utf-8").strip()
            if not data:
                return []
            import json

            parsed = json.loads(data)
            return parsed if isinstance(parsed, list) else []
    except (OSError, ValueError):
        return []
    return []


def _save_agents(agents: list[dict]) -> tuple[bool, str]:
    path = _agents_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        import json

        path.write_text(json.dumps(agents, indent=2), encoding="utf-8")
        return True, ""
    except OSError as exc:
        return False, str(exc)


def _load_backbones() -> list[dict]:
    path = _backbones_path()
    try:
        if path.exists():
            data = path.read_text(encoding="utf-8").strip()
            if not data:
                return []
            import json

            parsed = json.loads(data)
            return parsed if isinstance(parsed, list) else []
    except (OSError, ValueError):
        return []
    return []


def _save_backbones(backbones: list[dict]) -> tuple[bool, str]:
    path = _backbones_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        import json

        path.write_text(json.dumps(backbones, indent=2), encoding="utf-8")
        return True, ""
    except OSError as exc:
        return False, str(exc)


def _load_saved_key() -> str:
    path = _key_path()
    try:
        if path.exists():
            return path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""
    return ""


def _save_key(key: str) -> tuple[bool, str]:
    value = key.strip()
    if not value:
        return False, "API key is empty."
    path = _key_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")
        return True, ""
    except OSError as exc:
        return False, str(exc)


def _health_check(key: str) -> tuple[bool, str]:
    if not key.strip():
        return False, "API key is empty."
    headers = {"X-Hermes-Key": key.strip()}
    try:
        r = requests.get(f"{_gateway_base()}/health", headers=headers, timeout=8)
        r.raise_for_status()
        return True, ""
    except requests.RequestException as exc:
        return False, str(exc)


def _deploy_agent(
    key: str,
    specialty: str,
    steps: int,
    candidates: int,
    sql_signal: float,
    internet_signal: float,
    llm_signal: float,
    stability_bias: float,
) -> tuple[bool, str]:
    payload = {
        "Mode": "deploy",
        "Scope": "single",
        "Specialty": specialty,
        "BatchSize": 1,
        "Steps": steps,
        "Candidates": candidates,
        "SqlSignal": sql_signal,
        "InternetSignal": internet_signal,
        "LlmSignal": llm_signal,
        "StabilityBias": stability_bias,
    }
    headers = {"X-Hermes-Key": key.strip()}
    try:
        r = requests.post(f"{_gateway_base()}/runtime-orchestrate/deploy", json=payload, headers=headers, timeout=20)
        r.raise_for_status()
        return True, ""
    except requests.RequestException as exc:
        return False, str(exc)


def _apply_aihub_upgrade(
    key: str,
    specialty: str,
    steps: int,
    candidates: int,
    sql_signal: float,
    internet_signal: float,
    llm_signal: float,
    stability_bias: float,
) -> tuple[bool, str]:
    payload = {
        "Specialty": specialty,
        "Steps": steps,
        "Candidates": candidates,
        "SqlSignal": sql_signal,
        "InternetSignal": internet_signal,
        "LlmSignal": llm_signal,
        "StabilityBias": stability_bias,
    }
    headers = {"X-Hermes-Key": key.strip()}
    try:
        r = requests.post(f"{_gateway_base()}/aihub-max-upgrade", json=payload, headers=headers, timeout=30)
        r.raise_for_status()
        return True, ""
    except requests.RequestException as exc:
        return False, str(exc)


def _run_learning_sql_pulse(
    key: str,
    specialty: str,
    steps: int,
    candidates: int,
    sql_signal: float,
    internet_signal: float,
    llm_signal: float,
    stability_bias: float,
) -> tuple[bool, str]:
    payload = {
        "Specialty": specialty,
        "Steps": steps,
        "Candidates": candidates,
        "SqlSignal": sql_signal,
        "InternetSignal": internet_signal,
        "LlmSignal": llm_signal,
        "StabilityBias": stability_bias,
    }
    headers = {"X-Hermes-Key": key.strip()}
    try:
        r = requests.post(f"{_gateway_base()}/learning-pulse", json=payload, headers=headers, timeout=30)
        r.raise_for_status()
        return True, ""
    except requests.RequestException as exc:
        return False, str(exc)


def _llm_optimization_factor(
    mesh_size: int,
    cost_bias: int,
    power_bias: int,
    perf_bias: int,
    profile: str,
    force_ultimate: bool = False,
) -> float:
    base = 0.60 + (0.03 * max(0, mesh_size))
    profile_boosts = {
        "balanced": 0.00,
        "cost-saver": -0.06,
        "power-max": 0.08,
        "latency-max": 0.06,
        "throughput-max": 0.10,
    }
    profile_boost = profile_boosts.get(profile, 0.0)
    cost_penalty = (max(0, min(100, cost_bias)) / 100.0) * 0.18
    power_boost = (max(0, min(100, power_bias)) / 100.0) * 0.20
    perf_boost = (max(0, min(100, perf_bias)) / 100.0) * 0.20
    score = base + profile_boost + power_boost + perf_boost - cost_penalty
    if force_ultimate:
        score = max(score, 0.99)
    return max(0.35, min(0.99, score))


st.set_page_config(page_title="Hermes Simple GUI", layout="centered")
st.title("Hermes Simple GUI")
st.caption("Simple mode: Hermes or X, clear choices, fast deploy.")

if "api_key" not in st.session_state:
    st.session_state["api_key"] = _load_saved_key() or "local-hermes-ui-key"
if "login_ok" not in st.session_state:
    st.session_state["login_ok"] = False
if "last_error" not in st.session_state:
    st.session_state["last_error"] = ""
if "agents" not in st.session_state:
    st.session_state["agents"] = _load_agents()

st.text_input("API Key", key="api_key", type="password")
st.caption(f"Gateway: {_gateway_base()}")

c1, c2 = st.columns(2)
with c1:
    if st.button("Save Key", use_container_width=True):
        saved, err = _save_key(st.session_state["api_key"])
        if saved:
            st.success("Key saved.")
        else:
            st.error(f"Save failed: {err}")
with c2:
    if st.button("Login", use_container_width=True):
        ok, err = _health_check(st.session_state["api_key"])
        st.session_state["login_ok"] = ok
        st.session_state["last_error"] = err
        if ok:
            st.success("Login successful.")
        else:
            st.error(f"Login failed: {err}")

st.divider()
st.subheader("Agent / X Builder")
agent_name = st.text_input("Agent Name", value="agent-01")
family_pick = st.radio("Step 1: Pick Family", options=["Hermes", "X"], horizontal=True)
hermes_four = ["Hermes Core", "Hermes Builder", "Hermes Analyst", "Hermes Guardian"]
ultimate_three = ["X (auto)", "X Core", "X5", "X6"]
hermes_variant = st.selectbox("Step 2A: Hermes Type (4 options)", options=hermes_four, index=0, disabled=(family_pick != "Hermes"))
ultimate_variant = st.selectbox("Step 2B: X Selection (4 options)", options=ultimate_three, index=0, disabled=(family_pick != "X"))
profile = st.selectbox("Step 3: Mission Profile", options=["balanced", "deep-analysis", "rapid-deploy", "safe-production"], index=0)
variable_set_one = st.selectbox(
    "Variable Set 1 (required)",
    options=["adaptive-routing", "precision-mode", "burst-mode", "safe-guarded"],
    index=0,
)
variable_set_two = st.selectbox(
    "Variable Set 2 (required)",
    options=["sql-focus", "code-focus", "ops-focus", "research-focus"],
    index=0,
)
subagent_count = st.slider("Step 4: Subagent Number", 1, 10, 4)
recommended_subagents = {
    "balanced": ["planner", "coder", "deployer", "observer"],
    "deep-analysis": ["planner", "researcher", "sql-engineer", "observer"],
    "rapid-deploy": ["planner", "coder", "deployer", "guardian"],
    "safe-production": ["planner", "guardian", "deployer", "observer"],
}
subagents = st.multiselect(
    "Step 5: Subagent Roles",
    options=["planner", "researcher", "coder", "sql-engineer", "deployer", "guardian", "observer"],
    default=recommended_subagents[profile][:subagent_count],
)
fleet_mode = st.selectbox(
    "Fleet Assignment",
    options=["working", "training", "working+training"],
    index=0,
)
if len(subagents) > subagent_count:
    st.warning(f"You selected {len(subagents)} roles. Recommended max for this run: {subagent_count}.")

attribute_defaults = {
    ("Hermes", "balanced"): {"speed": 78, "intelligence": 76, "stability": 84, "memory": 82, "power": 80},
    ("Hermes", "deep-analysis"): {"speed": 72, "intelligence": 90, "stability": 86, "memory": 92, "power": 82},
    ("Hermes", "rapid-deploy"): {"speed": 90, "intelligence": 74, "stability": 78, "memory": 76, "power": 88},
    ("Hermes", "safe-production"): {"speed": 74, "intelligence": 82, "stability": 94, "memory": 88, "power": 80},
    ("X", "balanced"): {"speed": 88, "intelligence": 90, "stability": 90, "memory": 90, "power": 92},
    ("X", "deep-analysis"): {"speed": 84, "intelligence": 98, "stability": 92, "memory": 98, "power": 94},
    ("X", "rapid-deploy"): {"speed": 98, "intelligence": 86, "stability": 86, "memory": 88, "power": 96},
    ("X", "safe-production"): {"speed": 86, "intelligence": 92, "stability": 99, "memory": 94, "power": 90},
}
defaults = attribute_defaults[(family_pick, profile)]
if st.button("Apply Recommended 5 Attributes", use_container_width=True):
    st.session_state["attr_speed"] = defaults["speed"]
    st.session_state["attr_intelligence"] = defaults["intelligence"]
    st.session_state["attr_stability"] = defaults["stability"]
    st.session_state["attr_memory"] = defaults["memory"]
    st.session_state["attr_power"] = defaults["power"]
if "attr_speed" not in st.session_state:
    st.session_state["attr_speed"] = defaults["speed"]
if "attr_intelligence" not in st.session_state:
    st.session_state["attr_intelligence"] = defaults["intelligence"]
if "attr_stability" not in st.session_state:
    st.session_state["attr_stability"] = defaults["stability"]
if "attr_memory" not in st.session_state:
    st.session_state["attr_memory"] = defaults["memory"]
if "attr_power" not in st.session_state:
    st.session_state["attr_power"] = defaults["power"]

st.markdown("**Step 6: 5 Attributes (recommended for your selected type)**")
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    speed_attr = st.slider("Speed", 50, 100, int(st.session_state["attr_speed"]), key="attr_speed")
with c2:
    intelligence_attr = st.slider("Intelligence", 50, 100, int(st.session_state["attr_intelligence"]), key="attr_intelligence")
with c3:
    stability_attr = st.slider("Stability", 50, 100, int(st.session_state["attr_stability"]), key="attr_stability")
with c4:
    memory_attr = st.slider("Memory", 50, 100, int(st.session_state["attr_memory"]), key="attr_memory")
with c5:
    power_attr = st.slider("Power", 50, 100, int(st.session_state["attr_power"]), key="attr_power")

if family_pick == "X":
    if ultimate_variant == "X5":
        x_tier = "ultimate-x5"
    elif ultimate_variant == "X6":
        x_tier = "ultimate-x6"
    elif ultimate_variant == "X Core":
        x_tier = "ultimate-x5"
    else:
        x_tier = "ultimate-x6" if profile in {"deep-analysis", "safe-production"} else "ultimate-x5"
    type_label = ultimate_variant
else:
    x_tier = "ultimate-x6" if profile in {"deep-analysis", "safe-production"} else "ultimate-x5"
    type_label = hermes_variant

max_cpu = min(99, int((power_attr + stability_attr) / 2))
max_gpu = min(99, int((speed_attr + power_attr) / 2))
max_ram = min(99, int((memory_attr + intelligence_attr) / 2))
xp_boost = min(99, int((speed_attr + intelligence_attr + stability_attr + memory_attr + power_attr) / 5))
sql_level = min(99, int((memory_attr + intelligence_attr) / 2))
profile_map = {
    "balanced": {"steps": 250, "candidates": 150, "stability": 0.86},
    "deep-analysis": {"steps": 390, "candidates": 190, "stability": 0.90},
    "rapid-deploy": {"steps": 220, "candidates": 210, "stability": 0.82},
    "safe-production": {"steps": 280, "candidates": 160, "stability": 0.95},
}
p = profile_map[profile]
steps = min(560, p["steps"] + int(memory_attr / 4))
candidates = min(240, p["candidates"] + int(speed_attr / 6))
llm_mesh = ["openai", "anthropic", "gemini", "mistral", "deepseek", "llama", "qwen"]
llm_signal = _llm_optimization_factor(
    mesh_size=len(llm_mesh),
    cost_bias=max(5, 100 - power_attr),
    power_bias=power_attr,
    perf_bias=intelligence_attr,
    profile="throughput-max",
    force_ultimate=(family_pick == "X"),
)

st.caption(
    f"Auto resources from attributes -> CPU {max_cpu}, GPU {max_gpu}, Memory {max_ram} | "
    f"Resolved tier: {x_tier} | XP {xp_boost}"
)


def _upsert_agent(entry: dict) -> None:
    agents = [a for a in st.session_state["agents"] if a.get("name") != entry.get("name")]
    agents.append(entry)
    st.session_state["agents"] = agents


def _save_agent_state() -> None:
    saved, save_err = _save_agents(st.session_state["agents"])
    if not saved:
        st.error(f"Save failed: {save_err}")


def _build_agent(name: str, family: str, type_name: str) -> dict:
    return {
        "name": name,
        "family": family,
        "type": type_name,
        "tier": x_tier,
        "profile": profile,
        "variable_set_one": variable_set_one,
        "variable_set_two": variable_set_two,
        "subagents": subagents[:subagent_count] if subagents else recommended_subagents[profile][:subagent_count],
        "subagent_count": subagent_count,
        "fleet_mode": fleet_mode,
        "fleet_assigned": True,
        "speed": speed_attr,
        "intelligence": intelligence_attr,
        "stability": stability_attr,
        "memory": memory_attr,
        "power": power_attr,
        "xp_boost": xp_boost,
        "sql_level": sql_level,
        "max_cpu": max_cpu,
        "max_gpu": max_gpu,
        "max_ram": max_ram,
        "deployed": False,
        "created_utc": datetime.now(timezone.utc).isoformat(),
    }


b1, b2, b3, b4 = st.columns(4)
with b1:
    if st.button("Buy 10 Hermes", use_container_width=True):
        for i in range(1, 11):
            _upsert_agent(_build_agent(f"hermes-{i:02d}", "Hermes", hermes_variant))
        _save_agent_state()
        st.success("Added 10 Hermes agents.")
with b2:
    if st.button("Buy 10 X", use_container_width=True):
        for i in range(1, 11):
            _upsert_agent(_build_agent(f"x-{i:02d}", "X", ultimate_variant))
        _save_agent_state()
        st.success("Added 10 X agents.")
with b3:
    if st.button("Buy 1 Hermes + 1 X", use_container_width=True):
        _upsert_agent(_build_agent("hermes-01", "Hermes", hermes_variant))
        _upsert_agent(_build_agent("x-01", "X", ultimate_variant))
        _save_agent_state()
        st.success("Added 1 Hermes and 1 X agent.")
with b4:
    if st.button("Save Selected Build", use_container_width=True):
        selected_family = "X" if family_pick == "X" else "Hermes"
        selected_type = ultimate_variant if family_pick == "X" else hermes_variant
        _upsert_agent(_build_agent(agent_name.strip() or "agent-01", selected_family, selected_type))
        _save_agent_state()
        st.success("Saved selected build.")

saved_agent_names = [str(a.get("name", "")).strip() for a in st.session_state["agents"] if str(a.get("name", "")).strip()]
deploy_selected = st.multiselect("Deploy these saved agents", options=saved_agent_names, default=saved_agent_names[:1])
d1, d2, d3, d4 = st.columns(4)
with d1:
    if st.button("Deploy Selected", use_container_width=True):
        if not st.session_state["login_ok"]:
            st.error("Log in first, then deploy.")
        elif not deploy_selected:
            st.warning("Select at least one saved agent.")
        else:
            ok_count = 0
            deployed_names = set(deploy_selected)
            for agent in st.session_state["agents"]:
                if str(agent.get("name", "")) not in deployed_names:
                    continue
                specialty = (
                    f"{str(agent.get('family', 'Hermes')).lower()}-{str(agent.get('type', 'core')).lower().replace(' ', '-')}-"
                    f"{agent.get('tier', 'ultimate-x5')}-{agent.get('profile', 'balanced')}-"
                    f"subs-{str(agent.get('subagent_count', 3))}-fleet-{str(agent.get('fleet_mode', 'working')).replace('+', 'plus')}-"
                    f"cpu{agent.get('max_cpu', 90)}-gpu{agent.get('max_gpu', 90)}-mem{agent.get('max_ram', 90)}"
                )
                ok, _ = _deploy_agent(
                    st.session_state["api_key"],
                    specialty=specialty,
                    steps=steps,
                    candidates=candidates,
                    sql_signal=max(0.70, float(agent.get("sql_level", 80)) / 100.0),
                    internet_signal=max(0.60, float(agent.get("max_ram", 85)) / 100.0),
                    llm_signal=llm_signal,
                    stability_bias=min(0.99, p["stability"] + (float(agent.get("stability", 85)) / 1000.0)),
                )
                if ok:
                    ok_count += 1
                    agent["deployed"] = True
                    agent["deployed_utc"] = datetime.now(timezone.utc).isoformat()
            _save_agent_state()
            st.success(f"Deployed {ok_count}/{len(deploy_selected)} selected agents.")
with d2:
    if st.button("Deploy All", use_container_width=True):
        if not st.session_state["login_ok"]:
            st.error("Log in first, then deploy.")
        else:
            ok_count = 0
            total = len(st.session_state["agents"])
            families = {str(a.get("family", "Hermes")) for a in st.session_state["agents"]}
            for agent in st.session_state["agents"]:
                specialty = (
                    f"{str(agent.get('family', 'Hermes')).lower()}-{str(agent.get('type', 'core')).lower().replace(' ', '-')}-"
                    f"{agent.get('tier', 'ultimate-x5')}-{agent.get('profile', 'balanced')}-"
                    f"smart-swarm-{len(families)}-subs-{str(agent.get('subagent_count', 3))}-"
                    f"fleet-{str(agent.get('fleet_mode', 'working')).replace('+', 'plus')}"
                )
                ok, _ = _deploy_agent(
                    st.session_state["api_key"],
                    specialty=specialty,
                    steps=steps,
                    candidates=candidates,
                    sql_signal=max(0.70, float(agent.get("sql_level", 80)) / 100.0),
                    internet_signal=max(0.60, float(agent.get("max_ram", 85)) / 100.0),
                    llm_signal=llm_signal,
                    stability_bias=min(0.99, p["stability"] + (float(agent.get("stability", 85)) / 1000.0)),
                )
                if ok:
                    ok_count += 1
                    agent["deployed"] = True
                    agent["deployed_utc"] = datetime.now(timezone.utc).isoformat()
            _save_agent_state()
            st.success(f"Deploy all completed: {ok_count}/{total}")
with d3:
    if st.button("Bring Back All", use_container_width=True):
        for agent in st.session_state["agents"]:
            agent["deployed"] = False
            agent["returned_utc"] = datetime.now(timezone.utc).isoformat()
        _save_agent_state()
        st.success("All fleets brought back. Fleet assignments were kept.")
with d4:
    if st.button("Save All", use_container_width=True):
        _save_agent_state()
        st.success("All fleet settings saved.")

guide_rows = [
    {
        "Family": "Hermes",
        "Option": "Hermes Core",
        "Best For": "Daily balanced workloads",
        "Recommendation": "Use with balanced profile and 3-4 subagents",
    },
    {
        "Family": "Hermes",
        "Option": "Hermes Builder",
        "Best For": "Shipping features quickly",
        "Recommendation": "Use rapid-deploy with higher speed/power",
    },
    {
        "Family": "Hermes",
        "Option": "Hermes Analyst",
        "Best For": "Reasoning and SQL deep dives",
        "Recommendation": "Use deep-analysis with higher intelligence/memory",
    },
    {
        "Family": "Hermes",
        "Option": "Hermes Guardian",
        "Best For": "Stable production operations",
        "Recommendation": "Use safe-production with high stability",
    },
    {
        "Family": "X",
        "Option": "X (auto)",
        "Best For": "Adaptive strongest default",
        "Recommendation": "Auto-picks X5/X6 based on mission profile",
    },
    {
        "Family": "X",
        "Option": "X Core",
        "Best For": "General X orchestration",
        "Recommendation": "Balanced X mode between speed and depth",
    },
    {
        "Family": "X",
        "Option": "X5",
        "Best For": "Fastest deployment throughput",
        "Recommendation": "Use for speed-first rollouts",
    },
    {
        "Family": "X",
        "Option": "X6",
        "Best For": "Maximum depth and reliability",
        "Recommendation": "Use for deep-analysis and safe-production",
    },
]
with st.expander("Super Detailed Guide + Recommendations Table", expanded=False):
    st.markdown(
        "**How to pick quickly**\n"
        "1. Pick `Hermes` or `X`.\n"
        "2. If Hermes: choose one of 4 types.\n"
        "3. If X: choose one of 4 (`X auto`, `X Core`, `X5`, `X6`).\n"
        "4. Pick both required variable sets (4 options each).\n"
        "5. Set subagent number, then roles.\n"
        "6. Apply recommended 5 attributes, then fine-tune.\n"
        "7. Buy/save builds, then deploy selected or deploy all.\n\n"
        "**Mixing strategy**\n"
        "- Use `Buy 1 Hermes + 1 X` for mixed swarm testing.\n"
        "- Use `Buy 10 Hermes` for stable broad operations.\n"
        "- Use `Buy 10 X` for max-performance campaigns.\n"
    )
    st.table(pd.DataFrame(guide_rows))

if st.session_state["agents"]:
    display_rows: list[dict] = []
    for a in st.session_state["agents"]:
        display_rows.append(
            {
                "name": a.get("name"),
                "family": a.get("family", a.get("type", "Hermes")),
                "type": a.get("type", ""),
                "tier": a.get("tier", ""),
                "profile": a.get("profile", ""),
                "fleet_mode": a.get("fleet_mode", "working"),
                "xp": int(a.get("xp_boost", 0)),
                "speed": int(a.get("speed", 0)),
                "intelligence": int(a.get("intelligence", 0)),
                "stability": int(a.get("stability", 0)),
                "memory": int(a.get("memory", a.get("max_ram", 0))),
                "power": int(a.get("power", 0)),
                "deployed": bool(a.get("deployed", False)),
            }
        )
    st.subheader("Agent Board")
    st.dataframe(pd.DataFrame(display_rows), use_container_width=True, hide_index=True)
    st.subheader("Detailed Graph (team averages)")
    avg_df = pd.DataFrame(display_rows)[["xp", "speed", "intelligence", "stability", "memory", "power"]].mean().to_frame(name="avg").T
    st.bar_chart(avg_df)
    st.subheader("XP + Stats by Agent")
    for row in display_rows[:20]:
        state_icon = "🟢" if row["deployed"] else "⚪"
        st.markdown(f"{state_icon} **{row['name']}** ({row['family']} / {row['type']}) - fleet: `{row['fleet_mode']}`")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.caption(f"XP {row['xp']}")
            st.progress(row["xp"] / 100.0)
            st.caption(f"Speed {row['speed']}")
            st.progress(row["speed"] / 100.0)
        with col_b:
            st.caption(f"Intelligence {row['intelligence']}")
            st.progress(row["intelligence"] / 100.0)
            st.caption(f"Stability {row['stability']}")
            st.progress(row["stability"] / 100.0)
        with col_c:
            st.caption(f"Memory {row['memory']}")
            st.progress(row["memory"] / 100.0)
            st.caption(f"Power {row['power']}")
            st.progress(row["power"] / 100.0)

st.divider()
st.subheader("Automatic Backend Upgrades")
st.caption("AIHub, JVC learning, brain, and SQL comprehension run automatically in the background.")
if "last_auto_upgrade_ts" not in st.session_state:
    st.session_state["last_auto_upgrade_ts"] = 0.0
if st.session_state["login_ok"]:
    now_ts = time.time()
    if now_ts - float(st.session_state["last_auto_upgrade_ts"]) >= 90.0:
        fleet_count = len(st.session_state["agents"])
        working_count = len([a for a in st.session_state["agents"] if str(a.get("fleet_mode", "")) == "working"])
        training_count = len([a for a in st.session_state["agents"] if str(a.get("fleet_mode", "")) == "training"])
        hybrid_count = len([a for a in st.session_state["agents"] if str(a.get("fleet_mode", "")) == "working+training"])
        aihub_ok, _ = _apply_aihub_upgrade(
            st.session_state["api_key"],
            specialty=f"ultimate-x-{x_tier}-auto-aihub",
            steps=520,
            candidates=220,
            sql_signal=0.96,
            internet_signal=0.70,
            llm_signal=llm_signal,
            stability_bias=0.94,
        )
        learn_ok, _ = _run_learning_sql_pulse(
            st.session_state["api_key"],
            specialty=f"ultimate-x-{x_tier}-auto-learning-sql",
            steps=500,
            candidates=220,
            sql_signal=max(0.95, sql_level / 100.0),
            internet_signal=0.86,
            llm_signal=llm_signal,
            stability_bias=0.93,
        )
        jvc_ok, _ = _run_learning_sql_pulse(
            st.session_state["api_key"],
            specialty=(
                f"jvc-learning-auto-fleets-{fleet_count}-working-{working_count}-"
                f"training-{training_count}-hybrid-{hybrid_count}"
            ),
            steps=520,
            candidates=max(180, min(240, 120 + (fleet_count * 4))),
            sql_signal=max(0.90, sql_level / 100.0),
            internet_signal=max(0.70, max_ram / 100.0),
            llm_signal=llm_signal,
            stability_bias=0.94,
        )
        st.session_state["last_auto_upgrade_ts"] = now_ts
        if aihub_ok and learn_ok and jvc_ok:
            st.success("Automatic backend upgrades completed (including JVC learning).")

st.divider()
st.subheader("Status")
if st.session_state["login_ok"]:
    st.success("Logged in and gateway reachable.")
elif st.session_state["last_error"]:
    st.warning(f"Not logged in: {st.session_state['last_error']}")
else:
    st.info("Not logged in yet.")
st.caption(f"UTC: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
