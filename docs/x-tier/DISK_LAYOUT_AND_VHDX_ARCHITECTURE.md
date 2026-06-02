# Disk Layout Correction and VHDX Architecture Design

This integrates the X-Tier plan into a concrete, reviewable architecture package with **no blind execution**.

## Source Blueprint

- `docs/bootstrap-and-hermes-xcore-training-loop-x-tier-build-implementation-plan.md`

## Corrected Storage Model

1. **C:** OS-only, core Windows/runtime binaries, minimal user profile growth.
2. **D:\DevDrive (ReFS, 64K cluster):** all development workloads, caches, containers, WSL2, VM disks, logs, databases.
3. **E: (optional):** very large model weights/checkpoints, attached via junction/symlink from `D:\DevDrive\ai-hub\models`.

## Target Layout

```text
D:\DevDrive\
  ai-hub\
    models\              # junction -> E:\models (optional)
    checkpoints\
    embeddings\
    venvs\
  hermes\
    nodes\
    orchestrator\
    configs\
    logs\
  data\
    raw\
    processed\
    features\
    exports\
  wsl2\
    distros\             # imported distro roots
    vhdx\                # explicit VHDX storage policy location
  hyperv\
    vms\                 # VM configs
    vhdx\                # VM disks
  docker\
    data-root\           # Docker engine data-root
  postgres\
  qdrant\
  caches\{pip,conda,npm,nuget,cargo,gradle,tmp,delivery}
  sandbox\
  logs\
```

## VHDX Placement Policy

- **WSL2**
  - Distros imported to `D:\DevDrive\wsl2\distros\<distro>`
  - Swap and utility VHDX under `D:\DevDrive\wsl2\vhdx\`
  - `.wslconfig` points swap file to `D:\DevDrive\wsl2\vhdx\swap.vhdx`
- **Hyper-V**
  - VM config path: `D:\DevDrive\hyperv\vms`
  - VM disk path: `D:\DevDrive\hyperv\vhdx`
  - No VM disks on C:
- **Docker**
  - `data-root` at `D:\DevDrive\docker\data-root`
  - WSL backend distros remain under relocated WSL2 policy above

## Safety and Integrity Rules

1. Snapshot before move.
2. Export/import WSL2 distros; never copy mounted VHDX directly.
3. Verify hashes for tar/backup artifacts.
4. Keep rollback artifacts in `D:\DevDrive\logs\` and `D:\DevDrive\backup\`.
5. Do not enable remote access (RDP/SSH) by default.

## Integrated Artifacts

- YAML architecture config: `config/x-tier/disk-layout.v1.yaml`
- Validation pseudo-script: `scripts/x-tier/01_validate_disk_layout.ps1`
- VHDX move planner: `scripts/x-tier/02_plan_vhdx_moves.ps1`
- Python XCore pseudo-loop: `python/x-tier/hermes_xcore_training_loop_pseudo.py`
- Python XCore integrated package: `python/x-tier/hermes_xcore/`
- SQL schema integration: `sql-learning/hermes_xcore_schema.sql`
