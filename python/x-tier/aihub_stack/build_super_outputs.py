from __future__ import annotations

import json
from pathlib import Path

from ml_registry import MLRegistry
from security_optimizer import build_plan
from vm_orchestrator import VMOrchestrator


def main() -> int:
    out = Path("artifacts/aihub")
    out.mkdir(parents=True, exist_ok=True)

    reg = MLRegistry(str(out / "ml-registry.json"))
    reg.seed_default()
    reg.save()

    plan = build_plan("balanced")
    (out / "security-optimization-plan.json").write_text(json.dumps(plan.__dict__, indent=2), encoding="utf-8")

    topo = VMOrchestrator().build_default_topology()
    (out / "vm-topology.json").write_text(
        json.dumps([t.__dict__ for t in topo], indent=2),
        encoding="utf-8",
    )
    print("Wrote AIHub registry, security plan, and VM topology")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

