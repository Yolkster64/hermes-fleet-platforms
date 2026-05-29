import os
from typing import Any, Dict

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


def api_post(path: str, payload: Dict[str, Any], timeout: int = 90) -> Dict[str, Any]:
    r = requests.post(f"{API_BASE}{path}", json=payload, headers=headers(), timeout=timeout)
    r.raise_for_status()
    return r.json()


def log_text(label: str, payload: Dict[str, Any]) -> None:
    st.session_state.setdefault("logs", [])
    st.session_state["logs"].insert(0, {"label": label, "payload": payload})
    st.session_state["logs"] = st.session_state["logs"][:15]


def run_auto_cycle(max_mode: bool) -> Dict[str, Any]:
    steps = 1400 if max_mode else 400
    candidates = 320 if max_mode else 120
    sim = api_post("/simulate", {"specialty": "fleet", "simulations": 900 if max_mode else 240})
    pulse = api_post("/learning-pulse", {"specialty": "fleet", "steps": steps, "candidates": candidates}, timeout=120)
    return {"simulate": sim, "learning_pulse": pulse}


st.set_page_config(page_title="Hermes Easy Control", page_icon="🧠", layout="wide")
st.title("Hermes Easy Control")
st.caption("Simple automatic control center — one button runs the full training flow.")

if "api_key" not in st.session_state:
    st.session_state["api_key"] = DEFAULT_API_KEY
if "auto_boot_done" not in st.session_state:
    st.session_state["auto_boot_done"] = False

with st.sidebar:
    st.subheader("Connection")
    st.text_input("API Key", key="api_key", type="password")
    st.caption(f"Gateway: {API_BASE}")

try:
    unified = api_get("/unified-config", timeout=20)
    bonus = api_get("/aihub-bonus", timeout=20).get("aihub_bonus", 0.0)
    c1, c2, c3 = st.columns(3)
    c1.metric("System", "Online")
    c2.metric("AIHub Bonus", f"{bonus*100:.1f}%")
    c3.metric("Model", str(unified.get("llm_api_model", "aihub-unified-temp")))
    st.write(
        f"**Status:** ready | provider={unified.get('llm_api_provider', 'temp-api')} | "
        f"entry={unified.get('single_exe_entrypoint', 'hermes-gateway')}"
    )
except Exception:
    st.error("System is not ready yet. Start runtime and refresh.")

mode = st.radio("Mode", ["Easy", "Max Hermes"], horizontal=True, index=1)
max_mode = mode == "Max Hermes"

col1, col2 = st.columns([2, 1])
with col1:
    if st.button("Run Automatic Training Now", use_container_width=True):
        try:
            result = run_auto_cycle(max_mode=max_mode)
            log_text("auto-run", result)
            st.success("Automatic training cycle complete.")
            st.text_area("Result Summary", value=str(result), height=280)
        except Exception as exc:
            st.error(f"Automatic run failed: {exc}")
with col2:
    if st.button("Ask Hermes (Quick Text)", use_container_width=True):
        try:
            chat = api_post(
                "/llm-chat",
                {
                    "prompt": "Give me the next best optimization step for this runtime.",
                    "system_prompt": "You are Hermes AIHub assistant.",
                },
            )
            log_text("quick-chat", chat)
            st.success("Response received.")
            st.text_area("Hermes Text", value=chat.get("response_text", ""), height=280)
        except Exception as exc:
            st.error(f"Hermes text request failed: {exc}")

if not st.session_state["auto_boot_done"]:
    try:
        warm = api_post("/learning-pulse", {"specialty": "fleet", "steps": 180, "candidates": 120}, timeout=90)
        log_text("auto-boot-warmstart", warm)
        st.session_state["auto_boot_done"] = True
        st.info("Automatic warm-start finished.")
    except Exception:
        st.warning("Automatic warm-start pending.")

with st.expander("Advanced (optional)"):
    prompt = st.text_area("Custom Prompt", value="Optimize Hermes performance and safety for the next cycle.")
    if st.button("Send Custom Prompt"):
        try:
            chat = api_post("/llm-chat", {"prompt": prompt, "system_prompt": "You are Hermes AIHub assistant."})
            log_text("custom-chat", chat)
            st.text_area("Custom Response", value=chat.get("response_text", ""), height=220)
        except Exception as exc:
            st.error(f"Custom prompt failed: {exc}")

st.subheader("Text Log")
for item in st.session_state.get("logs", []):
    st.code(f"{item['label']}: {item['payload']}")
