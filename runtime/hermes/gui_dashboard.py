import os
import sqlite3
from pathlib import Path

import requests
import streamlit as st

DB_PATH = Path("runtime/auto/hermes_super_orchestrator.db")
API_BASE = os.getenv("HERMES_API_BASE_URL", "http://localhost:8787")


def read_latest_scores(limit: int = 20):
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


def trigger_simulations(simulations: int):
    response = requests.post(
        f"{API_BASE}/simulate",
        json={"simulations": simulations},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def fetch_snapshot():
    response = requests.get(f"{API_BASE}/snapshot", timeout=20)
    response.raise_for_status()
    return response.json()


def fetch_aihub_bonus():
    response = requests.get(f"{API_BASE}/aihub-bonus", timeout=20)
    response.raise_for_status()
    return response.json().get("aihub_bonus", 0.0)


def run_llm_chat(prompt: str, system_prompt: str, model: str, temperature: float, max_tokens: int):
    response = requests.post(
        f"{API_BASE}/llm-chat",
        json={
            "prompt": prompt,
            "system_prompt": system_prompt,
            "model": model or None,
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


st.set_page_config(page_title="Hermes Runtime", page_icon="⚙️", layout="wide")
st.title("Hermes Local Runtime")
st.caption("QNAA/KNAA training control, SQL telemetry, and quick API controls")

try:
    snap = fetch_snapshot()
    bonus = fetch_aihub_bonus()
    pressure = snap.get("resource_pressure", {})
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("CPU Pressure", f"{pressure.get('cpu', 0.0)*100:.1f}%")
    m2.metric("Memory Pressure", f"{pressure.get('memory', 0.0)*100:.1f}%")
    m3.metric("GPU Pressure", f"{pressure.get('gpu', 0.0)*100:.1f}%")
    m4.metric("AIHub Bonus", f"{bonus*100:.1f}%")
except Exception:
    st.info("Live snapshot unavailable yet.")

col1, col2 = st.columns(2)
with col1:
    sims = st.slider("Simulation count", min_value=10, max_value=2000, value=200, step=10)
    if st.button("Run simulations"):
        try:
            payload = trigger_simulations(sims)
            st.success(f"Completed {payload.get('simulations', sims)} simulations.")
            st.json(payload)
        except Exception as exc:
            st.error(f"Simulation call failed: {exc}")

with col2:
    if st.button("Run horizon test suite"):
        try:
            response = requests.post(f"{API_BASE}/horizon-tests", json={}, timeout=30)
            response.raise_for_status()
            st.success("Horizon tests completed.")
            st.json(response.json())
        except Exception as exc:
            st.error(f"Horizon call failed: {exc}")
    if st.button("Optimize fleet topology"):
        try:
            response = requests.post(f"{API_BASE}/optimize-fleet", json={"candidates": 120, "specialty": "fleet"}, timeout=30)
            response.raise_for_status()
            st.success("Fleet topology optimization completed.")
            st.json(response.json())
        except Exception as exc:
            st.error(f"Fleet optimization failed: {exc}")
    if st.button("Curate learning sources"):
        try:
            response = requests.post(
                f"{API_BASE}/curate-learning",
                json={"sql_signal": 0.75, "internet_signal": 0.55, "llm_signal": 0.70, "stability_bias": 0.72},
                timeout=30,
            )
            response.raise_for_status()
            st.success("Learning curation completed.")
            st.json(response.json())
        except Exception as exc:
            st.error(f"Curation failed: {exc}")
    if st.button("Run full learning pulse"):
        try:
            response = requests.post(
                f"{API_BASE}/learning-pulse",
                json={"specialty": "fleet", "steps": 180, "candidates": 120},
                timeout=60,
            )
            response.raise_for_status()
            st.success("Learning pulse completed.")
            st.json(response.json())
        except Exception as exc:
            st.error(f"Learning pulse failed: {exc}")
    if st.button("Run dedupe optimization scan"):
        try:
            response = requests.post(
                f"{API_BASE}/dedupe-optimize",
                json={"roots": ["imports", "core", "src", "runtime"], "max_file_mb": 8},
                timeout=90,
            )
            response.raise_for_status()
            st.success("Dedupe optimization scan completed.")
            st.json(response.json())
        except Exception as exc:
            st.error(f"Dedupe optimization failed: {exc}")

st.subheader("Training Ground (Text)")
prompt = st.text_area("Prompt", value="Give me a concise fleet optimization plan for Hermes.")
system_prompt = st.text_input("System prompt", value="You are Hermes AIHub assistant focused on safe, efficient optimization.")
model_name = st.text_input("Model override (optional)", value="")
temperature = st.slider("Temperature", min_value=0.0, max_value=1.5, value=0.3, step=0.05)
max_tokens = st.slider("Max tokens", min_value=64, max_value=2048, value=512, step=64)
if st.button("Send text to AIHub LLM"):
    try:
        llm_payload = run_llm_chat(prompt, system_prompt, model_name, temperature, max_tokens)
        if llm_payload.get("ok"):
            st.success("LLM response received.")
            st.text_area("Response", value=llm_payload.get("response_text", ""), height=220)
        else:
            st.error(f"LLM call failed: {llm_payload.get('error', 'unknown_error')}")
        st.json(llm_payload)
    except Exception as exc:
        st.error(f"LLM chat failed: {exc}")

st.subheader("Recent SQL horizon metrics")
rows = read_latest_scores()
if not rows:
    st.info("No metrics yet. Run simulations or horizon tests to populate telemetry.")
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
