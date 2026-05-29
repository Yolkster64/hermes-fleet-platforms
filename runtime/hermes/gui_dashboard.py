import os
import sqlite3
from pathlib import Path
from typing import Any, Dict

import requests
import streamlit as st

DB_PATH = Path("runtime/auto/hermes_super_orchestrator.db")
API_BASE = os.getenv("HERMES_API_BASE_URL", "http://localhost:8788")
DEFAULT_API_KEY = os.getenv("HERMES_GUI_API_KEY", "")


def request_headers() -> Dict[str, str]:
    key = st.session_state.get("api_key", "").strip()
    if not key:
        return {}
    return {"X-Hermes-Key": key}


def api_get(path: str, timeout: int = 30) -> Dict[str, Any]:
    response = requests.get(f"{API_BASE}{path}", headers=request_headers(), timeout=timeout)
    response.raise_for_status()
    return response.json()


def api_post(path: str, payload: Dict[str, Any], timeout: int = 60) -> Dict[str, Any]:
    response = requests.post(f"{API_BASE}{path}", json=payload, headers=request_headers(), timeout=timeout)
    response.raise_for_status()
    return response.json()


def read_latest_scores(limit: int = 30):
    if not DB_PATH.exists():
        return []
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute(
            """
            SELECT ts, horizon, specialty, score, quality, speed, cost_efficiency, truth_score
            FROM horizon_test_scores
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()


def remember_result(label: str, payload: Dict[str, Any]) -> None:
    st.session_state.setdefault("console", [])
    st.session_state["console"].insert(0, {"label": label, "payload": payload})
    st.session_state["console"] = st.session_state["console"][:20]


st.set_page_config(page_title="Hermes Runtime Training Ground", page_icon="🧠", layout="wide")
st.title("Hermes Runtime Training Ground")
st.caption("Text-first control center for AIHub/Hermes training, optimization, and fleet communication")
if "api_key" not in st.session_state:
    st.session_state["api_key"] = DEFAULT_API_KEY

with st.sidebar:
    st.header("Connection")
    st.text_input("Gateway API Key", key="api_key", type="password", help="Used as X-Hermes-Key header.")
    st.caption(f"Gateway: {API_BASE}")

try:
    snap = api_get("/snapshot", timeout=20)
    bonus = api_get("/aihub-bonus", timeout=20).get("aihub_bonus", 0.0)
    unified = api_get("/unified-config", timeout=20)
    pressure = snap.get("resource_pressure", {})
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("CPU", f"{pressure.get('cpu', 0.0)*100:.1f}%")
    c2.metric("Memory", f"{pressure.get('memory', 0.0)*100:.1f}%")
    c3.metric("GPU", f"{pressure.get('gpu', 0.0)*100:.1f}%")
    c4.metric("AIHub Bonus", f"{bonus*100:.1f}%")
    c5.metric("LLM Provider", str(unified.get("llm_api_provider", "temp-api")))
    st.text(
        "Status: unified AIHub/Hermes active | "
        f"model={unified.get('llm_api_model', 'aihub-unified-temp')} | "
        f"entrypoint={unified.get('single_exe_entrypoint', 'hermes-gateway')}"
    )
except Exception:
    st.info("Runtime snapshot not available yet.")

tab_controls, tab_training, tab_telemetry = st.tabs(["Control Center", "Text Training Ground", "Telemetry & Console"])

with tab_controls:
    st.subheader("Fleet and Learning Controls")
    preset = st.radio("Mode", ["Balanced", "Max Hermes"], horizontal=True, index=1)
    if preset == "Max Hermes":
        default_steps = 1200
        default_candidates = 320
        default_simulations = 900
    else:
        default_steps = 240
        default_candidates = 120
        default_simulations = 200

    a, b, c = st.columns(3)
    with a:
        simulations = st.slider("Simulations", min_value=20, max_value=3000, value=default_simulations, step=20)
    with b:
        pulse_steps = st.slider("Learning Pulse Steps", min_value=60, max_value=3000, value=default_steps, step=20)
    with c:
        candidates = st.slider("Fleet Candidates", min_value=40, max_value=500, value=default_candidates, step=10)

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Run Simulations", use_container_width=True):
            try:
                payload = api_post("/simulate", {"simulations": simulations, "specialty": "fleet"})
                remember_result("simulate", payload)
                st.success("Simulations completed.")
                st.json(payload)
            except Exception as exc:
                st.error(f"Simulations failed: {exc}")

        if st.button("Run Horizon Tests", use_container_width=True):
            try:
                payload = api_post("/horizon-tests", {"specialty": "fleet"})
                remember_result("horizon-tests", payload)
                st.success("Horizon tests completed.")
                st.json(payload)
            except Exception as exc:
                st.error(f"Horizon tests failed: {exc}")

    with c2:
        if st.button("Optimize Fleet", use_container_width=True):
            try:
                payload = api_post("/optimize-fleet", {"candidates": candidates, "specialty": "fleet"})
                remember_result("optimize-fleet", payload)
                st.success("Fleet optimization completed.")
                st.json(payload)
            except Exception as exc:
                st.error(f"Fleet optimization failed: {exc}")

        if st.button("Curate Learning Sources", use_container_width=True):
            try:
                payload = api_post(
                    "/curate-learning",
                    {"sql_signal": 0.82, "internet_signal": 0.62, "llm_signal": 0.78, "stability_bias": 0.76},
                )
                remember_result("curate-learning", payload)
                st.success("Learning source curation completed.")
                st.json(payload)
            except Exception as exc:
                st.error(f"Curation failed: {exc}")

    with c3:
        if st.button("Run Full Learning Pulse", use_container_width=True):
            try:
                payload = api_post(
                    "/learning-pulse",
                    {"specialty": "fleet", "steps": pulse_steps, "candidates": candidates},
                    timeout=120,
                )
                remember_result("learning-pulse", payload)
                st.success("Learning pulse completed.")
                st.json(payload)
            except Exception as exc:
                st.error(f"Learning pulse failed: {exc}")

        if st.button("Run Dedupe Optimization", use_container_width=True):
            try:
                payload = api_post(
                    "/dedupe-optimize",
                    {"roots": ["imports", "core", "src", "runtime"], "max_file_mb": 10},
                    timeout=120,
                )
                remember_result("dedupe-optimize", payload)
                st.success("Dedupe optimization completed.")
                st.json(payload)
            except Exception as exc:
                st.error(f"Dedupe optimization failed: {exc}")

with tab_training:
    st.subheader("Text for Everything: Prompt Training Area")
    system_prompt = st.text_input(
        "System Prompt",
        value="You are Hermes AIHub assistant focused on safe, high-throughput fleet optimization.",
    )
    prompt = st.text_area(
        "Prompt",
        height=170,
        value="Build a max-performance Hermes fleet plan with training priorities, safety checks, and optimization sequence.",
    )
    m1, m2, m3 = st.columns(3)
    with m1:
        model_name = st.text_input("Model Label", value="aihub-unified-temp")
    with m2:
        temperature = st.slider("Temperature", min_value=0.0, max_value=1.5, value=0.35, step=0.05)
    with m3:
        max_tokens = st.slider("Max Tokens", min_value=128, max_value=4096, value=1024, step=64)

    if st.button("Send to Hermes LLM (Training Ground)", use_container_width=True):
        try:
            payload = api_post(
                "/llm-chat",
                {
                    "prompt": prompt,
                    "system_prompt": system_prompt,
                    "model": model_name,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                timeout=90,
            )
            remember_result("llm-chat", payload)
            if payload.get("ok"):
                st.success("Training-ground response received.")
            else:
                st.error(f"LLM response returned error: {payload.get('error', 'unknown_error')}")
            st.text_area("Response Text", value=payload.get("response_text", ""), height=260)
            st.json(payload)
        except Exception as exc:
            st.error(f"LLM chat failed: {exc}")

with tab_telemetry:
    st.subheader("Runtime Text Console")
    console = st.session_state.get("console", [])
    if not console:
        st.info("No actions yet. Run controls or send training prompts to populate console.")
    else:
        for item in console:
            with st.expander(item["label"], expanded=False):
                st.json(item["payload"])

    st.subheader("Recent SQL Horizon Metrics")
    rows = read_latest_scores()
    if not rows:
        st.info("No metrics yet. Run controls to populate telemetry.")
    else:
        st.dataframe(
            [
                {
                    "ts": r[0],
                    "horizon": r[1],
                    "specialty": r[2],
                    "score": r[3],
                    "quality": r[4],
                    "speed": r[5],
                    "cost_efficiency": r[6],
                    "truth_score": r[7],
                }
                for r in rows
            ],
            use_container_width=True,
        )
