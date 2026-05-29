import os
import time
from typing import Any, Dict, Tuple

import requests
import streamlit as st

API_BASE = os.getenv("HERMES_API_BASE_URL", "http://localhost:8788")


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


def run_logged_post_action(
    label: str,
    path: str,
    payload: Dict[str, Any],
    success_message: str,
    error_prefix: str,
    timeout: int = 120,
) -> Tuple[Dict[str, Any], str]:
    response, err = safe_post(path, payload, timeout=timeout)
    if err:
        st.error(f"{error_prefix}: {err}")
        response = {"error": err}
    else:
        st.success(success_message)
    log_text(label, response)
    return response, err
