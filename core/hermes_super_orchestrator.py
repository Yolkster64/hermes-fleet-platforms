import json
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
    success: float


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
        self.governor = ResourceGovernor(gpu_target_utilization=0.75)
        self.reward_weights = {"quality": 0.32, "speed": 0.20, "cost": 0.16, "truth": 0.22, "novelty": 0.10}
        self.truth_threshold = 0.68
        self.native_bridge = HermesCppNativeBridge()
        self.algorithm_state = {
            "bandit_values": {},  # specialty -> value
            "q_table": {},  # (specialty, bin) -> value
            "beta_priors": {},  # specialty -> (alpha, beta)
        }
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

    def _multi_objective_score(self, outcome: InteractionOutcome) -> float:
        weights = [
            self.reward_weights["quality"],
            self.reward_weights["speed"],
            self.reward_weights["cost"],
            self.reward_weights["truth"],
            self.reward_weights["novelty"],
        ]
        return self.native_bridge.reward_update(
            quality=outcome.quality,
            speed=outcome.speed,
            cost_efficiency=outcome.cost_efficiency,
            truth_score=outcome.truth_score,
            novelty=outcome.novelty,
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

            success = 1.0 if random.random() < (0.32 + agent.success_rate * 0.62) else 0.0
            quality = max(0.0, min(1.0, (agent.success_rate * 0.65) + random.uniform(0.0, 0.35)))
            speed = max(0.0, 1.0 - effective_work * random.uniform(0.68, 1.25))
            cost_efficiency = max(0.0, 1.0 - (effective_work * random.uniform(0.3, 0.9)))
            truth_score = max(0.0, min(1.0, quality * 0.7 + success * 0.2 + random.uniform(0.0, 0.1)))
            novelty = max(0.0, min(1.0, random.gauss(0.55, 0.2)))
            outcome = InteractionOutcome(
                quality=quality,
                speed=speed,
                cost_efficiency=cost_efficiency,
                truth_score=truth_score,
                novelty=novelty,
                success=success,
            )
            objective_score = self._multi_objective_score(outcome)
            delta = self._truth_gate_adjustment(objective_score, truth_score)

            agent.reward_score = max(0.0, min(10.0, agent.reward_score + (delta - 0.28)))
            agent.success_rate = max(0.0, min(1.0, (agent.success_rate * 0.86) + (success * 0.14)))
            agent.load = max(0.0, min(1.0, effective_work))

            self._run_algorithm_updates(agent.specialty, workload_complexity, delta, success)
            self._gaussian_tune_rewards()
            self._natural_selection()

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
                "objective_score": objective_score,
                "reward_score": agent.reward_score,
                "success_rate": agent.success_rate,
                "capacity_scale": scale,
            }
            self.store.write_event("train_step", event)
            return event

    def run_simulations(self, steps: int = 250, specialty: str = "general") -> Dict:
        steps = max(1, min(20000, int(steps)))
        results = []
        for _ in range(steps):
            complexity = max(0.05, min(1.0, random.gauss(0.58, 0.22)))
            results.append(self.train_step(specialty, complexity))

        avg_reward = sum(r["reward_score"] for r in results) / len(results)
        avg_truth = sum(r["truth_score"] for r in results) / len(results)
        avg_quality = sum(r["quality"] for r in results) / len(results)
        avg_speed = sum(r["speed"] for r in results) / len(results)
        avg_cost = sum(r["cost_efficiency"] for r in results) / len(results)
        truth_violations = len([r for r in results if r["truth_score"] < self.truth_threshold])
        return {
            "steps": steps,
            "avg_reward_score": avg_reward,
            "avg_truth_score": avg_truth,
            "avg_quality": avg_quality,
            "avg_speed": avg_speed,
            "avg_cost_efficiency": avg_cost,
            "truth_violations": truth_violations,
            "reward_weights": self.reward_weights,
        }

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
                if self.path not in ("/train-step", "/simulate"):
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
                    result = orchestrator.run_simulations(
                        steps=int(payload.get("steps", 500)),
                        specialty=str(payload.get("specialty", "general")),
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
