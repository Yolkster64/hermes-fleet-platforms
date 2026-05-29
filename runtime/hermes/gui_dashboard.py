import json
import os
from typing import Any, Dict, Tuple

import requests
import streamlit as st

API_BASE = os.getenv("HERMES_API_BASE_URL", "http://localhost:8788")
DEFAULT_API_KEY = os.getenv("HERMES_GUI_API_KEY", "local-hermes-ui-key")


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
    try:
        return api_post(path, payload=payload, timeout=timeout), ""
    except Exception as exc:  # pragma: no cover
        return {}, str(exc)


def log_text(label: str, payload: Dict[str, Any]) -> None:
    st.session_state.setdefault("logs", [])
    st.session_state["logs"].insert(0, {"label": label, "payload": payload})
    st.session_state["logs"] = st.session_state["logs"][:20]


def run_auto_cycle(max_mode: bool) -> Dict[str, Any]:
    steps = 2200 if max_mode else 600
    candidates = 480 if max_mode else 160
    sim_steps = 2000 if max_mode else 500

    simulate, sim_err = safe_post("/simulate", {"specialty": "fleet", "steps": sim_steps})
    pulse, pulse_err = safe_post(
        "/learning-pulse",
        {"specialty": "fleet", "steps": steps, "candidates": candidates, "sql_signal": 0.86, "internet_signal": 0.72, "llm_signal": 0.90, "stability_bias": 0.83},
        timeout=140,
    )
    optimize, opt_err = safe_post("/optimize-fleet", {"specialty": "fleet", "candidates": candidates}, timeout=120)
    curate, curate_err = safe_post("/curate-learning", {"sql_signal": 0.86, "internet_signal": 0.72, "llm_signal": 0.90, "stability_bias": 0.83}, timeout=90)
    dedupe, dedupe_err = safe_post("/dedupe-optimize", {"roots": ["core", "runtime", "src"], "max_file_mb": 8}, timeout=120)
    return {
        "simulate": simulate,
        "learning_pulse": pulse,
        "optimize_fleet": optimize,
        "curate_learning": curate,
        "dedupe_optimize": dedupe,
        "errors": {"simulate": sim_err, "learning_pulse": pulse_err, "optimize_fleet": opt_err, "curate_learning": curate_err, "dedupe_optimize": dedupe_err},
    }


st.set_page_config(page_title="Hermes Super Easy", page_icon="🧠", layout="wide")
st.title("Hermes Super Easy")
st.caption("One-screen control: connect, train near max, learn, and view fleet data.")

if "api_key" not in st.session_state:
    st.session_state["api_key"] = DEFAULT_API_KEY
if "auto_boot_done" not in st.session_state:
    st.session_state["auto_boot_done"] = False
if "last_chat" not in st.session_state:
    st.session_state["last_chat"] = ""

with st.sidebar:
    st.subheader("Easy Connection")
    st.text_input("API Key", key="api_key", type="password")
    st.caption(f"Gateway: {API_BASE}")
    st.caption("Default Docker key is pre-filled.")

unified, unified_err = safe_get("/unified-config", timeout=20)
bonus_data, bonus_err = safe_get("/aihub-bonus", timeout=20)
snapshot, snapshot_err = safe_get("/snapshot", timeout=20)

c1, c2, c3, c4 = st.columns(4)
c1.metric("System", "Online" if not unified_err else "Offline")
c2.metric("AIHub Bonus", f"{bonus_data.get('aihub_bonus', 0.0) * 100:.1f}%")
c3.metric("Mode", "MAX")
c4.metric("Model", str(unified.get("aihub_shared_model_id", "aihub-unified-v1")))

if unified_err:
    st.error(f"Gateway not ready: {unified_err}")
if bonus_err:
    st.warning(f"AIHub bonus pending: {bonus_err}")

st.write(
    f"**Unified AI/ML:** provider={unified.get('llm_api_provider', 'temp-api')} | "
    f"entry={unified.get('single_exe_entrypoint', 'hermes-gateway')} | "
    f"profile={unified.get('aihub_shared_ml_profile', 'global-learning')}"
)

mode = st.radio("Training Level", ["Easy", "Near Max Hermes"], horizontal=True, index=1)
max_mode = mode == "Near Max Hermes"

act1, act2, act3 = st.columns([1.4, 1, 1])
with act1:
    if st.button("Run Full Auto Learning + Fleet Upgrade", use_container_width=True):
        result = run_auto_cycle(max_mode=max_mode)
        log_text("full-auto-cycle", result)
        st.success("Auto cycle finished.")
        st.text_area("Auto Cycle Result", value=json.dumps(result, indent=2), height=260)
with act2:
    if st.button("Refresh Fleet Data", use_container_width=True):
        snapshot, snapshot_err = safe_get("/snapshot", timeout=20)
        if snapshot_err:
            st.error(f"Fleet data refresh failed: {snapshot_err}")
        else:
            log_text("fleet-refresh", snapshot)
            st.success("Fleet data refreshed.")
with act3:
    if st.button("Quick Optimize Now", use_container_width=True):
        optimize, opt_err = safe_post("/optimize-fleet", {"specialty": "fleet", "candidates": 480 if max_mode else 160}, timeout=120)
        if opt_err:
            st.error(f"Optimize failed: {opt_err}")
        else:
            log_text("quick-optimize", optimize)
            st.success("Fleet optimization complete.")

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

st.subheader("Fleet Data")
if snapshot_err:
    st.warning(f"Fleet snapshot unavailable: {snapshot_err}")
else:
    st.json(snapshot)

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
