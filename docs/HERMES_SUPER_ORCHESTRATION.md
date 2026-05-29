# Hermes Super Orchestration (GPU-Targeted, SQL-First)

This profile provides a practical baseline for a high-complexity Hermes AI hub:

- Multi-agent orchestration with specialization routing
- Adaptive reward tuning (gaussian perturbation)
- Natural-selection style retirement and spawning
- SQL telemetry with compressed event payloads
- Local API for GUI and automation integration
- Resource governor targeting ~75% GPU utilization

## Runtime Module

- `core/hermes_super_orchestrator.py`

Main classes:

1. `HermesSuperOrchestrator`
2. `ResourceGovernor`
3. `SqlTelemetryStore`
4. `OrchestratorApi`

## Quick Start

```bash
python core/hermes_super_orchestrator.py
```

API endpoints:

1. `GET /health`
2. `GET /snapshot`
3. `POST /train-step`

Example training call:

```bash
curl -X POST http://127.0.0.1:8787/train-step -H "Content-Type: application/json" -d "{\"specialty\":\"sql_learning\",\"complexity\":0.7}"
```

## Optimization Model

Each train step computes:

- `success` (task completion outcome)
- `speed` (throughput proxy under current load)
- `novelty` (exploration factor)

Reward update:

1. weighted sum of success/speed/novelty
2. gaussian adjustment of reward weights for exploration
3. bounded reward score and success-rate updates

Natural selection:

1. retire persistently weak agents when fleet size is high
2. periodically spawn evolved specialists from top performers

## SQL + Compression

Database path:

- `runtime/auto/hermes_super_orchestrator.db`

Tables:

1. `agent_metrics`
2. `orchestrator_events`

`orchestrator_events.payload_compressed` stores zlib-compressed JSON for compact retention.

## C++ and ML Integration Guidance

The baseline includes a `cpp_ml_kernels` specialty and can route C++ kernel work to a dedicated agent.
Use this with native kernels for critical hot paths and keep orchestration in Python/C#.

Recommended split:

1. C++: tight kernels, quantization, high-throughput transforms
2. Python: orchestration, experimentation, reward tuning
3. SQL: telemetry, retention, analytics, policy triggers

## Security Notes

1. Bind API to localhost by default.
2. Keep credentials out of source; use environment variables.
3. Add auth/token middleware before exposing beyond local machine.
