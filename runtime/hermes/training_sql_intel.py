import json
import math
import os
import sqlite3
import subprocess
import time
from typing import Dict, List

_SCHEMA_READY: set[str] = set()


def _db_path(volume_root: str) -> str:
    return os.path.join(volume_root, "training", "hermes_training_intel.sqlite3")


def _connect(db: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA foreign_keys=OFF")
    conn.execute("PRAGMA cache_size=-20000")
    return conn


def ensure_training_sql(volume_root: str) -> str:
    db = _db_path(volume_root)
    os.makedirs(os.path.dirname(db), exist_ok=True)
    if db in _SCHEMA_READY and os.path.exists(db):
        return db
    with _connect(db) as conn:
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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS hermes_agent_variables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cycle INTEGER NOT NULL,
                hermes_id TEXT NOT NULL,
                specialty TEXT NOT NULL,
                signal_score REAL NOT NULL,
                art_pattern_score REAL NOT NULL,
                variables_json TEXT NOT NULL,
                created_unix REAL NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_training_cycles_cycle ON training_cycles(cycle)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_training_cycles_created ON training_cycles(created_unix)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_vars_cycle ON hermes_agent_variables(cycle)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_vars_created ON hermes_agent_variables(created_unix)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_vars_hermes ON hermes_agent_variables(hermes_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_github_context_created ON github_context(created_unix)")
        conn.commit()
    _SCHEMA_READY.add(db)
    return db


def prune_training_sql(
    volume_root: str,
    max_cycles: int = 6000,
    max_agent_rows: int = 24000,
    max_github_rows: int = 4000,
) -> Dict[str, int]:
    db = ensure_training_sql(volume_root)
    pruned = {"training_cycles": 0, "hermes_agent_variables": 0, "github_context": 0}
    with _connect(db) as conn:
        conn.execute(
            """
            DELETE FROM training_cycles
            WHERE id NOT IN (
                SELECT id FROM training_cycles ORDER BY id DESC LIMIT ?
            )
            """,
            (int(max_cycles),),
        )
        pruned["training_cycles"] = int(conn.total_changes)
        conn.execute(
            """
            DELETE FROM hermes_agent_variables
            WHERE id NOT IN (
                SELECT id FROM hermes_agent_variables ORDER BY id DESC LIMIT ?
            )
            """,
            (int(max_agent_rows),),
        )
        pruned["hermes_agent_variables"] = int(conn.total_changes) - pruned["training_cycles"]
        conn.execute(
            """
            DELETE FROM github_context
            WHERE id NOT IN (
                SELECT id FROM github_context ORDER BY id DESC LIMIT ?
            )
            """,
            (int(max_github_rows),),
        )
        pruned["github_context"] = int(conn.total_changes) - pruned["training_cycles"] - pruned["hermes_agent_variables"]
        conn.commit()
    return pruned


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
    with _connect(db) as conn:
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


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _art_pattern_metrics(variable_means: Dict[str, float]) -> Dict[str, float]:
    value_list = list(variable_means.values())
    if value_list:
        value_avg = sum(value_list) / len(value_list)
        variance = sum((v - value_avg) ** 2 for v in value_list) / max(1, len(value_list))
    else:
        variance = 0.0
    symmetry_index = _clamp01(1.0 - abs(variable_means.get("group_strength", 0.5) - variable_means.get("solo_strength", 0.5)))
    contrast_index = _clamp01(math.sqrt(max(0.0, variance)) * 2.0)
    quantized = [int(_clamp01(v) * 100.0) for v in value_list]
    unique_bins = len(set(quantized)) if quantized else 0
    compression_ratio = _clamp01(1.0 - (float(unique_bins) / float(max(1, len(quantized)))))
    overlap_3d = _clamp01(
        (
            (1.0 - abs(variable_means.get("group_strength", 0.5) - variable_means.get("coordination_cohesion", 0.5)))
            + (1.0 - abs(variable_means.get("solo_strength", 0.5) - variable_means.get("knowledge_transfer", 0.5)))
            + (1.0 - abs(variable_means.get("reward_adaptation", 0.5) - variable_means.get("retention_strength", 0.5)))
        )
        / 3.0
    )
    fractal_flow = _clamp01(sum(abs(math.sin(v * math.pi * 2.0)) for v in value_list[:24]) / max(1, min(24, len(value_list))))
    return {
        "symmetry_index": float(symmetry_index),
        "contrast_index": float(contrast_index),
        "fractal_flow": float(fractal_flow),
        "compression_ratio": float(compression_ratio),
        "overlap_3d": float(overlap_3d),
    }


def _build_recent_hermes_profile(row: tuple) -> Dict[str, object]:
    vars_payload = json.loads(row[4]) if isinstance(row[4], str) and row[4] else {}
    if not isinstance(vars_payload, dict):
        vars_payload = {}
    xp = max(
        0.0,
        min(
            10000.0,
            (
                float(row[2]) * 2200.0
                + float(row[3]) * 1800.0
                + float(vars_payload.get("retention_strength", 0.5)) * 1600.0
                + float(vars_payload.get("knowledge_transfer", 0.5)) * 1400.0
            ),
        ),
    )
    level = max(1, min(99, int(1 + (xp / 140.0))))
    speed_bonus = _clamp01(float(vars_payload.get("speed_efficiency", 0.5)) * 0.8 + float(vars_payload.get("position_score", 0.5)) * 0.2)
    token_power_gain = _clamp01(float(vars_payload.get("yield_efficiency", 0.5)) * 0.7 + float(row[3]) * 0.3)
    size_mode = "mini" if float(vars_payload.get("size_factor", 0.5)) < 0.45 else ("full" if float(vars_payload.get("size_factor", 0.5)) > 0.70 else "mid")
    specialties = [
        "pattern-hunter",
        "sql-reasoner" if float(vars_payload.get("retention_strength", 0.5)) > 0.55 else "fast-explorer",
        "aihub-bridge" if float(vars_payload.get("knowledge_transfer", 0.5)) > 0.55 else "field-adapter",
    ]
    tools = ["compression", "3d-overlap", "xp-memory", "token-optimizer"]
    return {
        "hermes_id": row[0],
        "specialty": row[1],
        "signal_score": float(row[2]),
        "art_pattern_score": float(row[3]),
        "experience_xp": float(xp),
        "level": int(level),
        "speed_bonus": float(speed_bonus),
        "token_power_gain": float(token_power_gain),
        "size_mode": size_mode,
        "specialties": specialties,
        "tools": tools,
        "variables": vars_payload,
    }


def _benefits_and_ideas(art_pattern: Dict[str, float], trend: float) -> tuple[List[str], List[str]]:
    compression_ratio = float(art_pattern.get("compression_ratio", 0.0))
    overlap_3d = float(art_pattern.get("overlap_3d", 0.0))
    fractal_flow = float(art_pattern.get("fractal_flow", 0.0))
    benefits = [
        f"Compression ratio: {compression_ratio * 100.0:.1f}% (higher = more reusable patterns).",
        f"3D overlap coherence: {overlap_3d * 100.0:.1f}% (higher = better cross-variable alignment).",
        f"Fractal flow: {fractal_flow * 100.0:.1f}% (higher = richer long-range pattern dynamics).",
    ]
    ideas: List[str] = []
    if compression_ratio < 0.40:
        ideas.append("Increase retention/knowledge-transfer variables to improve compression and reusable memory.")
    if overlap_3d < 0.55:
        ideas.append("Boost coordination_cohesion and reward_adaptation to tighten 3D overlap zones.")
    if trend < 0.0:
        ideas.append("Run lock mode and reduce wrongness tolerance for 2-3 cycles to stabilize gains.")
    if not ideas:
        ideas.append("Current SQL pattern layer is healthy; push more specialty diversity to find new high-value puzzles.")
    return benefits, ideas


def compute_sql_pattern_intel(volume_root: str, lookback: int = 240) -> Dict[str, object]:
    db = ensure_training_sql(volume_root)
    with _connect(db) as conn:
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
        latest_agents = conn.execute(
            """
            SELECT hermes_id, specialty, signal_score, art_pattern_score, variables_json
            FROM hermes_agent_variables
            ORDER BY id DESC
            LIMIT 30
            """
        ).fetchall()

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
    art_pattern = _art_pattern_metrics(variable_means)
    trend = signals[-1] - signals[0] if len(signals) > 1 else signals[-1]
    pattern_score = max(
        0.0,
        min(
            1.0,
            ((sum(signals) / len(signals)) * 0.36)
            + ((sum(rewards) / len(rewards)) * 0.20)
            + ((sum(truths) / len(truths)) * 0.16)
            + ((sum(shapes) / len(shapes)) * 0.12)
            + (float(art_pattern.get("symmetry_index", 0.0)) * 0.08)
            + (float(art_pattern.get("fractal_flow", 0.0)) * 0.07)
            + (float(art_pattern.get("contrast_index", 0.0)) * 0.06)
            + (float(art_pattern.get("compression_ratio", 0.0)) * 0.06)
            + (float(art_pattern.get("overlap_3d", 0.0)) * 0.05)
            + (trend * 0.10),
        ),
    )
    github_payload = {}
    if latest_github:
        github_payload = {
            "branch": latest_github[0],
            "commit_sha": latest_github[1],
            "commit_subject": latest_github[2],
            "changed_files": int(latest_github[3]),
            "created_unix": float(latest_github[4]),
        }
    recent_hermes_profiles = [_build_recent_hermes_profile(row) for row in latest_agents]
    benefits, ideas = _benefits_and_ideas(art_pattern, trend)
    return {
        "rows": len(rows),
        "pattern_score": float(pattern_score),
        "trend": float(trend),
        "signal_avg": float(sum(signals) / len(signals)),
        "reward_avg": float(sum(rewards) / len(rewards)),
        "truth_avg": float(sum(truths) / len(truths)),
        "shape_avg": float(sum(shapes) / len(shapes)),
        "variable_means": variable_means,
        "art_pattern": art_pattern,
        "latest_github": github_payload,
        "recent_hermes_profiles": recent_hermes_profiles,
        "benefits": benefits,
        "ideas": ideas,
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
    except (subprocess.CalledProcessError, OSError):
        branch = "unknown"
        commit_sha = "unknown"
        commit_subject = ""
        changed_files = 0
    payload = {
        "branch": branch,
        "commit_sha": commit_sha,
        "commit_subject": commit_subject,
        "changed_files": int(changed_files),
        "created_unix": time.time(),
    }
    with _connect(db) as conn:
        conn.execute(
            """
            INSERT INTO github_context (branch, commit_sha, commit_subject, changed_files, created_unix)
            VALUES (?, ?, ?, ?, ?)
            """,
            (payload["branch"], payload["commit_sha"], payload["commit_subject"], payload["changed_files"], payload["created_unix"]),
        )
        conn.commit()
    return payload


def record_hermes_agent_variables(
    volume_root: str,
    cycle: int,
    specialty: str,
    signal_score: float,
    training_variables: Dict[str, float],
    micro_agents: int,
) -> None:
    db = ensure_training_sql(volume_root)
    count = max(6, min(24, int(micro_agents // 12)))
    base = {k: float(v) for k, v in training_variables.items() if isinstance(v, (int, float))}
    rows = []
    now = time.time()
    for idx in range(count):
        ratio = (idx + 1) / max(1.0, float(count))
        agent_vars = dict(base)
        agent_vars["agent_focus"] = max(0.0, min(1.0, base.get("success_signal", 0.5) * (0.7 + ratio * 0.6)))
        agent_vars["agent_exploration"] = max(0.0, min(1.0, base.get("wrongness_signal", 0.3) * (1.2 - ratio * 0.5)))
        agent_vars["agent_memory_depth"] = max(0.0, min(1.0, base.get("retention_strength", 0.5) * (0.8 + ratio * 0.4)))
        art_pattern_score = max(
            0.0,
            min(
                1.0,
                (agent_vars.get("agent_focus", 0.5) * 0.35)
                + ((1.0 - agent_vars.get("agent_exploration", 0.5)) * 0.20)
                + (agent_vars.get("agent_memory_depth", 0.5) * 0.20)
                + (agent_vars.get("coordination_cohesion", 0.5) * 0.25),
            ),
        )
        rows.append(
            (
                int(cycle),
                f"hermes-{idx + 1:03d}",
                str(specialty),
                float(signal_score),
                float(art_pattern_score),
                json.dumps(agent_vars, sort_keys=True),
                now,
            )
        )
    with _connect(db) as conn:
        conn.executemany(
            """
            INSERT INTO hermes_agent_variables (
                cycle, hermes_id, specialty, signal_score, art_pattern_score, variables_json, created_unix
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
