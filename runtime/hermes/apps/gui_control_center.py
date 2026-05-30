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
        r = requests.get(f"{_gateway_base()}/health", headers=headers, timeout=10)
        r.raise_for_status()
        return True, ""
    except requests.RequestException as exc:
        return False, str(exc)


def _health_with_headers(headers: dict[str, str]) -> tuple[bool, str]:
    try:
        r = requests.get(f"{_gateway_base()}/health", headers=headers, timeout=10)
        r.raise_for_status()
        return True, ""
    except requests.RequestException as exc:
        return False, str(exc)


def _active_headers() -> dict[str, str]:
    token = str(st.session_state.get("session_token", "")).strip()
    if token:
        return {
            "X-Hermes-Session": token,
            "Authorization": f"Bearer {token}",
        }
    key = str(st.session_state.get("api_key", "")).strip()
    if key:
        return {"X-Hermes-Key": key, "X-Hermes-Session": key}
    return {}


def _attempt_login(secret: str) -> tuple[bool, str]:
    secret = secret.strip()
    if not secret:
        return False, "API key is empty."
    token_err = ""
    login_err = ""

    # 1) Try key-based auth directly.
    ok, err = _health_with_headers({"X-Hermes-Key": secret})
    if ok:
        st.session_state["session_token"] = ""
        st.session_state["auth_mode"] = "key"
        return True, ""

    # 2) Try as an existing session token (or bearer token).
    session_headers = {"X-Hermes-Session": secret, "Authorization": f"Bearer {secret}"}
    ok, token_err = _health_with_headers(session_headers)
    if ok:
        st.session_state["session_token"] = secret
        st.session_state["auth_mode"] = "session"
        return True, ""

    # 3) Ask gateway for a short-lived session token using the provided key.
    try:
        login = requests.post(
            f"{_gateway_base()}/auth/login",
            json={"gateway_key": secret},
            timeout=10,
        )
        login.raise_for_status()
        body = login.json() if login.content else {}
        token = str(body.get("token", "")).strip() if isinstance(body, dict) else ""
        if not token:
            return False, "Gateway login returned no session token."
        token_headers = {"X-Hermes-Session": token, "Authorization": f"Bearer {token}"}
        token_ok, token_verify_err = _health_with_headers(token_headers)
        if not token_ok:
            return False, token_verify_err
        st.session_state["session_token"] = token
        st.session_state["auth_mode"] = "session"
        return True, ""
    except requests.RequestException as exc:
        login_err = str(exc)
    except ValueError as exc:
        login_err = f"Invalid login response: {exc}"

    return False, err or token_err or login_err or "Authentication failed."


st.set_page_config(page_title="Hermes Control Center", page_icon="🛡️", layout="centered")
st.title("Hermes Control Center (Simple Mode)")
st.caption("Minimal, stable UI for login and health status.")

if "api_key" not in st.session_state:
    st.session_state["api_key"] = _load_saved_key() or "local-hermes-ui-key"
if "session_token" not in st.session_state:
    st.session_state["session_token"] = ""
if "auth_mode" not in st.session_state:
    st.session_state["auth_mode"] = "key"

st.text_input("API Key", key="api_key", type="password")
st.caption(f"Gateway: {_gateway_base()}")

c1, c2 = st.columns(2)
with c1:
    if st.button("Submit + Save Key", use_container_width=True):
        ok, err = _attempt_login(st.session_state["api_key"])
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
        active = _active_headers()
        ok, err = _health_with_headers(active) if active else (False, "No active key or session.")
        if ok:
            st.success("Connection is healthy.")
        else:
            st.error(f"Connection failed: {err}")

st.divider()
st.subheader("Status")
active = _active_headers()
ok, err = _health_with_headers(active) if active else (False, "No active key or session.")
if ok:
    st.success("Hermes gateway is reachable.")
else:
    st.warning(f"Gateway check failed: {err}")
st.caption(f"Auth mode: {st.session_state.get('auth_mode', 'key')}")
st.caption(f"UTC: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
