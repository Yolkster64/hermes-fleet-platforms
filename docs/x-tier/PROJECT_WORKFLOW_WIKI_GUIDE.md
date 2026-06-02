# X-Tier Project Workflow + TODO + Wiki Guide

This is the unified navigation path for integration, optimization, and ongoing delivery.

## Start here

1. Read architecture context:
   - `docs/x-tier/SUPER_DEEP_AIHUB_SYSTEM_GUIDE.md`
   - `docs/x-tier/AIHUB_UPGRADE_INTEGRATION.md`
2. Rebuild artifacts:
   - `scripts/x-tier/build_all_polyglot.ps1`
3. Start control surfaces:
   - `scripts/x-tier/Start-AIHubControl.ps1`
   - or `runtime/hermes/docker-compose.yml`

## Source-of-truth ownership

| Layer | Owner path | Responsibility |
|---|---|---|
| C++ kernel | `cpp/x-tier/` | CPU/memory/GPU/security optimization telemetry, watch/quarantine/governance plans |
| C# integration | `src/PolyglotXTier/` | Frontend projection contracts and integration host mapping |
| Python orchestration | `python/x-tier/` | Polyglot merge orchestration, AIHub API, ML/meta-learning adapters |
| GUI operator console | `runtime/hermes/apps/gui_control_center.py` | Unified control center: fleets, setup tracker, security, engines, hyper-v phase1 |
| Runtime profile/config | `config/x-tier/aihub-control.json` | Shared limits, runtime profile, Hyper-V phase1 settings |

## Workflow and backlog model

1. **Integration lane**
   - Keep schema compatibility between `super_integrated_report.json`, API payloads, and GUI widgets.
2. **Performance lane**
   - Tune runtime profile (`target_cpu_cores`, `target_memory_gb`, GPU mode) in config first, then compose.
3. **Security lane**
   - Extend C++ watch/governance structures, then propagate through C# map and Python API.
4. **Ops lane**
   - Keep setup tracker + autoboot plan synchronized with executable scripts and compose behavior.

## TODO tracking

- Operational todos are tracked in session SQL (`todos` + `todo_deps`) during active implementation runs.
- Commit-ready documentation TODOs should be added to:
  - `docs/x-tier/AIHUB_UPGRADE_INTEGRATION.md` (API/runtime impact)
  - `docs/README.md` (navigation impact)

## Wiki mapping (living structure)

- **Architecture wiki:** link to C++/C#/Python ownership table above.
- **Operations wiki:** link to setup tracker and Docker profile usage.
- **Security wiki:** link to security watch plan + alert channel payloads from `cpp_source_of_truth`.
- **ML wiki:** link to deep engine catalog/recommend endpoints and training telemetry flow.
