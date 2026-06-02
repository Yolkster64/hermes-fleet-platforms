from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).resolve().parent))
from deep_engine_fabric import build_engine_catalog, recommend_engine_mix


DASHBOARD_HTML = """<!doctype html>
<html><head><meta charset='utf-8'><title>AIHub Control</title>
<style>body{font-family:Segoe UI,Arial;background:#0f172a;color:#e2e8f0;margin:24px}
.card{background:#111827;border:1px solid #334155;border-radius:10px;padding:16px;margin-bottom:14px}
button{background:#1d4ed8;color:#fff;border:0;padding:8px 12px;border-radius:6px;cursor:pointer}</style></head>
<body><h1>XTier AIHub Control</h1>
<div class='card'><h3>Health</h3><pre id='health'></pre></div>
<div class='card'><h3>Polyglot Report</h3><pre id='report'></pre></div>
<div class='card'><h3>Conversation Integration</h3><pre id='conversation'></pre></div>
<div class='card'><h3>Training</h3><button onclick='triggerTrain()'>Trigger Training Job</button><pre id='train'></pre></div>
<script>
async function load(){const h=await fetch('/api/health').then(r=>r.json());document.getElementById('health').textContent=JSON.stringify(h,null,2);
const rp=await fetch('/api/report').then(r=>r.json());document.getElementById('report').textContent=JSON.stringify(rp,null,2);
const cv=await fetch('/api/conversation/report').then(r=>r.json());document.getElementById('conversation').textContent=JSON.stringify(cv,null,2);}
async function triggerTrain(){const r=await fetch('/api/train/trigger',{method:'POST'}).then(x=>x.json());document.getElementById('train').textContent=JSON.stringify(r,null,2);}
load();</script></body></html>"""


class AIHubServer(BaseHTTPRequestHandler):
    config: dict = {}

    def _read_json_file(self, path: Path) -> dict[str, Any] | list[Any] | None:
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None

    def _load_polyglot_report(self) -> dict[str, Any]:
        report = Path(self.config["services"]["polyglot_report"])
        data = self._read_json_file(report)
        return data if isinstance(data, dict) else {}

    def _load_conversation_report(self) -> dict[str, Any]:
        report = Path(self.config["services"]["conversation_report"])
        data = self._read_json_file(report)
        return data if isinstance(data, dict) else {}

    def _load_agents(self) -> list[dict[str, Any]]:
        path = Path(self.config["services"].get("fleet_agents_path", "runtime/hermes_persist/agents/simple_agents.json"))
        data = self._read_json_file(path)
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        return []

    def _load_setup_tracker(self) -> dict[str, Any]:
        path = Path(self.config["services"].get("setup_tracker_path", "config/x-tier/unified-super-system-tracker.json"))
        data = self._read_json_file(path)
        return data if isinstance(data, dict) else {}

    def _tail_jsonl_count(self, path: Path, max_lines: int = 2000) -> tuple[int, int]:
        if not path.exists():
            return 0, 0
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return 0, 0
        clipped = lines[-max_lines:]
        return len(lines), len([ln for ln in clipped if ln.strip()])

    def _build_fleet_live(self) -> dict[str, Any]:
        agents = self._load_agents()
        total = len(agents)
        deployed = len([a for a in agents if bool(a.get("deployed", False))])
        hermes = len([a for a in agents if str(a.get("family", "")).lower() == "hermes"])
        xcore = len([a for a in agents if str(a.get("family", "")).lower() == "x"])
        profiles: dict[str, int] = {}
        for a in agents:
            p = str(a.get("profile", "unknown"))
            profiles[p] = profiles.get(p, 0) + 1
        return {
            "total_agents": total,
            "deployed_agents": deployed,
            "hermes_agents": hermes,
            "xcore_agents": xcore,
            "deployment_ratio": round((deployed / total), 4) if total else 0.0,
            "profiles": profiles,
        }

    def _build_knowledge_summary(self) -> dict[str, Any]:
        poly = self._load_polyglot_report()
        conv = self._load_conversation_report()
        coverage = conv.get("component_coverage", {}) if isinstance(conv.get("component_coverage", {}), dict) else {}
        cpp_core = poly.get("cpp_source_of_truth", {}) if isinstance(poly.get("cpp_source_of_truth", {}), dict) else {}
        cpp_resource = cpp_core.get("security_optimization_data", {}) if isinstance(cpp_core.get("security_optimization_data", {}), dict) else {}
        req_count = len(conv.get("requirements", [])) if isinstance(conv.get("requirements", []), list) else 0
        milestone_count = len(conv.get("milestones", [])) if isinstance(conv.get("milestones", []), list) else 0
        uniq_req_count = len(conv.get("unique_requirements", [])) if isinstance(conv.get("unique_requirements", []), list) else 0

        # Heuristic ops metrics from available corpus + runtime signals.
        estimated_tokens = max(1200, (req_count * 240) + (milestone_count * 170))
        token_efficiency = round(min(100.0, 55.0 + (uniq_req_count / max(1, req_count)) * 45.0), 2)
        estimated_cost_usd = round((estimated_tokens / 1000.0) * 0.0035, 4)
        perf_speed_score = round(min(100.0, 40.0 + (coverage.get("optimization", 0) * 3.8) + (coverage.get("runtime", 0) * 2.1)), 2)
        power_efficiency_score = round(min(100.0, 45.0 + (coverage.get("optimization", 0) * 3.4)), 2)
        security_score = round(min(100.0, 50.0 + (coverage.get("security", 0) * 3.8) + (coverage.get("vhdx", 0) * 1.5)), 2)
        if cpp_resource:
            perf_speed_score = round(min(100.0, perf_speed_score + (float(cpp_resource.get("kernel_parallel_lane_utilization", 0.0)) * 5.0)), 2)
            power_efficiency_score = round(
                min(100.0, power_efficiency_score + (float(cpp_resource.get("lightweight_score", 0.0)) * 35.0)),
                2,
            )
            security_score = round(min(100.0, security_score + (float(cpp_resource.get("kernel_cpu_clamp", 0.0)) * 8.0)), 2)

        training_log = Path(self.config["aihub"]["training_log"])
        training_total, training_recent = self._tail_jsonl_count(training_log)
        fleet_live = self._build_fleet_live()
        cuda_enabled = bool(self.config["aihub"].get("cuda_enabled", True))
        engine_catalog = build_engine_catalog(cuda_enabled=cuda_enabled)
        engine_mix = recommend_engine_mix(
            cuda_enabled=cuda_enabled,
            security_profile=str(self.config["aihub"].get("security_profile", "balanced")),
            optimization_pressure=min(1.0, (perf_speed_score + power_efficiency_score) / 200.0),
            fleet_size=int(fleet_live.get("total_agents", 0)),
        )

        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "llm_token_optimization": {
                "estimated_tokens_per_cycle": estimated_tokens,
                "token_efficiency_score": token_efficiency,
                "estimated_cost_usd_per_cycle": estimated_cost_usd,
            },
            "performance": {
                "speed_score": perf_speed_score,
                "power_efficiency_score": power_efficiency_score,
                "security_score": security_score,
            },
            "fleet": fleet_live,
            "training": {
                "training_log_path": str(training_log),
                "training_events_total": training_total,
                "training_events_recent_window": training_recent,
            },
            "knowledge_mesh": {
                "requirements_count": req_count,
                "unique_requirements_count": uniq_req_count,
                "milestones_count": milestone_count,
                "component_coverage": coverage,
            },
            "deep_engines": {
                "catalog_total": engine_catalog["total_engines"],
                "backend_distribution": engine_catalog["backends"],
                "selected_for_runtime": engine_mix["selected_count"],
                "expected_memory_efficiency_score": engine_mix["expected_memory_efficiency_score"],
            },
            "cpp_source_of_truth": {
                "generated_by": cpp_core.get("generated_by", "cpp_native"),
                "runtime_decision": cpp_core.get("runtime_decision", {}),
                "optimization_plan": cpp_core.get("optimization_plan", {}),
                "security_optimization_data": cpp_resource,
                "major_parallelization_types": cpp_core.get("major_parallelization_types", []),
            },
            "runtime_endpoints": {
                "gateway": self.config["services"].get("hermes_gateway_url"),
                "gui": self.config["services"].get("hermes_gui_url"),
                "api": self.config["services"].get("hermes_api_url"),
            },
            "sources": {
                "polyglot_report": self.config["services"]["polyglot_report"],
                "conversation_report": self.config["services"]["conversation_report"],
                "fleet_agents_path": self.config["services"].get("fleet_agents_path"),
            },
            "consensus": poly.get("consensus", {}),
        }

    def _build_security_live(self) -> dict[str, Any]:
        poly = self._load_polyglot_report()
        conv = self._load_conversation_report()
        coverage = conv.get("component_coverage", {}) if isinstance(conv.get("component_coverage", {}), dict) else {}
        cpp_core = poly.get("cpp_source_of_truth", {}) if isinstance(poly.get("cpp_source_of_truth", {}), dict) else {}
        csharp_contract = poly.get("csharp_frontend_contract", {}) if isinstance(poly.get("csharp_frontend_contract", {}), dict) else {}
        firewall_weight = coverage.get("security", 0) + coverage.get("networking", 0)
        quarantine_weight = coverage.get("vhdx", 0) + coverage.get("security", 0)
        return {
            "profile": self.config["aihub"]["security_profile"],
            "live_scores": {
                "firewall_posture": round(min(100.0, 45.0 + firewall_weight * 3.0), 2),
                "quarantine_readiness": round(min(100.0, 40.0 + quarantine_weight * 3.4), 2),
                "zero_trust_alignment": round(min(100.0, 50.0 + coverage.get("security", 0) * 4.0), 2),
            },
            "coverage": coverage,
            "cpp_watch_plan": cpp_core.get("security_watch_plan", {}),
            "cpp_folder_governance": cpp_core.get("folder_governance_plan", {}),
            "cpp_alert_channels": cpp_core.get("alert_channels", []),
            "csharp_frontend_contract": csharp_contract,
        }

    def _json(self, payload: dict, status: int = 200) -> None:
        data = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _file(self, path: Path) -> dict:
        if not path.exists():
            return {"exists": False, "path": str(path)}
        return {"exists": True, "path": str(path), "content": json.loads(path.read_text(encoding="utf-8"))}

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/":
            html = DASHBOARD_HTML.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)
            return

        if self.path == "/api/health":
            self._json(
                {
                    "status": "ok",
                    "service": self.config["aihub"]["name"],
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "security_profile": self.config["aihub"]["security_profile"],
                }
            )
            return

        if self.path == "/api/report":
            report = Path(self.config["services"]["polyglot_report"])
            self._json(self._file(report))
            return

        if self.path == "/api/conversation/report":
            report = Path(self.config["services"]["conversation_report"])
            self._json(self._file(report))
            return

        if self.path == "/api/docker/status":
            self._json(
                {
                    "stack": "hermes-runtime",
                    "services": {
                        "gateway": self.config["services"].get("hermes_gateway_url"),
                        "gui": self.config["services"].get("hermes_gui_url"),
                        "api": self.config["services"].get("hermes_api_url"),
                        "aihub_control": f"http://127.0.0.1:{self.config['services']['dashboard_port']}",
                    },
                }
            )
            return

        if self.path == "/api/fleet/live":
            self._json(self._build_fleet_live())
            return

        if self.path == "/api/security/live":
            self._json(self._build_security_live())
            return

        if self.path == "/api/security/watch/live":
            self._json(self._build_security_live())
            return

        if self.path == "/api/knowledge/summary":
            self._json(self._build_knowledge_summary())
            return

        if self.path == "/api/engines/catalog":
            self._json(build_engine_catalog(cuda_enabled=bool(self.config["aihub"].get("cuda_enabled", True))))
            return

        if self.path == "/api/engines/recommend":
            fleet_live = self._build_fleet_live()
            summary = self._build_knowledge_summary()
            speed_score = float(summary.get("performance", {}).get("speed_score", 60.0))
            power_score = float(summary.get("performance", {}).get("power_efficiency_score", 60.0))
            pressure = min(1.0, (speed_score + power_score) / 200.0)
            self._json(
                recommend_engine_mix(
                    cuda_enabled=bool(self.config["aihub"].get("cuda_enabled", True)),
                    security_profile=str(self.config["aihub"].get("security_profile", "balanced")),
                    optimization_pressure=pressure,
                    fleet_size=int(fleet_live.get("total_agents", 0)),
                )
            )
            return

        if self.path == "/api/setup/tracker":
            self._json(self._load_setup_tracker())
            return

        if self.path == "/api/setup/autoboot-plan":
            tracker = self._load_setup_tracker()
            phases = tracker.get("phases", [])
            autoboot = next((p for p in phases if isinstance(p, dict) and p.get("id") == "phase-8"), {})
            self._json({"tracker_name": tracker.get("name"), "autoboot_phase": autoboot, "stubs_for_later": tracker.get("stubs_for_later", [])})
            return

        self._json({"error": "not_found", "path": self.path}, status=404)

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/api/train/trigger":
            training_log = Path(self.config["aihub"]["training_log"])
            training_log.parent.mkdir(parents=True, exist_ok=True)
            line = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "action": "training_triggered",
                "source": "aihub_control_server",
            }
            with training_log.open("a", encoding="utf-8") as f:
                f.write(json.dumps(line) + "\n")
            self._json({"status": "queued", "log": str(training_log)})
            return

        self._json({"error": "not_found", "path": self.path}, status=404)


def load_config(path: Path) -> dict:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    # Allow container/runtime overrides without mutating repo config.
    if os.getenv("AIHUB_POLYGLOT_REPORT"):
        cfg["services"]["polyglot_report"] = os.environ["AIHUB_POLYGLOT_REPORT"]
    if os.getenv("AIHUB_CONVERSATION_REPORT"):
        cfg["services"]["conversation_report"] = os.environ["AIHUB_CONVERSATION_REPORT"]
    if os.getenv("HERMES_GATEWAY_URL"):
        cfg["services"]["hermes_gateway_url"] = os.environ["HERMES_GATEWAY_URL"]
    if os.getenv("HERMES_GUI_URL"):
        cfg["services"]["hermes_gui_url"] = os.environ["HERMES_GUI_URL"]
    if os.getenv("HERMES_API_URL"):
        cfg["services"]["hermes_api_url"] = os.environ["HERMES_API_URL"]
    if os.getenv("AIHUB_FLEET_AGENTS_PATH"):
        cfg["services"]["fleet_agents_path"] = os.environ["AIHUB_FLEET_AGENTS_PATH"]
    if os.getenv("AIHUB_SETUP_TRACKER_PATH"):
        cfg["services"]["setup_tracker_path"] = os.environ["AIHUB_SETUP_TRACKER_PATH"]
    if os.getenv("AIHUB_CUDA_ENABLED"):
        cfg["aihub"]["cuda_enabled"] = os.environ["AIHUB_CUDA_ENABLED"].lower() in {"1", "true", "yes", "on"}
    return cfg


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local AIHub control server.")
    parser.add_argument("--config", default="config/x-tier/aihub-control.json")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--health-check", action="store_true")
    args = parser.parse_args()

    cfg = load_config(Path(args.config))
    if args.health_check:
        print(json.dumps({"status": "ok", "service": cfg["aihub"]["name"], "port": args.port}, indent=2))
        return 0

    AIHubServer.config = cfg
    server = ThreadingHTTPServer(("127.0.0.1", args.port), AIHubServer)
    print(f"AIHub control server running on http://127.0.0.1:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    raise SystemExit(main())
