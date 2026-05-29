# Hermes Local Runtime

1. Start stack:
   - `pwsh ./runtime/hermes/start-local.ps1`
2. API:
   - `http://localhost:8787`
3. GUI:
   - `http://localhost:8501`

This runtime enables:
- QNAA/KNAA training simulations through `/simulate` and `/horizon-tests`
- SQL telemetry in `runtime/auto/hermes_super_orchestrator.db`
- Resource targeting via env vars:
  - `HERMES_GPU_TARGET_UTILIZATION` (default `0.75`)
  - `HERMES_CPU_TARGET_UTILIZATION` (default `0.80`)
