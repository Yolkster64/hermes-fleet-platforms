import json
import random
import sqlite3
import threading
import time
import zlib
from dataclasses import dataclass, asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict, List, Optional

import psutil

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


class SqlTelemetryStore:
    def __init__(self, db_path: str = "runtime/auto/hermes_super_orchestrator.db") -> None:
        self.db_path = db_path
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path, check_same_thread=False)

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

    def write_metric(self, agent: AgentProfile) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO agent_metrics(ts, agent_name, reward_score, success_rate, load)
                VALUES (?, ?, ?, ?, ?)
                """,
                (time.time(), agent.name, agent.reward_score, agent.success_rate, agent.load),
            )

    def write_event(self, event_type: str, payload: Dict) -> None:
        compressed = zlib.compress(json.dumps(payload).encode("utf-8"))
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO orchestrator_events(ts, event_type, payload_compressed) VALUES (?, ?, ?)",
                (time.time(), event_type, compressed),
            )

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
        cpu = psutil.cpu_percent(interval=0.05) / 100.0
        mem = psutil.virtual_memory().percent / 100.0
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
        self.governor = ResourceGovernor(gpu_target_utilization=0.75)
        self.reward_weights = {"success": 0.55, "speed": 0.25, "novelty": 0.20}
        self.lock = threading.Lock()

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

    def train_step(self, specialty_hint: str, workload_complexity: float = 0.5) -> Dict:
        with self.lock:
            agent = self._select_agent(specialty_hint)
            scale = max(0.1, min(1.0, self.governor.capacity_scale()))
            effective_work = workload_complexity * scale

            success = 1.0 if random.random() < (0.35 + agent.success_rate * 0.6) else 0.0
            speed = max(0.0, 1.0 - effective_work * random.uniform(0.7, 1.3))
            novelty = random.uniform(0.0, 1.0)
            delta = (
                success * self.reward_weights["success"]
                + speed * self.reward_weights["speed"]
                + novelty * self.reward_weights["novelty"]
            )

            agent.reward_score = max(0.0, min(10.0, agent.reward_score + (delta - 0.35)))
            agent.success_rate = max(0.0, min(1.0, (agent.success_rate * 0.9) + (success * 0.1)))
            agent.load = max(0.0, min(1.0, effective_work))

            self._gaussian_tune_rewards()
            self._natural_selection()

            self.store.write_metric(agent)
            event = {
                "agent": agent.name,
                "specialty": agent.specialty,
                "success": success,
                "speed": speed,
                "novelty": novelty,
                "reward_score": agent.reward_score,
                "success_rate": agent.success_rate,
                "capacity_scale": scale,
            }
            self.store.write_event("train_step", event)
            return event

    def snapshot(self) -> Dict:
        p = self.governor.pressure()
        return {
            "resource_pressure": p,
            "reward_weights": self.reward_weights,
            "agents": [asdict(a) for a in self.agents],
            "recent_events": self.store.recent_events(limit=10),
        }


class OrchestratorApi:
    def __init__(self, orchestrator: HermesSuperOrchestrator, host: str = "127.0.0.1", port: int = 8787) -> None:
        self.orchestrator = orchestrator
        self.host = host
        self.port = port

    def _handler(self):
        orchestrator = self.orchestrator

        class Handler(BaseHTTPRequestHandler):
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
                if self.path == "/snapshot":
                    self._json(orchestrator.snapshot())
                    return
                self._json({"error": "not_found"}, status=404)

            def do_POST(self):  # noqa: N802
                if self.path != "/train-step":
                    self._json({"error": "not_found"}, status=404)
                    return
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length) if length else b"{}"
                payload = json.loads(body.decode("utf-8"))
                result = orchestrator.train_step(
                    specialty_hint=str(payload.get("specialty", "general")),
                    workload_complexity=float(payload.get("complexity", 0.5)),
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
    api = OrchestratorApi(build_default_orchestrator())
    api.serve()
