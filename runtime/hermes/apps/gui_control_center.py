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
agent_name = st.text_input("Agent Name", value="hermes-agent-1")
agent_type = st.selectbox(
    "Agent Type",
    options=["hermes", "analyst", "builder", "optimizer", "deployer", "guardian"],
    index=0,
)
saved_agent_names = [str(a.get("name", "")).strip() for a in st.session_state["agents"] if str(a.get("name", "")).strip()]
deploy_target = st.selectbox("Select Saved Agent", options=["(new agent)"] + saved_agent_names, index=0)

st.subheader("Ultimate X5/X6 Controls")
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
    brain_mode = st.selectbox("Brain Mode", options=["lite", "standard", "full-brain", "x5-ultimate", "x6"], index=2)
with caihub:
    aihub_mode = st.selectbox("AIHub Mode", options=["off", "assist", "max"], index=2)

ccpu, cram, cgpu = st.columns(3)
with ccpu:
    max_cpu = st.slider("Max CPU %", 10, 100, 85)
with cram:
    max_ram = st.slider("Max RAM %", 10, 100, 82)
with cgpu:
    max_gpu = st.slider("Max GPU %", 10, 100, 90)

with st.expander("Quick Guide", expanded=False):
    st.markdown(
        "1. Save API key and click Login.\n"
        "2. Create an agent (or select a saved one).\n"
        "3. Pick packs/modes/sliders.\n"
        "4. Click Deploy Agent."
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
                "xp_boost": xp_boost,
                "saber_power": saber_power,
                "training_intensity": training_intensity,
                "selected_packs": selected_packs,
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
                    "xp_boost": xp_boost,
                    "saber_power": saber_power,
                    "feature_packs": len(selected_packs),
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
            active_training = int((backbone or {}).get("training_intensity", training_intensity))
            active_packs = (backbone or {}).get("selected_packs", selected_packs)
            active_cpu = int((backbone or {}).get("max_cpu", max_cpu))
            active_ram = int((backbone or {}).get("max_ram", max_ram))
            active_gpu = int((backbone or {}).get("max_gpu", max_gpu))
            active_xp = int((backbone or {}).get("xp_boost", xp_boost))
            active_saber = int((backbone or {}).get("saber_power", saber_power))
            pack_count = len(active_packs) if isinstance(active_packs, list) else len(selected_packs)

            specialty = f"{agent_type}-{active_brain}-{active_aihub}"
            steps = max(60, int(active_training))
            candidates = max(40, min(240, pack_count * 8))
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
