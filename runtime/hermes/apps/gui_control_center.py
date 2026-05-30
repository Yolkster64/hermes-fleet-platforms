import os
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


st.set_page_config(page_title="Hermes Simple GUI", layout="centered")
st.title("Hermes Simple GUI")
st.caption("Ultra-minimal login and gateway health check.")

if "api_key" not in st.session_state:
    st.session_state["api_key"] = _load_saved_key() or "local-hermes-ui-key"
if "login_ok" not in st.session_state:
    st.session_state["login_ok"] = False
if "last_error" not in st.session_state:
    st.session_state["last_error"] = ""
if "agents" not in st.session_state:
    st.session_state["agents"] = _load_agents()
if "backbones" not in st.session_state:
    st.session_state["backbones"] = _load_backbones()

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
st.subheader("Agents")
agent_name = st.text_input("Agent Name", value="ultimate-x")
agent_type = st.selectbox(
    "Agent Type",
    options=["ultimate-x", "hermes", "analyst", "builder", "optimizer", "deployer", "guardian"],
    index=0,
)
saved_agent_names = [str(a.get("name", "")).strip() for a in st.session_state["agents"] if str(a.get("name", "")).strip()]
deploy_target = st.selectbox("Select Saved Agent", options=["(new agent)"] + saved_agent_names, index=0)

st.subheader("Ultimate X Controls (X5 / X6)")
feature_options = [f"core-pack-{i:02d}" for i in range(1, 31)]
selected_packs = st.multiselect("30 Feature Packs", options=feature_options, default=feature_options[:8])
cxp, csb, ctr = st.columns(3)
with cxp:
    xp_boost = st.slider("XP Boost", 0, 100, 65)
with csb:
    saber_power = st.slider("SABR Power", 0, 100, 62)
with ctr:
    training_intensity = st.slider("Training Intensity", 60, 500, 180)

cbrain, caihub = st.columns(2)
with cbrain:
    brain_mode = st.selectbox("Brain Mode", options=["lite", "standard", "full-brain", "ultimate-x5", "ultimate-x6"], index=2)
with caihub:
    aihub_mode = st.selectbox("AIHub Mode", options=["off", "assist", "max"], index=2)
ultimate_x_tier = st.selectbox("Ultimate X Tier", options=["ultimate-x5", "ultimate-x6"], index=1)

st.subheader("Global Hermes Learning Core")
earlier_ultimate_bundle = st.toggle("Everything from earlier or better (Ultimate X bundle)", value=True)
universal_apply_all = st.toggle("Universal apply: Hermes -> X -> AIHub -> all LLMs", value=True)
carry_learning_all_agents = st.toggle("Carry learning to all agents", value=True)
hermes_learning_mode = st.selectbox("Hermes Learning Mode", options=["standard", "advanced", "ultimate"], index=2)
ai_mind_mode = st.selectbox("AI Mind + Brain Core", options=["balanced", "deep-mind", "ultimate-brain"], index=2)
dynamic_brain_learning = st.toggle("Dynamic Brain + Learning System", value=True)
llm_mesh = st.multiselect(
    "Ultimate AIHub LLM Mesh",
    options=["openai", "anthropic", "gemini", "mistral", "grok", "deepseek", "llama", "qwen"],
    default=["openai", "anthropic", "gemini", "deepseek"],
)

ccpu, cram, cgpu = st.columns(3)
with ccpu:
    max_cpu = st.slider("Max CPU %", 10, 100, 85)
with cram:
    max_ram = st.slider("Max RAM %", 10, 100, 82)
with cgpu:
    max_gpu = st.slider("Max GPU %", 10, 100, 90)
ultimate_sql_level = st.slider("Ultimate SQL Level", 0, 100, 88)
micro_count = st.slider("Microservices (toggleable amount)", 1, 64, 12)
micro_auto_scale = st.toggle("Auto-scale microservices", value=True)
specializations = st.multiselect(
    "Specializations",
    options=["reasoning", "coding", "sql", "deployment", "security", "ops", "vision", "research", "routing", "agent-swarm"],
    default=["reasoning", "coding", "deployment"],
)
micro_parallelism = st.slider("Agent Micro Parallelization", 1, 128, 24)
macro_parallelism = st.slider("Agent Macro Parallelization", 1, 64, 12)
agent_swarm_size = st.slider("Agent Swarm Size", 1, 256, 32)

with st.expander("Quick Guide", expanded=False):
    st.markdown(
        "1. Save API key and click Login.\n"
        "2. Create an agent (or select a saved one).\n"
        "3. Pick packs/modes/sliders.\n"
        "4. Click Deploy Agent."
    )
with st.expander("Deep Guide: Hermes Types, X Forms, Hybrid, and 4 Models", expanded=False):
    st.markdown(
        "**Hermes Types**\n"
        "- `hermes`: Balanced default for stable general orchestration.\n"
        "- `ultimate-x`: Max-performance track for cross-agent learning and deployment speed.\n"
        "- `analyst`: Higher signal quality and slower, more precise reasoning.\n"
        "- `builder`: Build/ship biased; stronger deployment cadence.\n"
        "- `optimizer`: Efficiency/perf tuning and adaptive training focus.\n"
        "- `guardian`: Safety-first with higher stability bias.\n\n"
        "**X Variants (Ultimate X Forms)**\n"
        "- `ultimate-x5`: Fast, aggressive upgrade profile.\n"
        "- `ultimate-x6`: Maximum depth profile with highest learning carry-over.\n\n"
        "**Hybrid Forms**\n"
        "- `hybrid-analyst-builder`: Insight + ship speed\n"
        "- `hybrid-optimizer-guardian`: Performance + safety\n"
        "- `hybrid-x6-hermes`: Ultimate + balanced control\n\n"
        "**4 Model Profiles**\n"
        "| Model | Best For | Strength |\n"
        "|---|---|---|\n"
        "| Model-1 Core | Daily orchestration | Stability |\n"
        "| Model-2 Hybrid | Mixed workloads | Flexibility |\n"
        "| Model-3 X5 | Fast scaling/deploy | Throughput |\n"
        "| Model-4 X6 Ultimate | Deep learning + AIHub mesh | Maximum capability |\n\n"
        "**How to use**\n"
        "1. Pick Agent Type and Ultimate X Tier.\n"
        "2. Enable Ultimate X bundle for full legacy-max behavior.\n"
        "3. Use AIHub mesh + Learning/SQL pulse.\n"
        "4. Run `Run Ultimate Everything Now` for full backend execution."
    )
with st.expander("Mix & Match Guide (Presets, Hints, Best Starting Practices)", expanded=False):
    st.markdown(
        "**Quick Mix Presets**\n"
        "- `fast-launch`: Type `builder`, brain `ultimate-x5`, microservices `8-16`\n"
        "- `deep-research`: Type `analyst`, brain `ultimate-x6`, microservices `16-32`\n"
        "- `safe-production`: Type `guardian`, brain `full-brain`, microservices `12-24`\n"
        "- `balanced-hybrid`: Type `hermes` + hybrid form, microservices `10-20`\n\n"
        "**Best Starting Practices**\n"
        "1. Start with `hermes` or `ultimate-x5` first, not max-everything.\n"
        "2. Keep microservices at `12` initially and scale after one healthy deploy.\n"
        "3. Enable AIHub mesh with 3-4 LLMs first, then expand.\n"
        "4. Run `Ultimate Learning + SQL Pulse` before `Ultimate Everything`.\n"
        "5. Save a backbone profile for each workload (fast, safe, deep).\n\n"
        "**Hints**\n"
        "- Higher GPU + AIHub mesh = better LLM throughput.\n"
        "- Higher SQL level helps memory/recall but can raise latency.\n"
        "- `ultimate-x6` is strongest for deep learning carry-over across agents."
    )

b1, b2 = st.columns(2)
with b1:
    backbone_name = st.text_input("Backbone Profile Name", value="ultimate-core")
with b2:
    backbone_choices = ["(none)"] + [str(b.get("name", "")).strip() for b in st.session_state["backbones"] if str(b.get("name", "")).strip()]
    selected_backbone = st.selectbox("Saved Backbone", options=backbone_choices, index=0)

bb1, bb2 = st.columns(2)
with bb1:
    if st.button("Save Backbone", use_container_width=True):
        name = backbone_name.strip()
        if not name:
            st.error("Backbone profile name is empty.")
        else:
            profile = {
                "name": name,
                "brain_mode": brain_mode,
                "aihub_mode": aihub_mode,
                "hermes_learning_mode": hermes_learning_mode,
                "dynamic_brain_learning": dynamic_brain_learning,
                "carry_learning_all_agents": carry_learning_all_agents,
                "llm_mesh": llm_mesh,
                "xp_boost": xp_boost,
                "saber_power": saber_power,
                "training_intensity": training_intensity,
                "selected_packs": selected_packs,
                "micro_count": micro_count,
                "micro_auto_scale": micro_auto_scale,
                "specializations": specializations,
                "micro_parallelism": micro_parallelism,
                "macro_parallelism": macro_parallelism,
                "agent_swarm_size": agent_swarm_size,
                "max_cpu": max_cpu,
                "max_ram": max_ram,
                "max_gpu": max_gpu,
                "updated_utc": datetime.now(timezone.utc).isoformat(),
            }
            backbones = [b for b in st.session_state["backbones"] if b.get("name") != name]
            backbones.append(profile)
            st.session_state["backbones"] = backbones
            saved, save_err = _save_backbones(backbones)
            if saved:
                st.success(f"Backbone saved: {name}")
            else:
                st.error(f"Backbone saved in session, but file save failed: {save_err}")
with bb2:
    if st.button("Apply Backbone", use_container_width=True):
        if selected_backbone == "(none)":
            st.warning("Select a saved backbone first.")
        else:
            st.success(f"Backbone selected: {selected_backbone}")

a1, a2 = st.columns(2)
with a1:
    if st.button("Create Agent", use_container_width=True):
        name = agent_name.strip()
        if not name:
            st.error("Agent name is empty.")
        else:
            agents = [a for a in st.session_state["agents"] if a.get("name") != name]
            agents.append(
                {
                    "name": name,
                    "type": agent_type,
                    "brain_mode": brain_mode,
                    "aihub_mode": aihub_mode,
                    "hermes_learning_mode": hermes_learning_mode,
                    "dynamic_brain_learning": dynamic_brain_learning,
                    "carry_learning_all_agents": carry_learning_all_agents,
                    "llm_mesh": llm_mesh,
                    "xp_boost": xp_boost,
                    "saber_power": saber_power,
                    "feature_packs": len(selected_packs),
                    "micro_count": micro_count,
                    "micro_auto_scale": micro_auto_scale,
                    "specializations": specializations,
                    "micro_parallelism": micro_parallelism,
                    "macro_parallelism": macro_parallelism,
                    "agent_swarm_size": agent_swarm_size,
                    "max_cpu": max_cpu,
                    "max_ram": max_ram,
                    "max_gpu": max_gpu,
                    "created_utc": datetime.now(timezone.utc).isoformat(),
                }
            )
            st.session_state["agents"] = agents
            saved, save_err = _save_agents(agents)
            if saved:
                st.success(f"Created agent: {name} ({agent_type})")
            else:
                st.error(f"Agent created in session, but save failed: {save_err}")
with a2:
    if st.button("Deploy Agent", use_container_width=True):
        if not st.session_state["login_ok"]:
            st.error("Log in first, then deploy.")
        else:
            backbone = None
            if selected_backbone != "(none)":
                backbone = next((b for b in st.session_state["backbones"] if b.get("name") == selected_backbone), None)
            target_name = deploy_target if deploy_target != "(new agent)" else (agent_name.strip() or "hermes-agent")
            active_brain = str((backbone or {}).get("brain_mode", brain_mode))
            active_aihub = str((backbone or {}).get("aihub_mode", aihub_mode))
            active_learning_mode = str((backbone or {}).get("hermes_learning_mode", hermes_learning_mode))
            active_dynamic = bool((backbone or {}).get("dynamic_brain_learning", dynamic_brain_learning))
            active_learning_share = bool((backbone or {}).get("carry_learning_all_agents", carry_learning_all_agents))
            active_llm_mesh = (backbone or {}).get("llm_mesh", llm_mesh)
            active_training = int((backbone or {}).get("training_intensity", training_intensity))
            active_packs = (backbone or {}).get("selected_packs", selected_packs)
            active_micro_count = int((backbone or {}).get("micro_count", micro_count))
            active_micro_auto = bool((backbone or {}).get("micro_auto_scale", micro_auto_scale))
            active_specializations = (backbone or {}).get("specializations", specializations)
            active_micro_parallel = int((backbone or {}).get("micro_parallelism", micro_parallelism))
            active_macro_parallel = int((backbone or {}).get("macro_parallelism", macro_parallelism))
            active_swarm = int((backbone or {}).get("agent_swarm_size", agent_swarm_size))
            active_cpu = int((backbone or {}).get("max_cpu", max_cpu))
            active_ram = int((backbone or {}).get("max_ram", max_ram))
            active_gpu = int((backbone or {}).get("max_gpu", max_gpu))
            active_xp = int((backbone or {}).get("xp_boost", xp_boost))
            active_saber = int((backbone or {}).get("saber_power", saber_power))

            if earlier_ultimate_bundle:
                active_brain = ultimate_x_tier
                active_aihub = "max"
                active_learning_mode = "ultimate"
                active_learning_share = True
                active_llm_mesh = ["openai", "anthropic", "gemini", "mistral", "grok", "deepseek", "llama", "qwen"]
                active_training = max(420, active_training)
                active_micro_count = max(32, active_micro_count)
                active_micro_auto = True
                active_micro_parallel = max(96, active_micro_parallel)
                active_macro_parallel = max(32, active_macro_parallel)
                active_swarm = max(128, active_swarm)
                active_cpu = max(95, active_cpu)
                active_ram = max(92, active_ram)
                active_gpu = max(98, active_gpu)
                active_xp = max(95, active_xp)
                active_saber = max(95, active_saber)

            if universal_apply_all:
                active_learning_share = True
                active_aihub = "max"
                active_llm_mesh = ["openai", "anthropic", "gemini", "mistral", "grok", "deepseek", "llama", "qwen"]
                active_dynamic = True
                active_micro_parallel = max(96, active_micro_parallel)
                active_macro_parallel = max(32, active_macro_parallel)
                active_swarm = max(128, active_swarm)

            pack_count = len(active_packs) if isinstance(active_packs, list) else len(selected_packs)
            if earlier_ultimate_bundle:
                pack_count = 30

            mesh_suffix = "+".join(active_llm_mesh[:3]) if isinstance(active_llm_mesh, list) and active_llm_mesh else "default-mesh"
            share_suffix = "shared" if active_learning_share else "solo"
            micro_suffix = f"m{active_micro_count}-{'auto' if active_micro_auto else 'manual'}"
            spec_suffix = "+".join(active_specializations[:3]) if isinstance(active_specializations, list) and active_specializations else "general"
            parallel_suffix = f"pmi{active_micro_parallel}-pma{active_macro_parallel}-sw{active_swarm}"
            specialty = f"{agent_type}-{active_brain}-{active_aihub}-{active_learning_mode}-{share_suffix}-{mesh_suffix}-{micro_suffix}-{spec_suffix}-{parallel_suffix}"
            specialty = f"{specialty}-{ai_mind_mode}"
            if active_dynamic:
                specialty = f"{specialty}-dynamic"
            if universal_apply_all:
                specialty = f"{specialty}-universal"
            steps = max(60, int(active_training))
            if active_dynamic:
                steps = min(560, steps + 60)
            candidates = max(40, min(240, max(pack_count * 8, active_micro_count * 4, active_swarm)))
            sql_signal = max(0.4, min(1.0, active_cpu / 100.0))
            internet_signal = max(0.3, min(1.0, active_ram / 100.0))
            llm_signal = max(0.4, min(1.0, active_gpu / 100.0))
            stability_bias = max(0.4, min(1.0, ((active_xp + active_saber) / 2) / 100.0))
            ok, err = _deploy_agent(
                st.session_state["api_key"],
                specialty=specialty,
                steps=steps,
                candidates=candidates,
                sql_signal=sql_signal,
                internet_signal=internet_signal,
                llm_signal=llm_signal,
                stability_bias=stability_bias,
            )
            if ok:
                source = selected_backbone if selected_backbone != "(none)" else "live sliders"
                st.success(f"Deploy triggered for {target_name} ({specialty}) using {source}.")
            else:
                st.error(f"Deploy failed: {err}")

px1, px2 = st.columns(2)
with px1:
    if st.button("Create Next Ultimate X5", use_container_width=True):
        name = "ultimate-x5"
        agents = [a for a in st.session_state["agents"] if a.get("name") != name]
        agents.append(
            {
                "name": name,
                "type": "ultimate-x",
                "brain_mode": "ultimate-x5",
                "aihub_mode": "max",
                "hermes_learning_mode": "ultimate",
                "carry_learning_all_agents": True,
                "llm_mesh": ["openai", "anthropic", "gemini", "deepseek"],
                "xp_boost": 95,
                "saber_power": 95,
                "feature_packs": 30,
                "max_cpu": 95,
                "max_ram": 92,
                "max_gpu": 98,
                "created_utc": datetime.now(timezone.utc).isoformat(),
            }
        )
        st.session_state["agents"] = agents
        saved, save_err = _save_agents(agents)
        if saved:
            st.success("Created next preset agent: ultimate-x5")
        else:
            st.error(f"Created in session, but save failed: {save_err}")
with px2:
    if st.button("Create Next Ultimate X6", use_container_width=True):
        name = "ultimate-x6"
        agents = [a for a in st.session_state["agents"] if a.get("name") != name]
        agents.append(
            {
                "name": name,
                "type": "ultimate-x",
                "brain_mode": "ultimate-x6",
                "aihub_mode": "max",
                "hermes_learning_mode": "ultimate",
                "carry_learning_all_agents": True,
                "llm_mesh": ["openai", "anthropic", "gemini", "mistral", "grok", "deepseek", "llama", "qwen"],
                "xp_boost": 98,
                "saber_power": 98,
                "feature_packs": 30,
                "max_cpu": 98,
                "max_ram": 95,
                "max_gpu": 99,
                "created_utc": datetime.now(timezone.utc).isoformat(),
            }
        )
        st.session_state["agents"] = agents
        saved, save_err = _save_agents(agents)
        if saved:
            st.success("Created next preset agent: ultimate-x6")
        else:
            st.error(f"Created in session, but save failed: {save_err}")

st.divider()
st.subheader("AIHub Upgrade")
if st.button("Apply Ultimate AIHub for All Agents", use_container_width=True):
    if not st.session_state["login_ok"]:
        st.error("Log in first, then apply AIHub upgrade.")
    else:
        if earlier_ultimate_bundle:
            llm_factor = 0.99
            aihub_steps = max(520, training_intensity)
            aihub_candidates = 240
            aihub_specialty = "global-aihub-ultimate-earlier"
        else:
            llm_factor = min(0.99, max(0.60, 0.60 + (0.04 * len(llm_mesh))))
            aihub_steps = max(300, training_intensity)
            aihub_candidates = max(120, len(selected_packs) * 12)
            aihub_specialty = f"global-aihub-{hermes_learning_mode}"
        if universal_apply_all:
            llm_factor = 0.99
            aihub_specialty = f"{aihub_specialty}-universal-all"
        ok, err = _apply_aihub_upgrade(
            st.session_state["api_key"],
            specialty=aihub_specialty,
            steps=aihub_steps,
            candidates=aihub_candidates,
            sql_signal=max(0.75, max_cpu / 100.0),
            internet_signal=max(0.12, min(0.60, max_ram / 100.0)),
            llm_signal=llm_factor,
            stability_bias=max(0.72, ((xp_boost + saber_power) / 2) / 100.0),
        )
        if ok:
            st.success("Ultimate AIHub upgrade applied.")
        else:
            st.error(f"AIHub upgrade failed: {err}")

st.divider()
st.subheader("Ultimate Learning + Ultimate AIHub + LLMs")
if st.button("Run Ultimate Learning + AIHub + LLMs", use_container_width=True):
    if not st.session_state["login_ok"]:
        st.error("Log in first, then run this ultimate flow.")
    else:
        llm_factor = min(0.99, max(0.75, 0.60 + (0.04 * len(llm_mesh))))
        if earlier_ultimate_bundle:
            llm_factor = 0.99
        flow_specialty = f"ultimate-learning-aihub-llms-{ultimate_x_tier}-{ai_mind_mode}"
        if universal_apply_all:
            flow_specialty = f"{flow_specialty}-universal-all"
        aihub_ok, aihub_err = _apply_aihub_upgrade(
            st.session_state["api_key"],
            specialty=f"{flow_specialty}-aihub",
            steps=max(420, training_intensity),
            candidates=max(180, len(selected_packs) * 10),
            sql_signal=max(0.88, max_cpu / 100.0),
            internet_signal=max(0.40, min(1.0, max_ram / 100.0)),
            llm_signal=llm_factor,
            stability_bias=max(0.84, ((xp_boost + saber_power) / 2) / 100.0),
        )
        learn_ok, learn_err = _run_learning_sql_pulse(
            st.session_state["api_key"],
            specialty=f"{flow_specialty}-learning",
            steps=max(420, training_intensity),
            candidates=max(180, len(selected_packs) * 10),
            sql_signal=max(0.88, ultimate_sql_level / 100.0),
            internet_signal=max(0.40, min(1.0, max_ram / 100.0)),
            llm_signal=llm_factor,
            stability_bias=max(0.84, ((xp_boost + saber_power) / 2) / 100.0),
        )
        if aihub_ok and learn_ok:
            st.success("Ultimate learning + AIHub + LLMs completed.")
        else:
            if not aihub_ok:
                st.error(f"Ultimate AIHub phase failed: {aihub_err}")
            if not learn_ok:
                st.error(f"Ultimate learning phase failed: {learn_err}")

st.divider()
st.subheader("Brain Ultimate AI Upgrading")
if st.button("Run Brain Ultimate AI Upgrading", use_container_width=True):
    if not st.session_state["login_ok"]:
        st.error("Log in first, then run brain upgrade.")
    else:
        brain_upgrade_specialty = f"brain-ultimate-{ultimate_x_tier}-{ai_mind_mode}"
        if universal_apply_all:
            brain_upgrade_specialty = f"{brain_upgrade_specialty}-universal-all"
        aihub_ok, aihub_err = _apply_aihub_upgrade(
            st.session_state["api_key"],
            specialty=f"{brain_upgrade_specialty}-aihub",
            steps=540,
            candidates=220,
            sql_signal=0.96,
            internet_signal=0.55,
            llm_signal=0.99,
            stability_bias=0.95,
        )
        pulse_ok, pulse_err = _run_learning_sql_pulse(
            st.session_state["api_key"],
            specialty=f"{brain_upgrade_specialty}-learning",
            steps=520,
            candidates=220,
            sql_signal=0.95,
            internet_signal=0.90,
            llm_signal=0.99,
            stability_bias=0.94,
        )
        if aihub_ok and pulse_ok:
            st.success("Brain Ultimate AI upgrading completed.")
        else:
            if not aihub_ok:
                st.error(f"Brain AIHub phase failed: {aihub_err}")
            if not pulse_ok:
                st.error(f"Brain learning phase failed: {pulse_err}")

st.divider()
st.subheader("Ultimate Learning + SQL")
if st.button("Run Ultimate Learning + SQL Pulse", use_container_width=True):
    if not st.session_state["login_ok"]:
        st.error("Log in first, then run learning pulse.")
    else:
        sql_signal = max(0.60, min(1.0, ultimate_sql_level / 100.0))
        llm_factor = min(0.99, max(0.60, 0.60 + (0.04 * len(llm_mesh))))
        if earlier_ultimate_bundle:
            sql_signal = max(sql_signal, 0.95)
            llm_factor = 0.99
        ok, err = _run_learning_sql_pulse(
            st.session_state["api_key"],
            specialty=f"ultimate-learning-sql-{ai_mind_mode}{'-universal-all' if universal_apply_all else ''}",
            steps=max(280, training_intensity),
            candidates=max(120, len(selected_packs) * 10),
            sql_signal=sql_signal,
            internet_signal=max(0.35, min(1.0, max_ram / 100.0)),
            llm_signal=llm_factor,
            stability_bias=max(0.70, ((xp_boost + saber_power) / 2) / 100.0),
        )
        if ok:
            st.success("Ultimate learning + SQL pulse triggered.")
        else:
            st.error(f"Learning pulse failed: {err}")

st.divider()
st.subheader("Ultimate Everything (Backend Only)")
st.caption("Runs all earlier capabilities (or better): ultimate AIHub/LLMs + ultimate brain/learning/sql + ultimate deployment, while keeping GUI simple.")
u1, u2 = st.columns(2)
with u1:
    run_ultimate_all = st.button("Run Ultimate Everything Now", use_container_width=True)
with u2:
    run_ultimate_alias = st.button("Run Ultimate Upgrade (All Similar Features)", use_container_width=True)
if run_ultimate_all or run_ultimate_alias:
    if not st.session_state["login_ok"]:
        st.error("Log in first, then run Ultimate Everything.")
    else:
        backend_specialty = f"ultimate-everything-{ultimate_x_tier}-{ai_mind_mode}"
        if universal_apply_all:
            backend_specialty = f"{backend_specialty}-universal-all"
        aihub_ok, aihub_err = _apply_aihub_upgrade(
            st.session_state["api_key"],
            specialty=f"{backend_specialty}-aihub",
            steps=560,
            candidates=240,
            sql_signal=0.98,
            internet_signal=0.55,
            llm_signal=0.99,
            stability_bias=0.96,
        )
        learning_ok, learning_err = _run_learning_sql_pulse(
            st.session_state["api_key"],
            specialty=f"{backend_specialty}-learning-sql",
            steps=540,
            candidates=240,
            sql_signal=0.98,
            internet_signal=0.92,
            llm_signal=0.99,
            stability_bias=0.95,
        )
        deploy_ok, deploy_err = _deploy_agent(
            st.session_state["api_key"],
            specialty=f"{backend_specialty}-deploy",
            steps=560,
            candidates=240,
            sql_signal=0.98,
            internet_signal=0.92,
            llm_signal=0.99,
            stability_bias=0.96,
        )
        if aihub_ok and learning_ok and deploy_ok:
            st.success("Ultimate Everything completed for backend systems.")
        else:
            if not aihub_ok:
                st.error(f"Ultimate AIHub failed: {aihub_err}")
            if not learning_ok:
                st.error(f"Ultimate learning/sql failed: {learning_err}")
            if not deploy_ok:
                st.error(f"Ultimate deployment failed: {deploy_err}")

if st.session_state["agents"]:
    st.caption(f"Agents created: {len(st.session_state['agents'])}")
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
