# Hermes Local Runtime

1. Start stack:
   - `pwsh ./runtime/hermes/start-local.ps1`
2. API:
   - `http://localhost:8787`
3. GUI:
   - `http://localhost:8501`

This runtime enables:
- QNAA/KNAA training simulations through `/simulate` and `/horizon-tests`
- External/online signal ingest through `/ingest-signal` for cross-model learning influence
- Fleet topology optimization through `/optimize-fleet`
- Learning source curation through `/curate-learning` (SQL vs internet vs LLM weighting)
- Long-horizon meta-learning blended across gaussian alignment + correction + all-data signals
- SQL telemetry in `runtime/auto/hermes_super_orchestrator.db`
- Continuous fleet auto-training via `hermes-trainer` service
- Resource targeting via env vars:
  - `HERMES_GPU_TARGET_UTILIZATION` (default `0.75`)
  - `HERMES_CPU_TARGET_UTILIZATION` (default `0.80`)
