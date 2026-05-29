# Hermes Local Runtime

1. Start stack:
   - `pwsh ./runtime/hermes/start-local.ps1`
2. MCP Docker gateway (primary entry):
   - `http://localhost:${MCP_DOCKER_PORT:-8788}`
3. GUI:
   - `http://localhost:${HERMES_GUI_PORT:-8501}`

This runtime enables:
- QNAA/KNAA training simulations through `/simulate` and `/horizon-tests`
- External/online signal ingest through `/ingest-signal` for cross-model learning influence
- Fleet topology optimization through `/optimize-fleet`
- Learning source curation through `/curate-learning` (SQL vs internet vs LLM weighting)
- Long-horizon meta-learning blended across gaussian alignment + correction + all-data signals
- Unified non-blocking flow pulse through `/learning-pulse` (simulate + optimize + curate in one call)
- Duplicate-data optimization scan through `/dedupe-optimize` to reduce redundant learning input
- AIHub intelligence bonus endpoint `/aihub-bonus` for cross-LLM/Hermes uplift signal
- SQL telemetry in `runtime/auto/hermes_super_orchestrator.db`
- Continuous fleet auto-training via `hermes-trainer` service
- C# performance front-end (`hermes-gateway`) for smoother API routing and integration
- API security between gateway and backend via `HERMES_API_KEY`
- Single EXE entrypoint through C# gateway publish (`runtime/hermes/build-single-exe.ps1`)
  - Output: `runtime/hermes/dist/HermesUnified.exe`
- LLM API bridge for Hermes via `/llm-chat` (through gateway) uses a built-in temporary API by default (no env vars required)
- GUI text training ground for direct prompt/response workflow against the shared AIHub model
- Expanded text-first GUI control center with:
  - One-screen super-easy flow
  - Learning Space text panel (prompt -> Hermes response)
  - Fleet Data section (`/snapshot`) for live runtime context
  - Full auto cycle button (simulate + pulse + optimize + curate + dedupe)
  - Built-in API key field in GUI sidebar (uses `X-Hermes-Key`)
- Resource targeting via env vars:
  - `HERMES_GPU_TARGET_UTILIZATION` (default `0.75`)
  - `HERMES_CPU_TARGET_UTILIZATION` (default `0.80`)
- Unified AI/ML contract across AIHub + Hermes + security/optimization services:
  - `AIHUB_UNIFIED_ENABLED` (default `true`)
  - `AIHUB_SHARED_MODEL_ID` (default `aihub-unified-v1`)
  - `AIHUB_SHARED_ML_PROFILE` (default `global-learning`)
  - Inspect with `GET /unified-config` on gateway (`:${MCP_DOCKER_PORT:-8788}`)
- Auto trainer defaults are tuned near max throughput in Docker:
  - `HERMES_TRAIN_STEPS=2000`
  - `HERMES_TRAIN_INTERVAL_SECONDS=6`
  - `HERMES_FLEET_OPTIMIZE_EVERY=1`
  - `HERMES_FLEET_CANDIDATES=480`
  - `HERMES_MAX_MODE=true`
- Gateway API key is enabled by default in compose:
  - `HERMES_GATEWAY_KEY=local-hermes-ui-key`
  - GUI and trainer are pre-wired to use the same key
- Startup script auto-opens both GUI and unified-config pages:
  - `pwsh ./runtime/hermes/start-local.ps1`
