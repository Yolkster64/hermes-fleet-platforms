import os
import time
from typing import Any, Dict, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
import streamlit as st

API_BASE = os.getenv("HERMES_API_BASE_URL", "http://localhost:8788")


def _candidate_keys() -> list[str]:
    raw = [
        str(st.session_state.get("api_key", "")).strip(),
        os.getenv("HERMES_GUI_API_KEY", "").strip(),
        os.getenv("HERMES_GATEWAY_KEY", "").strip(),
        os.getenv("HERMES_API_KEY", "").strip(),
        "local-hermes-ui-key",
        "local-hermes-dev-key",
    ]
    seen = set()
    keys: list[str] = []
    for item in raw:
        if item and item not in seen:
            keys.append(item)
            seen.add(item)
    return keys


def headers() -> Dict[str, str]:
    key = str(st.session_state.get("api_key", "")).strip()
    if not key:
        keys = _candidate_keys()
        key = keys[0] if keys else ""
    if not key:
        return {}
    return {"X-Hermes-Key": key, "X-Hermes-Session": key}


def current_api_base() -> str:
    base = str(st.session_state.get("_active_api_base", "")).strip()
    return base or API_BASE


def _candidate_api_bases() -> list[str]:
    preferred = [
        str(os.getenv("HERMES_API_BASE_URL", "")).strip(),
        "http://localhost:8788",
        "http://localhost:8787",
        "http://127.0.0.1:8788",
        "http://127.0.0.1:8787",
        "http://hermes-gateway:8788",
        "http://hermes-api:8787",
    ]
    seen = set()
    ordered: list[str] = []
    active = str(st.session_state.get("_active_api_base", "")).strip()
    if active:
        preferred.insert(0, active)
    for item in preferred:
        if item and item not in seen:
            ordered.append(item)
            seen.add(item)
    return ordered


def _session() -> requests.Session:
    if "_api_http_session" not in st.session_state:
        sess = requests.Session()
        sess.mount("http://", HTTPAdapter(pool_connections=16, pool_maxsize=16, max_retries=0))
        sess.mount("https://", HTTPAdapter(pool_connections=8, pool_maxsize=8, max_retries=0))
        st.session_state["_api_http_session"] = sess
    return st.session_state["_api_http_session"]


def _request_json(method: str, path: str, timeout: int = 30, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    last_exc: Optional[requests.RequestException] = None
    for base in _candidate_api_bases():
        keys = _candidate_keys() or [""]
        for key in keys:
            request_headers = {"X-Hermes-Key": key, "X-Hermes-Session": key} if key else {}
            try:
                if method == "GET":
                    response = _session().get(f"{base}{path}", headers=request_headers, timeout=timeout)
                else:
                    response = _session().post(f"{base}{path}", json=(payload or {}), headers=request_headers, timeout=timeout)
                response.raise_for_status()
                st.session_state["_active_api_base"] = base
                return response.json()
            except requests.HTTPError as exc:
                last_exc = exc
                status_code = exc.response.status_code if exc.response is not None else 0
                if status_code in (404,):
                    break
                continue
            except requests.RequestException as exc:
                last_exc = exc
                continue
    if last_exc is not None:
        raise last_exc
    raise requests.RequestException("No reachable Hermes API base URL")


def api_get(path: str, timeout: int = 30) -> Dict[str, Any]:
    return _request_json("GET", path=path, timeout=timeout)


def api_post(path: str, payload: Dict[str, Any], timeout: int = 120) -> Dict[str, Any]:
    return _request_json("POST", path=path, timeout=timeout, payload=payload)


def safe_get(path: str, timeout: int = 30) -> Tuple[Dict[str, Any], str]:
    try:
        return api_get(path, timeout=timeout), ""
    except requests.RequestException as exc:  # pragma: no cover
        return {}, str(exc)


def safe_post(path: str, payload: Dict[str, Any], timeout: int = 120) -> Tuple[Dict[str, Any], str]:
    last_error = ""
    for attempt in range(3):
        try:
            return api_post(path, payload=payload, timeout=timeout), ""
        except requests.RequestException as exc:  # pragma: no cover
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
