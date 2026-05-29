import json
import copy
import hashlib
import os
import random
import sqlite3
import threading
import time
import zlib
from dataclasses import dataclass, asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict, List, Optional

try:
    from .hermes_cpp_native_bridge import HermesCppNativeBridge
except ImportError:
    from hermes_cpp_native_bridge import HermesCppNativeBridge

try:
    import psutil
except ImportError:  # Optional dependency
    psutil = None

try:
    import torch
except ImportError:  # Optional dependency
    torch = None


@dataclass
class AgentProfile:
    name: str
    specialty: str
    reward_score: float = 0.0
    success_rate: float = 0.5
    load: float = 0.0
    active: bool = True


@dataclass
class InteractionOutcome:
    quality: float
    speed: float
    cost_efficiency: float
    truth_score: float
    novelty: float
    compression_gain: float
    data_freshness: float
    pattern_diversity: float
    risk_adjusted: float
    success: float


class SqlTelemetryStore:
    def __init__(self, db_path: str = "runtime/auto/hermes_super_orchestrator.db") -> None:
        env_db_path = os.getenv("HERMES_TELEMETRY_DB_PATH")
        if env_db_path:
            db_path = env_db_path
        if os.path.isabs(db_path):
            resolved = db_path
        else:
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            resolved = os.path.abspath(os.path.join(repo_root, db_path))
        os.makedirs(os.path.dirname(resolved), exist_ok=True)
        self.db_path = resolved
        self._max_external_payload_bytes = int(os.getenv("HERMES_MAX_EXTERNAL_SIGNAL_BYTES", "65536"))
        self._prune_interval_seconds = float(os.getenv("HERMES_TELEMETRY_PRUNE_INTERVAL_SECONDS", "20"))
        self._prune_on_start = os.getenv("HERMES_TELEMETRY_PRUNE_ON_START", "false").lower() in ("1", "true", "yes", "on")
        self._max_rows = {
            "agent_metrics": int(os.getenv("HERMES_MAX_AGENT_METRICS_ROWS", "25000")),
            "orchestrator_events": int(os.getenv("HERMES_MAX_ORCHESTRATOR_EVENTS_ROWS", "12000")),
            "horizon_test_scores": int(os.getenv("HERMES_MAX_HORIZON_SCORES_ROWS", "12000")),
            "llm_output_rankings": int(os.getenv("HERMES_MAX_LLM_RANKINGS_ROWS", "12000")),
            "temporal_memory_bands": int(os.getenv("HERMES_MAX_MEMORY_BANDS_ROWS", "6000")),
            "external_signals": int(os.getenv("HERMES_MAX_EXTERNAL_SIGNALS_ROWS", "8000")),
            "fleet_optimization_runs": int(os.getenv("HERMES_MAX_FLEET_RUN_ROWS", "8000")),
            "dedupe_candidates": int(os.getenv("HERMES_MAX_DEDUPE_CANDIDATES_ROWS", "10000")),
            "knowledge_mesh_links": int(os.getenv("HERMES_MAX_KNOWLEDGE_MESH_ROWS", "12000")),
        }
        self._last_prune = 0.0
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)
        try:
            conn.execute("PRAGMA journal_mode=WAL")
        except sqlite3.OperationalError:
            conn.execute("PRAGMA journal_mode=DELETE")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute(f"PRAGMA busy_timeout={int(os.getenv('HERMES_SQLITE_BUSY_TIMEOUT_MS', '5000'))}")
        return conn

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    agent_name TEXT NOT NULL,
                    reward_score REAL NOT NULL,
                    success_rate REAL NOT NULL,
                    load REAL NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS orchestrator_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    event_type TEXT NOT NULL,
                    payload_compressed BLOB NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS horizon_test_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    horizon TEXT NOT NULL,
                    specialty TEXT NOT NULL,
                    score REAL NOT NULL,
                    quality REAL NOT NULL,
                    speed REAL NOT NULL,
                    cost_efficiency REAL NOT NULL,
                    truth_score REAL NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS llm_output_rankings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    goal TEXT NOT NULL,
                    output_hash TEXT NOT NULL,
                    rank_score REAL NOT NULL,
                    quality REAL NOT NULL,
                    speed REAL NOT NULL,
                    cost_efficiency REAL NOT NULL,
                    truth_score REAL NOT NULL,
                    shape3d_x REAL NOT NULL,
                    shape3d_y REAL NOT NULL,
                    shape3d_z REAL NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS temporal_memory_bands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    band TEXT NOT NULL,
                    ttl_class TEXT NOT NULL,
                    retention_score REAL NOT NULL,
                    payload_compressed BLOB NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS external_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    source TEXT NOT NULL,
                    signal_score REAL NOT NULL,
                    payload_compressed BLOB NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS fleet_optimization_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    specialty TEXT NOT NULL,
                    team_shape TEXT NOT NULL,
                    active_agents INTEGER NOT NULL,
                    score REAL NOT NULL,
                    payload_compressed BLOB NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS dedupe_candidates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    file_hash TEXT NOT NULL,
                    file_count INTEGER NOT NULL,
                    total_bytes INTEGER NOT NULL,
                    sample_path TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS knowledge_mesh_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    source_agent TEXT NOT NULL,
                    target_agent TEXT NOT NULL,
                    task_family TEXT NOT NULL,
                    pattern_hash TEXT NOT NULL,
                    shape_x REAL NOT NULL,
                    shape_y REAL NOT NULL,
                    shape_z REAL NOT NULL,
                    weight REAL NOT NULL,
                    confidence REAL NOT NULL,
                    payload_compressed BLOB NOT NULL
                )
                """
            )
            if self._prune_on_start:
                self._prune_locked(conn, force=True)

    def _prune_table_locked(self, conn: sqlite3.Connection, table: str, max_rows: int) -> None:
        conn.execute(
            f"""
            DELETE FROM {table}
            WHERE id IN (
                SELECT id FROM {table}
                ORDER BY id DESC
                LIMIT -1 OFFSET ?
            )
            """,
            (max_rows,),
        )

    def _prune_locked(self, conn: sqlite3.Connection, force: bool = False) -> None:
        now = time.time()
        if not force and (now - self._last_prune) < self._prune_interval_seconds:
            return
        for table, max_rows in self._max_rows.items():
            self._prune_table_locked(conn, table, max_rows)
        self._last_prune = now

    def _write_with_retry(self, conn: sqlite3.Connection, query: str, params: tuple) -> None:
        retries = int(os.getenv("HERMES_SQLITE_WRITE_RETRIES", "3"))
        base_delay = float(os.getenv("HERMES_SQLITE_WRITE_RETRY_DELAY_SECONDS", "0.03"))
        for attempt in range(max(1, retries)):
            try:
                conn.execute(query, params)
                return
            except sqlite3.OperationalError as exc:
                if "locked" not in str(exc).lower() or attempt >= (retries - 1):
                    raise
                time.sleep(base_delay * (attempt + 1))

    def write_metric(self, agent: AgentProfile) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO agent_metrics(ts, agent_name, reward_score, success_rate, load)
                VALUES (?, ?, ?, ?, ?)
                """,
                (time.time(), agent.name, agent.reward_score, agent.success_rate, agent.load),
            )
            self._prune_locked(conn)

    def write_event(self, event_type: str, payload: Dict) -> None:
        compressed = zlib.compress(json.dumps(payload).encode("utf-8"))
        with self._conn() as conn:
            self._write_with_retry(
                conn,
                "INSERT INTO orchestrator_events(ts, event_type, payload_compressed) VALUES (?, ?, ?)",
                (time.time(), event_type, compressed),
            )
            self._prune_locked(conn)

    def recent_events(self, limit: int = 25) -> List[Dict]:
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT ts, event_type, payload_compressed
                FROM orchestrator_events
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        out: List[Dict] = []
        for ts, event_type, payload in rows:
            out.append(
                {
                    "ts": ts,
                    "event_type": event_type,
                    "payload": json.loads(zlib.decompress(payload).decode("utf-8")),
                }
            )
        return out

    def write_horizon_score(self, horizon: str, specialty: str, score: float, outcome: InteractionOutcome) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO horizon_test_scores(
                    ts, horizon, specialty, score, quality, speed, cost_efficiency, truth_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    time.time(),
                    horizon,
                    specialty,
                    score,
                    outcome.quality,
                    outcome.speed,
                    outcome.cost_efficiency,
                    outcome.truth_score,
                ),
            )
            self._prune_locked(conn)

    def write_llm_ranking(
        self,
        goal: str,
        output_hash: str,
        rank_score: float,
        quality: float,
        speed: float,
        cost_efficiency: float,
        truth_score: float,
        shape3d: tuple[float, float, float],
    ) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO llm_output_rankings(
                    ts, goal, output_hash, rank_score, quality, speed, cost_efficiency, truth_score, shape3d_x, shape3d_y, shape3d_z
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    time.time(),
                    goal,
                    output_hash,
                    rank_score,
                    quality,
                    speed,
                    cost_efficiency,
                    truth_score,
                    shape3d[0],
                    shape3d[1],
                    shape3d[2],
                ),
            )
            self._prune_locked(conn)

    def write_memory_band(self, band: str, ttl_class: str, retention_score: float, payload: Dict) -> None:
        compressed = zlib.compress(json.dumps(payload).encode("utf-8"))
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO temporal_memory_bands(ts, band, ttl_class, retention_score, payload_compressed)
                VALUES (?, ?, ?, ?, ?)
                """,
                (time.time(), band, ttl_class, retention_score, compressed),
            )
            self._prune_locked(conn)

    def write_external_signal(self, source: str, signal_score: float, payload: Dict) -> None:
        raw = json.dumps(payload, default=str)
        if len(raw.encode("utf-8")) > self._max_external_payload_bytes:
            payload = {
                "truncated": True,
                "reason": "payload_too_large",
                "max_bytes": self._max_external_payload_bytes,
                "keys": list(payload.keys())[:50] if isinstance(payload, dict) else [],
                "preview": raw[: self._max_external_payload_bytes],
            }
        compressed = zlib.compress(json.dumps(payload).encode("utf-8"))
        with self._conn() as conn:
            self._write_with_retry(
                conn,
                """
                INSERT INTO external_signals(ts, source, signal_score, payload_compressed)
                VALUES (?, ?, ?, ?)
                """,
                (time.time(), source, signal_score, compressed),
            )
            self._prune_locked(conn)

    def recent_external_signal_score(self, lookback: int = 40) -> float:
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT signal_score
                FROM external_signals
                ORDER BY id DESC
                LIMIT ?
                """,
                (lookback,),
            ).fetchall()
        if not rows:
            return 0.5
        return sum(r[0] for r in rows) / len(rows)

    def recent_external_signal_score_by_source(self, source_like: str, lookback: int = 80) -> float:
        token = f"%{source_like.lower()}%"
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT signal_score
                FROM external_signals
                WHERE lower(source) LIKE ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (token, lookback),
            ).fetchall()
        if not rows:
            return 0.5
        return sum(r[0] for r in rows) / len(rows)

    def recent_external_signals(self, limit: int = 20) -> List[Dict]:
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT ts, source, signal_score, payload_compressed
                FROM external_signals
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        out: List[Dict] = []
        for ts, source, signal_score, payload in rows:
            out.append(
                {
                    "ts": ts,
                    "source": source,
                    "signal_score": signal_score,
                    "payload": json.loads(zlib.decompress(payload).decode("utf-8")),
                }
            )
        return out

    def write_fleet_optimization_run(self, specialty: str, team_shape: str, active_agents: int, score: float, payload: Dict) -> None:
        compressed = zlib.compress(json.dumps(payload).encode("utf-8"))
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO fleet_optimization_runs(ts, specialty, team_shape, active_agents, score, payload_compressed)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (time.time(), specialty, team_shape, active_agents, score, compressed),
            )
            self._prune_locked(conn)

    def write_dedupe_candidate(self, file_hash: str, file_count: int, total_bytes: int, sample_path: str) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO dedupe_candidates(ts, file_hash, file_count, total_bytes, sample_path)
                VALUES (?, ?, ?, ?, ?)
                """,
                (time.time(), file_hash, file_count, total_bytes, sample_path),
            )
            self._prune_locked(conn)

    def write_knowledge_mesh_link(
        self,
        source_agent: str,
        target_agent: str,
        task_family: str,
        pattern_hash: str,
        shape3d: tuple[float, float, float],
        weight: float,
        confidence: float,
        payload: Dict,
    ) -> None:
        compressed = zlib.compress(json.dumps(payload).encode("utf-8"))
        with self._conn() as conn:
            self._write_with_retry(
                conn,
                """
                INSERT INTO knowledge_mesh_links(
                    ts, source_agent, target_agent, task_family, pattern_hash,
                    shape_x, shape_y, shape_z, weight, confidence, payload_compressed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    time.time(),
                    source_agent,
                    target_agent,
                    task_family,
                    pattern_hash,
                    shape3d[0],
                    shape3d[1],
                    shape3d[2],
                    weight,
                    confidence,
                    compressed,
                ),
            )
            self._prune_locked(conn)

    def recent_knowledge_mesh_links(self, limit: int = 40) -> List[Dict]:
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT ts, source_agent, target_agent, task_family, pattern_hash, shape_x, shape_y, shape_z, weight, confidence, payload_compressed
                FROM knowledge_mesh_links
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        out: List[Dict] = []
        for row in rows:
            ts, source_agent, target_agent, task_family, pattern_hash, shape_x, shape_y, shape_z, weight, confidence, payload = row
            out.append(
                {
                    "ts": ts,
                    "source_agent": source_agent,
                    "target_agent": target_agent,
                    "task_family": task_family,
                    "pattern_hash": pattern_hash,
                    "shape3d": [shape_x, shape_y, shape_z],
                    "weight": weight,
                    "confidence": confidence,
                    "payload": json.loads(zlib.decompress(payload).decode("utf-8")),
                }
            )
        return out

    def knowledge_mesh_summary(self) -> Dict:
        with self._conn() as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(*) AS link_count,
                    COUNT(DISTINCT source_agent || '->' || target_agent) AS unique_paths,
                    COUNT(DISTINCT task_family) AS task_families,
                    COALESCE(AVG(weight), 0.0) AS avg_weight,
                    COALESCE(AVG(confidence), 0.0) AS avg_confidence
                FROM knowledge_mesh_links
                """
            ).fetchone()
        return {
            "link_count": int(row[0]) if row else 0,
            "unique_paths": int(row[1]) if row else 0,
            "task_families": int(row[2]) if row else 0,
            "avg_weight": float(row[3]) if row else 0.0,
            "avg_confidence": float(row[4]) if row else 0.0,
        }

    def knowledge_mesh_task_signal(self, task_family_like: str) -> float:
        token = f"%{task_family_like.lower()}%"
        with self._conn() as conn:
            row = conn.execute(
                """
                SELECT COALESCE(AVG((weight * 0.6) + (confidence * 0.4)), 0.0)
                FROM knowledge_mesh_links
                WHERE lower(task_family) LIKE ?
                """,
                (token,),
            ).fetchone()
        return float(row[0]) if row else 0.0


class ResourceGovernor:
    def __init__(self, gpu_target_utilization: float = 0.75, cpu_target_utilization: float = 0.8) -> None:
        self.gpu_target_utilization = gpu_target_utilization
        self.cpu_target_utilization = cpu_target_utilization

    def _gpu_pressure(self) -> float:
        if not torch or not torch.cuda.is_available():
            return 0.0
        total = torch.cuda.get_device_properties(0).total_memory
        used = torch.cuda.memory_allocated(0)
        if total <= 0:
            return 0.0
        return float(used) / float(total)

    def pressure(self) -> Dict[str, float]:
        if psutil:
            cpu = psutil.cpu_percent(interval=0.05) / 100.0
            mem = psutil.virtual_memory().percent / 100.0
        else:
            cpu = 0.5
            mem = 0.5
        gpu = self._gpu_pressure()
        return {"cpu": cpu, "memory": mem, "gpu": gpu}

    def capacity_scale(self) -> float:
        p = self.pressure()
        cpu_headroom = max(0.05, self.cpu_target_utilization - p["cpu"])
        gpu_headroom = max(0.05, self.gpu_target_utilization - p["gpu"])
        mem_headroom = max(0.05, 0.9 - p["memory"])
        return min(1.0, cpu_headroom, gpu_headroom, mem_headroom) / 0.75


class HermesSuperOrchestrator:
    def __init__(self, agents: List[AgentProfile], store: Optional[SqlTelemetryStore] = None) -> None:
        self.agents = agents
        self.store = store or SqlTelemetryStore()
        gpu_target = float(os.getenv("HERMES_GPU_TARGET_UTILIZATION", "0.75"))
        cpu_target = float(os.getenv("HERMES_CPU_TARGET_UTILIZATION", "0.80"))
        self.governor = ResourceGovernor(gpu_target_utilization=gpu_target, cpu_target_utilization=cpu_target)
        self.low_bandwidth_mode = os.getenv("HERMES_LOW_BANDWIDTH_MODE", "true").lower() in ("1", "true", "yes", "on")
        self.offline_only_mode = os.getenv("HERMES_OFFLINE_ONLY", "false").lower() in ("1", "true", "yes", "on")
        self.user_routed_internet = os.getenv("HERMES_USER_ROUTED_INTERNET", "true").lower() in ("1", "true", "yes", "on")
        self.mcp_server = os.getenv("HERMES_MCP_SERVER", "github")
        self.fleet_model_label = os.getenv("HERMES_FLEET_MODEL_LABEL", "hermes-fleet-newest")
        self.unified_config = {
            "single_exe_entrypoint": os.getenv("HERMES_SINGLE_EXE_ENTRYPOINT", "hermes-gateway"),
            "aihub_unified_enabled": os.getenv("AIHUB_UNIFIED_ENABLED", "true").lower() in ("1", "true", "yes", "on"),
            "aihub_shared_model_id": os.getenv("AIHUB_SHARED_MODEL_ID", "hermes-fleet-latest"),
            "aihub_shared_ml_profile": os.getenv("AIHUB_SHARED_ML_PROFILE", "global-learning"),
            "llm_api_provider": "temp-api",
            "llm_api_url": "internal://temp-llm",
            "llm_api_model": "aihub-unified-temp",
            "mcp_server": self.mcp_server,
            "fleet_model_label": self.fleet_model_label,
            "low_bandwidth_mode": self.low_bandwidth_mode,
            "offline_only_mode": self.offline_only_mode,
            "user_routed_internet": self.user_routed_internet,
        }
        self.reward_weights = {
            "quality": 0.22,
            "speed": 0.16,
            "cost": 0.12,
            "truth": 0.21,
            "novelty": 0.08,
            "compression": 0.07,
            "freshness": 0.07,
            "diversity": 0.04,
            "risk": 0.03,
        }
        self.horizon_weights = {
            "short": {"quality": 0.28, "speed": 0.30, "cost": 0.12, "truth": 0.20, "compression": 0.10},
            "mid": {"quality": 0.26, "speed": 0.20, "cost": 0.20, "truth": 0.24, "compression": 0.10},
            "long": {"quality": 0.24, "speed": 0.10, "cost": 0.20, "truth": 0.30, "compression": 0.16},
        }
        self.truth_threshold = 0.68
        self.native_bridge = HermesCppNativeBridge()
        self.cpp_native_library_path = self.native_bridge.dll_path
        self.algorithm_state = {
            "bandit_values": {},  # specialty -> value
            "q_table": {},  # (specialty, bin) -> value
            "beta_priors": {},  # specialty -> (alpha, beta)
            "horizon_memory": {"short": [], "mid": [], "long": []},
            "knaa_qnaa_memory": [],
            "punishment_memory": [],
            "fleet_shape_memory": [],
            "long_haul_meta_memory": [],
            "aihub_bonus_memory": [],
            "adaptive_brain_memory": [],
            "hard_facts": {},
            "adaptive_dynamic_modifiers": {},
        }
        self.goal_shape_targets = {
            "quality": (0.90, 0.62, 0.52),
            "speed": (0.74, 0.92, 0.60),
            "cost": (0.68, 0.70, 0.93),
            "balanced": (0.82, 0.82, 0.82),
        }
        self.learning_state_path = os.getenv("HERMES_ORCHESTRATOR_STATE_PATH", "runtime/hermes_persist/hermes_orchestrator_state.json")
        self.learning_state_save_interval = float(os.getenv("HERMES_ORCHESTRATOR_STATE_SAVE_SECONDS", "12"))
        self._last_learning_state_save = 0.0
        self.lock = threading.Lock()
        self.unified_config["cpp_native_kernel_available"] = self.native_bridge.available
        self.unified_config["cpp_native_library"] = self.cpp_native_library_path
        self._load_learning_state()

    def _resolved_learning_state_path(self) -> str:
        if os.path.isabs(self.learning_state_path):
            return self.learning_state_path
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        return os.path.abspath(os.path.join(repo_root, self.learning_state_path))

    def _serialize_algorithm_state(self) -> Dict:
        max_q_states = int(os.getenv("HERMES_STATE_MAX_Q_TABLE", "6000"))
        max_beta = int(os.getenv("HERMES_STATE_MAX_BETA_PRIORS", "4000"))
        max_bandits = int(os.getenv("HERMES_STATE_MAX_BANDITS", "4000"))
        max_tail = int(os.getenv("HERMES_STATE_MAX_MEMORY_TAIL", "4000"))
        max_key_chars = int(os.getenv("HERMES_STATE_MAX_KEY_CHARS", "160"))

        def _trim_key(raw: str) -> str:
            text = str(raw)
            if len(text) <= max_key_chars:
                return text
            keep = max(24, max_key_chars - 17)
            return f"{text[:keep]}:{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"

        q_items = list(self.algorithm_state["q_table"].items())[-max_q_states:]
        q_table = {f"{_trim_key(k[0])}|{_trim_key(k[1])}": float(v) for k, v in q_items}
        beta_items = list(self.algorithm_state["beta_priors"].items())[-max_beta:]
        beta_priors = {_trim_key(k): [float(v[0]), float(v[1])] for k, v in beta_items}
        state = {}
        bandits = list(self.algorithm_state.get("bandit_values", {}).items())[-max_bandits:]
        state["bandit_values"] = {_trim_key(k): float(v) for k, v in bandits}
        source_horizon = self.algorithm_state.get("horizon_memory", {})
        state["horizon_memory"] = {
            "short": [float(v) for v in list(source_horizon.get("short", []))[-max_tail:]],
            "mid": [float(v) for v in list(source_horizon.get("mid", []))[-max_tail:]],
            "long": [float(v) for v in list(source_horizon.get("long", []))[-max_tail:]],
        }
        for key in ("knaa_qnaa_memory", "punishment_memory", "fleet_shape_memory", "long_haul_meta_memory", "aihub_bonus_memory", "adaptive_brain_memory"):
            values = self.algorithm_state.get(key, [])
            if isinstance(values, list):
                state[key] = [float(v) for v in values[-max_tail:]]
        hard_facts = self.algorithm_state.get("hard_facts", {})
        if isinstance(hard_facts, dict):
            max_hard_facts = int(os.getenv("HERMES_STATE_MAX_HARD_FACTS", "1200"))
            items = list(hard_facts.items())[-max_hard_facts:]
            state["hard_facts"] = {str(k): v for k, v in items if isinstance(v, dict)}
        dynamic_modifiers = self.algorithm_state.get("adaptive_dynamic_modifiers", {})
        if isinstance(dynamic_modifiers, dict):
            state["adaptive_dynamic_modifiers"] = dynamic_modifiers
        state["q_table"] = q_table
        state["beta_priors"] = beta_priors
        return state

    def _deserialize_algorithm_state(self, payload: Dict) -> None:
        if not isinstance(payload, dict):
            return
        for key in ("bandit_values", "horizon_memory", "knaa_qnaa_memory", "punishment_memory", "fleet_shape_memory", "long_haul_meta_memory", "aihub_bonus_memory", "adaptive_brain_memory", "hard_facts", "adaptive_dynamic_modifiers"):
            if key in payload and isinstance(payload[key], (dict, list)):
                self.algorithm_state[key] = payload[key]
        q_table = payload.get("q_table", {})
        if isinstance(q_table, dict):
            rebuilt = {}
            for raw_key, value in q_table.items():
                if isinstance(raw_key, str) and "|" in raw_key:
                    specialty, bin_key = raw_key.split("|", 1)
                    rebuilt[(specialty, bin_key)] = float(value)
            self.algorithm_state["q_table"] = rebuilt
        beta_priors = payload.get("beta_priors", {})
        if isinstance(beta_priors, dict):
            rebuilt_priors = {}
            for k, pair in beta_priors.items():
                if isinstance(pair, (list, tuple)) and len(pair) == 2:
                    rebuilt_priors[k] = (float(pair[0]), float(pair[1]))
            self.algorithm_state["beta_priors"] = rebuilt_priors

    def _save_learning_state(self, force: bool = False) -> None:
        now = time.time()
        if not force and (now - self._last_learning_state_save) < self.learning_state_save_interval:
            return
        state_path = self._resolved_learning_state_path()
        os.makedirs(os.path.dirname(state_path), exist_ok=True)
        with open(state_path, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "version": 1,
                    "saved_at_unix": now,
                    "unified_config": self.unified_config,
                    "reward_weights": self.reward_weights,
                    "algorithm_state": self._serialize_algorithm_state(),
                    "growth": self.growth_metrics(),
                },
                fh,
                indent=2,
                sort_keys=True,
            )
        self._last_learning_state_save = now

    def _load_learning_state(self) -> None:
        state_path = self._resolved_learning_state_path()
        if not os.path.exists(state_path):
            return
        try:
            with open(state_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except (json.JSONDecodeError, OSError):
            try:
                os.replace(state_path, f"{state_path}.corrupt")
            except OSError:
                pass
            return
        if isinstance(data.get("reward_weights"), dict):
            for k in self.reward_weights.keys():
                if k in data["reward_weights"]:
                    self.reward_weights[k] = float(data["reward_weights"][k])
        self._deserialize_algorithm_state(data.get("algorithm_state", {}))

    def growth_metrics(self) -> Dict:
        def _tail_avg(values: List[float], n: int = 80) -> float:
            tail = values[-n:]
            return (sum(tail) / len(tail)) if tail else 0.0

        knaa = self.algorithm_state["knaa_qnaa_memory"]
        fleet = self.algorithm_state["fleet_shape_memory"]
        meta = self.algorithm_state["long_haul_meta_memory"]
        bonus = self.algorithm_state["aihub_bonus_memory"]
        adaptive = self.algorithm_state["adaptive_brain_memory"]
        total_learning_events = len(knaa) + len(fleet) + len(meta) + len(adaptive)
        growth_index = max(0.0, min(1.0, (_tail_avg(knaa) * 0.28) + (_tail_avg(fleet) * 0.24) + (_tail_avg(meta) * 0.24) + (_tail_avg(adaptive) * 0.24)))
        mesh_summary = self.store.knowledge_mesh_summary()
        return {
            "growth_index": growth_index,
            "avg_knaa_qnaa": _tail_avg(knaa),
            "avg_fleet_shape": _tail_avg(fleet),
            "avg_long_haul_meta": _tail_avg(meta),
            "avg_aihub_bonus": _tail_avg(bonus),
            "avg_adaptive_brain": _tail_avg(adaptive),
            "total_learning_events": total_learning_events,
            "knowledge_depth": {
                "bandit_specialties": len(self.algorithm_state["bandit_values"]),
                "q_table_states": len(self.algorithm_state["q_table"]),
                "beta_priors": len(self.algorithm_state["beta_priors"]),
                "mesh_links": mesh_summary["link_count"],
                "mesh_paths": mesh_summary["unique_paths"],
                "hard_facts": len(self.algorithm_state.get("hard_facts", {})),
                "adaptive_dynamic_channels": len(self.algorithm_state.get("adaptive_dynamic_modifiers", {})),
            },
        }

    def cpp_kernel_status(self) -> Dict:
        return {
            "available": self.native_bridge.available,
            "library_path": self.cpp_native_library_path,
            "mode": "native_cpp" if self.native_bridge.available else "python_fallback",
            "capabilities": [
                "reward_update",
                "gaussian_3d_score",
                "knaa_qnaa_score",
                "fleet_shape_score",
                "quantized_compression_score",
                "long_haul_meta_score",
                "adaptive_brain_decision",
                "linear_regression_predict",
            ],
        }

    def ingest_knowledge_mesh(self, payload: Dict) -> Dict:
        source_agent = str(payload.get("source_agent", "hermes-trainer"))
        target_agent = str(payload.get("target_agent", "hermes-orchestrator"))
        task_family = str(payload.get("task_family", "general"))
        pattern_text = str(payload.get("pattern", payload.get("task_family", "general")))
        pattern_hash = hashlib.sha1(pattern_text.encode("utf-8")).hexdigest()
        shape3d = payload.get("shape3d", [0.5, 0.5, 0.5])
        if not isinstance(shape3d, list) or len(shape3d) != 3:
            shape3d = [0.5, 0.5, 0.5]
        shape = (
            float(max(0.0, min(1.0, shape3d[0]))),
            float(max(0.0, min(1.0, shape3d[1]))),
            float(max(0.0, min(1.0, shape3d[2]))),
        )
        weight = float(max(0.0, min(1.0, payload.get("weight", payload.get("signal_score", 0.6)))))
        confidence = float(max(0.0, min(1.0, payload.get("confidence", 0.65))))
        transfer_payload = payload.get("payload", {})
        if not isinstance(transfer_payload, dict):
            transfer_payload = {"value": str(transfer_payload)}
        self.store.write_knowledge_mesh_link(
            source_agent=source_agent,
            target_agent=target_agent,
            task_family=task_family,
            pattern_hash=pattern_hash,
            shape3d=shape,
            weight=weight,
            confidence=confidence,
            payload=transfer_payload,
        )
        return {"ok": True, "pattern_hash": pattern_hash, "summary": self.store.knowledge_mesh_summary()}

    def knowledge_mesh_state(self) -> Dict:
        return {
            "summary": self.store.knowledge_mesh_summary(),
            "links": self.store.recent_knowledge_mesh_links(limit=60),
        }

    def export_learning_state(self) -> Dict:
        return {
            "version": 1,
            "fleet_model_label": self.fleet_model_label,
            "mcp_server": self.mcp_server,
            "unified_config": self.unified_config,
            "reward_weights": self.reward_weights,
            "algorithm_state": self._serialize_algorithm_state(),
            "growth": self.growth_metrics(),
            "learning_state_path": self._resolved_learning_state_path(),
        }

    def import_learning_state(self, payload: Dict) -> Dict:
        if not isinstance(payload, dict):
            return {"ok": False, "error": "invalid_payload"}
        if isinstance(payload.get("reward_weights"), dict):
            for k in self.reward_weights.keys():
                if k in payload["reward_weights"]:
                    self.reward_weights[k] = float(payload["reward_weights"][k])
        self._deserialize_algorithm_state(payload.get("algorithm_state", {}))
        self._save_learning_state(force=True)
        return {"ok": True, "growth": self.growth_metrics()}

    def _agent_score(self, agent: AgentProfile) -> float:
        return (agent.reward_score * 0.6) + (agent.success_rate * 0.4) - (agent.load * 0.2)

    def _select_agent(self, specialty_hint: str) -> AgentProfile:
        candidates = [a for a in self.agents if a.active]
        hinted = [a for a in candidates if specialty_hint.lower() in a.specialty.lower()]
        pool = hinted or candidates
        return max(pool, key=self._agent_score)

    def _gaussian_tune_rewards(self) -> None:
        for k in self.reward_weights:
            self.reward_weights[k] += random.gauss(0.0, 0.015)
        total = sum(max(0.01, v) for v in self.reward_weights.values())
        for k in self.reward_weights:
            self.reward_weights[k] = max(0.01, self.reward_weights[k]) / total

    def _multi_objective_score(self, outcome: InteractionOutcome) -> float:
        weights = [
            self.reward_weights["quality"],
            self.reward_weights["speed"],
            self.reward_weights["cost"],
            self.reward_weights["truth"],
            self.reward_weights["compression"] + self.reward_weights["novelty"],
        ]
        return self.native_bridge.reward_update(
            quality=outcome.quality,
            speed=outcome.speed,
            cost_efficiency=outcome.cost_efficiency,
            truth_score=outcome.truth_score,
            novelty=outcome.compression_gain + outcome.pattern_diversity,
            weights=weights,
        )

    def _truth_gate_adjustment(self, score: float, truth_score: float) -> float:
        if truth_score >= self.truth_threshold:
            return score
        # Strong penalty to prevent false promotions.
        penalty = (self.truth_threshold - truth_score) * 1.5
        return score - penalty

    def _bandit_update(self, specialty: str, reward: float) -> None:
        old = self.algorithm_state["bandit_values"].get(specialty, 0.0)
        lr = 0.12
        self.algorithm_state["bandit_values"][specialty] = old + lr * (reward - old)

    def _q_learning_update(self, specialty: str, complexity: float, reward: float) -> None:
        bin_key = f"c{int(max(0.0, min(0.99, complexity)) * 5)}"
        state_key = (specialty, bin_key)
        old_q = self.algorithm_state["q_table"].get(state_key, 0.0)
        alpha = 0.2
        gamma = 0.9
        future = max([v for (s, _), v in self.algorithm_state["q_table"].items() if s == specialty] or [0.0])
        self.algorithm_state["q_table"][state_key] = old_q + alpha * (reward + gamma * future - old_q)

    def _bayesian_update(self, specialty: str, success: float) -> None:
        alpha, beta = self.algorithm_state["beta_priors"].get(specialty, (1.0, 1.0))
        if success >= 0.5:
            alpha += 1.0
        else:
            beta += 1.0
        self.algorithm_state["beta_priors"][specialty] = (alpha, beta)

    def _run_algorithm_updates(self, specialty: str, complexity: float, reward: float, success: float) -> None:
        self._bandit_update(specialty, reward)
        self._q_learning_update(specialty, complexity, reward)
        self._bayesian_update(specialty, success)

    def _horizon_score(self, horizon: str, outcome: InteractionOutcome) -> float:
        w = self.horizon_weights[horizon]
        return (
            outcome.quality * w["quality"]
            + outcome.speed * w["speed"]
            + outcome.cost_efficiency * w["cost"]
            + outcome.truth_score * w["truth"]
            + outcome.compression_gain * w["compression"]
        )

    def _update_horizon_memory(self, horizon: str, value: float) -> None:
        mem = self.algorithm_state["horizon_memory"][horizon]
        mem.append(value)
        if len(mem) > 1500:
            del mem[: len(mem) - 1500]

    def _gaussian_3d_shape_score(self, point: tuple[float, float, float], target: tuple[float, float, float], sigma: float = 0.20) -> float:
        return self.native_bridge.gaussian_3d_score(
            x=point[0],
            y=point[1],
            z=point[2],
            target_x=target[0],
            target_y=target[1],
            target_z=target[2],
            sigma=sigma,
        )

    def _knaa_qnaa_score(
        self,
        short_variables: Dict[str, float],
        mid_variables: Dict[str, float],
        long_variables: Dict[str, float],
        truth_score: float,
        reward_score: float,
    ) -> float:
        short_values = [max(0.0, min(1.0, v)) for v in short_variables.values()]
        mid_values = [max(0.0, min(1.0, v)) for v in mid_variables.values()]
        long_values = [max(0.0, min(1.0, v)) for v in long_variables.values()]
        exploration_rate = max(0.01, min(0.6, 1.0 - truth_score))
        score = self.native_bridge.knaa_qnaa_score(
            short_values=short_values,
            mid_values=mid_values,
            long_values=long_values,
            truth_score=truth_score,
            reward_score=reward_score,
            exploration_rate=exploration_rate,
        )
        mem = self.algorithm_state["knaa_qnaa_memory"]
        mem.append(score)
        if len(mem) > 2000:
            del mem[: len(mem) - 2000]
        return score

    def _fleet_shape_score(
        self,
        active_agents: int,
        latency_ms: float,
        throughput_rps: float,
        error_rate: float,
        diversity: float,
        memory_retention: float,
    ) -> float:
        score = self.native_bridge.fleet_shape_score(
            active_agents=float(active_agents),
            latency_ms=latency_ms,
            throughput_rps=throughput_rps,
            error_rate=error_rate,
            diversity=diversity,
            memory_retention=memory_retention,
        )
        mem = self.algorithm_state["fleet_shape_memory"]
        mem.append(score)
        if len(mem) > 2000:
            del mem[: len(mem) - 2000]
        return score

    def _punishment_correction(self, truth_score: float, quality: float, drift: float) -> float:
        if truth_score >= self.truth_threshold and quality >= 0.6:
            correction = min(0.18, (truth_score - self.truth_threshold) * 0.25 + quality * 0.05)
        else:
            truth_gap = max(0.0, self.truth_threshold - truth_score)
            correction = -min(0.6, truth_gap * 1.35 + drift * 0.22)
        pmem = self.algorithm_state["punishment_memory"]
        pmem.append(correction)
        if len(pmem) > 2000:
            del pmem[: len(pmem) - 2000]
        return correction

    def _persist_temporal_memory_bands(self, event: Dict) -> None:
        short_payload = {
            "agent": event["agent"],
            "specialty": event["specialty"],
            "short_score": event["short_score"],
            "knaa_qnaa_score": event["knaa_qnaa_score"],
            "fleet_shape_score": event["fleet_shape_score"],
        }
        mid_payload = {
            "objective_score": event["objective_score"],
            "truth_score": event["truth_score"],
            "compression_gain": event["compression_gain"],
            "external_signal_score": event["external_signal_score"],
        }
        long_payload = {
            "long_score": event["long_score"],
            "retention_score": event["long_variables"]["retention_score"],
            "correction": event["punishment_correction"],
            "long_haul_meta_score": event["long_haul_meta_score"],
            "reward_score": event["reward_score"],
        }
        self.store.write_memory_band("short", "short_ttl", short_payload["short_score"], short_payload)
        self.store.write_memory_band("mid", "mid_ttl", event["mid_score"], mid_payload)
        self.store.write_memory_band("long", "long_ttl", long_payload["retention_score"], long_payload)

    def _compression_shape_score(
        self,
        short_variables: Dict[str, float],
        mid_variables: Dict[str, float],
        long_variables: Dict[str, float],
    ) -> float:
        values = [*short_variables.values(), *mid_variables.values(), *long_variables.values()]
        safe_values = [max(0.0, min(1.0, v)) for v in values]
        return self.native_bridge.quantized_compression_score(safe_values)

    def _long_haul_meta_score(
        self,
        short_variables: Dict[str, float],
        mid_variables: Dict[str, float],
        long_variables: Dict[str, float],
        external_signal_score: float,
        correction_signal: float,
        truth_score: float,
        gaussian_alignment: float,
    ) -> float:
        short_values = [max(0.0, min(1.0, v)) for v in short_variables.values()]
        mid_values = [max(0.0, min(1.0, v)) for v in mid_variables.values()]
        long_values = [max(0.0, min(1.0, v)) for v in long_variables.values()]
        score = self.native_bridge.long_haul_meta_score(
            short_values=short_values,
            mid_values=mid_values,
            long_values=long_values,
            external_signal_score=max(0.0, min(1.0, external_signal_score)),
            correction_signal=max(-1.0, min(1.0, correction_signal)),
            truth_score=max(0.0, min(1.0, truth_score)),
            gaussian_alignment=max(0.0, min(1.0, gaussian_alignment)),
        )
        mem = self.algorithm_state["long_haul_meta_memory"]
        mem.append(score)
        if len(mem) > 2000:
            del mem[: len(mem) - 2000]
        return score

    def _adaptive_brain_decision(
        self,
        variables: List[float],
        variable_weights: List[float],
        truth_score: float,
        stability_signal: float,
        exploration_pressure: float,
        chaos_control: float,
        proactive_bias: float,
    ) -> Dict[str, float]:
        def _clamp(v: float, low: float = 0.0, high: float = 1.0) -> float:
            return max(low, min(high, float(v)))

        tail = self.algorithm_state.get("adaptive_brain_memory", [])[-240:]
        baseline = tail if tail else [0.46, 0.5, 0.54]
        center = sum(baseline) / len(baseline)
        variance = sum((v - center) ** 2 for v in baseline) / max(1, len(baseline))
        spread = max(0.08, min(0.48, (variance ** 0.5) + 0.14))
        stable_hits = len([v for v in baseline if abs(v - center) <= (spread * 0.35)])
        pivot_hits = len([v for v in baseline if abs(v - center) >= (spread * 0.75)])
        evidence_ratio = _clamp(stable_hits / max(1, len(baseline)))
        pivot_ratio = _clamp(pivot_hits / max(1, len(baseline)))
        hard_facts = self.algorithm_state.get("hard_facts", {})
        locked_facts = len([f for f in hard_facts.values() if isinstance(f, dict) and f.get("locked")]) if isinstance(hard_facts, dict) else 0
        hard_fact_signal = _clamp(locked_facts / max(1, len(hard_facts))) if isinstance(hard_facts, dict) and hard_facts else 0.0
        confidence_signal = _clamp((evidence_ratio * 0.6) + (truth_score * 0.2) + ((1.0 - chaos_control) * 0.1) + (hard_fact_signal * 0.1))
        modifier_gain = _clamp(0.55 + (confidence_signal ** 2.2), 0.35, 1.95)
        caution_level = _clamp(1.0 - confidence_signal)
        pivot_bias = _clamp((pivot_ratio * 0.55) + (exploration_pressure * 0.25) + (chaos_control * 0.20))
        risk_damping = _clamp((stability_signal * 0.45) + (hard_fact_signal * 0.35) + (evidence_ratio * 0.20))
        range_low = _clamp(center - spread)
        range_high = _clamp(center + spread)

        denom = max(0.12, (range_high - range_low))
        normalized_variables = [_clamp((v - range_low) / denom) for v in variables]
        adjusted_weights = []
        for idx, w in enumerate(variable_weights):
            phase_amp = 1.0 + (((idx % 5) / 10.0) * pivot_bias)
            adaptive_amp = (0.68 + (confidence_signal * 0.42)) * (1.0 + (modifier_gain * 0.14))
            adjusted_weights.append(max(0.01, float(w) * phase_amp * adaptive_amp))

        decision = self.native_bridge.adaptive_brain_decision(
            variables=normalized_variables,
            variable_weights=adjusted_weights,
            truth_score=truth_score,
            stability_signal=_clamp((stability_signal * (0.72 + (risk_damping * 0.28))) + ((1.0 - caution_level) * 0.08)),
            exploration_pressure=_clamp((exploration_pressure * (0.72 + (pivot_bias * 0.38))) + (caution_level * 0.10)),
            chaos_control=_clamp((chaos_control * (0.75 + ((1.0 - risk_damping) * 0.35))) + (pivot_bias * 0.08)),
            proactive_bias=_clamp((proactive_bias * (0.7 + (modifier_gain * 0.2))) + (confidence_signal * 0.1)),
        )
        confidence_boost = 1.0 + ((max(0.0, confidence_signal - 0.5)) ** 2) * 1.2
        caution_blend = 0.74 + (confidence_signal * 0.26)
        decision["decision_score"] = _clamp(decision.get("decision_score", 0.0) * (confidence_boost if confidence_signal >= 0.5 else caution_blend))
        decision["proactive_score"] = _clamp(
            decision.get("proactive_score", 0.0)
            * ((0.62 + (confidence_signal * 0.38)) if confidence_signal < 0.5 else (1.0 + ((confidence_signal - 0.5) ** 2)))
        )
        decision["adaptation_rate"] = _clamp(
            decision.get("adaptation_rate", 0.0) * (0.72 + (pivot_bias * 0.45) + ((1.0 - caution_level) * 0.12))
        )
        decision["fleet_boost"] = _clamp(decision.get("fleet_boost", 0.0) * (0.84 + (modifier_gain * 0.25)))
        decision["llm_boost"] = _clamp(decision.get("llm_boost", 0.0) * (0.86 + (modifier_gain * 0.22)))
        decision["chaos_intensity"] = _clamp(decision.get("chaos_intensity", 0.0) * (0.78 + (pivot_bias * 0.33)) * (1.0 - (risk_damping * 0.18)))
        decision["confidence"] = _clamp(decision.get("confidence", 0.0) * (0.76 + (confidence_signal * 0.32)))
        decision["dynamic_context"] = {
            "moving_range_low": range_low,
            "moving_range_high": range_high,
            "moving_center": center,
            "moving_spread": spread,
            "evidence_ratio": evidence_ratio,
            "modifier_gain": modifier_gain,
            "caution_level": caution_level,
            "pivot_bias": pivot_bias,
            "risk_damping": risk_damping,
            "hard_fact_signal": hard_fact_signal,
            "confidence_signal": confidence_signal,
        }
        self.algorithm_state["adaptive_dynamic_modifiers"] = decision["dynamic_context"]
        mem = self.algorithm_state["adaptive_brain_memory"]
        mem.append(float(decision.get("decision_score", 0.0)))
        if len(mem) > 2000:
            del mem[: len(mem) - 2000]
        return decision

    def _build_big_decision_plan(self, specialty_hint: str, adaptive_decision: Dict[str, float], workload_complexity: float) -> Optional[Dict]:
        context = adaptive_decision.get("dynamic_context", {}) if isinstance(adaptive_decision, dict) else {}
        confidence_signal = float(context.get("confidence_signal", adaptive_decision.get("confidence", 0.0)))
        pivot_bias = float(context.get("pivot_bias", adaptive_decision.get("chaos_intensity", 0.0)))
        if confidence_signal >= 0.52 and pivot_bias < 0.66 and workload_complexity < 0.78:
            return None
        active = sorted([a for a in self.agents if a.active], key=self._agent_score, reverse=True)
        if not active:
            return None
        max_size = max(2, min(len(active), 10))
        half_size = max(2, min(max_size, max(2, len(active) // 2)))
        reduced_size = max(1, min(half_size, max(1, len(active) // 3)))

        def _team(size: int) -> List[Dict]:
            result = []
            for agent in active[:size]:
                result.append(
                    {
                        "agent": agent.name,
                        "specialty": agent.specialty,
                        "behavior": "normal" if confidence_signal >= 0.55 else ("specialist-mesh" if "research" in agent.specialty.lower() else "swarm"),
                        "focus_weight": max(0.2, min(1.0, (agent.success_rate * 0.65) + (float(adaptive_decision.get("adaptation_rate", 0.0)) * 0.35))),
                    }
                )
            return result

        trigger = "uncertainty" if confidence_signal < 0.45 else ("pivot-pressure" if pivot_bias >= 0.66 else "high-complexity")
        return {
            "trigger": trigger,
            "confidence_to_pivot": max(0.0, min(1.0, (pivot_bias * 0.6) + ((1.0 - confidence_signal) * 0.4))),
            "teams": {
                "max_capacity": _team(max_size),
                "half_capacity": _team(half_size),
                "reduced_capacity": _team(reduced_size),
            },
            "swap_policy": {
                "enabled": True,
                "replace_when_success_below": max(0.12, 0.34 - (confidence_signal * 0.15)),
                "rotate_specialists_every_steps": int(max(4, min(24, 16 - (pivot_bias * 8)))),
            },
        }

    def _natural_selection(self) -> None:
        inactive_candidates = [a for a in self.agents if a.success_rate < 0.2 and a.reward_score < 0.1]
        if inactive_candidates and len(self.agents) > 6:
            retire = min(inactive_candidates, key=lambda a: a.reward_score)
            retire.active = False
            self.store.write_event("agent_retired", asdict(retire))

        active = [a for a in self.agents if a.active]
        if len(active) >= 2 and random.random() < 0.18:
            top = sorted(active, key=self._agent_score, reverse=True)[:2]
            new_name = f"hermes-evo-{int(time.time())}"
            evolved = AgentProfile(
                name=new_name,
                specialty=f"{top[0].specialty}+{top[1].specialty}",
                reward_score=(top[0].reward_score + top[1].reward_score) / 2.0,
                success_rate=(top[0].success_rate + top[1].success_rate) / 2.0,
            )
            self.agents.append(evolved)
            self.store.write_event("agent_spawned", asdict(evolved))

    def _prethink_fleet_plan(self, specialty_hint: str, steps: int) -> Dict:
        active = [a for a in self.agents if a.active]
        if not active:
            return {"lines": [], "source_mix": {"manual": 0.6, "pattern": 0.3, "internet": 0.1}, "predicted_reward": 0.5}
        reward_tail = self.algorithm_state["adaptive_brain_memory"][-64:] or [0.5, 0.52, 0.54]
        predicted_reward = max(0.0, min(1.0, self.native_bridge.linear_regression_predict(reward_tail, x_query=len(reward_tail) + max(1, steps), l2_alpha=0.02)))
        source_mix = {
            "manual": max(0.35, min(0.85, 0.56 + ((1.0 - predicted_reward) * 0.20))),
            "pattern": max(0.10, min(0.45, 0.28 + (predicted_reward * 0.18))),
            "internet": 0.0 if self.offline_only_mode else (0.06 if self.low_bandwidth_mode else 0.16),
        }
        total = sum(source_mix.values()) or 1.0
        source_mix = {k: (v / total) for k, v in source_mix.items()}

        behavior_types = ["normal", "swarm", "mesh", "multipolar", "specialist-mix"]
        lines = []
        for idx, agent in enumerate(sorted(active, key=self._agent_score, reverse=True)):
            behavior = behavior_types[idx % len(behavior_types)]
            if "research" in agent.specialty.lower():
                behavior = "mesh"
            elif "fleet" in agent.specialty.lower():
                behavior = "normal" if idx % 2 == 0 else "swarm"
            line_weight = max(0.2, min(1.0, (agent.success_rate * 0.55) + 0.35))
            focus = specialty_hint if specialty_hint != "general" else (agent.specialty if agent.specialty else "normal")
            lines.append(
                {
                    "agent": agent.name,
                    "focus": focus,
                    "behavior_type": behavior,
                    "line_weight": line_weight,
                    "data_source": max(source_mix, key=source_mix.get),
                }
            )
        return {"lines": lines, "source_mix": source_mix, "predicted_reward": predicted_reward, "launch_mode": "parallel-prethink"}

    def _apply_hard_facts(self, specialty: str, adaptive: Dict[str, float], truth_score: float, quality: float) -> Dict[str, float]:
        hard_facts = self.algorithm_state.get("hard_facts", {})
        if not isinstance(hard_facts, dict):
            hard_facts = {}
            self.algorithm_state["hard_facts"] = hard_facts
        key = f"{specialty}|stable"
        fact = hard_facts.get(key, {"evidence_count": 0, "confidence": 0.0, "locked": False})
        if truth_score > 0.86 and quality > 0.82 and adaptive.get("decision_score", 0.0) > 0.72:
            fact["evidence_count"] = int(fact.get("evidence_count", 0)) + 1
            fact["confidence"] = max(float(fact.get("confidence", 0.0)), min(1.0, (truth_score * 0.52) + (quality * 0.28) + (adaptive.get("confidence", 0.0) * 0.20)))
        elif fact.get("evidence_count", 0) > 0:
            fact["evidence_count"] = max(0, int(fact.get("evidence_count", 0)) - 1)
            fact["confidence"] = max(0.0, float(fact.get("confidence", 0.0)) * 0.995)
        threshold = int(os.getenv("HERMES_HARD_FACT_EVIDENCE_THRESHOLD", "12"))
        fact["locked"] = bool(fact.get("evidence_count", 0) >= threshold and fact.get("confidence", 0.0) >= 0.82)
        hard_facts[key] = fact
        return fact

    def train_step(self, specialty_hint: str, workload_complexity: float = 0.5) -> Dict:
        with self.lock:
            agent = self._select_agent(specialty_hint)
            scale = max(0.1, min(1.0, self.governor.capacity_scale()))
            effective_work = workload_complexity * scale

            success = 1.0 if random.random() < (0.32 + agent.success_rate * 0.62) else 0.0
            quality = max(0.0, min(1.0, (agent.success_rate * 0.65) + random.uniform(0.0, 0.35)))
            speed = max(0.0, 1.0 - effective_work * random.uniform(0.68, 1.25))
            cost_efficiency = max(0.0, 1.0 - (effective_work * random.uniform(0.3, 0.9)))
            truth_score = max(0.0, min(1.0, quality * 0.7 + success * 0.2 + random.uniform(0.0, 0.1)))
            novelty = max(0.0, min(1.0, random.gauss(0.55, 0.2)))
            compression_gain = max(0.0, min(1.0, random.gauss(0.58, 0.18)))
            data_freshness = max(0.0, min(1.0, random.gauss(0.62, 0.20)))
            pattern_diversity = max(0.0, min(1.0, random.gauss(0.5, 0.22)))
            risk_adjusted = max(0.0, min(1.0, truth_score * 0.65 + quality * 0.2 + speed * 0.15))
            short_variables = {
                "latency_pressure": max(0.0, min(1.0, random.gauss(0.62, 0.18))),
                "cache_hit_proxy": max(0.0, min(1.0, random.gauss(0.66, 0.20))),
                "io_efficiency": max(0.0, min(1.0, random.gauss(0.6, 0.21))),
            }
            mid_variables = {
                "stability_drift": max(0.0, min(1.0, random.gauss(0.52, 0.22))),
                "schema_health": max(0.0, min(1.0, random.gauss(0.7, 0.18))),
                "agent_alignment": max(0.0, min(1.0, random.gauss(0.68, 0.17))),
            }
            long_variables = {
                "retention_score": max(0.0, min(1.0, random.gauss(0.71, 0.19))),
                "generalization": max(0.0, min(1.0, random.gauss(0.65, 0.23))),
                "compression_longevity": max(0.0, min(1.0, random.gauss(0.63, 0.21))),
            }
            external_signal_score = max(0.0, min(1.0, self.store.recent_external_signal_score()))
            outcome = InteractionOutcome(
                quality=quality,
                speed=speed,
                cost_efficiency=cost_efficiency,
                truth_score=truth_score,
                novelty=novelty,
                compression_gain=compression_gain,
                data_freshness=data_freshness,
                pattern_diversity=pattern_diversity,
                risk_adjusted=risk_adjusted,
                success=success,
            )
            short_score = self._horizon_score("short", outcome)
            mid_score = self._horizon_score("mid", outcome)
            long_score = self._horizon_score("long", outcome)
            objective_score = (short_score * 0.45) + (mid_score * 0.33) + (long_score * 0.22)
            objective_score += (
                outcome.data_freshness * self.reward_weights["freshness"]
                + outcome.pattern_diversity * self.reward_weights["diversity"]
                + outcome.risk_adjusted * self.reward_weights["risk"]
            )
            objective_score += (
                short_variables["latency_pressure"] * 0.025
                + mid_variables["agent_alignment"] * 0.02
                + long_variables["retention_score"] * 0.03
            )
            knaa_qnaa_score = self._knaa_qnaa_score(
                short_variables=short_variables,
                mid_variables=mid_variables,
                long_variables=long_variables,
                truth_score=truth_score,
                reward_score=agent.reward_score / 10.0,
            )
            quantized_compression_score = self._compression_shape_score(short_variables, mid_variables, long_variables)
            fleet_shape_score = self._fleet_shape_score(
                active_agents=len([a for a in self.agents if a.active]),
                latency_ms=max(25.0, 400.0 * (1.0 - speed)),
                throughput_rps=max(1.0, 40.0 + quality * 220.0),
                error_rate=max(0.0, 1.0 - truth_score),
                diversity=pattern_diversity,
                memory_retention=long_variables["retention_score"],
            )
            punishment_correction = self._punishment_correction(
                truth_score=truth_score,
                quality=quality,
                drift=mid_variables["stability_drift"],
            )
            gaussian_alignment = self._gaussian_3d_shape_score(
                point=(truth_score, quality, speed),
                target=self.goal_shape_targets["balanced"],
                sigma=0.24,
            )
            long_haul_meta_score = self._long_haul_meta_score(
                short_variables=short_variables,
                mid_variables=mid_variables,
                long_variables=long_variables,
                external_signal_score=external_signal_score,
                correction_signal=punishment_correction,
                truth_score=truth_score,
                gaussian_alignment=gaussian_alignment,
            )
            adaptive_variables = [
                quality,
                speed,
                cost_efficiency,
                truth_score,
                novelty,
                compression_gain,
                data_freshness,
                pattern_diversity,
                long_variables["retention_score"],
                knaa_qnaa_score,
                fleet_shape_score,
                long_haul_meta_score,
                external_signal_score,
                gaussian_alignment,
            ]
            adaptive_weights = [
                self.reward_weights["quality"],
                self.reward_weights["speed"],
                self.reward_weights["cost"],
                self.reward_weights["truth"],
                self.reward_weights["novelty"],
                self.reward_weights["compression"],
                self.reward_weights["freshness"],
                self.reward_weights["diversity"],
                self.reward_weights["risk"] + 0.02,
                0.08,
                0.10,
                0.11,
                0.06,
                0.07,
            ]
            adaptive_decision = self._adaptive_brain_decision(
                variables=adaptive_variables,
                variable_weights=adaptive_weights,
                truth_score=truth_score,
                stability_signal=max(0.0, min(1.0, 1.0 - mid_variables["stability_drift"])),
                exploration_pressure=max(0.0, min(1.0, (1.0 - truth_score) * 0.55 + (1.0 - long_variables["generalization"]) * 0.25 + novelty * 0.20)),
                chaos_control=max(0.0, min(1.0, abs(mid_variables["stability_drift"] - long_variables["retention_score"]) * 0.7 + pattern_diversity * 0.3)),
                proactive_bias=max(0.0, min(1.0, (self.algorithm_state["bandit_values"].get(agent.specialty, 0.5) * 0.5) + (data_freshness * 0.5))),
            )
            big_decision_plan = self._build_big_decision_plan(specialty_hint=specialty_hint, adaptive_decision=adaptive_decision, workload_complexity=effective_work)
            hard_fact = self._apply_hard_facts(agent.specialty, adaptive_decision, truth_score, quality)
            aihub_bonus = self.compute_aihub_bonus()
            objective_score += knaa_qnaa_score * 0.12
            objective_score += quantized_compression_score * 0.06
            objective_score += fleet_shape_score * 0.08
            objective_score += external_signal_score * 0.05
            objective_score += long_haul_meta_score * 0.10
            objective_score += adaptive_decision["decision_score"] * 0.14
            objective_score += adaptive_decision["proactive_score"] * 0.06
            objective_score += adaptive_decision["fleet_boost"] * 0.05
            objective_score += adaptive_decision["llm_boost"] * 0.05
            if isinstance(big_decision_plan, dict):
                objective_score += max(0.0, min(0.08, float(big_decision_plan.get("confidence_to_pivot", 0.0)) * 0.06))
            if hard_fact.get("locked", False):
                objective_score += 0.07
                adaptive_decision["chaos_intensity"] = max(0.0, adaptive_decision["chaos_intensity"] * 0.55)
            objective_score += aihub_bonus * 0.09
            objective_score = (objective_score * 0.55) + (self._multi_objective_score(outcome) * 0.45)
            delta = self._truth_gate_adjustment(objective_score, truth_score)
            delta += punishment_correction
            delta += (adaptive_decision["confidence"] - 0.5) * 0.20

            agent.reward_score = max(0.0, min(10.0, agent.reward_score + (delta - 0.28)))
            agent.success_rate = max(
                0.0,
                min(
                    1.0,
                    (agent.success_rate * (0.85 - (adaptive_decision["adaptation_rate"] * 0.05)))
                    + (success * (0.15 + (adaptive_decision["proactive_score"] * 0.03))),
                ),
            )
            agent.load = max(0.0, min(1.0, effective_work))

            self._run_algorithm_updates(agent.specialty, workload_complexity, delta, success)
            self._gaussian_tune_rewards()
            self._natural_selection()
            self._update_horizon_memory("short", short_score)
            self._update_horizon_memory("mid", mid_score)
            self._update_horizon_memory("long", long_score)
            self.store.write_horizon_score("short", agent.specialty, short_score, outcome)
            self.store.write_horizon_score("mid", agent.specialty, mid_score, outcome)
            self.store.write_horizon_score("long", agent.specialty, long_score, outcome)

            self.store.write_metric(agent)
            event = {
                "agent": agent.name,
                "specialty": agent.specialty,
                "success": success,
                "quality": quality,
                "speed": speed,
                "cost_efficiency": cost_efficiency,
                "truth_score": truth_score,
                "novelty": novelty,
                "compression_gain": compression_gain,
                "data_freshness": data_freshness,
                "pattern_diversity": pattern_diversity,
                "risk_adjusted": risk_adjusted,
                "short_score": short_score,
                "mid_score": mid_score,
                "long_score": long_score,
                "short_variables": short_variables,
                "mid_variables": mid_variables,
                "long_variables": long_variables,
                "knaa_qnaa_score": knaa_qnaa_score,
                "quantized_compression_score": quantized_compression_score,
                "fleet_shape_score": fleet_shape_score,
                "external_signal_score": external_signal_score,
                "punishment_correction": punishment_correction,
                "gaussian_alignment": gaussian_alignment,
                "long_haul_meta_score": long_haul_meta_score,
                "adaptive_brain": adaptive_decision,
                "big_decision_plan": big_decision_plan,
                "hard_fact": hard_fact,
                "aihub_bonus": aihub_bonus,
                "objective_score": objective_score,
                "reward_score": agent.reward_score,
                "success_rate": agent.success_rate,
                "capacity_scale": scale,
            }
            if isinstance(big_decision_plan, dict):
                self.store.write_event("big_decision_replan", big_decision_plan)
            self.store.write_event("train_step", event)
            self._persist_temporal_memory_bands(event)
            self._save_learning_state()
            return event

    def run_simulations(self, steps: int = 250, specialty: str = "general") -> Dict:
        steps = max(1, min(20000, int(steps)))
        prethink = self._prethink_fleet_plan(specialty_hint=specialty, steps=steps)
        lines = prethink.get("lines", []) if isinstance(prethink, dict) else []
        results = []
        for i in range(steps):
            complexity = max(0.05, min(1.0, random.gauss(0.58, 0.22)))
            selected_line = lines[i % len(lines)] if lines else None
            focus = specialty
            if isinstance(selected_line, dict):
                focus = str(selected_line.get("focus", specialty))
                complexity = max(0.05, min(1.0, complexity * float(selected_line.get("line_weight", 1.0))))
            results.append(self.train_step(focus, complexity))

        avg_reward = sum(r["reward_score"] for r in results) / len(results)
        avg_truth = sum(r["truth_score"] for r in results) / len(results)
        avg_quality = sum(r["quality"] for r in results) / len(results)
        avg_speed = sum(r["speed"] for r in results) / len(results)
        avg_cost = sum(r["cost_efficiency"] for r in results) / len(results)
        avg_short = sum(r["short_score"] for r in results) / len(results)
        avg_mid = sum(r["mid_score"] for r in results) / len(results)
        avg_long = sum(r["long_score"] for r in results) / len(results)
        avg_knaa_qnaa = sum(r["knaa_qnaa_score"] for r in results) / len(results)
        avg_quantized_compression = sum(r["quantized_compression_score"] for r in results) / len(results)
        avg_fleet_shape = sum(r["fleet_shape_score"] for r in results) / len(results)
        avg_long_haul_meta = sum(r["long_haul_meta_score"] for r in results) / len(results)
        avg_adaptive = sum(float(r.get("adaptive_brain", {}).get("decision_score", 0.0)) for r in results) / len(results)
        avg_aihub_bonus = sum(r["aihub_bonus"] for r in results) / len(results)
        truth_violations = len([r for r in results if r["truth_score"] < self.truth_threshold])
        return {
            "steps": steps,
            "avg_reward_score": avg_reward,
            "avg_truth_score": avg_truth,
            "avg_quality": avg_quality,
            "avg_speed": avg_speed,
            "avg_cost_efficiency": avg_cost,
            "avg_short_score": avg_short,
            "avg_mid_score": avg_mid,
            "avg_long_score": avg_long,
            "avg_knaa_qnaa_score": avg_knaa_qnaa,
            "avg_quantized_compression_score": avg_quantized_compression,
            "avg_fleet_shape_score": avg_fleet_shape,
            "avg_long_haul_meta_score": avg_long_haul_meta,
            "avg_adaptive_brain_score": avg_adaptive,
            "avg_aihub_bonus": avg_aihub_bonus,
            "truth_violations": truth_violations,
            "prethink_plan": prethink,
            "reward_weights": self.reward_weights,
        }

    def optimize_fleet_topology(self, specialty: str = "fleet", candidates: int = 80) -> Dict:
        candidates = max(8, min(500, int(candidates)))
        shapes = ["triangle", "hex", "mesh", "swarm", "hybrid"]
        best = None
        for _ in range(candidates):
            team_shape = random.choice(shapes)
            active_agents = random.randint(4, 72)
            latency_ms = max(18.0, random.gauss(180.0, 65.0))
            throughput_rps = max(10.0, random.gauss(165.0, 70.0))
            error_rate = max(0.0, min(1.0, random.gauss(0.12, 0.08)))
            diversity = max(0.0, min(1.0, random.gauss(0.68, 0.18)))
            memory_retention = max(0.0, min(1.0, random.gauss(0.72, 0.16)))
            score = self._fleet_shape_score(
                active_agents=active_agents,
                latency_ms=latency_ms,
                throughput_rps=throughput_rps,
                error_rate=error_rate,
                diversity=diversity,
                memory_retention=memory_retention,
            )
            candidate = {
                "specialty": specialty,
                "team_shape": team_shape,
                "active_agents": active_agents,
                "latency_ms": latency_ms,
                "throughput_rps": throughput_rps,
                "error_rate": error_rate,
                "diversity": diversity,
                "memory_retention": memory_retention,
                "score": score,
            }
            if best is None or candidate["score"] > best["score"]:
                best = candidate

        assert best is not None
        self.store.write_fleet_optimization_run(
            specialty=best["specialty"],
            team_shape=best["team_shape"],
            active_agents=best["active_agents"],
            score=best["score"],
            payload=best,
        )
        self.store.write_event("fleet_optimized", best)
        self._save_learning_state()
        return {"candidates": candidates, "best": best}

    def curate_learning_plan(
        self,
        sql_signal: float = 0.7,
        internet_signal: float = 0.5,
        llm_signal: float = 0.6,
        stability_bias: float = 0.65,
        persist_telemetry: bool = True,
    ) -> Dict:
        sql = max(0.0, min(1.0, sql_signal))
        internet = max(0.0, min(1.0, internet_signal))
        if self.offline_only_mode:
            internet = 0.0
        elif self.user_routed_internet:
            internet = min(internet, 0.14)
        llm = max(0.0, min(1.0, llm_signal))
        stability = max(0.0, min(1.0, stability_bias))

        source_weights = {
            "sql": (sql * 0.55) + (stability * 0.20),
            "internet": (internet * 0.45) + ((1.0 - stability) * 0.20),
            "llm": (llm * 0.50) + (stability * 0.10),
        }
        if self.native_bridge.available:
            source_weights["sql"] *= 1.12
            source_weights["llm"] *= 1.08
            source_weights["internet"] *= 0.92
        if self.low_bandwidth_mode:
            source_weights["sql"] *= 1.12
            source_weights["llm"] *= 1.08
            source_weights["internet"] *= 0.35
        if self.offline_only_mode:
            source_weights["internet"] = 0.0
        elif self.user_routed_internet:
            source_weights["internet"] *= 0.22
        total = sum(source_weights.values()) or 1.0
        normalized = {k: v / total for k, v in source_weights.items()}
        primary = max(normalized, key=normalized.get)

        plan = {
            "primary_source": primary,
            "source_weights": normalized,
            "stability_bias": stability,
            "cpp_kernel": self.cpp_kernel_status(),
            "recommendation": "focus-local-fast-low-bandwidth" if self.low_bandwidth_mode else ("focus-truth-and-retention" if stability > 0.62 else "focus-exploration-and-diversity"),
        }
        if persist_telemetry:
            telemetry_warnings: List[str] = []
            try:
                self.store.write_event("learning_curated", plan)
            except sqlite3.OperationalError as exc:
                telemetry_warnings.append(f"learning_curated_event_failed:{exc}")
            try:
                self.store.write_external_signal("curation", normalized[primary], plan)
            except sqlite3.OperationalError as exc:
                telemetry_warnings.append(f"curation_signal_failed:{exc}")
            if telemetry_warnings:
                plan["telemetry_warnings"] = telemetry_warnings
        self._save_learning_state()
        return plan

    def learning_pulse(
        self,
        specialty: str = "fleet",
        steps: int = 120,
        candidates: int = 60,
        sql_signal: float = 0.7,
        internet_signal: float = 0.55,
        llm_signal: float = 0.65,
        stability_bias: float = 0.68,
    ) -> Dict:
        sim = self.run_simulations(steps=steps, specialty=specialty)
        fleet = self.optimize_fleet_topology(specialty=specialty, candidates=candidates)
        curation = self.curate_learning_plan(
            sql_signal=sql_signal,
            internet_signal=internet_signal,
            llm_signal=llm_signal,
            stability_bias=stability_bias,
        )
        pulse = {
            "specialty": specialty,
            "simulation": sim,
            "fleet": fleet,
            "curation": curation,
            "cpp_kernel": self.cpp_kernel_status(),
            "pulse_score": (
                sim["avg_long_haul_meta_score"] * 0.38
                + sim["avg_fleet_shape_score"] * 0.24
                + sim["avg_quantized_compression_score"] * 0.18
                + sim["avg_truth_score"] * 0.20
            ),
        }
        self.store.write_event("learning_pulse", pulse)
        return pulse

    def run_dedupe_optimization(self, roots: Optional[List[str]] = None, max_file_mb: int = 8) -> Dict:
        roots = roots or ["imports", "core", "src", "runtime"]
        max_bytes = max(1, int(max_file_mb)) * 1024 * 1024
        skip_dirs = {".git", "obj", "bin", "node_modules", "__pycache__"}
        hash_map: Dict[str, List[Dict]] = {}

        for root in roots:
            if not os.path.exists(root):
                continue
            for base, dirs, files in os.walk(root):
                dirs[:] = [d for d in dirs if d not in skip_dirs]
                for name in files:
                    path = os.path.join(base, name)
                    try:
                        size = os.path.getsize(path)
                    except OSError:
                        continue
                    if size <= 0 or size > max_bytes:
                        continue
                    try:
                        with open(path, "rb") as f:
                            digest = hashlib.sha256(f.read()).hexdigest()
                    except OSError:
                        continue
                    hash_map.setdefault(digest, []).append({"path": path, "size": size})

        groups = []
        potential_saved = 0
        for digest, items in hash_map.items():
            if len(items) < 2:
                continue
            total = sum(i["size"] for i in items)
            potential_saved += total - min(i["size"] for i in items)
            sample = items[0]["path"]
            self.store.write_dedupe_candidate(digest, len(items), total, sample)
            groups.append(
                {
                    "hash": digest,
                    "count": len(items),
                    "total_bytes": total,
                    "sample_path": sample,
                }
            )

        groups.sort(key=lambda g: g["total_bytes"], reverse=True)
        result = {
            "roots": roots,
            "duplicate_groups": len(groups),
            "potential_saved_bytes": potential_saved,
            "top_groups": groups[:20],
        }
        self.store.write_event("dedupe_optimization", result)
        return result

    def llm_chat(
        self,
        prompt: str,
        system_prompt: str = "You are Hermes AIHub assistant.",
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 512,
    ) -> Dict:
        llm_model = (model or self.unified_config["llm_api_model"]).strip()
        if not prompt.strip():
            prompt = "Provide a short Hermes training-ground recommendation."
        curated = self.curate_learning_plan(
            sql_signal=0.75 + random.uniform(-0.1, 0.1),
            internet_signal=(
                0.0
                if self.offline_only_mode
                else (
                    min(0.14, (0.20 if self.low_bandwidth_mode else 0.55) + random.uniform(-0.06, 0.06))
                    if self.user_routed_internet
                    else ((0.20 if self.low_bandwidth_mode else 0.55) + random.uniform(-0.06, 0.06))
                )
            ),
            llm_signal=0.7 + random.uniform(-0.08, 0.08),
            stability_bias=0.7,
            persist_telemetry=False,
        )
        aihub_bonus = self.compute_aihub_bonus()
        multi_llm = self._multi_llm_optimizer(
            model_hint=llm_model,
            curated=curated,
            max_tokens=max_tokens,
            aihub_bonus=aihub_bonus,
        )
        text = (
            f"[TEMP API::{multi_llm['selected_model']}] {system_prompt}\n"
            f"Hermes response to prompt: {prompt[:220]}\n"
            f"Recommended source focus: {curated['primary_source']} "
            f"(sql={curated['source_weights']['sql']:.2f}, internet={curated['source_weights']['internet']:.2f}, llm={curated['source_weights']['llm']:.2f}).\n"
            f"Stability bias={curated['stability_bias']:.2f}, recommendation={curated['recommendation']}, "
            f"aihub_bonus={aihub_bonus:.3f}, temperature={temperature:.2f}, max_tokens={max_tokens}.\n"
            f"Multi-LLM optimizer: model={multi_llm['selected_model']}, "
            f"blend={multi_llm['blend_mode']}, est_cost=${multi_llm['estimated_cost_usd']:.4f}, "
            f"speed_tokens_per_sec={multi_llm['estimated_tokens_per_sec']:.1f}, "
            f"token_efficiency={multi_llm['token_efficiency']:.3f}."
        )
        parsed = {
            "provider": "temp-api",
            "model": multi_llm["selected_model"],
            "curation": curated,
            "aihub_bonus": aihub_bonus,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "multi_llm_optimizer": multi_llm,
        }

        result = {
            "ok": True,
            "provider": "temp-api",
            "model": multi_llm["selected_model"],
            "response_text": text,
            "provider_response": parsed,
        }
        if os.getenv("HERMES_LLM_CHAT_EVENT_LOG", "false").lower() in ("1", "true", "yes", "on"):
            try:
                self.store.write_event(
                    "llm_chat",
                    {"model": multi_llm["selected_model"], "prompt_chars": len(prompt), "response_chars": len(text), "llm_optimizer": multi_llm},
                )
            except sqlite3.OperationalError as exc:
                result["telemetry_warning"] = f"llm_chat_event_failed:{exc}"
        return result

    def _multi_llm_optimizer(self, model_hint: str, curated: Dict, max_tokens: int, aihub_bonus: float) -> Dict:
        # Simulated multi-LLM routing profiles for low-cost/high-power blended selection.
        profiles = [
            {"id": "hermes-mini-fast", "cost_per_1k": 0.0018, "speed_tps": 125.0, "quality": 0.68},
            {"id": "hermes-balanced-plus", "cost_per_1k": 0.0055, "speed_tps": 72.0, "quality": 0.82},
            {"id": "hermes-reasoning-max", "cost_per_1k": 0.0120, "speed_tps": 36.0, "quality": 0.94},
        ]
        if model_hint:
            hint = model_hint.lower()
            for p in profiles:
                if p["id"] in hint:
                    p["quality"] = min(0.99, p["quality"] + 0.03)
        source = curated.get("source_weights", {})
        llm_weight = float(source.get("llm", 0.6))
        stability = float(curated.get("stability_bias", 0.7))
        bonus_amp = max(0.0, min(1.0, aihub_bonus))
        token_load = max(1, int(max_tokens))

        scored = []
        for p in profiles:
            speed_score = min(1.0, p["speed_tps"] / 130.0)
            cost_score = max(0.0, min(1.0, 1.0 - (p["cost_per_1k"] / 0.013)))
            power_score = p["quality"]
            blend = (
                power_score * (0.40 + (llm_weight * 0.25))
                + speed_score * (0.25 + ((1.0 - stability) * 0.15))
                + cost_score * (0.25 + (stability * 0.10))
                + bonus_amp * 0.10
            )
            scored.append((blend, p, speed_score, cost_score, power_score))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[0]
        selected = top[1]
        estimated_cost = (token_load / 1000.0) * selected["cost_per_1k"] * (1.0 - (bonus_amp * 0.22))
        token_efficiency = max(0.0, min(1.0, (top[2] * 0.35) + (top[3] * 0.40) + (top[4] * 0.25)))
        blend_mode = "cost-speed-power-amplified" if bonus_amp > 0.55 else "cost-speed-power-balanced"
        return {
            "selected_model": selected["id"],
            "blend_mode": blend_mode,
            "estimated_cost_usd": float(max(0.0001, estimated_cost)),
            "estimated_tokens_per_sec": float(selected["speed_tps"] * (1.0 + (bonus_amp * 0.08))),
            "token_efficiency": float(token_efficiency),
            "candidates": [
                {
                    "model": item[1]["id"],
                    "blend_score": float(item[0]),
                    "cost_per_1k_tokens": float(item[1]["cost_per_1k"]),
                    "speed_tokens_per_sec": float(item[1]["speed_tps"]),
                    "quality_score": float(item[1]["quality"]),
                }
                for item in scored
            ],
        }

    def compute_aihub_bonus(self, persist: bool = True) -> float:
        signal = self.store.recent_external_signal_score()
        movie_signal = self.store.recent_external_signal_score_by_source("movie")
        media_signal = self.store.recent_external_signal_score_by_source("media")
        movie_mesh_signal = self.store.knowledge_mesh_task_signal("movie")
        media_mesh_signal = self.store.knowledge_mesh_task_signal("media")
        movie_domain_signal = max(0.0, min(1.0, (movie_signal * 0.4) + (media_signal * 0.2) + (movie_mesh_signal * 0.25) + (media_mesh_signal * 0.15)))
        knaa_tail = self.algorithm_state["knaa_qnaa_memory"][-80:]
        fleet_tail = self.algorithm_state["fleet_shape_memory"][-80:]
        meta_tail = self.algorithm_state["long_haul_meta_memory"][-80:]
        adaptive_tail = self.algorithm_state["adaptive_brain_memory"][-80:]
        knaa_avg = (sum(knaa_tail) / len(knaa_tail)) if knaa_tail else 0.5
        fleet_avg = (sum(fleet_tail) / len(fleet_tail)) if fleet_tail else 0.5
        meta_avg = (sum(meta_tail) / len(meta_tail)) if meta_tail else 0.5
        adaptive_avg = (sum(adaptive_tail) / len(adaptive_tail)) if adaptive_tail else 0.5
        bonus = max(0.0, min(1.0, (signal * 0.24) + (movie_domain_signal * 0.14) + (knaa_avg * 0.15) + (fleet_avg * 0.16) + (meta_avg * 0.16) + (adaptive_avg * 0.15)))
        if persist:
            mem = self.algorithm_state["aihub_bonus_memory"]
            mem.append(bonus)
            if len(mem) > 2000:
                del mem[: len(mem) - 2000]
        return bonus

    def rank_llm_output(
        self,
        output_text: str,
        goal: str = "balanced",
        quality: float = 0.7,
        speed: float = 0.7,
        cost_efficiency: float = 0.7,
        truth_score: float = 0.7,
    ) -> Dict:
        goal_key = goal if goal in self.goal_shape_targets else "balanced"
        point = (
            max(0.0, min(1.0, quality)),
            max(0.0, min(1.0, speed)),
            max(0.0, min(1.0, cost_efficiency)),
        )
        target = self.goal_shape_targets[goal_key]
        shape_score = self._gaussian_3d_shape_score(point, target, sigma=0.22)
        rank_score = (
            shape_score * 0.48
            + max(0.0, min(1.0, truth_score)) * 0.32
            + max(0.0, min(1.0, quality)) * 0.12
            + max(0.0, min(1.0, speed)) * 0.08
        )
        out_hash = str(abs(hash(output_text)) % 10_000_000_000)
        self.store.write_llm_ranking(
            goal=goal_key,
            output_hash=out_hash,
            rank_score=rank_score,
            quality=quality,
            speed=speed,
            cost_efficiency=cost_efficiency,
            truth_score=truth_score,
            shape3d=point,
        )
        event = {
            "goal": goal_key,
            "output_hash": out_hash,
            "rank_score": rank_score,
            "shape3d_score": shape_score,
            "shape3d_point": point,
            "shape3d_target": target,
        }
        self.store.write_event("llm_output_ranked", event)
        return event

    def run_horizon_test_suite(self, specialty: str = "general", short_steps: int = 80, mid_steps: int = 300, long_steps: int = 1200) -> Dict:
        short = self.run_simulations(steps=short_steps, specialty=specialty)
        mid = self.run_simulations(steps=mid_steps, specialty=specialty)
        long = self.run_simulations(steps=long_steps, specialty=specialty)
        weighted = (
            short["avg_short_score"] * 0.42
            + mid["avg_mid_score"] * 0.33
            + long["avg_long_score"] * 0.25
        )
        return {
            "specialty": specialty,
            "short": short,
            "mid": mid,
            "long": long,
            "weighted_horizon_score": weighted,
        }

    def snapshot(self) -> Dict:
        p = self.governor.pressure()
        return {
            "resource_pressure": p,
            "reward_weights": self.reward_weights,
            "knaa_qnaa_memory_tail": self.algorithm_state["knaa_qnaa_memory"][-20:],
            "fleet_shape_memory_tail": self.algorithm_state["fleet_shape_memory"][-20:],
            "punishment_memory_tail": self.algorithm_state["punishment_memory"][-20:],
            "long_haul_meta_memory_tail": self.algorithm_state["long_haul_meta_memory"][-20:],
            "adaptive_brain_memory_tail": self.algorithm_state["adaptive_brain_memory"][-20:],
            "adaptive_dynamic_modifiers": self.algorithm_state.get("adaptive_dynamic_modifiers", {}),
            "aihub_bonus_memory_tail": self.algorithm_state["aihub_bonus_memory"][-20:],
            "agents": [asdict(a) for a in self.agents],
            "unified_config": self.unified_config,
            "growth": self.growth_metrics(),
            "cpp_kernel": self.cpp_kernel_status(),
            "knowledge_mesh": self.knowledge_mesh_state(),
            "aihub_bonus_live": self.compute_aihub_bonus(persist=False),
            "learning_state_path": self._resolved_learning_state_path(),
            "recent_events": self.store.recent_events(limit=10),
            "external_signals_tail": self.store.recent_external_signals(limit=20),
        }

    def training_status(self, max_idle_seconds: int = 120) -> Dict:
        now = time.time()
        max_idle = max(30, int(max_idle_seconds))
        recent_events = self.store.recent_events(limit=80)
        recent_signals = self.store.recent_external_signals(limit=80)

        last_event_ts = 0.0
        for item in recent_events:
            if item.get("event_type") in ("learning_pulse", "train_step", "learning_curated", "fleet_optimized"):
                ts = float(item.get("ts", 0.0))
                if ts > last_event_ts:
                    last_event_ts = ts

        last_trainer_signal_ts = 0.0
        for item in recent_signals:
            src = str(item.get("source", "")).lower()
            if "auto_trainer" in src or "trainer" in src:
                ts = float(item.get("ts", 0.0))
                if ts > last_trainer_signal_ts:
                    last_trainer_signal_ts = ts

        last_training_ts = max(last_event_ts, last_trainer_signal_ts)
        idle_seconds = max(0.0, now - last_training_ts) if last_training_ts > 0 else float("inf")
        training_active = idle_seconds <= float(max_idle)
        cpp = self.cpp_kernel_status()
        rules = {
            "training_active": training_active,
            "cpp_brain_available": bool(cpp.get("available", False)),
            "aihub_unified_enabled": bool(self.unified_config.get("aihub_unified_enabled", True)),
            "offline_only_mode": bool(self.offline_only_mode),
            "user_routed_internet": bool(self.user_routed_internet),
        }
        passing_rules = len([v for v in rules.values() if bool(v)])
        return {
            "ok": True,
            "training_active": training_active,
            "max_idle_seconds": max_idle,
            "idle_seconds": None if last_training_ts <= 0 else idle_seconds,
            "last_training_unix": None if last_training_ts <= 0 else last_training_ts,
            "recent_learning_events": len([e for e in recent_events if e.get("event_type") == "learning_pulse"]),
            "recent_train_steps": len([e for e in recent_events if e.get("event_type") == "train_step"]),
            "recent_trainer_signals": len([s for s in recent_signals if "trainer" in str(s.get("source", "")).lower()]),
            "rules": rules,
            "rule_score": f"{passing_rules}/{len(rules)}",
            "recommended_action": "continue_training" if training_active else "trigger_learning_pulse_or_auto_trainer",
        }


class OrchestratorApi:
    def __init__(self, orchestrator: HermesSuperOrchestrator, host: str = "127.0.0.1", port: int = 8787) -> None:
        self.orchestrator = orchestrator
        self.host = host
        self.port = port
        self.api_key = os.getenv("HERMES_API_KEY", "")
        self.allow_insecure_no_key = os.getenv("HERMES_ALLOW_INSECURE_NO_KEY", "false").lower() in ("1", "true", "yes", "on")

    def _handler(self):
        orchestrator = self.orchestrator
        api_key = self.api_key
        allow_insecure_no_key = self.allow_insecure_no_key

        class Handler(BaseHTTPRequestHandler):
            def _authorized(self) -> bool:
                if not api_key:
                    return allow_insecure_no_key
                incoming = self.headers.get("X-Hermes-Key", "")
                return incoming == api_key

            def _json(self, payload: Dict, status: int = 200) -> None:
                body = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):  # noqa: N802
                if self.path == "/health":
                    self._json({"ok": True})
                    return
                if not self._authorized():
                    self._json({"error": "unauthorized"}, status=401)
                    return
                if self.path == "/snapshot":
                    self._json(orchestrator.snapshot())
                    return
                if self.path == "/aihub-bonus":
                    self._json({"aihub_bonus": orchestrator.compute_aihub_bonus()})
                    return
                if self.path == "/unified-config":
                    self._json(orchestrator.unified_config)
                    return
                if self.path == "/learning-state":
                    self._json(orchestrator.export_learning_state())
                    return
                if self.path == "/learning-growth":
                    self._json(orchestrator.growth_metrics())
                    return
                if self.path == "/cpp-kernel-status":
                    self._json(orchestrator.cpp_kernel_status())
                    return
                if self.path == "/knowledge-mesh":
                    self._json(orchestrator.knowledge_mesh_state())
                    return
                if self.path == "/training-status":
                    self._json(orchestrator.training_status())
                    return
                self._json({"error": "not_found"}, status=404)

            def do_POST(self):  # noqa: N802
                if not self._authorized():
                    self._json({"error": "unauthorized"}, status=401)
                    return
                if self.path not in ("/train-step", "/simulate", "/horizon-tests", "/rank-output", "/ingest-signal", "/ingest-knowledge-mesh", "/optimize-fleet", "/curate-learning", "/learning-pulse", "/dedupe-optimize", "/aihub-bonus", "/llm-chat", "/learning-state/import"):
                    self._json({"error": "not_found"}, status=404)
                    return
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length) if length else b"{}"
                payload = json.loads(body.decode("utf-8"))
                if self.path == "/train-step":
                    result = orchestrator.train_step(
                        specialty_hint=str(payload.get("specialty", "general")),
                        workload_complexity=float(payload.get("complexity", 0.5)),
                    )
                else:
                    if self.path == "/simulate":
                        result = orchestrator.run_simulations(
                            steps=int(payload.get("steps", payload.get("simulations", 500))),
                            specialty=str(payload.get("specialty", "general")),
                        )
                    elif self.path == "/horizon-tests":
                        result = orchestrator.run_horizon_test_suite(
                            specialty=str(payload.get("specialty", "general")),
                            short_steps=int(payload.get("short_steps", 80)),
                            mid_steps=int(payload.get("mid_steps", 300)),
                            long_steps=int(payload.get("long_steps", 1200)),
                        )
                    elif self.path == "/ingest-signal":
                        source = str(payload.get("source", "external"))
                        signal_score = max(0.0, min(1.0, float(payload.get("signal_score", 0.5))))
                        signal_payload = payload.get("payload", {})
                        if not isinstance(signal_payload, dict):
                            signal_payload = {"value": str(signal_payload)}
                        orchestrator.store.write_external_signal(source, signal_score, signal_payload)
                        result = {"ok": True, "source": source, "signal_score": signal_score}
                    elif self.path == "/ingest-knowledge-mesh":
                        result = orchestrator.ingest_knowledge_mesh(payload)
                    elif self.path == "/optimize-fleet":
                        result = orchestrator.optimize_fleet_topology(
                            specialty=str(payload.get("specialty", "fleet")),
                            candidates=int(payload.get("candidates", 80)),
                        )
                    elif self.path == "/curate-learning":
                        result = orchestrator.curate_learning_plan(
                            sql_signal=float(payload.get("sql_signal", 0.7)),
                            internet_signal=float(payload.get("internet_signal", 0.5)),
                            llm_signal=float(payload.get("llm_signal", 0.6)),
                            stability_bias=float(payload.get("stability_bias", 0.65)),
                        )
                    elif self.path == "/learning-pulse":
                        result = orchestrator.learning_pulse(
                            specialty=str(payload.get("specialty", "fleet")),
                            steps=int(payload.get("steps", 120)),
                            candidates=int(payload.get("candidates", 60)),
                            sql_signal=float(payload.get("sql_signal", 0.7)),
                            internet_signal=float(payload.get("internet_signal", 0.55)),
                            llm_signal=float(payload.get("llm_signal", 0.65)),
                            stability_bias=float(payload.get("stability_bias", 0.68)),
                        )
                    elif self.path == "/dedupe-optimize":
                        roots = payload.get("roots", ["imports", "core", "src", "runtime"])
                        if not isinstance(roots, list):
                            roots = ["imports", "core", "src", "runtime"]
                        result = orchestrator.run_dedupe_optimization(
                            roots=[str(r) for r in roots],
                            max_file_mb=int(payload.get("max_file_mb", 8)),
                        )
                    elif self.path == "/aihub-bonus":
                        result = {"aihub_bonus": orchestrator.compute_aihub_bonus()}
                    elif self.path == "/llm-chat":
                        result = orchestrator.llm_chat(
                            prompt=str(payload.get("prompt", "")),
                            system_prompt=str(payload.get("system_prompt", "You are Hermes AIHub assistant.")),
                            model=(str(payload.get("model", "")).strip() or None),
                            temperature=float(payload.get("temperature", 0.3)),
                            max_tokens=int(payload.get("max_tokens", 512)),
                        )
                    elif self.path == "/learning-state/import":
                        result = orchestrator.import_learning_state(payload)
                    else:
                        result = orchestrator.rank_llm_output(
                            output_text=str(payload.get("output", "")),
                            goal=str(payload.get("goal", "balanced")),
                            quality=float(payload.get("quality", 0.7)),
                            speed=float(payload.get("speed", 0.7)),
                            cost_efficiency=float(payload.get("cost_efficiency", 0.7)),
                            truth_score=float(payload.get("truth_score", 0.7)),
                        )
                self._json(result)

        return Handler

    def serve(self) -> None:
        server = ThreadingHTTPServer((self.host, self.port), self._handler())
        print(f"Hermes super orchestrator API running at http://{self.host}:{self.port}")
        server.serve_forever()


def build_default_orchestrator() -> HermesSuperOrchestrator:
    agents = [
        AgentProfile("hermes-llm-core", "llm_orchestration", reward_score=0.6, success_rate=0.7),
        AgentProfile("hermes-sql-mind", "sql_learning", reward_score=0.7, success_rate=0.75),
        AgentProfile("hermes-chaos", "chaos_engine", reward_score=0.4, success_rate=0.6),
        AgentProfile("hermes-cpp-tight", "cpp_ml_kernels", reward_score=0.5, success_rate=0.65),
        AgentProfile("hermes-compress", "quantization_compression", reward_score=0.6, success_rate=0.7),
        AgentProfile("hermes-gui-pilot", "gui_runtime", reward_score=0.55, success_rate=0.72),
    ]
    return HermesSuperOrchestrator(agents=agents)


if __name__ == "__main__":
    api_host = os.getenv("HERMES_API_HOST", "0.0.0.0")
    api_port = int(os.getenv("HERMES_API_PORT", "8787"))
    api = OrchestratorApi(build_default_orchestrator(), host=api_host, port=api_port)
    api.serve()
