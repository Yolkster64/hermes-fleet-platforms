import json
import math
import os
import sqlite3
import subprocess
import time
from typing import Dict, List

_SCHEMA_READY: set[str] = set()
_SQL_INTEL_CACHE: Dict[str, Dict[str, object]] = {}


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


def _training_volume_health(volume_root: str, db_path: str) -> Dict[str, float]:
    training_dir = os.path.join(volume_root, "training")
    file_count = 0
    total_bytes = 0
    if os.path.isdir(training_dir):
        for name in os.listdir(training_dir):
            path = os.path.join(training_dir, name)
            if not os.path.isfile(path):
                continue
            try:
                st = os.stat(path)
            except OSError:
                continue
            file_count += 1
            total_bytes += int(st.st_size)
    wal_bytes = 0
    wal_path = f"{db_path}-wal"
    if os.path.exists(wal_path):
        try:
            wal_bytes = int(os.path.getsize(wal_path))
        except OSError:
            wal_bytes = 0
    snapshot_path = os.path.join(training_dir, "hermes_agent_profiles_snapshot.json")
    snapshot_age_minutes = -1.0
    if os.path.exists(snapshot_path):
        try:
            snapshot_age_minutes = max(0.0, (time.time() - float(os.path.getmtime(snapshot_path))) / 60.0)
        except OSError:
            snapshot_age_minutes = -1.0
    return {
        "training_files": float(file_count),
        "training_dir_mb": float(total_bytes) / (1024.0 * 1024.0),
        "wal_mb": float(wal_bytes) / (1024.0 * 1024.0),
        "snapshot_age_minutes": float(snapshot_age_minutes),
    }


def optimize_training_sql(volume_root: str, quick: bool = True) -> Dict[str, object]:
    db = ensure_training_sql(volume_root)
    payload = {"wal_checkpoint": "none", "analyze": False, "vacuum": False}
    with _connect(db) as conn:
        try:
            checkpoint_row = conn.execute("PRAGMA wal_checkpoint(PASSIVE)").fetchone()
            if checkpoint_row:
                payload["wal_checkpoint"] = [int(v) for v in checkpoint_row]
        except sqlite3.Error:
            payload["wal_checkpoint"] = "error"
        try:
            conn.execute("ANALYZE")
            payload["analyze"] = True
        except sqlite3.Error:
            payload["analyze"] = False
        if not quick:
            try:
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                payload["vacuum"] = True
            except sqlite3.Error:
                payload["vacuum"] = False
        conn.commit()
    return payload


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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS hermes_agent_profiles (
                hermes_id TEXT PRIMARY KEY,
                specialty TEXT NOT NULL,
                signal_score REAL NOT NULL,
                art_pattern_score REAL NOT NULL,
                experience_xp REAL NOT NULL,
                level INTEGER NOT NULL,
                speed_bonus REAL NOT NULL,
                token_power_gain REAL NOT NULL,
                size_mode TEXT NOT NULL,
                specialties_json TEXT NOT NULL,
                tools_json TEXT NOT NULL,
                variables_json TEXT NOT NULL,
                updated_unix REAL NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS training_evidence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cycle INTEGER NOT NULL,
                occasion TEXT NOT NULL,
                strategy TEXT NOT NULL,
                agent_size TEXT NOT NULL,
                ratio_key TEXT NOT NULL,
                reward REAL NOT NULL,
                truth_score REAL NOT NULL,
                shape_score REAL NOT NULL,
                evidence_score REAL NOT NULL,
                created_unix REAL NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_training_cycles_cycle ON training_cycles(cycle)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_training_cycles_created ON training_cycles(created_unix)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_vars_cycle ON hermes_agent_variables(cycle)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_vars_created ON hermes_agent_variables(created_unix)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_vars_hermes ON hermes_agent_variables(hermes_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_profiles_updated ON hermes_agent_profiles(updated_unix)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_github_context_created ON github_context(created_unix)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_training_evidence_cycle ON training_evidence(cycle)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_training_evidence_created ON training_evidence(created_unix)")
        conn.commit()
    _SCHEMA_READY.add(db)
    return db


def prune_training_sql(
    volume_root: str,
    max_cycles: int = 6000,
    max_agent_rows: int = 24000,
    max_github_rows: int = 4000,
    max_profile_rows: int = 3000,
    max_evidence_rows: int = 12000,
) -> Dict[str, int]:
    db = ensure_training_sql(volume_root)
    pruned = {"training_cycles": 0, "hermes_agent_variables": 0, "github_context": 0, "hermes_agent_profiles": 0, "training_evidence": 0}
    with _connect(db) as conn:
        conn.execute(
            """
            DELETE FROM training_cycles
            WHERE id < COALESCE(
                (
                    SELECT id
                    FROM training_cycles
                    ORDER BY id DESC
                    LIMIT 1 OFFSET ?
                ),
                -1
            )
            """,
            (max(0, int(max_cycles) - 1),),
        )
        pruned["training_cycles"] = int(conn.total_changes)
        conn.execute(
            """
            DELETE FROM hermes_agent_variables
            WHERE id < COALESCE(
                (
                    SELECT id
                    FROM hermes_agent_variables
                    ORDER BY id DESC
                    LIMIT 1 OFFSET ?
                ),
                -1
            )
            """,
            (max(0, int(max_agent_rows) - 1),),
        )
        pruned["hermes_agent_variables"] = int(conn.total_changes) - pruned["training_cycles"]
        conn.execute(
            """
            DELETE FROM github_context
            WHERE id < COALESCE(
                (
                    SELECT id
                    FROM github_context
                    ORDER BY id DESC
                    LIMIT 1 OFFSET ?
                ),
                -1
            )
            """,
            (max(0, int(max_github_rows) - 1),),
        )
        pruned["github_context"] = int(conn.total_changes) - pruned["training_cycles"] - pruned["hermes_agent_variables"]
        conn.execute(
            """
            DELETE FROM hermes_agent_profiles
            WHERE hermes_id NOT IN (
                SELECT hermes_id
                FROM hermes_agent_profiles
                ORDER BY updated_unix DESC
                LIMIT ?
            )
            """,
            (int(max_profile_rows),),
        )
        pruned["hermes_agent_profiles"] = (
            int(conn.total_changes) - pruned["training_cycles"] - pruned["hermes_agent_variables"] - pruned["github_context"]
        )
        conn.execute(
            """
            DELETE FROM training_evidence
            WHERE id < COALESCE(
                (
                    SELECT id
                    FROM training_evidence
                    ORDER BY id DESC
                    LIMIT 1 OFFSET ?
                ),
                -1
            )
            """,
            (max(0, int(max_evidence_rows) - 1),),
        )
        pruned["training_evidence"] = (
            int(conn.total_changes)
            - pruned["training_cycles"]
            - pruned["hermes_agent_variables"]
            - pruned["github_context"]
            - pruned["hermes_agent_profiles"]
        )
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
                json.dumps(training_variables),
                time.time(),
            ),
        )
        conn.commit()


def record_training_evidence(
    volume_root: str,
    cycle: int,
    occasion: str,
    strategy: str,
    agent_size: str,
    ratio_key: str,
    reward: float,
    truth_score: float,
    shape_score: float,
    evidence_score: float,
) -> None:
    db = ensure_training_sql(volume_root)
    with _connect(db) as conn:
        conn.execute(
            """
            INSERT INTO training_evidence (
                cycle, occasion, strategy, agent_size, ratio_key, reward, truth_score, shape_score, evidence_score, created_unix
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(cycle),
                str(occasion),
                str(strategy),
                str(agent_size),
                str(ratio_key),
                float(reward),
                float(truth_score),
                float(shape_score),
                float(evidence_score),
                time.time(),
            ),
        )
        conn.commit()


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _read_git_context(repo_root: str) -> tuple[str, str, str, int]:
    branch = "unknown"
    commit_sha = "unknown"
    commit_subject = ""
    changed_files = 0
    try:
        status_out = subprocess.check_output(
            ["git", "--no-pager", "status", "--short", "--branch"],
            cwd=repo_root,
            text=True,
            timeout=6,
        )
        status_lines = [line for line in status_out.splitlines() if line.strip()]
        if status_lines:
            head = status_lines[0].strip()
            if head.startswith("## "):
                branch = head[3:].split("...", 1)[0].strip() or "unknown"
            changed_files = sum(1 for line in status_lines[1:] if line and not line.startswith("## "))
        log_out = subprocess.check_output(
            ["git", "--no-pager", "log", "-1", "--pretty=%h|%s"],
            cwd=repo_root,
            text=True,
            timeout=6,
        ).strip()
        if "|" in log_out:
            sha, subject = log_out.split("|", 1)
            commit_sha = sha.strip() or "unknown"
            commit_subject = subject.strip()
    except (subprocess.CalledProcessError, OSError, subprocess.TimeoutExpired):
        return "unknown", "unknown", "", 0
    return branch, commit_sha, commit_subject, int(changed_files)


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


def _derive_hermes_profile_fields(signal_score: float, art_pattern_score: float, vars_payload: Dict[str, object]) -> Dict[str, object]:
    watch_efficiency = _clamp01(float(vars_payload.get("watch_efficiency", 0.5)))
    xp = max(
        0.0,
        min(
            10000.0,
            (
                float(signal_score) * 2200.0
                + float(art_pattern_score) * 1800.0
                + float(vars_payload.get("retention_strength", 0.5)) * 1600.0
                + float(vars_payload.get("knowledge_transfer", 0.5)) * 1400.0
                + watch_efficiency * 1000.0
            ),
        ),
    )
    level = max(1, min(99, int(1 + (xp / 140.0))))
    speed_bonus = _clamp01(
        float(vars_payload.get("speed_efficiency", 0.5)) * 0.65
        + float(vars_payload.get("position_score", 0.5)) * 0.20
        + watch_efficiency * 0.15
    )
    token_power_gain = _clamp01(float(vars_payload.get("yield_efficiency", 0.5)) * 0.60 + float(art_pattern_score) * 0.25 + watch_efficiency * 0.15)
    size_mode = "mini" if float(vars_payload.get("size_factor", 0.5)) < 0.45 else ("full" if float(vars_payload.get("size_factor", 0.5)) > 0.70 else "mid")
    specialties = [
        "pattern-hunter",
        "sql-reasoner" if float(vars_payload.get("retention_strength", 0.5)) > 0.55 else "fast-explorer",
        "aihub-bridge" if float(vars_payload.get("knowledge_transfer", 0.5)) > 0.55 else "field-adapter",
    ]
    if watch_efficiency > 0.56:
        specialties.append("observer-core")
    tools = ["compression", "3d-overlap", "xp-memory", "token-optimizer", "watch-grid"]
    return {
        "experience_xp": float(xp),
        "level": int(level),
        "speed_bonus": float(speed_bonus),
        "token_power_gain": float(token_power_gain),
        "size_mode": size_mode,
        "specialties": specialties,
        "tools": tools,
    }


def _build_recent_hermes_profile(row: tuple) -> Dict[str, object]:
    vars_payload = json.loads(row[4]) if isinstance(row[4], str) and row[4] else {}
    if not isinstance(vars_payload, dict):
        vars_payload = {}
    profile_fields = _derive_hermes_profile_fields(float(row[2]), float(row[3]), vars_payload)
    return {
        "hermes_id": row[0],
        "specialty": row[1],
        "signal_score": float(row[2]),
        "art_pattern_score": float(row[3]),
        "experience_xp": profile_fields["experience_xp"],
        "level": profile_fields["level"],
        "speed_bonus": profile_fields["speed_bonus"],
        "token_power_gain": profile_fields["token_power_gain"],
        "size_mode": profile_fields["size_mode"],
        "specialties": profile_fields["specialties"],
        "tools": profile_fields["tools"],
        "variables": vars_payload,
    }


def _build_saved_hermes_profile(row: tuple) -> Dict[str, object]:
    specialties = json.loads(row[9]) if isinstance(row[9], str) and row[9] else []
    tools = json.loads(row[10]) if isinstance(row[10], str) and row[10] else []
    variables = json.loads(row[11]) if isinstance(row[11], str) and row[11] else {}
    if not isinstance(specialties, list):
        specialties = []
    if not isinstance(tools, list):
        tools = []
    if not isinstance(variables, dict):
        variables = {}
    return {
        "hermes_id": str(row[0]),
        "specialty": str(row[1]),
        "signal_score": float(row[2]),
        "art_pattern_score": float(row[3]),
        "experience_xp": float(row[4]),
        "level": int(row[5]),
        "speed_bonus": float(row[6]),
        "token_power_gain": float(row[7]),
        "size_mode": str(row[8]),
        "specialties": specialties,
        "tools": tools,
        "variables": variables,
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
    cache = _SQL_INTEL_CACHE.get(db, {})
    cache_window = max(1, min(2000, int(lookback)))
    with _connect(db) as conn:
        latest_cycle_id_row = conn.execute("SELECT COALESCE(MAX(id), 0) FROM training_cycles").fetchone()
        latest_cycle_id = int(latest_cycle_id_row[0]) if latest_cycle_id_row else 0
        if (
            cache
            and int(cache.get("latest_cycle_id", -1)) == latest_cycle_id
            and int(cache.get("lookback", 0)) == cache_window
            and isinstance(cache.get("payload"), dict)
        ):
            return dict(cache["payload"])
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
        saved_profiles = conn.execute(
            """
            SELECT
                hermes_id, specialty, signal_score, art_pattern_score, experience_xp,
                level, speed_bonus, token_power_gain, size_mode, specialties_json, tools_json, variables_json
            FROM hermes_agent_profiles
            ORDER BY updated_unix DESC
            LIMIT 30
            """
        ).fetchall()
        evidence_rows = conn.execute(
            """
            SELECT evidence_score, reward, truth_score, shape_score, strategy
            FROM training_evidence
            ORDER BY id DESC
            LIMIT ?
            """,
            (max(12, min(lookback, 300)),),
        ).fetchall()
        total_cycles = conn.execute("SELECT COUNT(1) FROM training_cycles").fetchone()
        total_agents = conn.execute("SELECT COUNT(1) FROM hermes_agent_variables").fetchone()
        total_profiles = conn.execute("SELECT COUNT(1) FROM hermes_agent_profiles").fetchone()
        total_github = conn.execute("SELECT COUNT(1) FROM github_context").fetchone()
        total_evidence = conn.execute("SELECT COUNT(1) FROM training_evidence").fetchone()

    if not rows:
        return {"rows": 0, "pattern_score": 0.0, "trend": 0.0, "variable_means": {}, "latest_github": {}}

    rows = list(reversed(rows))
    signals = [float(r[1]) for r in rows]
    rewards = [float(r[2]) for r in rows]
    truths = [float(r[3]) for r in rows]
    shapes = [float(r[4]) for r in rows]
    tail_n = min(64, len(rows))
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
    if saved_profiles:
        recent_hermes_profiles = [_build_saved_hermes_profile(row) for row in saved_profiles]
    else:
        recent_hermes_profiles = [_build_recent_hermes_profile(row) for row in latest_agents]
    evidence_payload: Dict[str, object]
    if evidence_rows:
        ev_count = len(evidence_rows)
        strategy_counts: Dict[str, int] = {}
        for row in evidence_rows:
            key = str(row[4] or "unknown")
            strategy_counts[key] = strategy_counts.get(key, 0) + 1
        top_strategy = max(strategy_counts.items(), key=lambda item: item[1])[0] if strategy_counts else "unknown"
        evidence_payload = {
            "rows": ev_count,
            "score": float(sum(float(r[0]) for r in evidence_rows) / ev_count),
            "reward": float(sum(float(r[1]) for r in evidence_rows) / ev_count),
            "truth": float(sum(float(r[2]) for r in evidence_rows) / ev_count),
            "shape": float(sum(float(r[3]) for r in evidence_rows) / ev_count),
            "top_strategy": top_strategy,
        }
    else:
        evidence_payload = {"rows": 0, "score": 0.0, "reward": 0.0, "truth": 0.0, "shape": 0.0, "top_strategy": "unknown"}
    benefits, ideas = _benefits_and_ideas(art_pattern, trend)
    db_bytes = os.path.getsize(db) if os.path.exists(db) else 0
    volume_health = _training_volume_health(volume_root, db)
    payload = {
        "rows": len(rows),
        "pattern_score": float(pattern_score),
        "trend": float(trend),
        "signal_avg": float(sum(signals) / len(signals)),
        "reward_avg": float(sum(rewards) / len(rewards)),
        "truth_avg": float(sum(truths) / len(truths)),
        "shape_avg": float(sum(shapes) / len(shapes)),
        "signal_series": signals[-tail_n:],
        "reward_series": rewards[-tail_n:],
        "truth_series": truths[-tail_n:],
        "shape_series": shapes[-tail_n:],
        "variable_means": variable_means,
        "art_pattern": art_pattern,
        "latest_github": github_payload,
        "recent_hermes_profiles": recent_hermes_profiles,
        "evidence": evidence_payload,
        "sql_health": {
            "db_mb": float(db_bytes) / (1024.0 * 1024.0),
            "total_cycles": int(total_cycles[0]) if total_cycles else len(rows),
            "total_agent_rows": int(total_agents[0]) if total_agents else 0,
            "total_profile_rows": int(total_profiles[0]) if total_profiles else 0,
            "total_github_rows": int(total_github[0]) if total_github else 0,
            "total_evidence_rows": int(total_evidence[0]) if total_evidence else 0,
            "training_files": float(volume_health.get("training_files", 0.0)),
            "training_dir_mb": float(volume_health.get("training_dir_mb", 0.0)),
            "wal_mb": float(volume_health.get("wal_mb", 0.0)),
            "snapshot_age_minutes": float(volume_health.get("snapshot_age_minutes", -1.0)),
        },
        "benefits": benefits,
        "ideas": ideas,
    }
    _SQL_INTEL_CACHE[db] = {
        "latest_cycle_id": latest_cycle_id,
        "lookback": cache_window,
        "payload": payload,
    }
    return payload


def ingest_github_context(volume_root: str, repo_root: str) -> Dict[str, object]:
    db = ensure_training_sql(volume_root)
    branch, commit_sha, commit_subject, changed_files = _read_git_context(repo_root)
    payload = {
        "branch": branch,
        "commit_sha": commit_sha,
        "commit_subject": commit_subject,
        "changed_files": int(changed_files),
        "created_unix": time.time(),
    }
    with _connect(db) as conn:
        latest = conn.execute(
            """
            SELECT branch, commit_sha, commit_subject, changed_files, created_unix
            FROM github_context
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()
        if latest and (
            latest[0] == payload["branch"]
            and latest[1] == payload["commit_sha"]
            and latest[2] == payload["commit_subject"]
            and int(latest[3]) == payload["changed_files"]
        ):
            return {
                "branch": str(latest[0]),
                "commit_sha": str(latest[1]),
                "commit_subject": str(latest[2]),
                "changed_files": int(latest[3]),
                "created_unix": float(latest[4]),
            }
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
    profile_rows = []
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
                json.dumps(agent_vars),
                now,
            )
        )
        profile = _derive_hermes_profile_fields(float(signal_score), float(art_pattern_score), agent_vars)
        profile_rows.append(
            (
                f"hermes-{idx + 1:03d}",
                str(specialty),
                float(signal_score),
                float(art_pattern_score),
                float(profile["experience_xp"]),
                int(profile["level"]),
                float(profile["speed_bonus"]),
                float(profile["token_power_gain"]),
                str(profile["size_mode"]),
                json.dumps(profile["specialties"]),
                json.dumps(profile["tools"]),
                json.dumps(agent_vars),
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
        conn.executemany(
            """
            INSERT INTO hermes_agent_profiles (
                hermes_id, specialty, signal_score, art_pattern_score, experience_xp,
                level, speed_bonus, token_power_gain, size_mode, specialties_json, tools_json, variables_json, updated_unix
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(hermes_id) DO UPDATE SET
                specialty=excluded.specialty,
                signal_score=excluded.signal_score,
                art_pattern_score=excluded.art_pattern_score,
                experience_xp=excluded.experience_xp,
                level=excluded.level,
                speed_bonus=excluded.speed_bonus,
                token_power_gain=excluded.token_power_gain,
                size_mode=excluded.size_mode,
                specialties_json=excluded.specialties_json,
                tools_json=excluded.tools_json,
                variables_json=excluded.variables_json,
                updated_unix=excluded.updated_unix
            """,
            profile_rows,
        )
        conn.commit()


def export_hermes_profiles_snapshot(volume_root: str, max_rows: int = 200) -> Dict[str, object]:
    db = ensure_training_sql(volume_root)
    output_path = os.path.join(volume_root, "training", "hermes_agent_profiles_snapshot.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with _connect(db) as conn:
        rows = conn.execute(
            """
            SELECT
                hermes_id, specialty, signal_score, art_pattern_score, experience_xp,
                level, speed_bonus, token_power_gain, size_mode, specialties_json, tools_json, variables_json, updated_unix
            FROM hermes_agent_profiles
            ORDER BY updated_unix DESC
            LIMIT ?
            """,
            (max(1, int(max_rows)),),
        ).fetchall()
    profiles: List[Dict[str, object]] = []
    for row in rows:
        profile = _build_saved_hermes_profile(row[:12])
        profile["updated_unix"] = float(row[12])
        profiles.append(profile)
    payload = {
        "created_unix": time.time(),
        "rows": len(profiles),
        "profiles": profiles,
    }
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=True, separators=(",", ":"))
    return {"path": output_path, "rows": len(profiles), "created_unix": payload["created_unix"]}
