from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class EngineSpec:
    name: str
    family: str
    tier: str
    backend: str
    cuda_ready: bool
    objective: str
    memory_class: str


def _engine_specs() -> list[EngineSpec]:
    return [
        EngineSpec("gaussian-regression", "regression", "core", "python", True, "continuous signal fitting", "medium"),
        EngineSpec("linear-regression", "regression", "core", "python", True, "baseline predictive fit", "low"),
        EngineSpec("ridge-regression", "regression", "core", "python", True, "regularized trend learning", "low"),
        EngineSpec("lasso-regression", "regression", "core", "python", True, "sparse feature selection", "low"),
        EngineSpec("elasticnet-regression", "regression", "core", "python", True, "hybrid sparse regularization", "low"),
        EngineSpec("extreme-calculus-solver", "symbolic", "advanced", "csharp", False, "differential optimization", "medium"),
        EngineSpec("geometry-topology-optimizer", "geometry", "advanced", "csharp", False, "spatial route shaping", "medium"),
        EngineSpec("gaussian-blur-anomaly", "vision", "support", "cpp", True, "noise suppression + anomaly prep", "low"),
        EngineSpec("knn-clustering", "clustering", "core", "python", True, "nearest-neighbor grouping", "medium"),
        EngineSpec("knaa-routing", "mesh", "advanced", "python", True, "k-neighbor adaptive allocation", "high"),
        EngineSpec("gnaa-graph-attention", "graph", "advanced", "python", True, "graph neural attention policy", "high"),
        EngineSpec("rnaa-recurrent-anomaly", "sequence", "advanced", "python", True, "temporal anomaly scoring", "high"),
        EngineSpec("rnn-sequence-predictor", "sequence", "core", "python", True, "sequence forecasting", "high"),
        EngineSpec("transformer-router", "routing", "advanced", "python", True, "LLM route selection", "high"),
        EngineSpec("contextual-bandit-router", "routing", "core", "python", True, "online model selection", "low"),
        EngineSpec("autoencoder-shape-compressor", "compression", "core", "python", True, "latent compression", "medium"),
        EngineSpec("variational-autoencoder", "compression", "advanced", "python", True, "distributional latent spaces", "high"),
        EngineSpec("pca-fast-compressor", "compression", "support", "cpp", False, "low-memory dimension reduction", "low"),
        EngineSpec("drift-detector", "governance", "core", "python", False, "data drift guardrails", "low"),
        EngineSpec("chaos-engine", "exploration", "experimental", "python", True, "controlled stochastic exploration", "medium"),
        EngineSpec("natural-selection-engine", "evolutionary", "advanced", "python", True, "candidate survival optimization", "medium"),
        EngineSpec("genetic-policy-search", "evolutionary", "advanced", "python", True, "policy mutation and crossover", "medium"),
        EngineSpec("bayesian-optimizer", "optimization", "core", "python", True, "hyperparameter optimization", "medium"),
        EngineSpec("simulated-annealing", "optimization", "support", "cpp", False, "global objective search", "low"),
        EngineSpec("multi-armed-bandit-swarm", "routing", "advanced", "python", True, "swarm routing policy", "medium"),
        EngineSpec("mesh-consensus-engine", "mesh", "advanced", "csharp", False, "fleet consensus propagation", "medium"),
        EngineSpec("sql-pattern-miner", "analytics", "core", "python", False, "training signal extraction", "low"),
        EngineSpec("vector-retrieval-ranker", "retrieval", "core", "python", True, "semantic ranking", "medium"),
        EngineSpec("security-anomaly-core", "security", "core", "cpp", False, "runtime threat scoring", "low"),
        EngineSpec("memory-pressure-optimizer", "optimization", "support", "cpp", False, "memory compaction and pressure control", "low"),
    ]


def build_engine_catalog(cuda_enabled: bool = True) -> dict[str, Any]:
    specs = _engine_specs()
    engines = [asdict(s) for s in specs if cuda_enabled or not s.cuda_ready]
    by_family: dict[str, int] = {}
    by_backend: dict[str, int] = {}
    for e in engines:
        by_family[e["family"]] = by_family.get(e["family"], 0) + 1
        by_backend[e["backend"]] = by_backend.get(e["backend"], 0) + 1
    return {
        "total_engines": len(engines),
        "cuda_enabled": cuda_enabled,
        "families": by_family,
        "backends": by_backend,
        "major_parallelization_types": [
            "task-parallel",
            "data-parallel",
            "pipeline-parallel",
            "tensor-parallel",
            "model-parallel",
            "fleet-swarm-parallel",
            "multi-llm-routing-parallel",
            "subagent-specialist-parallel",
            "hybrid-mesh-parallel",
            "async-event-parallel",
        ],
        "specialization_tools": [
            "agent-role-specializer",
            "xcore-routing-specializer",
            "sql-pattern-specializer",
            "security-guard-specializer",
            "compression-speed-specializer",
            "fleet-chaos-balance-specializer",
        ],
        "hybridization_strategies": [
            "chaos+bandit",
            "natural-selection+bayesian",
            "graph-attention+mesh-consensus",
            "autoencoder+vector-retrieval",
            "security-anomaly+drift-detector",
        ],
        "github_learning_sources": [
            "https://github.com/scikit-learn/scikit-learn",
            "https://github.com/pytorch/pytorch",
            "https://github.com/dmlc/xgboost",
            "https://github.com/pyg-team/pytorch_geometric",
            "https://github.com/Lightning-AI/pytorch-lightning",
            "https://github.com/ray-project/ray",
            "https://github.com/facebookresearch/faiss",
            "https://github.com/qdrant/qdrant",
        ],
        "engines": engines,
    }


def recommend_engine_mix(
    *,
    cuda_enabled: bool,
    security_profile: str,
    optimization_pressure: float,
    fleet_size: int,
) -> dict[str, Any]:
    catalog = build_engine_catalog(cuda_enabled=cuda_enabled)
    engines: list[dict[str, Any]] = catalog["engines"]

    selected: list[dict[str, Any]] = []
    required_families = ["routing", "security", "optimization", "compression", "analytics", "retrieval"]
    for family in required_families:
        for e in engines:
            if e["family"] == family:
                selected.append(e)
                break

    if optimization_pressure >= 0.7:
        selected.extend([e for e in engines if e["name"] in {"chaos-engine", "natural-selection-engine", "bayesian-optimizer"}])
    if security_profile == "paranoid":
        selected.extend([e for e in engines if e["family"] in {"security", "governance"}])
    if fleet_size >= 200:
        selected.extend([e for e in engines if e["name"] in {"mesh-consensus-engine", "multi-armed-bandit-swarm", "gnaa-graph-attention"}])

    unique = {e["name"]: e for e in selected}
    memory_score = round(100 - (len([e for e in unique.values() if e["memory_class"] == "high"]) * 1.8), 2)
    return {
        "selected_count": len(unique),
        "selected_engines": list(unique.values()),
        "expected_memory_efficiency_score": max(40.0, memory_score),
        "major_parallelization_types": catalog["major_parallelization_types"],
        "specialization_tools": catalog["specialization_tools"],
        "hybridization_strategies": catalog["hybridization_strategies"],
        "notes": [
            "C++ engines focus on low-memory runtime control/security.",
            "Python engines provide meta-learning and adaptive policy layers.",
            "C# engines coordinate mesh consensus and enterprise integration policies.",
        ],
    }
