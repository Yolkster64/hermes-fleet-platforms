import json
import os
import sqlite3
import subprocess
import time
from typing import Dict, List


def _db_path(volume_root: str) -> str:
    return os.path.join(volume_root, "training", "hermes_training_intel.sqlite3")


def ensure_training_sql(volume_root: str) -> str:
    db = _db_path(volume_root)
    os.makedirs(os.path.dirname(db), exist_ok=True)
    with sqlite3.connect(db) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS training_cycles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cycle INTEGER NOT NULL,
                specialty TEXT NOT NULL,
                signal_score REAL NOT NULL,
                reward REAL NOT NULL,
                truth_score REAL NOT NULL,
                shape_score REAL NOT NULL,
                training_variables_json TEXT NOT NULL,
                created_unix REAL NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS github_context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                branch TEXT NOT NULL,
                commit_sha TEXT NOT NULL,
                commit_subject TEXT NOT NULL,
                changed_files INTEGER NOT NULL,
                created_unix REAL NOT NULL
            )
            """
        )
        conn.commit()
    return db


def record_training_cycle(
    volume_root: str,
    cycle: int,
    specialty: str,
    signal_score: float,
    reward: float,
    truth_score: float,
    shape_score: float,
    training_variables: Dict[str, float],
) -> None:
    db = ensure_training_sql(volume_root)
    with sqlite3.connect(db) as conn:
        conn.execute(
            """
            INSERT INTO training_cycles (
                cycle, specialty, signal_score, reward, truth_score, shape_score, training_variables_json, created_unix
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(cycle),
                str(specialty),
                float(signal_score),
                float(reward),
                float(truth_score),
                float(shape_score),
                json.dumps(training_variables, sort_keys=True),
                time.time(),
            ),
        )
        conn.commit()


def compute_sql_pattern_intel(volume_root: str, lookback: int = 240) -> Dict[str, object]:
    db = ensure_training_sql(volume_root)
    with sqlite3.connect(db) as conn:
        rows = conn.execute(
            """
            SELECT cycle, signal_score, reward, truth_score, shape_score, training_variables_json
            FROM training_cycles
            ORDER BY id DESC
            LIMIT ?
            """,
            (int(max(20, lookback)),),
        ).fetchall()
        latest_github = conn.execute(
            """
            SELECT branch, commit_sha, commit_subject, changed_files, created_unix
            FROM github_context
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

    if not rows:
        return {"rows": 0, "pattern_score": 0.0, "trend": 0.0, "variable_means": {}, "latest_github": {}}

    rows = list(reversed(rows))
    signals = [float(r[1]) for r in rows]
    rewards = [float(r[2]) for r in rows]
    truths = [float(r[3]) for r in rows]
    shapes = [float(r[4]) for r in rows]
    var_buckets: Dict[str, List[float]] = {}
    for r in rows:
        payload = json.loads(r[5]) if isinstance(r[5], str) and r[5] else {}
        if isinstance(payload, dict):
            for key, value in payload.items():
                if isinstance(value, (int, float)):
                    var_buckets.setdefault(str(key), []).append(float(value))
    variable_means = {k: (sum(v) / len(v)) for k, v in var_buckets.items() if v}
    trend = signals[-1] - signals[0] if len(signals) > 1 else signals[-1]
    pattern_score = max(0.0, min(1.0, ((sum(signals) / len(signals)) * 0.4) + ((sum(rewards) / len(rewards)) * 0.25) + ((sum(truths) / len(truths)) * 0.2) + ((sum(shapes) / len(shapes)) * 0.15) + (trend * 0.1)))
    github_payload = {}
    if latest_github:
        github_payload = {
            "branch": latest_github[0],
            "commit_sha": latest_github[1],
            "commit_subject": latest_github[2],
            "changed_files": int(latest_github[3]),
            "created_unix": float(latest_github[4]),
        }
    return {
        "rows": len(rows),
        "pattern_score": float(pattern_score),
        "trend": float(trend),
        "signal_avg": float(sum(signals) / len(signals)),
        "reward_avg": float(sum(rewards) / len(rewards)),
        "truth_avg": float(sum(truths) / len(truths)),
        "shape_avg": float(sum(shapes) / len(shapes)),
        "variable_means": variable_means,
        "latest_github": github_payload,
    }


def ingest_github_context(volume_root: str, repo_root: str) -> Dict[str, object]:
    db = ensure_training_sql(volume_root)
    branch = "unknown"
    commit_sha = "unknown"
    commit_subject = ""
    changed_files = 0
    try:
        branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root, text=True).strip()
        commit_sha = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=repo_root, text=True).strip()
        commit_subject = subprocess.check_output(["git", "log", "-1", "--pretty=%s"], cwd=repo_root, text=True).strip()
        status = subprocess.check_output(["git", "--no-pager", "status", "--short"], cwd=repo_root, text=True)
        changed_files = len([line for line in status.splitlines() if line.strip()])
    except Exception:
        pass
    payload = {
        "branch": branch,
        "commit_sha": commit_sha,
        "commit_subject": commit_subject,
        "changed_files": int(changed_files),
        "created_unix": time.time(),
    }
    with sqlite3.connect(db) as conn:
        conn.execute(
            """
            INSERT INTO github_context (branch, commit_sha, commit_subject, changed_files, created_unix)
            VALUES (?, ?, ?, ?, ?)
            """,
            (payload["branch"], payload["commit_sha"], payload["commit_subject"], payload["changed_files"], payload["created_unix"]),
        )
        conn.commit()
    return payload
