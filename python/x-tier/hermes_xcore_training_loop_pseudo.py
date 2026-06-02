"""
Hermes XCore training loop pseudo-runner.

This script is intentionally lightweight and serves as the execution entrypoint
for the integrated Python modules under python/x-tier/hermes_xcore.
"""

from __future__ import annotations

import numpy as np

from hermes_xcore.orchestrator import HermesOrchestrator, HermesTask
from hermes_xcore.routing_policy import ContextualBanditRouter


async def main() -> None:
    policy = ContextualBanditRouter(
        arms=["node_01_inference", "node_02_feature_eng", "node_03_training"],
        context_dim=128,
        alpha=1.0,
    )
    orchestrator = HermesOrchestrator(policy=policy)
    orchestrator.register_node("node_01", "http://127.0.0.1:8701", {"inference": True})
    orchestrator.register_node("node_02", "http://127.0.0.1:8702", {"feature_eng": True})
    orchestrator.register_node("node_03", "http://127.0.0.1:8703", {"training": True})

    task = HermesTask(task_type="inference", payload={"x": np.zeros(4).tolist()})
    await orchestrator.dispatch_task(task)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

