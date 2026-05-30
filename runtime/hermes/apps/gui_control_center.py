import os
import time
from datetime import datetime, timezone
from pathlib import Path

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
st.caption("Simple mode: Ultimate X only, fewer choices, fast deploy.")

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
st.subheader("Ultimate X Agent")
agent_name = st.text_input("Agent Name", value="ultimate-x")
setup_combo = st.selectbox(
    "Setup Combo",
    options=[
        "Nova Starter - simple daily driver",
        "Velocity Forge - fastest ship path",
        "DeepSight Scholar - strongest analysis + SQL",
        "Aegis Guardian - safest production setup",
        "Titan Mesh Max - highest overall power",
    ],
    index=0,
)
combo_defaults = {
    "Nova Starter - simple daily driver": {
        "hermes_type": "Hermes",
        "variation": "Normal",
        "x_choice": "Ultimate X (auto choose)",
        "profile": "balanced",
        "subagents": ["planner", "coder", "deployer"],
    },
    "Velocity Forge - fastest ship path": {
        "hermes_type": "Hermes",
        "variation": "Hybrid",
        "x_choice": "Ultimate X5",
        "profile": "rapid-deploy",
        "subagents": ["planner", "coder", "deployer", "observer"],
    },
    "DeepSight Scholar - strongest analysis + SQL": {
        "hermes_type": "Ultimate X",
        "variation": "Deep Thinker",
        "x_choice": "Ultimate X6",
        "profile": "deep-analysis",
        "subagents": ["planner", "researcher", "sql-engineer", "observer"],
    },
    "Aegis Guardian - safest production setup": {
        "hermes_type": "Ultimate X",
        "variation": "Mesh",
        "x_choice": "Ultimate X6",
        "profile": "safe-production",
        "subagents": ["planner", "guardian", "deployer", "observer"],
    },
    "Titan Mesh Max - highest overall power": {
        "hermes_type": "Ultimate X",
        "variation": "Mesh",
        "x_choice": "Ultimate X6",
        "profile": "balanced",
        "subagents": ["planner", "researcher", "coder", "sql-engineer", "deployer"],
    },
}
combo = combo_defaults[setup_combo]
hermes_type_options = ["Hermes", "Ultimate X"]
variation_options = ["Normal", "Hybrid", "Mesh", "Deep Thinker"]
x_options = ["Ultimate X (auto choose)", "Ultimate X5", "Ultimate X6"]
profile_options = ["balanced", "deep-analysis", "rapid-deploy", "safe-production"]
hermes_type = st.selectbox("Hermes Type", options=hermes_type_options, index=hermes_type_options.index(combo["hermes_type"]))
hermes_variation = st.selectbox("Hermes Variation", options=variation_options, index=variation_options.index(combo["variation"]))
x_choice = st.selectbox("X Family", options=x_options, index=x_options.index(combo["x_choice"]))
profile = st.selectbox("Profile", options=profile_options, index=profile_options.index(combo["profile"]))
subagents = st.multiselect(
    "Subagents",
    options=["planner", "researcher", "coder", "sql-engineer", "deployer", "guardian", "observer"],
    default=combo["subagents"],
)
deploy_mode = st.selectbox("Deploy", options=["single-agent", "deploy-10-agents"], index=0)
saved_agent_names = [str(a.get("name", "")).strip() for a in st.session_state["agents"] if str(a.get("name", "")).strip()]
deploy_10 = st.multiselect("Choose up to 10 agents", options=saved_agent_names, default=saved_agent_names[:10], max_selections=10)
resource_policy = st.selectbox("System Resource Policy", options=["Recommended Max", "Custom"], index=0)
if resource_policy == "Recommended Max":
    max_cpu = 99
    max_gpu = 99
    max_ram = 97
    tsm = 96
    st.caption("Recommended max system attributes applied: CPU 99, GPU 99, RAM 97, TSM 96.")
else:
    c_cpu, c_gpu = st.columns(2)
    with c_cpu:
        max_cpu = st.slider("Max CPU", 50, 100, 92)
    with c_gpu:
        max_gpu = st.slider("Max GPU", 50, 100, 94)
    c_ram, c_tsm = st.columns(2)
    with c_ram:
        max_ram = st.slider("Max RAM", 50, 100, 90)
    with c_tsm:
        tsm = st.slider("TSM", 50, 100, 90)

profile_map = {
    "balanced": {"xp": 78, "sql": 82, "steps": 240, "candidates": 130, "stability": 0.86},
    "deep-analysis": {"xp": 90, "sql": 96, "steps": 380, "candidates": 180, "stability": 0.90},
    "rapid-deploy": {"xp": 84, "sql": 76, "steps": 220, "candidates": 200, "stability": 0.82},
    "safe-production": {"xp": 80, "sql": 88, "steps": 260, "candidates": 150, "stability": 0.94},
}
p = profile_map[profile]
if x_choice == "Ultimate X5":
    x_tier = "ultimate-x5"
elif x_choice == "Ultimate X6":
    x_tier = "ultimate-x6"
else:
    x_tier = "ultimate-x6" if profile in {"deep-analysis", "safe-production"} else "ultimate-x5"
xp_boost = 98 if x_tier == "ultimate-x6" else p["xp"]
sql_level = 97 if x_tier == "ultimate-x6" else p["sql"]
steps = min(560, p["steps"] + (70 if x_tier == "ultimate-x6" else 35))
candidates = min(240, p["candidates"] + (35 if x_tier == "ultimate-x6" else 20))
llm_mesh = ["openai", "anthropic", "gemini", "mistral", "deepseek", "llama", "qwen"]
llm_signal = _llm_optimization_factor(
    mesh_size=len(llm_mesh),
    cost_bias=12,
    power_bias=98,
    perf_bias=98,
    profile="throughput-max",
    force_ultimate=True,
)
llm_signal = min(0.99, llm_signal + ((max_gpu - 85) / 1000.0))

st.progress(int(xp_boost) / 100.0)
st.caption(f"XP: {int(xp_boost)} | SQL data: {int(sql_level)} | LLM mode: automatic ultimate")
st.caption(f"Resolved tier: **{x_tier}** (auto-picked from your profile when using 'Ultimate X (auto choose)').")
st.caption(f"Combo: **{setup_combo}**")

if st.button("Save + Deploy", use_container_width=True):
    if not st.session_state["login_ok"]:
        st.error("Log in first, then deploy.")
    else:
        chosen = agent_name.strip() or "ultimate-x"
        agents = [a for a in st.session_state["agents"] if a.get("name") != chosen]
        agents.append(
            {
                "name": chosen,
                "type": hermes_type,
                "variation": hermes_variation,
                "tier": x_tier,
                "profile": profile,
                "subagents": subagents,
                "setup_combo": setup_combo,
                "xp_boost": xp_boost,
                "sql_level": sql_level,
                "max_cpu": max_cpu,
                "max_gpu": max_gpu,
                "max_ram": max_ram,
                "tsm": tsm,
                "created_utc": datetime.now(timezone.utc).isoformat(),
            }
        )
        st.session_state["agents"] = agents
        saved, save_err = _save_agents(agents)
        if not saved:
            st.error(f"Save failed: {save_err}")
        targets = deploy_10[:10] if deploy_mode == "deploy-10-agents" else [chosen]
        if not targets:
            targets = [chosen]
        ok_count = 0
        for target in targets:
            ok, _err = _deploy_agent(
                st.session_state["api_key"],
                specialty=(
                    f"{hermes_type.lower().replace(' ', '-')}-{hermes_variation.lower().replace(' ', '-')}-"
                    f"{x_tier}-{profile}-combo-{setup_combo.lower().replace(' ', '-').replace('+', 'plus')}"
                    f"-subs-{'-'.join(subagents[:4]) or 'default'}"
                    f"-cpu{max_cpu}-gpu{max_gpu}-ram{max_ram}-tsm{tsm}-agent-{target}"
                ),
                steps=min(560, steps + int(tsm / 8)),
                candidates=min(240, candidates + int(max_gpu / 6)),
                sql_signal=max(0.70, sql_level / 100.0),
                internet_signal=max(0.60, max_ram / 100.0),
                llm_signal=llm_signal,
                stability_bias=min(0.99, p["stability"] + (tsm / 1000.0)),
            )
            if ok:
                ok_count += 1
        if ok_count == len(targets):
            st.success(f"Saved and deployed {ok_count} agent(s).")
        else:
            st.warning(f"Partial deploy success: {ok_count}/{len(targets)}")

st.divider()
st.subheader("Automatic Backend Upgrades")
st.caption("AIHub, learning, brain, and SQL comprehension run automatically in the background.")
if "last_auto_upgrade_ts" not in st.session_state:
    st.session_state["last_auto_upgrade_ts"] = 0.0
if st.session_state["login_ok"]:
    now_ts = time.time()
    if now_ts - float(st.session_state["last_auto_upgrade_ts"]) >= 90.0:
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
        st.session_state["last_auto_upgrade_ts"] = now_ts
        if aihub_ok and learn_ok:
            st.success("Automatic backend upgrades completed.")

with st.expander("Deep Guide: what to pick", expanded=False):
    st.markdown(
        "**What is Ultimate X vs X5 vs X6?**\n"
        "- `Ultimate X` means the family; if you choose **auto**, the app picks X5 or X6 for you.\n"
        "- `Ultimate X5` is faster and lighter (good for speed/deploy).\n"
        "- `Ultimate X6` is deeper and stronger (good for learning/safety/analysis).\n\n"
        "**Detailed combo names and best use:**\n"
        "- `Nova Starter - simple daily driver`: easiest default.\n"
        "- `Velocity Forge - fastest ship path`: fastest deploy loop.\n"
        "- `DeepSight Scholar - strongest analysis + SQL`: best for data-heavy reasoning.\n"
        "- `Aegis Guardian - safest production setup`: strongest safety/stability profile.\n"
        "- `Titan Mesh Max - highest overall power`: max capability setup.\n\n"
        "**Who to pick for what:**\n"
        "- Need fastest shipping: `Velocity Forge`.\n"
        "- Need deep reasoning/SQL: `DeepSight Scholar`.\n"
        "- Need safest production: `Aegis Guardian`.\n"
        "- Need daily default: `Nova Starter`.\n"
        "- Need maximum power: `Titan Mesh Max`.\n\n"
        "**Subagent presets:**\n"
        "- `planner + coder + deployer`: build and ship.\n"
        "- `planner + researcher + sql-engineer`: analysis and data comprehension.\n"
        "- `planner + guardian + deployer`: stable production.\n\n"
        "**System attributes (few choices):**\n"
        "- Keep `System Resource Policy = Recommended Max` for auto CPU/GPU/RAM/TSM high-performance values.\n"
        "- Use `Custom` only when you need to cap resources.\n\n"
        "**Simple steps:**\n"
        "1. Pick a Setup Combo.\n"
        "2. Keep Resource Policy on Recommended Max.\n"
        "3. Adjust subagents only if needed.\n"
        "4. Keep X Family on auto unless you need forced X5/X6.\n"
        "5. Click Save + Deploy."
    )

if st.session_state["agents"]:
    st.caption(f"Saved agents: {len(st.session_state['agents'])}")
    st.dataframe(st.session_state["agents"], use_container_width=True, hide_index=True)

st.divider()
st.subheader("Status")
if st.session_state["login_ok"]:
    st.success("Logged in and gateway reachable.")
elif st.session_state["last_error"]:
    st.warning(f"Not logged in: {st.session_state['last_error']}")
else:
    st.info("Not logged in yet.")
st.caption(f"UTC: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
