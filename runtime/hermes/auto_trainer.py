import os
import time

import requests

API_BASE = os.getenv("HERMES_API_BASE_URL", "http://hermes-api:8787")
SPECIALTY = os.getenv("HERMES_TRAIN_SPECIALTY", "fleet")
STEPS = int(os.getenv("HERMES_TRAIN_STEPS", "400"))
SLEEP_SECONDS = int(os.getenv("HERMES_TRAIN_INTERVAL_SECONDS", "12"))
FLEET_OPTIMIZE_EVERY = int(os.getenv("HERMES_FLEET_OPTIMIZE_EVERY", "6"))
FLEET_CANDIDATES = int(os.getenv("HERMES_FLEET_CANDIDATES", "200"))
MAX_MODE = os.getenv("HERMES_MAX_MODE", "true").lower() in ("1", "true", "yes", "on")
GATEWAY_KEY = os.getenv("HERMES_GATEWAY_KEY", "")
_cycle = 0


def _headers():
    if GATEWAY_KEY.strip():
        return {"X-Hermes-Key": GATEWAY_KEY.strip()}
    return {}


def run_cycle() -> None:
    global _cycle
    _cycle += 1
    sim_steps = STEPS if not MAX_MODE else max(STEPS, 1000)
    payload = {"steps": sim_steps, "specialty": SPECIALTY}
    response = requests.post(f"{API_BASE}/simulate", json=payload, headers=_headers(), timeout=120)
    response.raise_for_status()
    data = response.json()
    signal_score = max(0.0, min(1.0, (data.get("avg_truth_score", 0.5) * 0.6) + (data.get("avg_quality", 0.5) * 0.4)))
    requests.post(
        f"{API_BASE}/ingest-signal",
        json={
            "source": "auto_trainer",
            "signal_score": signal_score,
            "payload": {
                "avg_reward_score": data.get("avg_reward_score"),
                "avg_knaa_qnaa_score": data.get("avg_knaa_qnaa_score"),
                "avg_fleet_shape_score": data.get("avg_fleet_shape_score"),
                "avg_long_haul_meta_score": data.get("avg_long_haul_meta_score"),
            },
        },
        headers=_headers(),
        timeout=30,
    ).raise_for_status()
    if _cycle % max(1, FLEET_OPTIMIZE_EVERY) == 0:
        pulse_steps = max(120, STEPS // 2 if not MAX_MODE else STEPS)
        pulse_candidates = FLEET_CANDIDATES if not MAX_MODE else max(FLEET_CANDIDATES, 300)
        requests.post(
            f"{API_BASE}/learning-pulse",
            json={
                "specialty": SPECIALTY,
                "steps": pulse_steps,
                "candidates": pulse_candidates,
                "sql_signal": data.get("avg_quantized_compression_score", 0.5),
                "internet_signal": data.get("avg_fleet_shape_score", 0.5),
                "llm_signal": data.get("avg_long_haul_meta_score", data.get("avg_knaa_qnaa_score", 0.5)),
                "stability_bias": data.get("avg_truth_score", 0.6),
            },
            headers=_headers(),
            timeout=90,
        ).raise_for_status()
        requests.post(
            f"{API_BASE}/dedupe-optimize",
            json={"roots": ["imports", "core", "src", "runtime"], "max_file_mb": 8},
            headers=_headers(),
            timeout=120,
        ).raise_for_status()
    print(
        f"[auto-trainer] cycle={_cycle} mode={'MAX' if MAX_MODE else 'BALANCED'} steps={data.get('steps')} "
        f"avg_reward={data.get('avg_reward_score'):.4f} "
        f"avg_truth={data.get('avg_truth_score'):.4f} "
        f"avg_knaa_qnaa={data.get('avg_knaa_qnaa_score', 0.0):.4f} "
        f"avg_fleet_shape={data.get('avg_fleet_shape_score', 0.0):.4f} "
        f"avg_long_haul_meta={data.get('avg_long_haul_meta_score', 0.0):.4f}"
    )


if __name__ == "__main__":
    while True:
        try:
            run_cycle()
        except Exception as exc:
            print(f"[auto-trainer] cycle failed: {exc}")
        time.sleep(SLEEP_SECONDS)
