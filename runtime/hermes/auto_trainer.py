import os
import time

import requests

API_BASE = os.getenv("HERMES_API_BASE_URL", "http://hermes-api:8787")
SPECIALTY = os.getenv("HERMES_TRAIN_SPECIALTY", "fleet")
STEPS = int(os.getenv("HERMES_TRAIN_STEPS", "400"))
SLEEP_SECONDS = int(os.getenv("HERMES_TRAIN_INTERVAL_SECONDS", "12"))


def run_cycle() -> None:
    payload = {"steps": STEPS, "specialty": SPECIALTY}
    response = requests.post(f"{API_BASE}/simulate", json=payload, timeout=120)
    response.raise_for_status()
    data = response.json()
    print(
        f"[auto-trainer] steps={data.get('steps')} "
        f"avg_reward={data.get('avg_reward_score'):.4f} "
        f"avg_truth={data.get('avg_truth_score'):.4f} "
        f"avg_knaa_qnaa={data.get('avg_knaa_qnaa_score', 0.0):.4f}"
    )


if __name__ == "__main__":
    while True:
        try:
            run_cycle()
        except Exception as exc:
            print(f"[auto-trainer] cycle failed: {exc}")
        time.sleep(SLEEP_SECONDS)
