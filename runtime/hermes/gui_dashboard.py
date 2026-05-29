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


st.set_page_config(page_title="Hermes Runtime", page_icon="⚙️", layout="wide")
st.title("Hermes Local Runtime")
st.caption("QNAA/KNAA training control, SQL telemetry, and quick API controls")

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
