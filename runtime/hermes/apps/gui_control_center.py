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
    headers = {"X-Hermes-Key": key, "X-Hermes-Session": key}
    try:
        r = requests.get(f"{_gateway_base()}/system-watch", headers=headers, timeout=10)
        r.raise_for_status()
        return True, ""
    except requests.RequestException as exc:
        return False, str(exc)


st.set_page_config(page_title="Hermes Control Center", page_icon="🛡️", layout="centered")
st.title("Hermes Control Center (Simple Mode)")
st.caption("Minimal, stable UI for login and health status.")

if "api_key" not in st.session_state:
    st.session_state["api_key"] = _load_saved_key() or "local-hermes-ui-key"

st.text_input("API Key", key="api_key", type="password")
st.caption(f"Gateway: {_gateway_base()}")

c1, c2 = st.columns(2)
with c1:
    if st.button("Submit + Save Key", use_container_width=True):
        ok, err = _health_check(st.session_state["api_key"])
        if not ok:
            st.error(f"Login failed: {err}")
        else:
            saved, save_err = _save_key(st.session_state["api_key"])
            if saved:
                st.success("Logged in and key saved.")
            else:
                st.warning(f"Logged in, but save failed: {save_err}")

with c2:
    if st.button("Reconnect Check", use_container_width=True):
        ok, err = _health_check(st.session_state["api_key"])
        if ok:
            st.success("Connection is healthy.")
        else:
            st.error(f"Connection failed: {err}")

st.divider()
st.subheader("Status")
ok, err = _health_check(st.session_state["api_key"])
if ok:
    st.success("Hermes gateway is reachable.")
else:
    st.warning(f"Gateway check failed: {err}")
st.caption(f"UTC: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
