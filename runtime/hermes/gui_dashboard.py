import json
import os
import time
from typing import Any, Dict, List, Tuple

import streamlit as st
from gui_api_client import current_api_base, log_text, run_logged_post_action, safe_get, safe_post
from gui_evolution_panels import render_evolution_centerpiece, render_learning_graphs
from gui_fleet_showcase import render_fleet_showcase_panels
from gui_next_level_panels import render_next_level_control_center
from gui_insights import fleet_score_history, latest_learned_profile, render_xp_bar
from gui_sql_panels import render_sql_intelligence_panels
from gui_watch_panels import render_aihub_watch_panels
from gui_volume_tools import (
    initialize_volume_layout,
    read_sql_training_intelligence,
    read_volume_file,
    resolve_volume_root,
    scan_volume_files,
    volume_health_summary,
)
try:
    from core.hermes_variable_registry import VARIABLE_CATALOG, default_user_entry_profile
except Exception:  # pragma: no cover
    VARIABLE_CATALOG = {}

    def default_user_entry_profile() -> Dict[str, Any]:
        return {
            "goal_profile": "balanced",
            "success_priority": 0.72,
            "wrongness_tolerance": 0.22,
            "group_preference": 0.58,
            "solo_preference": 0.42,
            "dynamic_response": 0.62,
            "speed_priority": 0.65,
            "energy_saver": 0.55,
        }

DEFAULT_API_KEY = os.getenv("HERMES_GUI_API_KEY", "local-hermes-ui-key")
LOW_BANDWIDTH_MODE = os.getenv("HERMES_LOW_BANDWIDTH_MODE", "true").lower() in ("1", "true", "yes", "on")
OFFLINE_ONLY_MODE = os.getenv("HERMES_OFFLINE_ONLY", "false").lower() in ("1", "true", "yes", "on")
USER_ROUTED_INTERNET = os.getenv("HERMES_USER_ROUTED_INTERNET", "true").lower() in ("1", "true", "yes", "on")
AGENT_SKILLS_25 = [
    "coding",
    "error_checking",
    "testing",
    "gui_design",
    "security_hardening",
    "performance_tuning",
    "data_engineering",
    "ml_modeling",
    "neural_optimization",
    "gaussian_learning",
    "prompt_engineering",
    "llm_routing",
    "communication_mesh",
    "fleet_orchestration",
    "quantization",
    "parallelization",
    "multipolar_reasoning",
    "memory_management",
    "refactoring",
    "observability",
    "cost_optimization",
    "deployment",
    "api_integration",
    "documentation",
    "reliability_engineering",
]
SIZE_MODE_DETAILS = {
    "small-fast": "Mini Hermes: quick cycles, low cost, rapid scouting.",
    "medium-balanced": "Balanced Hermes: steady quality/speed for daily training.",
    "large-deep": "Full Hermes: deeper reasoning and long-horizon adaptation.",
}
HERMES_TYPE_PRESETS: Dict[str, Dict[str, Any]] = {
    "hybrid-core": {
        "title": "Hybrid",
        "group": "Custom",
        "personality": "Adaptive orchestrator that balances speed, safety, and exploration.",
        "description": "Best all-around profile for mixed workloads and stable continuous upgrades.",
        "swarm_strategy": "hybrid",
        "micro_agents": 188,
        "gaussian_pressure": 0.83,
        "high_level_learning": 0.73,
        "techniques": ["KNAA/QNAA reasoning", "Cross-agent communication mesh", "Natural pressure adaptation"],
        "specialty_tag": "hybrid",
    },
    "mesh-swarm": {
        "title": "Mesh",
        "group": "Custom",
        "personality": "Highly collaborative specialist that links sub-agents into a dense coordination net.",
        "description": "Strong for big fleet/hub synchronization and multi-step joint reasoning.",
        "swarm_strategy": "mesh",
        "micro_agents": 210,
        "gaussian_pressure": 0.85,
        "high_level_learning": 0.77,
        "techniques": ["Cross-agent communication mesh", "GNAA adaptive memory", "Multi-parallel swarm"],
        "specialty_tag": "mesh",
    },
    "normal-steady": {
        "title": "Normal",
        "group": "Custom",
        "personality": "Predictable baseline profile focused on operational stability and consistency.",
        "description": "Good default when you want lower variance and cleaner repeatability.",
        "swarm_strategy": "specialist-mix",
        "micro_agents": 164,
        "gaussian_pressure": 0.78,
        "high_level_learning": 0.68,
        "techniques": ["Natural pressure adaptation", "Quantized compression", "KNAA/QNAA reasoning"],
        "specialty_tag": "normal",
    },
    "deep-thinker": {
        "title": "Deep Thinker",
        "group": "Custom",
        "personality": "Long-horizon planner with stronger analysis and pattern depth.",
        "description": "Best for complex decisions, SQL pattern mining, and higher-order strategy.",
        "swarm_strategy": "multipolar",
        "micro_agents": 228,
        "gaussian_pressure": 0.90,
        "high_level_learning": 0.86,
        "techniques": ["Gaussian 3D evidence", "Multipolar ensemble", "GNAA adaptive memory"],
        "specialty_tag": "deep-thinker",
    },
    "ultimate-aihub-fusion": {
        "title": "Ultimate AIHub Fusion",
        "group": "Official Hermes",
        "personality": "Top-tier AI integration profile for blended reasoning, SQL intelligence, and orchestration depth.",
        "description": "Best all-around AI integration type when you want strong coding, training, SQL signals, and fleet execution in one profile.",
        "swarm_strategy": "multipolar",
        "micro_agents": 236,
        "gaussian_pressure": 0.92,
        "high_level_learning": 0.91,
        "techniques": ["KNAA/QNAA reasoning", "GNAA adaptive memory", "Cross-agent communication mesh", "Multi-armed Bayesian planning"],
        "specialty_tag": "ultimate-aihub-fusion",
    },
    "ultimate-ml-x5": {
        "title": "Ultimate ML X5",
        "group": "Official Hermes",
        "personality": "Maximum-intensity machine learning profile for full brain integration and heavy training throughput.",
        "description": "X5 profile for the most advanced training setup: deep reasoning, high memory retention, and multi-signal optimization.",
        "swarm_strategy": "multipolar",
        "micro_agents": 252,
        "gaussian_pressure": 0.96,
        "high_level_learning": 0.98,
        "techniques": ["KNAA/QNAA reasoning", "GNAA adaptive memory", "Gaussian 3D evidence", "Cross-agent communication mesh", "Multi-armed Bayesian planning"],
        "specialty_tag": "ultimate-ml-x5",
    },
    "idealist-strategist": {
        "title": "Idealist Strategist",
        "group": "Official Hermes",
        "personality": "Principled high-standards profile balancing truth, safety, and long-horizon improvement.",
        "description": "Best for ideal outcomes: strong quality control, consistent learning ethics, and resilient optimization under pressure.",
        "swarm_strategy": "specialist-mix",
        "micro_agents": 208,
        "gaussian_pressure": 0.91,
        "high_level_learning": 0.94,
        "techniques": ["Chaos engine trials", "Multi-parallel swarm", "GNAA adaptive memory", "KNAA/QNAA reasoning"],
        "specialty_tag": "idealist-strategist",
    },
    "official-quick-thinker": {
        "title": "Quick Thinker",
        "group": "Official",
        "personality": "Fast-response profile tuned for speed and short-cycle actions.",
        "description": "Great for rapid iterations, quick diagnostics, and low-latency deployment loops.",
        "swarm_strategy": "swarm",
        "micro_agents": 200,
        "gaussian_pressure": 0.79,
        "high_level_learning": 0.62,
        "techniques": ["C++ neural kernel boost", "Multi-parallel swarm", "Quantized compression"],
        "specialty_tag": "official-quick",
    },
    "official-deep-thinker": {
        "title": "Official Deep Thinker",
        "group": "Official",
        "personality": "Reasoning-heavy profile optimized for depth, structure, and memory quality.",
        "description": "Use for hard strategy problems and long training arcs.",
        "swarm_strategy": "multipolar",
        "micro_agents": 236,
        "gaussian_pressure": 0.92,
        "high_level_learning": 0.88,
        "techniques": ["Gaussian 3D evidence", "GNAA adaptive memory", "Multipolar ensemble"],
        "specialty_tag": "official-deep",
    },
    "official-balanced-thinker": {
        "title": "Balanced Thinker",
        "group": "Official",
        "personality": "Even profile balancing throughput, stability, and interpretability.",
        "description": "Good for broad production use with less tuning overhead.",
        "swarm_strategy": "hybrid",
        "micro_agents": 192,
        "gaussian_pressure": 0.84,
        "high_level_learning": 0.74,
        "techniques": ["KNAA/QNAA reasoning", "Cross-agent communication mesh", "Natural pressure adaptation"],
        "specialty_tag": "official-balanced",
    },
    "official-creative-thinker": {
        "title": "Creative Thinker",
        "group": "Official",
        "personality": "Exploration-focused profile that favors diversity and novel combinations.",
        "description": "Best for ideation, alternate plans, and design-heavy AIHub work.",
        "swarm_strategy": "mesh",
        "micro_agents": 214,
        "gaussian_pressure": 0.87,
        "high_level_learning": 0.82,
        "techniques": ["Multipolar ensemble", "Cross-agent communication mesh", "GNAA adaptive memory"],
        "specialty_tag": "official-creative",
    },
}
ALGORITHMIC_HERMES_TYPE_PRESETS: Dict[str, Dict[str, Any]] = {
    "legacy-hybrid": {
        "title": "Hybrid Legacy",
        "group": "Legacy Strategy",
        "personality": "Balanced coordinator that keeps performance and stability aligned.",
        "description": "Legacy hybrid profile from the original strategy set.",
        "swarm_strategy": "hybrid",
        "micro_agents": 196,
        "gaussian_pressure": 0.84,
        "high_level_learning": 0.76,
        "techniques": ["KNAA/QNAA reasoning", "Cross-agent communication mesh", "Natural pressure adaptation"],
        "specialty_tag": "legacy-hybrid",
    },
    "legacy-mesh": {
        "title": "Mesh Legacy",
        "group": "Legacy Strategy",
        "personality": "Collaborative depth mode with stronger multi-agent linkage.",
        "description": "Legacy mesh profile focused on coordinated sub-agent reasoning.",
        "swarm_strategy": "mesh",
        "micro_agents": 214,
        "gaussian_pressure": 0.87,
        "high_level_learning": 0.80,
        "techniques": ["GNAA adaptive memory", "Cross-agent communication mesh", "Natural pressure adaptation"],
        "specialty_tag": "legacy-mesh",
    },
    "legacy-parallel-swarm": {
        "title": "Parallel Swarm",
        "group": "Legacy Strategy",
        "personality": "Parallel-heavy profile for rapid multi-lane execution.",
        "description": "The parallel-ish legacy mode for high-throughput operations.",
        "swarm_strategy": "swarm",
        "micro_agents": 236,
        "gaussian_pressure": 0.90,
        "high_level_learning": 0.72,
        "techniques": ["Multi-parallel swarm", "C++ neural kernel boost", "Quantized compression"],
        "specialty_tag": "legacy-parallel",
    },
    "legacy-multipolar": {
        "title": "Multipolar",
        "group": "Legacy Strategy",
        "personality": "Multi-perspective planner with rich strategy diversity.",
        "description": "Legacy multipolar mode for complex strategy comparisons.",
        "swarm_strategy": "multipolar",
        "micro_agents": 244,
        "gaussian_pressure": 0.91,
        "high_level_learning": 0.85,
        "techniques": ["Multipolar ensemble", "Multi-parallel swarm", "Cross-agent communication mesh"],
        "specialty_tag": "legacy-multipolar",
    },
    "legacy-specialist-mix": {
        "title": "Specialist Mix",
        "group": "Legacy Strategy",
        "personality": "Niche expert blend where each sub-agent handles a focused domain.",
        "description": "Legacy specialist profile for precision workflows and role partitioning.",
        "swarm_strategy": "specialist-mix",
        "micro_agents": 206,
        "gaussian_pressure": 0.82,
        "high_level_learning": 0.79,
        "techniques": ["Sub-agent niche shaping", "GNAA adaptive memory", "KNAA/QNAA reasoning"],
        "specialty_tag": "legacy-specialist",
    },
    "legacy-linear-regression": {
        "title": "Linear Regression",
        "group": "Legacy Strategy",
        "personality": "Signal trend fitter tuned for steady directional optimization.",
        "description": "Uses regression-like trend pressure for smooth iterative improvements.",
        "swarm_strategy": "normal",
        "micro_agents": 172,
        "gaussian_pressure": 0.76,
        "high_level_learning": 0.70,
        "techniques": ["Gaussian 3D evidence", "Natural pressure adaptation", "Quantized compression"],
        "specialty_tag": "legacy-linear-regression",
    },
    "legacy-bayesian-optimizer": {
        "title": "Bayesian Optimizer",
        "group": "Legacy Strategy",
        "personality": "Confidence-weighted explorer that balances exploration and exploitation.",
        "description": "Chooses upgrades via probabilistic confidence to improve sample efficiency.",
        "swarm_strategy": "hybrid",
        "micro_agents": 208,
        "gaussian_pressure": 0.88,
        "high_level_learning": 0.82,
        "techniques": ["Gaussian 3D evidence", "Multipolar ensemble", "GNAA adaptive memory"],
        "specialty_tag": "legacy-bayesian",
    },
    "legacy-gradient-boost": {
        "title": "Gradient Boost",
        "group": "Legacy Strategy",
        "personality": "Incremental improver stacking many small gains into stronger performance.",
        "description": "Strong for repeated optimization cycles where each pass refines weak spots.",
        "swarm_strategy": "specialist-mix",
        "micro_agents": 216,
        "gaussian_pressure": 0.86,
        "high_level_learning": 0.81,
        "techniques": ["Sub-agent niche shaping", "KNAA/QNAA reasoning", "Cross-agent communication mesh"],
        "specialty_tag": "legacy-gradient-boost",
    },
    "legacy-reinforcement-policy": {
        "title": "Reinforcement Policy",
        "group": "Legacy Strategy",
        "personality": "Reward-driven learner focused on action quality under changing conditions.",
        "description": "Great for adaptive policy tuning and long-running optimization campaigns.",
        "swarm_strategy": "swarm",
        "micro_agents": 228,
        "gaussian_pressure": 0.89,
        "high_level_learning": 0.84,
        "techniques": ["Chaos engine trials", "GNAA adaptive memory", "Multi-parallel swarm"],
        "specialty_tag": "legacy-reinforcement",
    },
    "legacy-gaussian-blur": {
        "title": "Gaussian Blur",
        "group": "Legacy Strategy",
        "personality": "Smoothing-heavy optimizer for stable convergence under noisy training signals.",
        "description": "Applies gaussian smoothing pressure to reduce spikes and improve consistent policy updates.",
        "swarm_strategy": "normal",
        "micro_agents": 184,
        "gaussian_pressure": 0.93,
        "high_level_learning": 0.83,
        "techniques": ["Gaussian 3D evidence", "GNAA adaptive memory", "Natural pressure adaptation"],
        "specialty_tag": "legacy-gaussian-blur",
    },
}
CENTER_ACTIVE_TYPE_KEYS: List[str] = [
    "hybrid-core",
    "mesh-swarm",
    "normal-steady",
    "deep-thinker",
    "legacy-parallel-swarm",
    "legacy-linear-regression",
    "legacy-gaussian-blur",
]
OPERATION_MODES: Dict[str, Dict[str, Any]] = {
    "Programming + C++": {
        "description": "Best for C++ heavy coding, compile loops, and deep refactor quality.",
        "recommended_type": "deep-thinker",
        "swarm": "multipolar",
        "agents_delta": 12,
        "gaussian_delta": 0.03,
        "learning_delta": 0.08,
    },
    "GUI + Visual": {
        "description": "Best for Streamlit/UI polish, smooth visuals, and fast visual iteration cycles.",
        "recommended_type": "mesh-swarm",
        "swarm": "mesh",
        "agents_delta": 8,
        "gaussian_delta": 0.01,
        "learning_delta": 0.05,
    },
    "Intensive Throughput": {
        "description": "Best for maximum throughput, heavy orchestration, and large parallel workloads.",
        "recommended_type": "legacy-parallel-swarm",
        "swarm": "swarm",
        "agents_delta": 24,
        "gaussian_delta": -0.02,
        "learning_delta": 0.00,
    },
    "Learning Depth": {
        "description": "Best for long-run learning, retention quality, and adaptive memory growth.",
        "recommended_type": "legacy-gaussian-blur",
        "swarm": "normal",
        "agents_delta": 0,
        "gaussian_delta": 0.05,
        "learning_delta": 0.10,
    },
}
SMART_TOOL_CATALOG: Dict[str, Dict[str, str]] = {
    "code-analysis": {"focus": "C++ Coding", "desc": "Static + semantic analysis for correctness and refactor safety.", "llm_bonus": "Boosts reasoning prompts with code-structure context.", "split": "Splits by module and dependency graph."},
    "sql-pattern-mining": {"focus": "Efficiency", "desc": "Extracts SQL patterns and storage signals for training optimization.", "llm_bonus": "Feeds query shape and trend context to LLM routing.", "split": "Splits by table/metric families."},
    "fleet-deploy-ops": {"focus": "Deploy/Return", "desc": "Coordinates deploy and bring-back cycles with safe orchestration.", "llm_bonus": "Adds orchestration state for command planning.", "split": "Splits by unit cohorts and batch size."},
    "chaos-engine-lab": {"focus": "Resilience", "desc": "Runs controlled chaos trials to harden strategy under variance.", "llm_bonus": "Supplies adversarial edge cases for robustness tuning.", "split": "Splits by chaos scenario class."},
    "multi-parallel-orchestrator": {"focus": "Throughput", "desc": "Expands multi-parallel execution with adaptive lane balancing.", "llm_bonus": "Enriches token budget by parallel result synthesis.", "split": "Splits by parallel lanes + merge policy."},
    "idealist-policy-guard": {"focus": "Security AI", "desc": "Applies policy guardrails and high-integrity constraints.", "llm_bonus": "Improves safety-aware model routing.", "split": "Splits by policy tier and risk class."},
    "aihub-routing-optimizer": {"focus": "LLM Bonus", "desc": "Optimizes model selection for speed/cost/quality balance.", "llm_bonus": "Directly increases routing bonus quality.", "split": "Splits by provider and task class."},
    "brain-fusion-monitor": {"focus": "Brain Integration", "desc": "Monitors learning/decision/conscious fusion quality.", "llm_bonus": "Improves prompt grounding with brain metrics.", "split": "Splits by brain channel."},
    "cpp-compile-advisor": {"focus": "C++ Coding", "desc": "Targets compile-time bottlenecks and build stability.", "llm_bonus": "Adds compile diagnostics to coding prompts.", "split": "Splits by target and compiler profile."},
    "ui-polish-engine": {"focus": "UI/UX", "desc": "Improves clarity, spacing, and interaction flow.", "llm_bonus": "Provides UX heuristics for generation quality.", "split": "Splits by panel and interaction type."},
    "security-threat-modeler": {"focus": "Security AI", "desc": "Models threat paths and hardens decision policies.", "llm_bonus": "Adds threat context for safer completions.", "split": "Splits by attack surface."},
    "efficiency-tuner": {"focus": "Efficiency", "desc": "Balances latency, throughput, and stability for sustained load.", "llm_bonus": "Improves high-efficiency response plans.", "split": "Splits by resource pool."},
    "llm-bonus-bridge": {"focus": "LLM Bonus", "desc": "Bridges internal metrics to external LLM bonus shaping.", "llm_bonus": "Direct bonus amplification path.", "split": "Splits by bonus channel."},
    "split-merge-planner": {"focus": "Splitting", "desc": "Plans split/merge trees for complex tasks and recovery.", "llm_bonus": "Improves decomposition prompts and re-aggregation.", "split": "Splits by objective tree depth."},
    "toolchain-skill-mapper": {"focus": "Tools", "desc": "Maps smart tools to workload types automatically.", "llm_bonus": "Raises tool-aware plan quality.", "split": "Splits by workload profile."},
    "adaptive-memory-weaver": {"focus": "Learning", "desc": "Weaves memory traces for stronger long-horizon retention.", "llm_bonus": "Adds richer historical context to prompts.", "split": "Splits by memory epoch."},
    "truth-shield-guardian": {"focus": "Security AI", "desc": "Protects truth/safety channels under adversarial pressure.", "llm_bonus": "Improves trust-calibrated model choice.", "split": "Splits by trust zone."},
    "network-signal-fuser": {"focus": "Integration", "desc": "Fuses SQL/internet/LLM signals for unified guidance.", "llm_bonus": "Strengthens multi-signal context blending.", "split": "Splits by signal source."},
    "agent-skill-amplifier": {"focus": "Fleets", "desc": "Amplifies 3-skill role packs per Hermes unit.", "llm_bonus": "Improves role-specialized generation quality.", "split": "Splits by role class."},
    "x6-learning-extender": {"focus": "X6 Learning", "desc": "Extends X5 training with deeper X6 learning pressure.", "llm_bonus": "Increases long-form reasoning gain.", "split": "Splits by stage (X1..X6)."},
}
MODEL_OPTIONS = [
    "hermes-fleet-latest",
    "hermes-fleet-mini",
    "hermes-fleet-reasoning-max",
    "bonusllm-ultra",
]
def pull_metric(payload: Any, names: Tuple[str, ...], default: float = 0.0) -> float:
    if isinstance(payload, dict):
        for name in names:
            if name in payload and isinstance(payload[name], (int, float)):
                return float(payload[name])
        for value in payload.values():
            found = pull_metric(value, names, default=default)
            if found != default:
                return found
    if isinstance(payload, list):
        for value in payload:
            found = pull_metric(value, names, default=default)
            if found != default:
                return found
    return default


def build_technique_profile(
    techniques: List[str], swarm_strategy: str, micro_agents: int, gaussian_pressure: float, permanent_intelligence: bool, high_level_learning: float
) -> Dict[str, Any]:
    has_knaa = "KNAA/QNAA reasoning" in techniques
    has_gnaa = "GNAA adaptive memory" in techniques
    has_chaos = "Chaos engine trials" in techniques
    has_quant = "Quantized compression" in techniques
    has_parallel = "Multi-parallel swarm" in techniques
    has_multipolar = "Multipolar ensemble" in techniques
    has_natural = "Natural pressure adaptation" in techniques
    learning_bias = max(0.0, min(1.0, high_level_learning))
    return {
        "techniques": techniques,
        "swarm_strategy": swarm_strategy,
        "micro_agents": micro_agents,
        "gaussian_pressure": gaussian_pressure,
        "permanent_intelligence": permanent_intelligence,
        "high_level_learning": learning_bias,
        "sql_signal": min(0.98, 0.80 + (0.06 if has_knaa else 0.0) + (0.04 if has_gnaa else 0.0) + (0.04 if has_natural else 0.0) + (learning_bias * 0.04)),
        "internet_signal": (
            0.0
            if OFFLINE_ONLY_MODE
            else (
                min(0.14, max(0.06, 0.10 + (0.02 if has_parallel else 0.0) + (learning_bias * 0.02)))
                if USER_ROUTED_INTERNET
                else min(0.98, (0.22 if LOW_BANDWIDTH_MODE else 0.78) + (0.06 if has_parallel else 0.0) + (0.04 if has_multipolar else 0.0) + (learning_bias * (0.03 if LOW_BANDWIDTH_MODE else 0.06)))
            )
        ),
        "llm_signal": min(0.99, 0.82 + (0.07 if has_knaa else 0.0) + (0.04 if has_gnaa else 0.0) + (0.05 if has_quant else 0.0) + (learning_bias * 0.05)),
        "stability_bias": min(0.96, 0.72 + (0.10 if permanent_intelligence else 0.0) + (0.04 if has_chaos else 0.0) + (0.06 if has_quant else 0.0) + ((1.0 - learning_bias) * 0.08)),
    }


def _effective_internet_signal(raw_signal: float, low_cap: bool = False) -> float:
    if OFFLINE_ONLY_MODE:
        return 0.0
    if USER_ROUTED_INTERNET:
        cap = 0.14 if low_cap else 0.22
        return min(cap, raw_signal)
    if LOW_BANDWIDTH_MODE:
        cap = 0.30 if low_cap else 0.60
        return min(cap, raw_signal)
    return raw_signal


def _use_algorithmic_presets() -> bool:
    return bool(st.session_state.get("ctl_enable_algorithmic_types", False))


def _active_hermes_presets() -> Dict[str, Dict[str, Any]]:
    if _use_algorithmic_presets():
        return {**HERMES_TYPE_PRESETS, **ALGORITHMIC_HERMES_TYPE_PRESETS}
    return dict(HERMES_TYPE_PRESETS)


def _all_hermes_presets() -> Dict[str, Dict[str, Any]]:
    return {**HERMES_TYPE_PRESETS, **ALGORITHMIC_HERMES_TYPE_PRESETS}


def _species_profile(species: str) -> Dict[str, Any]:
    lookup = {
        "Hybrid": {
            "agent_mult": 1.00,
            "gaussian_bias": 0.00,
            "learning_bias": 0.02,
            "ops": "Balanced operations mode: stable routing, medium risk, high consistency.",
        },
        "Normal": {
            "agent_mult": 0.92,
            "gaussian_bias": -0.04,
            "learning_bias": -0.02,
            "ops": "Stability mode: lower variance, cleaner repeatability, controlled exploration.",
        },
        "Mesh": {
            "agent_mult": 1.10,
            "gaussian_bias": 0.03,
            "learning_bias": 0.05,
            "ops": "Collaboration mode: stronger cross-agent linkage and deeper coordination.",
        },
    }
    return lookup.get(species, lookup["Hybrid"])


def _optimized_settings(preset: Dict[str, Any], species: str) -> Dict[str, Any]:
    base_agents = int(preset.get("micro_agents", 160))
    base_gaussian = float(preset.get("gaussian_pressure", 0.80))
    base_learning = float(preset.get("high_level_learning", 0.70))
    species_cfg = _species_profile(species)
    agents = int(max(32, min(256, round(base_agents * float(species_cfg.get("agent_mult", 1.0))))))
    gaussian = max(0.40, min(1.00, base_gaussian + float(species_cfg.get("gaussian_bias", 0.0))))
    learning = max(0.0, min(1.0, base_learning + float(species_cfg.get("learning_bias", 0.0))))
    operation = str(species_cfg.get("ops", "Balanced operations mode."))
    return {"micro_agents": agents, "gaussian_pressure": gaussian, "high_level_learning": learning, "operations": operation}


def _selected_hermes_type_key() -> str:
    key = str(st.session_state.get("ctl_hermes_type", "hybrid-core"))
    legacy_map = {
        "vanguard-guardian": "hybrid-core",
        "sql-oracle": "deep-thinker",
        "cpp-striker": "mesh-swarm",
        "aibox-architect": "normal-steady",
    }
    mapped = legacy_map.get(key, key)
    presets = _active_hermes_presets()
    return mapped if mapped in presets else "hybrid-core"


def _selected_model_override() -> str:
    return str(st.session_state.get("ctl_model_override", "")).strip()


def _specialty_base() -> str:
    type_key = _selected_hermes_type_key()
    tag = str(_active_hermes_presets().get(type_key, {}).get("specialty_tag", type_key))
    return f"fleet:{tag}"


def _guided_auto_bond_status(
    *,
    unified_err: str,
    watch_err: str,
    gateway_watch_err: str,
    auto_bootstrap: Dict[str, Any],
    sql_intel: Dict[str, Any],
    volume_root: str,
) -> Dict[str, Any]:
    sql_health = sql_intel.get("sql_health", {}) if isinstance(sql_intel, dict) else {}
    if not isinstance(sql_health, dict):
        sql_health = {}
    db_mb = float(sql_health.get("db_mb", 0.0))
    wal_mb = float(sql_health.get("wal_mb", 0.0))
    volume_ok = bool(os.path.isdir(volume_root))
    signals = {
        "api_link": 1.0 if not unified_err else 0.0,
        "watch_link": 1.0 if not watch_err else 0.0,
        "gateway_link": 1.0 if not gateway_watch_err else 0.0,
        "volume_link": 1.0 if volume_ok else 0.0,
        "auto_setup": 1.0 if bool(auto_bootstrap.get("ok", False)) else 0.0,
        "sql_link": max(0.0, min(1.0, 1.0 - min(1.0, (db_mb / 1536.0) + (wal_mb / 384.0)))),
    }
    bond_score = max(0.0, min(1.0, (signals["api_link"] * 0.23) + (signals["watch_link"] * 0.17) + (signals["gateway_link"] * 0.15) + (signals["volume_link"] * 0.17) + (signals["auto_setup"] * 0.13) + (signals["sql_link"] * 0.15)))
    return {"signals": signals, "bond_score": bond_score, "db_mb": db_mb, "wal_mb": wal_mb}


def _initialize_session_state() -> None:
    defaults: Dict[str, Any] = {
        "api_key": DEFAULT_API_KEY,
        "auto_boot_done": False,
        "last_chat": "",
        "ctl_study_areas": ["Optimization", "AIHub", "Truth & Safety", "Fleet Topology"],
        "ctl_techniques": ["KNAA/QNAA reasoning", "Quantized compression", "Multi-parallel swarm", "Multipolar ensemble", "Natural pressure adaptation"],
        "ctl_smart_tools": ["code-analysis", "sql-pattern-mining", "fleet-deploy-ops", "x6-learning-extender"],
        "ctl_swarm_strategy": "hybrid",
        "ctl_micro_agents": 200,
        "ctl_gaussian_pressure": 0.88,
        "ctl_permanent_intelligence": True,
        "ctl_high_level_learning": 0.72,
        "ctl_hermes_type": "hybrid-core",
        "ctl_hermes_species": "Hybrid",
        "ctl_enable_algorithmic_types": True,
        "ctl_operation_mode": "Programming + C++",
        "ctl_x5_brain_pack": False,
        "ctl_x6_learning_pack": True,
        "ctl_auto_x10_setup": True,
        "ctl_both_sides_training": True,
        "ctl_model_override": "hermes-fleet-latest",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def inject_majestic_theme() -> None:
    st.markdown(
        """
<style>
.stApp {background: radial-gradient(circle at 10% -12%, rgba(92,126,255,0.11), rgba(12,14,24,0.96) 42%), radial-gradient(circle at 92% 0%, rgba(94,166,255,0.08), rgba(10,10,20,0.0) 50%);}
.block-container {max-width: 1650px; padding-top: 1.4rem; padding-bottom: 2.2rem;}
[data-testid="stMetricValue"] {color: #e9f4ff;}
[data-testid="stSidebar"] {background: linear-gradient(180deg, rgba(12,16,32,0.98), rgba(10,13,26,0.95));}
div.stButton > button {border-radius: 10px; border: 1px solid rgba(120,205,255,0.30); box-shadow: none;}
[data-testid="stHorizontalBlock"] {gap: 1rem;}
.stProgress > div > div {height: 0.72rem; border-radius: 999px;}
</style>
""",
        unsafe_allow_html=True,
    )


def render_variable_guide() -> None:
    st.caption("Variable guide")
    st.markdown(
        "- **Micro Hermes agents**: number of active mini workers. Higher = broader exploration, more compute.\n"
        "- **Gaussian learning pressure**: how strongly learning is pulled toward stable evidence (high = stricter).\n"
        "- **High-level learning focus**: shifts from raw speed to long-term memory quality.\n"
        "- **SQL/Internet/LLM signals**: source weighting used for curation and orchestration decisions."
    )


def _algorithm_bar_pack(preset: Dict[str, Any], optimized: Dict[str, Any], mode_name: str) -> List[Tuple[str, float, str]]:
    techniques = [str(t) for t in preset.get("techniques", [])] if isinstance(preset, dict) else []
    mode_cfg = OPERATION_MODES.get(mode_name, {})
    gaussian = float(optimized.get("gaussian_pressure", preset.get("gaussian_pressure", 0.80)))
    learning = float(optimized.get("high_level_learning", preset.get("high_level_learning", 0.72)))
    micro = float(optimized.get("micro_agents", preset.get("micro_agents", 180)))
    knaa = 0.92 if "KNAA/QNAA reasoning" in techniques else 0.66
    gnaa = 0.90 if "GNAA adaptive memory" in techniques else 0.64
    linear_reg = max(0.45, min(1.0, 0.52 + ((1.0 - abs(gaussian - 0.78)) * 0.28) + (learning * 0.20)))
    knn_mesh = 0.90 if ("Cross-agent communication mesh" in techniques or str(preset.get("swarm_strategy", "")) in ("mesh", "swarm")) else 0.62
    return [
        ("Gaussian Blur", max(0.0, min(1.0, gaussian)), "Smoothing power for stable learning convergence."),
        ("KNAA Reasoning", max(0.0, min(1.0, knaa)), "Knowledge-neighborhood reasoning strength."),
        ("GNAA Memory", max(0.0, min(1.0, gnaa)), "Adaptive memory retention and recall consistency."),
        ("Linear Regression", max(0.0, min(1.0, linear_reg)), "Directional trend fitting for iterative optimization."),
        ("KNN Mesh", max(0.0, min(1.0, knn_mesh)), "Neighbor-based coordination and sub-agent similarity routing."),
        ("Parallelism", max(0.0, min(1.0, micro / 256.0)), "Parallel throughput capacity from active micro agents."),
        ("Mode Fit", max(0.0, min(1.0, 0.70 + float(mode_cfg.get("learning_delta", 0.0)))), "How strongly the current settings match selected operation mode."),
    ]


def render_modern_learning_canvas(agent_rows: List[Dict[str, Any]], growth_data: Dict[str, Any]) -> None:
    st.markdown("#### Hermes Learning Matrix (Upgraded)")
    growth = float(growth_data.get("growth_index", 0.0)) if isinstance(growth_data, dict) else 0.0
    maturity = float(growth_data.get("maturity_index", 0.0)) if isinstance(growth_data, dict) else 0.0
    integration = float(growth_data.get("integration_index", 0.0)) if isinstance(growth_data, dict) else 0.0
    matrix_rows: List[Dict[str, Any]] = []
    for row in agent_rows[:18]:
        matrix_rows.append(
            {
                "Hermes": str(row.get("name", "hermes")),
                "Zone": str(row.get("zone", "General Zone")),
                "Mode": str(row.get("interaction", "hybrid")),
                "Progress": f"{float(row.get('progress', 0.0)) * 100:.1f}%",
                "Load": f"{float(row.get('load', 0.0)) * 100:.1f}%",
            }
        )
    m1, m2, m3 = st.columns(3)
    m1.metric("Growth Matrix", f"{growth * 100:.1f}%")
    m2.metric("Maturity Matrix", f"{maturity * 100:.1f}%")
    m3.metric("Integration Matrix", f"{integration * 100:.1f}%")
    if matrix_rows:
        st.dataframe(matrix_rows, use_container_width=True, hide_index=True)
    else:
        st.caption("Learning matrix populates after fleet snapshots stream in.")


def run_auto_cycle(max_mode: bool, technique: Dict[str, Any]) -> Dict[str, Any]:
    steps = (280 if max_mode else 140) if LOW_BANDWIDTH_MODE else (520 if max_mode else 220)
    candidates = min(500, ((190 if max_mode else 90) if LOW_BANDWIDTH_MODE else (320 if max_mode else 140)) + int(technique.get("micro_agents", 48) * (0.12 if LOW_BANDWIDTH_MODE else 0.2)))
    sim_steps = (140 if max_mode else 70) if LOW_BANDWIDTH_MODE else (320 if max_mode else 120)
    specialty = f"{_specialty_base()}:{technique.get('swarm_strategy', 'hybrid')}"

    simulate, sim_err = safe_post("/simulate", {"specialty": specialty, "steps": sim_steps})
    pulse, pulse_err = safe_post(
        "/learning-pulse",
        {
            "specialty": specialty,
            "steps": steps,
            "candidates": candidates,
            "sql_signal": technique["sql_signal"],
            "internet_signal": _effective_internet_signal(technique["internet_signal"], low_cap=True),
            "llm_signal": technique["llm_signal"],
            "stability_bias": max(0.60, min(0.98, technique["stability_bias"] + (technique["gaussian_pressure"] * 0.04))),
        },
        timeout=140,
    )
    optimize, opt_err = safe_post("/optimize-fleet", {"specialty": specialty, "candidates": candidates}, timeout=120)
    curate, curate_err = safe_post(
        "/curate-learning",
        {
            "sql_signal": technique["sql_signal"],
            "internet_signal": _effective_internet_signal(technique["internet_signal"], low_cap=False),
            "llm_signal": technique["llm_signal"],
            "stability_bias": technique["stability_bias"],
        },
        timeout=90,
    )
    dedupe, dedupe_err = safe_post("/dedupe-optimize", {"roots": ["core", "runtime", "src"], "max_file_mb": 8}, timeout=120)
    return {
        "technique_profile": technique,
        "simulate": simulate,
        "learning_pulse": pulse,
        "optimize_fleet": optimize,
        "curate_learning": curate,
        "dedupe_optimize": dedupe,
        "errors": {"simulate": sim_err, "learning_pulse": pulse_err, "optimize_fleet": opt_err, "curate_learning": curate_err, "dedupe_optimize": dedupe_err},
    }


def run_special_fleet_training(max_mode: bool, study_areas: List[str], technique: Dict[str, Any]) -> Dict[str, Any]:
    steps = 760 if max_mode else 300
    candidates = min(500, (360 if max_mode else 180) + int(technique.get("micro_agents", 48) * 0.15))
    areas = "-".join([s.lower().replace(" & ", "-").replace(" ", "-") for s in study_areas[:3]]) if study_areas else "general"
    specialty = f"{_specialty_base()}:{technique.get('swarm_strategy', 'hybrid')}:{areas}"
    pulse, pulse_err = safe_post(
        "/learning-pulse",
        {
            "specialty": specialty,
            "steps": steps,
            "candidates": candidates,
            "sql_signal": technique["sql_signal"],
            "internet_signal": 0.0 if OFFLINE_ONLY_MODE else (min(0.14, technique["internet_signal"] + 0.01) if USER_ROUTED_INTERNET else min(0.99, technique["internet_signal"] + 0.03)),
            "llm_signal": min(0.99, technique["llm_signal"] + 0.02),
            "stability_bias": technique["stability_bias"],
        },
        timeout=180,
    )
    simulate, sim_err = safe_post("/simulate", {"specialty": specialty, "steps": 360 if max_mode else 140}, timeout=120)
    optimize, opt_err = safe_post("/optimize-fleet", {"specialty": specialty, "candidates": candidates}, timeout=140)
    return {
        "specialty": specialty,
        "technique_profile": technique,
        "learning_pulse": pulse,
        "simulate": simulate,
        "optimize_fleet": optimize,
        "errors": {"learning_pulse": pulse_err, "simulate": sim_err, "optimize_fleet": opt_err},
    }


def zone_for_agent(specialty: str) -> str:
    specialty_l = specialty.lower()
    if "security" in specialty_l:
        return "Security Zone"
    if "research" in specialty_l or "learning" in specialty_l:
        return "Learning Zone"
    if "infra" in specialty_l or "ops" in specialty_l:
        return "Ops Zone"
    if "fleet" in specialty_l:
        return "Fleet Core"
    return "General Zone"


def normalize_agents(snapshot_data: Dict[str, Any], global_bonus: float) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    agents = snapshot_data.get("agents", [])
    symbols = ["🧠", "⚙️", "🛡️", "📡", "🚀", "🔬", "🛰️", "📊"]
    for i, agent in enumerate(agents):
        reward = float(agent.get("reward_score", 0.0))
        success_rate = float(agent.get("success_rate", 0.0))
        load = float(agent.get("load", 0.0))
        bonus = max(0.0, reward * (0.5 + global_bonus))
        progress = max(0.0, min(1.0, (reward * 0.5) + (success_rate * 0.5)))
        size_mode = "small-fast" if progress < 0.45 else ("medium-balanced" if progress < 0.75 else "large-deep")
        interaction = "mesh" if "research" in str(agent.get("specialty", "")).lower() else "hybrid"
        skill_start = (i * 3) % len(AGENT_SKILLS_25)
        skill_pack = [AGENT_SKILLS_25[(skill_start + j) % len(AGENT_SKILLS_25)] for j in range(3)]
        rows.append(
            {
                "symbol": symbols[i % len(symbols)],
                "name": agent.get("name", f"hermes-{i+1}"),
                "specialty": agent.get("specialty", "general"),
                "zone": zone_for_agent(str(agent.get("specialty", "general"))),
                "reward": reward,
                "success_rate": success_rate,
                "load": load,
                "bonus": bonus,
                "progress": progress,
                "active": bool(agent.get("active", True)),
                "size_mode": size_mode,
                "size_description": SIZE_MODE_DETAILS.get(size_mode, "Hermes operational profile."),
                "interaction": interaction,
                "skills": skill_pack,
            }
        )
    return rows


def deep_auto_learning_zone(max_mode: bool, study_areas: List[str], rounds: int, technique: Dict[str, Any]) -> Dict[str, Any]:
    candidates = min(500, (300 if max_mode else 160) + int(technique.get("micro_agents", 48) * 0.2))
    steps = 520 if max_mode else 220
    outputs: List[Dict[str, Any]] = []
    for i in range(max(1, rounds)):
        pulse, pulse_err = safe_post(
            "/learning-pulse",
            {
                "specialty": f"{_specialty_base()}:{technique.get('swarm_strategy', 'hybrid')}",
                "steps": steps + (i * 120),
                "candidates": candidates,
                "sql_signal": technique["sql_signal"],
                "internet_signal": _effective_internet_signal(technique["internet_signal"], low_cap=True),
                "llm_signal": technique["llm_signal"],
                "stability_bias": max(0.60, min(0.98, technique["stability_bias"] + (technique["gaussian_pressure"] * 0.05))),
            },
            timeout=150,
        )
        compare_prompt = (
            "Compare the latest Hermes learning signals and rank improvement opportunities. "
            f"Study areas: {', '.join(study_areas) if study_areas else 'fleet, optimization, safety'}. "
            f"Use techniques: {', '.join(technique.get('techniques', []))}."
        )
        compare, compare_err = safe_post(
            "/llm-chat",
            {
                "prompt": compare_prompt,
                "system_prompt": "You are Hermes deep-learning coordinator.",
                "model": _selected_model_override() or None,
                "temperature": 0.2,
                "max_tokens": 900,
            },
            timeout=120,
        )
        outputs.append({"round": i + 1, "pulse": pulse, "pulse_error": pulse_err, "compare": compare, "compare_error": compare_err})
    return {"rounds": rounds, "study_areas": study_areas, "technique_profile": technique, "results": outputs}


st.set_page_config(page_title="Hermes Control Dashboard", page_icon="🧠", layout="wide")
inject_majestic_theme()
st.title("Hermes Fleet Control Dashboard")
st.caption("Clear control view: runtime status, SQL intelligence, and one-click fleet actions.")

_initialize_session_state()

with st.sidebar:
    st.subheader("Connection")
    st.text_input("API Key", key="api_key", type="password")
    st.caption(f"Gateway/API: {current_api_base()}")
    login_profile = st.selectbox(
        "Quick login profile",
        options=["auto", "local-hermes-ui-key", "local-hermes-dev-key"],
        index=0,
    )
    l1, l2 = st.columns(2)
    with l1:
        if st.button("Login", use_container_width=True):
            if login_profile != "auto":
                st.session_state["api_key"] = login_profile
            st.success("Login profile applied.")
    with l2:
        if st.button("Reconnect", use_container_width=True):
            ping, ping_err = safe_get("/system-watch", timeout=12)
            if ping_err:
                st.error(f"Reconnect failed: {ping_err}")
            else:
                st.success("Hermes connection restored.")
                st.rerun()
    st.caption("Quick login uses local Hermes keys and reconnect checks.")
    st.markdown("### How it works")
    st.caption("1. Send prompt or click auto action\n2. Hermes fleet simulates + learns\n3. Bonus and XP improve")
    live_refresh = st.checkbox("Live fleet auto-refresh", value=True)
    refresh_seconds = st.slider("Refresh seconds", min_value=10, max_value=90, value=20, step=5)
    focused_layout = st.checkbox("Focused layout (clean view)", value=True)
    show_legacy_map_ui = st.checkbox("Show AIHub Hub + Map panels", value=True)
    st.checkbox("Enable legacy strategy Hermes types", value=True, key="ctl_enable_algorithmic_types")
    st.selectbox("Hermes species", options=["Hybrid", "Normal", "Mesh"], key="ctl_hermes_species")
    _sidebar_mode_current = str(st.session_state.get("ctl_operation_mode", "Programming + C++"))
    _sidebar_mode_index = list(OPERATION_MODES.keys()).index(_sidebar_mode_current) if _sidebar_mode_current in OPERATION_MODES else 0
    sidebar_mode = st.selectbox(
        "Operation mode (4 modes)",
        options=list(OPERATION_MODES.keys()),
        index=_sidebar_mode_index,
        key="ctl_operation_mode_sidebar",
    )
    st.session_state["ctl_operation_mode"] = sidebar_mode
    st.markdown("### Hermes Type + Model")
    active_type_presets = _active_hermes_presets()
    hermes_type_labels = {k: str(v.get("title", k)) for k, v in active_type_presets.items()}
    hermes_type_keys = list(hermes_type_labels.keys())
    current_type = _selected_hermes_type_key()
    hermes_type_index = hermes_type_keys.index(current_type) if current_type in hermes_type_keys else 0
    selected_hermes_type = st.selectbox(
        "Choose Hermes type (7 active + extended)",
        options=hermes_type_keys,
        index=hermes_type_index,
        format_func=lambda key: hermes_type_labels.get(key, key),
        key="ctl_hermes_type",
    )
    selected_preset = active_type_presets.get(selected_hermes_type, {})
    optimized = _optimized_settings(selected_preset, str(st.session_state.get("ctl_hermes_species", "Hybrid")))
    mode_name = str(st.session_state.get("ctl_operation_mode", "Programming + C++"))
    mode_cfg = OPERATION_MODES.get(mode_name, {})
    st.caption(
        f"{selected_preset.get('group', 'Custom')} • "
        f"{selected_preset.get('personality', 'Adaptive Hermes profile.')}"
    )
    st.caption(str(selected_preset.get("description", "")))
    st.caption(f"Mode: {mode_name} — {mode_cfg.get('description', 'Balanced operation profile.')}")
    st.caption(f"Recommended type for this mode: {str(_all_hermes_presets().get(str(mode_cfg.get('recommended_type', 'hybrid-core')), {}).get('title', 'Hybrid'))}")
    st.progress(min(1.0, float(optimized.get("micro_agents", 0)) / 256.0), text="Auto Agent Scale")
    st.progress(min(1.0, float(optimized.get("gaussian_pressure", 0.0))), text="Auto Gaussian Pressure")
    st.progress(min(1.0, float(optimized.get("high_level_learning", 0.0))), text="Auto Learning Focus")
    for algo_name, algo_value, algo_tip in _algorithm_bar_pack(selected_preset, optimized, mode_name):
        st.progress(algo_value, text=f"{algo_name} {algo_value * 100:.1f}%")
        st.caption(algo_tip)
    st.caption(f"Operating style: {optimized.get('operations', 'Balanced operations mode.')}")
    selected_model = st.selectbox(
        "Preferred model",
        options=MODEL_OPTIONS,
        index=max(0, MODEL_OPTIONS.index(_selected_model_override())) if _selected_model_override() in MODEL_OPTIONS else 0,
        key="ctl_model_override",
    )
    s1, s2 = st.columns(2)
    with s1:
        if st.button("Apply Type Preset", use_container_width=True):
            preset = active_type_presets.get(selected_hermes_type, {})
            auto = _optimized_settings(preset, str(st.session_state.get("ctl_hermes_species", "Hybrid")))
            st.session_state["ctl_swarm_strategy"] = str(preset.get("swarm_strategy", st.session_state.get("ctl_swarm_strategy", "hybrid")))
            st.session_state["ctl_micro_agents"] = int(auto.get("micro_agents", st.session_state.get("ctl_micro_agents", 160)))
            st.session_state["ctl_gaussian_pressure"] = float(auto.get("gaussian_pressure", st.session_state.get("ctl_gaussian_pressure", 0.8)))
            st.session_state["ctl_high_level_learning"] = float(auto.get("high_level_learning", st.session_state.get("ctl_high_level_learning", 0.72)))
            preset_techniques = preset.get("techniques", [])
            if isinstance(preset_techniques, list) and preset_techniques:
                st.session_state["ctl_techniques"] = [str(t) for t in preset_techniques[:6]]
            safe_post(
                "/ingest-signal",
                {
                    "source": "gui_hermes_type",
                    "signal_score": 0.86,
                    "payload": {
                        "hermes_type": selected_hermes_type,
                        "title": hermes_type_labels.get(selected_hermes_type, selected_hermes_type),
                        "specialty_base": _specialty_base(),
                    },
                },
                timeout=45,
            )
            st.success(
                f"Applied optimized {hermes_type_labels.get(selected_hermes_type, selected_hermes_type)} "
                f"({st.session_state.get('ctl_hermes_species', 'Hybrid')}) preset."
            )
    with s2:
        if st.button("Apply Model", use_container_width=True):
            safe_post(
                "/ingest-signal",
                {
                    "source": "gui_model_preference",
                    "signal_score": 0.84,
                    "payload": {
                        "model_preference": selected_model,
                        "hermes_type": selected_hermes_type,
                        "specialty_base": _specialty_base(),
                    },
                },
                timeout=45,
            )
            st.success(f"Model preference set to {selected_model}.")
    st.caption(
        f"Active type: {hermes_type_labels.get(_selected_hermes_type_key(), _selected_hermes_type_key())} | "
        f"species: {st.session_state.get('ctl_hermes_species', 'Hybrid')} | model: {_selected_model_override() or 'auto'}"
    )

watch_payload, watch_err = safe_get("/system-watch", timeout=25)
gateway_watch, gateway_watch_err = safe_get("/gateway-max-status", timeout=20)
ultimate_entrance, ultimate_entrance_err = safe_get("/ultimate-entrance-status", timeout=20)
if not watch_err and isinstance(watch_payload, dict):
    unified = watch_payload.get("unified_config", {}) if isinstance(watch_payload.get("unified_config"), dict) else {}
    bonus_data = watch_payload.get("aihub_bonus", {}) if isinstance(watch_payload.get("aihub_bonus"), dict) else {}
    snapshot = watch_payload.get("snapshot", {}) if isinstance(watch_payload.get("snapshot"), dict) else {}
    growth_data = watch_payload.get("learning_growth", {}) if isinstance(watch_payload.get("learning_growth"), dict) else {}
    training_status = watch_payload.get("training_status", {}) if isinstance(watch_payload.get("training_status"), dict) else {}
    cpp_kernel = watch_payload.get("cpp_kernel_status", {}) if isinstance(watch_payload.get("cpp_kernel_status"), dict) else {}
    knowledge_mesh = watch_payload.get("knowledge_mesh", {}) if isinstance(watch_payload.get("knowledge_mesh"), dict) else {}
    unified_err = ""
    bonus_err = ""
    snapshot_err = ""
    growth_err = ""
    training_status_err = ""
    cpp_kernel_err = ""
    mesh_err = ""
else:
    unified, unified_err = safe_get("/unified-config", timeout=20)
    bonus_data, bonus_err = safe_get("/aihub-bonus", timeout=20)
    snapshot, snapshot_err = safe_get("/snapshot", timeout=20)
    growth_data, growth_err = safe_get("/learning-growth", timeout=20)
    training_status, training_status_err = safe_get("/training-status", timeout=20)
    cpp_kernel, cpp_kernel_err = safe_get("/cpp-kernel-status", timeout=20)
    knowledge_mesh, mesh_err = safe_get("/knowledge-mesh", timeout=20)
aihub_bonus = float(bonus_data.get("aihub_bonus", 0.0))
agent_rows = normalize_agents(snapshot, aihub_bonus) if not snapshot_err else []
runtime_hermes = len(agent_rows)
configured_hermes = int(st.session_state.get("ctl_micro_agents", 0))
total_hermes = runtime_hermes if runtime_hermes > 0 else configured_hermes
active_hermes = len([a for a in agent_rows if a["active"]])
avg_progress = (sum(a["progress"] for a in agent_rows) / total_hermes) if total_hermes else 0.0
live_volume_root = resolve_volume_root()
if "auto_volume_bootstrap" not in st.session_state:
    try:
        bootstrap_root, bootstrap_manifest = initialize_volume_layout(live_volume_root)
        scan_volume_files.clear()
        read_sql_training_intelligence.clear()
        st.session_state["auto_volume_bootstrap"] = {
            "root": bootstrap_root,
            "created_count": int(bootstrap_manifest.get("created_count", 0)) if isinstance(bootstrap_manifest, dict) else 0,
            "ok": True,
        }
    except Exception as bootstrap_exc:
        st.session_state["auto_volume_bootstrap"] = {"ok": False, "error": str(bootstrap_exc)}
live_sql_intel = read_sql_training_intelligence(live_volume_root)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("System", "Online" if not unified_err else "Offline")
c2.metric("Hermes Amount", str(total_hermes), delta=f"runtime {runtime_hermes} | target {configured_hermes}")
c3.metric("Active Hermes", str(active_hermes))
c4.metric("AIHub Bonus", f"{aihub_bonus * 100:.1f}%")
active_model_display = _selected_model_override() or str(unified.get("aihub_shared_model_id", "aihub-unified-v1"))
c5.metric("Model", active_model_display)
if unified_err:
    st.warning("Hermes is not connected yet. Use Login/Reconnect in the sidebar.")
    if st.button("Retry Hermes Connection", use_container_width=True):
        retry_watch, retry_err = safe_get("/system-watch", timeout=12)
        if retry_err:
            st.error(f"Still offline: {retry_err}")
        else:
            st.success("Hermes connection is back online.")
            st.rerun()
auto_bootstrap = st.session_state.get("auto_volume_bootstrap", {})
if isinstance(auto_bootstrap, dict):
    if bool(auto_bootstrap.get("ok", False)):
        st.caption(
            f"Container auto-setup volume ready: {auto_bootstrap.get('root', live_volume_root)} "
            f"(created {int(auto_bootstrap.get('created_count', 0))} paths)."
        )
    elif auto_bootstrap.get("error"):
        st.caption(f"Container auto-setup warning: {auto_bootstrap.get('error')}")
bond = _guided_auto_bond_status(
    unified_err=unified_err,
    watch_err=watch_err,
    gateway_watch_err=gateway_watch_err,
    auto_bootstrap=auto_bootstrap if isinstance(auto_bootstrap, dict) else {},
    sql_intel=live_sql_intel if isinstance(live_sql_intel, dict) else {},
    volume_root=live_volume_root,
)
bond_signals = bond.get("signals", {})
b1, b2, b3, b4, b5, b6 = st.columns(6)
b1.metric("Auto Bond", f"{float(bond.get('bond_score', 0.0)) * 100:.1f}%")
b2.metric("API", "OK" if float(bond_signals.get("api_link", 0.0)) > 0.5 else "Pending")
b3.metric("Watch", "OK" if float(bond_signals.get("watch_link", 0.0)) > 0.5 else "Pending")
b4.metric("Gateway", "OK" if float(bond_signals.get("gateway_link", 0.0)) > 0.5 else "Pending")
b5.metric("Volume", "OK" if float(bond_signals.get("volume_link", 0.0)) > 0.5 else "Missing")
b6.metric("SQL", "OK" if float(bond_signals.get("sql_link", 0.0)) > 0.5 else "Pressure")
st.caption(
    f"Guided auto-local bonding: api={int(float(bond_signals.get('api_link', 0.0)))} | watch={int(float(bond_signals.get('watch_link', 0.0)))} | "
    f"gateway={int(float(bond_signals.get('gateway_link', 0.0)))} | volume={int(float(bond_signals.get('volume_link', 0.0)))} | "
    f"auto_setup={int(float(bond_signals.get('auto_setup', 0.0)))} | sql_load(db/wal)={float(bond.get('db_mb', 0.0)):.1f}/{float(bond.get('wal_mb', 0.0)):.1f}MB"
)
st.subheader("Hermes Type Deck (7 Active Types)")
deck_presets = _all_hermes_presets()
deck_keys = [key for key in CENTER_ACTIVE_TYPE_KEYS if key in deck_presets]
deck_labels = {key: str(deck_presets.get(key, {}).get("title", key)) for key in deck_keys}
current_type_key = _selected_hermes_type_key()
if current_type_key not in deck_keys and deck_keys:
    current_type_key = deck_keys[0]
deck_pick = st.radio(
    "Pick from the 7 active Hermes types",
    options=deck_keys,
    index=deck_keys.index(current_type_key) if current_type_key in deck_keys else 0,
    format_func=lambda key: deck_labels.get(key, key),
    horizontal=True,
)
deck_preset = deck_presets.get(deck_pick, {})
deck_species = str(st.session_state.get("ctl_hermes_species", "Hybrid"))
deck_optimized = _optimized_settings(deck_preset, deck_species)
dcol1, dcol2 = st.columns([2, 1])
with dcol1:
    st.markdown(f"**{deck_preset.get('title', deck_pick)}** • {deck_preset.get('personality', 'Adaptive Hermes profile.')}")
    st.caption(str(deck_preset.get("description", "")))
    st.caption(f"Species: {deck_species} • Swarm: {deck_preset.get('swarm_strategy', 'hybrid')} • Group: {deck_preset.get('group', 'Custom')}")
with dcol2:
    if st.button("Apply Deck Type Now", use_container_width=True):
        st.session_state["ctl_hermes_type"] = deck_pick
        if deck_pick in ALGORITHMIC_HERMES_TYPE_PRESETS:
            st.session_state["ctl_enable_algorithmic_types"] = True
        auto = _optimized_settings(deck_preset, deck_species)
        st.session_state["ctl_swarm_strategy"] = str(deck_preset.get("swarm_strategy", st.session_state.get("ctl_swarm_strategy", "hybrid")))
        st.session_state["ctl_micro_agents"] = int(auto.get("micro_agents", st.session_state.get("ctl_micro_agents", 160)))
        st.session_state["ctl_gaussian_pressure"] = float(auto.get("gaussian_pressure", st.session_state.get("ctl_gaussian_pressure", 0.8)))
        st.session_state["ctl_high_level_learning"] = float(auto.get("high_level_learning", st.session_state.get("ctl_high_level_learning", 0.72)))
        st.success(f"Applied {deck_labels.get(deck_pick, deck_pick)} from the center deck.")
for algo_name, algo_value, algo_tip in _algorithm_bar_pack(deck_preset, deck_optimized, str(st.session_state.get("ctl_operation_mode", "Programming + C++"))):
    st.progress(algo_value, text=f"{algo_name} {algo_value * 100:.1f}%")
    st.caption(algo_tip)
st.markdown("#### Mix & Match Optimizer (Best Working Combos)")
mix_rows = [
    {
        "Goal": "C++ / Programming Depth",
        "Best Mode": "Programming + C++",
        "Best Type": "Deep Thinker",
        "Why it works": "Highest reasoning depth and strongest structure retention for compile/debug/refactor loops.",
        "Suggested bars": "Gaussian 82-90, KNAA high, GNAA high, Linear Regression medium-high",
    },
    {
        "Goal": "GUI / Smooth Visuals",
        "Best Mode": "GUI + Visual",
        "Best Type": "Mesh Swarm",
        "Why it works": "Fast visual iteration with high collaboration and stable design-cycle convergence.",
        "Suggested bars": "Gaussian 78-86, KNN Mesh high, GNAA medium-high, Parallelism medium",
    },
    {
        "Goal": "Intensive Throughput",
        "Best Mode": "Intensive Throughput",
        "Best Type": "Parallel Swarm",
        "Why it works": "Max parallel throughput and wide candidate search for heavy orchestration load.",
        "Suggested bars": "Parallelism high, KNN Mesh high, Gaussian 70-82, Linear Regression medium",
    },
    {
        "Goal": "Learning + Retention",
        "Best Mode": "Learning Depth",
        "Best Type": "Gaussian Blur",
        "Why it works": "Best long-horizon stability, memory retention, and robust adaptation under noise.",
        "Suggested bars": "Gaussian high, GNAA high, KNAA medium-high, Linear Regression medium-high",
    },
    {
        "Goal": "Ultimate AI Integration",
        "Best Mode": "Programming + C++",
        "Best Type": "Ultimate AIHub Fusion",
        "Why it works": "Highest blended performance for AIHub + SQL + fleet orchestration with strong reasoning quality.",
        "Suggested bars": "Gaussian 88-94, KNAA high, GNAA high, KNN Mesh high, Parallelism high",
    },
]
st.dataframe(mix_rows, use_container_width=True, hide_index=True)
st.caption(
    "Optimal practical flow: pick mode -> pick type -> apply deck type -> run one-click SQL/training setup in center SQL tab -> run Ultimate Hermes + AIHub upgrade."
)
st.markdown("#### Full Hermes Table + Best Bonus Guide")
all_type_rows: List[Dict[str, str]] = []
for type_key, preset in _all_hermes_presets().items():
    if not isinstance(preset, dict):
        continue
    techniques_text = ", ".join([str(t) for t in preset.get("techniques", [])[:4]])
    title = str(preset.get("title", type_key))
    best_mode = "Programming + C++" if ("Deep" in title or "Ultimate" in title) else ("GUI + Visual" if ("Mesh" in title or "Creative" in title) else ("Learning Depth" if ("Gaussian" in title or "Idealist" in title) else "Intensive Throughput"))
    best_action = "Deploy + optimize continuously" if best_mode in ("Intensive Throughput", "Programming + C++") else "Run guided learning + profile sync"
    bonus_hint = "Use AIHub routing optimizer + brain fusion monitor for max bonus."
    all_type_rows.append(
        {
            "Hermes Type": title,
            "Group": str(preset.get("group", "Custom")),
            "Best Mode": best_mode,
            "Best Action": best_action,
            "Bonus Guide": bonus_hint,
            "Core Techniques": techniques_text,
            "Agents/Gaussian/Learning": f"{int(preset.get('micro_agents', 0))} / {float(preset.get('gaussian_pressure', 0.0)):.2f} / {float(preset.get('high_level_learning', 0.0)):.2f}",
        }
    )
st.dataframe(all_type_rows, use_container_width=True, hide_index=True)
fleet_preset = st.selectbox(
    "Fleet customization preset",
    ["Balanced Ops", "C++ Forge", "UI Studio", "Security Guard", "Throughput Storm", "Learning Lab"],
    index=0,
)
if st.button("Apply Fleet Customization Preset", use_container_width=True):
    preset_map = {
        "Balanced Ops": {"mode": "Programming + C++", "type": "hybrid-core", "tools": ["code-analysis", "fleet-deploy-ops", "brain-fusion-monitor"]},
        "C++ Forge": {"mode": "Programming + C++", "type": "deep-thinker", "tools": ["code-analysis", "cpp-compile-advisor", "split-merge-planner"]},
        "UI Studio": {"mode": "GUI + Visual", "type": "mesh-swarm", "tools": ["ui-polish-engine", "multi-parallel-orchestrator", "network-signal-fuser"]},
        "Security Guard": {"mode": "Learning Depth", "type": "idealist-strategist", "tools": ["security-threat-modeler", "truth-shield-guardian", "idealist-policy-guard"]},
        "Throughput Storm": {"mode": "Intensive Throughput", "type": "legacy-parallel-swarm", "tools": ["multi-parallel-orchestrator", "efficiency-tuner", "fleet-deploy-ops"]},
        "Learning Lab": {"mode": "Learning Depth", "type": "ultimate-ml-x5", "tools": ["adaptive-memory-weaver", "x6-learning-extender", "brain-fusion-monitor"]},
    }
    chosen = preset_map.get(fleet_preset, preset_map["Balanced Ops"])
    st.session_state["ctl_operation_mode"] = str(chosen["mode"])
    st.session_state["ctl_hermes_type"] = str(chosen["type"])
    st.session_state["ctl_smart_tools"] = list(chosen["tools"])
    st.success(f"Applied preset: {fleet_preset}")
    st.rerun()
with st.expander("Hermes Type Catalog + Optimization Tips", expanded=False):
    catalog_presets = _active_hermes_presets()
    st.dataframe(
        [
            {
                "type": preset.get("title", key),
                "group": preset.get("group", "Custom"),
                "personality": preset.get("personality", ""),
                "description": preset.get("description", ""),
                "swarm": preset.get("swarm_strategy", ""),
                "agents": int(preset.get("micro_agents", 0)),
                "gaussian": float(preset.get("gaussian_pressure", 0.0)),
                "learning": float(preset.get("high_level_learning", 0.0)),
            }
            for key, preset in catalog_presets.items()
            if isinstance(preset, dict)
        ],
        use_container_width=True,
        hide_index=True,
    )
    if not _use_algorithmic_presets():
        st.caption("Turn on 'Enable legacy strategy Hermes types' in the sidebar to load Hybrid/Mesh/Parallel + additional legacy strategy modes.")
    else:
        st.caption("Legacy strategy modes are auto-calibrated with species-aware bars and applied as optimized settings.")
    st.markdown(
        "- **Optimization tip:** use Parallel/Hybrid for deployment speed, Mesh for collaboration breadth, and Deep modes for harder reasoning.\n"
        "- **Algorithm tip:** Gaussian Blur + GNAA improve stability; KNAA + Linear Regression improve directional optimization quality.\n"
        "- **Scale tip:** increase micro agents gradually (+16 to +32) while watching SQL storage pressure."
    )
if not watch_err and isinstance(watch_payload, dict):
    st.caption(f"Watch stream: {watch_payload.get('watch_timestamp_utc', 'n/a')} (gateway aggregated)")
orchestration_counts = snapshot.get("super_orchestration_counts", {}) if isinstance(snapshot, dict) else {}
if orchestration_counts:
    oc1, oc2, oc3 = st.columns(3)
    oc1.metric("Super Orchestration Train Steps", str(int(orchestration_counts.get("recent_train_steps", 0))))
    oc2.metric("Super Orchestration Pulses", str(int(orchestration_counts.get("recent_learning_pulses", 0))))
    oc3.metric("Super Orchestration Big Decisions", str(int(orchestration_counts.get("recent_big_decisions", 0))))

if unified_err:
    st.error(f"Gateway not ready: {unified_err}")
if bonus_err:
    st.warning(f"AIHub bonus pending: {bonus_err}")
if training_status_err:
    st.warning(f"Training status pending: {training_status_err}")

st.write(
    f"**Unified AI/ML:** provider={unified.get('llm_api_provider', 'temp-api')} | "
    f"entry={unified.get('single_exe_entrypoint', 'hermes-gateway')} | "
    f"profile={unified.get('aihub_shared_ml_profile', 'global-learning')}"
)
if LOW_BANDWIDTH_MODE:
    st.caption("Low-bandwidth mode: local-first routing with minimized internet-signal weight for faster, lighter cycles.")
if USER_ROUTED_INTERNET and not OFFLINE_ONLY_MODE:
    st.caption("Internet mode: routed through your controlled path only (capped low internet-signal).")
st.subheader("Hermes Stability + Entrance")
ue = ultimate_entrance if isinstance(ultimate_entrance, dict) else {}
decision_integration = float(growth_data.get("integration_index", 0.0)) if isinstance(growth_data, dict) else 0.0
decision_adaptive = float(growth_data.get("avg_adaptive_brain", 0.0)) if isinstance(growth_data, dict) else 0.0
decision_action = float(growth_data.get("avg_action_brain", 0.0)) if isinstance(growth_data, dict) else 0.0
u1, u2, u3, u4, u5 = st.columns(5)
u1.metric("Entrance Integration", f"{float(ue.get('integration_score', 0.0)) * 100:.1f}%")
u2.metric("Gateway Reliability", f"{float(ue.get('reliability', 0.0)) * 100:.1f}%")
u3.metric("Gateway Response", f"{float(ue.get('responsiveness', 0.0)) * 100:.1f}%")
u4.metric("Route Diversity", f"{float(ue.get('route_diversity', 0.0)) * 100:.1f}%")
u5.metric("Gateway Errors", str(int(ue.get('errors', 0))))
d1, d2, d3 = st.columns(3)
d1.metric("Decision Integration", f"{decision_integration * 100:.1f}%")
d2.metric("Adaptive Brain", f"{decision_adaptive * 100:.1f}%")
d3.metric("Action Brain", f"{decision_action * 100:.1f}%")
if ultimate_entrance_err:
    st.caption(f"Ultimate entrance telemetry pending: {ultimate_entrance_err}")
if st.button("Run Ultimate Entrance Upgrade", use_container_width=True):
    entrance_strength = max(0.0, min(1.0, (decision_integration * 0.5) + (decision_action * 0.25) + (decision_adaptive * 0.25)))
    run_logged_post_action(
        label="ultimate-entrance-upgrade",
        path="/aihub-max-upgrade",
        payload={
            "specialty": "fleet:ultimate-entrance",
            "steps": int(860 + (entrance_strength * 120)),
            "candidates": int(340 + (entrance_strength * 60)),
            "sql_signal": min(0.98, 0.93 + (entrance_strength * 0.05)),
            "internet_signal": 0.08,
            "llm_signal": min(0.99, 0.95 + (entrance_strength * 0.04)),
            "stability_bias": min(0.96, 0.86 + (entrance_strength * 0.08)),
        },
        success_message="Ultimate entrance upgrade triggered.",
        error_prefix="Ultimate entrance upgrade failed",
        timeout=180,
    )
if not focused_layout:
    render_modern_learning_canvas(
        agent_rows=agent_rows,
        growth_data=growth_data if isinstance(growth_data, dict) else {},
    )
    render_evolution_centerpiece(
        agent_rows=agent_rows,
        sql_intel=live_sql_intel if isinstance(live_sql_intel, dict) else {},
        growth_data=growth_data if isinstance(growth_data, dict) else {},
        training_status=training_status if isinstance(training_status, dict) else {},
    )
    render_learning_graphs(live_sql_intel if isinstance(live_sql_intel, dict) else {})
    render_fleet_showcase_panels(
        sql_intel=live_sql_intel if isinstance(live_sql_intel, dict) else {},
        growth_data=growth_data if isinstance(growth_data, dict) else {},
        training_status=training_status if isinstance(training_status, dict) else {},
        cpp_kernel=cpp_kernel if isinstance(cpp_kernel, dict) else {},
    )
    if show_legacy_map_ui:
        render_next_level_control_center(
            sql_intel=live_sql_intel if isinstance(live_sql_intel, dict) else {},
            growth_data=growth_data if isinstance(growth_data, dict) else {},
            training_status=training_status if isinstance(training_status, dict) else {},
            watch_payload=watch_payload if isinstance(watch_payload, dict) else {},
            unified=unified if isinstance(unified, dict) else {},
            cpp_kernel=cpp_kernel if isinstance(cpp_kernel, dict) else {},
            ultimate_entrance=ultimate_entrance if isinstance(ultimate_entrance, dict) else {},
            volume_root=live_volume_root,
            run_logged_post_action=run_logged_post_action,
            show_center_nexus=False,
        )
        watch_plan = render_aihub_watch_panels(
            unified=unified if isinstance(unified, dict) else {},
            watch_payload=watch_payload if isinstance(watch_payload, dict) else {},
            gateway_status=gateway_watch if isinstance(gateway_watch, dict) else {},
            sql_intel=live_sql_intel if isinstance(live_sql_intel, dict) else {},
            training_status=training_status if isinstance(training_status, dict) else {},
            growth_data=growth_data if isinstance(growth_data, dict) else {},
            optimizer_state=st.session_state.get("last_chat_optimizer", {}),
        )
        if gateway_watch_err:
            st.caption(f"Gateway watch telemetry pending: {gateway_watch_err}")
        if st.button("Auto-Design AIHub Plan for Complex Situations", use_container_width=True):
            payload = watch_plan.get("recommended_payload", {}) if isinstance(watch_plan, dict) else {}
            run_logged_post_action(
                label="aihub-max-upgrade",
                path="/aihub-max-upgrade",
                payload=payload,
                success_message="AIHub max-upgrade plan triggered.",
                error_prefix="AIHub max-upgrade failed",
                timeout=160,
            )
else:
    st.caption("Focused mode hides legacy diagram/map sections for a cleaner UI.")

if focused_layout:
    st.subheader("Focused Hermes Center")
    render_next_level_control_center(
        sql_intel=live_sql_intel if isinstance(live_sql_intel, dict) else {},
        growth_data=growth_data if isinstance(growth_data, dict) else {},
        training_status=training_status if isinstance(training_status, dict) else {},
        watch_payload=watch_payload if isinstance(watch_payload, dict) else {},
        unified=unified if isinstance(unified, dict) else {},
        cpp_kernel=cpp_kernel if isinstance(cpp_kernel, dict) else {},
        ultimate_entrance=ultimate_entrance if isinstance(ultimate_entrance, dict) else {},
        volume_root=live_volume_root,
        run_logged_post_action=run_logged_post_action,
        show_center_nexus=True,
    )
    render_fleet_showcase_panels(
        sql_intel=live_sql_intel if isinstance(live_sql_intel, dict) else {},
        growth_data=growth_data if isinstance(growth_data, dict) else {},
        training_status=training_status if isinstance(training_status, dict) else {},
        cpp_kernel=cpp_kernel if isinstance(cpp_kernel, dict) else {},
    )
    render_sql_intelligence_panels(
        sql_intel=live_sql_intel if isinstance(live_sql_intel, dict) else {},
        render_xp_bar=render_xp_bar,
        run_logged_post_action=run_logged_post_action,
        high_level_learning=float(st.session_state.get("ctl_high_level_learning", 0.72)),
    )
    st.caption("Focused layout is ON: legacy map UI is hidden so Hermes + SQL stay clean and stable.")
    if live_refresh:
        st.caption(f"Live refresh active: updating every {refresh_seconds}s")
        time.sleep(refresh_seconds)
        st.rerun()
    st.stop()

st.subheader("Training Compliance + Always-On Status")
ts1, ts2, ts3, ts4, ts5 = st.columns(5)
is_training_active = bool(training_status.get("training_active", False)) if not training_status_err else False
idle_seconds = training_status.get("idle_seconds") if isinstance(training_status, dict) else None
rule_score = str(training_status.get("rule_score", "n/a")) if isinstance(training_status, dict) else "n/a"
recent_pulses = int(training_status.get("recent_learning_events", 0)) if isinstance(training_status, dict) else 0
github_sync = bool(training_status.get("rules", {}).get("github_knowledge_sync", False)) if isinstance(training_status, dict) else False
ts1.metric("Training", "Active" if is_training_active else "Needs Pulse")
ts2.metric("Idle Seconds", "n/a" if idle_seconds is None else f"{float(idle_seconds):.1f}")
ts3.metric("Rule Score", rule_score)
ts4.metric("Recent Pulses", str(recent_pulses))
ts5.metric("GitHub Knowledge Sync", "Active" if github_sync else "Pending")
if not is_training_active:
    st.warning("Training appears idle. Use 'Force Training Pulse Now' to restart immediate learning.")
if st.button("Force Training Pulse Now", use_container_width=True):
    if bool(st.session_state.get("ctl_x6_learning_pack", True)):
        pulse_steps = 1320
        pulse_candidates = 840
    elif bool(st.session_state.get("ctl_x5_brain_pack", False)):
        pulse_steps = 1100
        pulse_candidates = 700
    else:
        pulse_steps = 220
        pulse_candidates = 140
    run_logged_post_action(
        label="force-training-pulse",
        path="/learning-pulse",
        payload={
            "specialty": _specialty_base(),
            "steps": pulse_steps,
            "candidates": pulse_candidates,
            "both_sides_training": bool(st.session_state.get("ctl_both_sides_training", True)),
        },
        success_message="Training pulse triggered.",
        error_prefix="Training pulse failed",
        timeout=120,
    )

brain_catalog = snapshot.get("brain_horizon_catalog", {}) if isinstance(snapshot, dict) else {}
if not isinstance(brain_catalog, dict) or not brain_catalog:
    brain_catalog = dict(VARIABLE_CATALOG)
brain_profile = snapshot.get("brain_horizon_profile", {}) if isinstance(snapshot, dict) else {}
training_variables = snapshot.get("training_variables", {}) if isinstance(snapshot, dict) else {}
with st.expander("Brain Variables: Short / Mid / Long + Growth Maturity", expanded=False):
    if brain_profile:
        st.caption("Live integrated profile")
        st.dataframe(
            [
                {
                    "Short Horizon": round(float(brain_profile.get("short_horizon", 0.0)), 4),
                    "Mid Horizon": round(float(brain_profile.get("mid_horizon", 0.0)), 4),
                    "Long Horizon": round(float(brain_profile.get("long_horizon", 0.0)), 4),
                    "Growth": round(float(brain_profile.get("growth_index", 0.0)), 4),
                    "Maturity": round(float(brain_profile.get("maturity_index", 0.0)), 4),
                    "Softening": round(float(brain_profile.get("softening_factor", 0.0)), 4),
                }
            ],
            use_container_width=True,
            hide_index=True,
        )
    if brain_catalog:
        rows = []
        for horizon, entries in brain_catalog.items():
            if isinstance(entries, dict):
                for key, desc in entries.items():
                    rows.append({"Horizon": horizon, "Variable": key, "Description": str(desc)})
        if rows:
            st.caption("Tracked brain variables")
            st.dataframe(rows, use_container_width=True, hide_index=True)
    if training_variables:
        st.caption("Training variables (size / position / success monitors)")
        st.dataframe(
            [{k: round(float(v), 4) if isinstance(v, (int, float)) else v for k, v in training_variables.items()}],
            use_container_width=True,
            hide_index=True,
        )

cpp1, cpp2, cpp3 = st.columns(3)
cpp_available = bool(cpp_kernel.get("available", False)) if not cpp_kernel_err else False
cpp1.metric("C++ Brain Kernel", "Active" if cpp_available else "Fallback")
cpp2.metric("Chaos + Gaussian", "On" if cpp_available else "Degraded")
cpp3.metric("KNAA/GNAA Core", "Native" if cpp_available else "Python")
if cpp_kernel_err:
    st.caption(f"C++ kernel status pending: {cpp_kernel_err}")
else:
    st.caption(f"C++ library: {cpp_kernel.get('library_path', 'n/a')}")

st.subheader("Knowledge Mesh + Long-Term Compression")
if mesh_err:
    st.caption(f"Knowledge mesh pending: {mesh_err}")
else:
    summary = knowledge_mesh.get("summary", {})
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Mesh Links", str(int(summary.get("link_count", 0))))
    m2.metric("Mesh Paths", str(int(summary.get("unique_paths", 0))))
    m3.metric("Task Families", str(int(summary.get("task_families", 0))))
    m4.metric("Avg Confidence", f"{float(summary.get('avg_confidence', 0.0)):.3f}")
    latest_links = knowledge_mesh.get("links", [])[:8]
    if latest_links:
        st.dataframe(
            [
                {
                    "Source": item.get("source_agent"),
                    "Target": item.get("target_agent"),
                    "Task": item.get("task_family"),
                    "Weight": round(float(item.get("weight", 0.0)), 4),
                    "Confidence": round(float(item.get("confidence", 0.0)), 4),
                    "Shape3D": ", ".join(f"{float(v):.3f}" for v in item.get("shape3d", [0.0, 0.0, 0.0])),
                }
                for item in latest_links
            ],
            use_container_width=True,
            hide_index=True,
        )

mode = st.radio("Training Mode (4 modes)", list(OPERATION_MODES.keys()), horizontal=True, key="ctl_operation_mode")
mode_cfg = OPERATION_MODES.get(mode, {})
max_mode = mode in ("Intensive Throughput", "Learning Depth")
x5_brain_pack = st.checkbox("Enable Ultimate Brain X5 Pack", key="ctl_x5_brain_pack")
x6_learning_pack = st.checkbox("Enable Hermes X6 Learning Plus", key="ctl_x6_learning_pack")
auto_x10_setup = st.checkbox("Auto setup X10 (training + brain + SQL)", key="ctl_auto_x10_setup")
both_sides_training = st.checkbox("Both-sides training active", key="ctl_both_sides_training")
st.caption("Hermes sizes: mini units focus speed; full-size units focus deep reasoning and retention.")
st.markdown(
    f"**Best fit guidance:** {mode_cfg.get('description', 'Balanced operation profile.')} "
    f"Recommended Hermes type: **{_all_hermes_presets().get(str(mode_cfg.get('recommended_type', 'hybrid-core')), {}).get('title', 'Hybrid')}**."
)
st.markdown(
    "- **Programming + C++:** use for heavy compile/debug/refactor loops; favors deeper reasoning and structure.\n"
    "- **GUI + Visual:** use for Streamlit/UI flow and smooth visuals; favors mesh collaboration and visual iteration.\n"
    "- **Intensive Throughput:** use for large parallel workloads and mass operations; favors swarm speed.\n"
    "- **Learning Depth:** use for long-horizon retention and adaptive growth; favors gaussian smoothing + memory quality."
)
if st.button("Enable Ultimate + All Options (X5/X6/Smart/AIHub)", use_container_width=True):
    st.session_state["ctl_operation_mode"] = "Programming + C++"
    st.session_state["ctl_hermes_type"] = "ultimate-ml-x5"
    st.session_state["ctl_x5_brain_pack"] = True
    st.session_state["ctl_x6_learning_pack"] = True
    st.session_state["ctl_auto_x10_setup"] = True
    st.session_state["ctl_both_sides_training"] = True
    st.session_state["ctl_study_areas"] = ["Security", "Optimization", "AIHub", "Fleet Topology", "Learning Retention", "Truth & Safety", "Internet Signals", "Cost Efficiency"]
    st.session_state["ctl_smart_tools"] = list(SMART_TOOL_CATALOG.keys())
    st.success("Ultimate stack enabled with all options, smart tools, and deep learning settings.")
    st.rerun()
if x5_brain_pack:
    st.info(
        "X5 pack enabled: training pulses, candidate search, and brain-horizon learning are multiplied for maximum depth. "
        "Best type: Ultimate ML X5 or Ultimate AIHub Fusion."
    )
    if st.button("Apply Ultimate ML X5 Type + Brain Setup", use_container_width=True):
        x5_preset = _all_hermes_presets().get("ultimate-ml-x5", {})
        auto_x5 = _optimized_settings(x5_preset, str(st.session_state.get("ctl_hermes_species", "Hybrid")))
        st.session_state["ctl_hermes_type"] = "ultimate-ml-x5"
        st.session_state["ctl_swarm_strategy"] = str(x5_preset.get("swarm_strategy", "multipolar"))
        st.session_state["ctl_micro_agents"] = int(max(16, min(256, int(auto_x5.get("micro_agents", 252)))))
        st.session_state["ctl_gaussian_pressure"] = float(max(0.40, min(1.00, float(auto_x5.get("gaussian_pressure", 0.96)))))
        st.session_state["ctl_high_level_learning"] = float(max(0.0, min(1.0, float(auto_x5.get("high_level_learning", 0.98)))))
        st.session_state["ctl_techniques"] = [str(t) for t in x5_preset.get("techniques", st.session_state.get("ctl_techniques", []))]
        st.success("Ultimate ML X5 type + brain setup applied.")
        st.rerun()
if x6_learning_pack:
    st.caption("X6 Learning Plus is ON: inherits Hermes/X5 stack and adds deeper long-horizon learning extension.")
if auto_x10_setup:
    st.caption("Auto X10 setup keeps training, brain, and SQL optimization pipelines warm automatically.")
if both_sides_training:
    st.caption("Both-sides training is ON: offensive and defensive learning signals are trained together.")

study_areas = st.multiselect(
    "Study Areas",
    ["Security", "Optimization", "AIHub", "Movies & Media", "Fleet Topology", "Learning Retention", "Truth & Safety", "Internet Signals", "Cost Efficiency"],
    key="ctl_study_areas",
)
with st.expander("Advanced Intelligence Techniques"):
    techniques = st.multiselect(
        "Techniques",
        [
            "KNAA/QNAA reasoning",
            "Quantized compression",
            "Multi-parallel swarm",
            "Multipolar ensemble",
            "Natural pressure adaptation",
            "GNAA adaptive memory",
            "Chaos engine trials",
            "Gaussian 3D evidence",
            "C++ neural kernel boost",
            "Sub-agent niche shaping",
            "Cross-agent communication mesh",
        ],
        key="ctl_techniques",
    )
    swarm_strategy = st.selectbox("Swarm strategy", ["normal", "hybrid", "swarm", "mesh", "multipolar", "specialist-mix"], key="ctl_swarm_strategy")
    st.caption("Type guide: normal=stable baseline, hybrid=balanced, swarm=parallel speed, mesh=collaboration depth, multipolar=diverse reasoning, specialist-mix=niche experts.")
    micro_agents = st.slider("Micro Hermes agents", min_value=16, max_value=256, step=16, key="ctl_micro_agents")
    st.caption("Micro agents ideal range: 96-224 for heavy learning; 48-128 for cost-sensitive runs.")
    gaussian_pressure = st.slider("Gaussian learning pressure", min_value=0.40, max_value=1.00, step=0.02, key="ctl_gaussian_pressure")
    st.caption("Gaussian pressure ideal range: 0.70-0.92 for stable growth; >0.92 is aggressive exploration.")
    permanent_intelligence = st.checkbox("Permanent intelligence memory mode", key="ctl_permanent_intelligence")
    st.caption("Permanent intelligence keeps long-horizon memory, affecting all future training cycles.")
    high_level_learning = st.slider(
        "High-level learning focus (performance -> long-term learning)",
        min_value=0.0,
        max_value=1.0,
        step=0.01,
        key="ctl_high_level_learning",
    )
    st.caption("High-level learning ideal range: 0.65-0.88 for best blend of performance + long-term adaptation.")
    render_variable_guide()
st.markdown("#### Smart Skills + Tools")
smart_tools = st.multiselect(
    "Enable smart operational tools",
    list(SMART_TOOL_CATALOG.keys()),
    key="ctl_smart_tools",
)
st.caption(
    "Smart stack active: "
    f"{', '.join(smart_tools) if smart_tools else 'none'} | "
    "Recommended for max setup: chaos-engine-lab + multi-parallel-orchestrator + brain-fusion-monitor."
)
st.markdown(
    "<div style='font-family:Segoe UI, Inter, Arial; font-size:1.05rem; font-weight:700; color:#dff3ff;'>"
    "Smart Tool Architecture (20 integrated tools)</div>",
    unsafe_allow_html=True,
)
tool_rows: List[Dict[str, str]] = []
for tool_key in list(SMART_TOOL_CATALOG.keys()):
    meta = SMART_TOOL_CATALOG.get(tool_key, {})
    tool_rows.append(
        {
            "Tool": tool_key,
            "Ideal for": str(meta.get("focus", "")),
            "Description": str(meta.get("desc", "")),
            "LLM bonus connection": str(meta.get("llm_bonus", "")),
            "How splitting works": str(meta.get("split", "")),
            "Enabled": "Yes" if tool_key in smart_tools else "No",
        }
    )
st.dataframe(tool_rows, use_container_width=True, hide_index=True)
st.markdown("#### Ultimate Built-In Guide (clear stack view)")
ultimate_guide_rows = [
    {
        "Layer": "Ultimate ML X5",
        "Status": "Enabled" if bool(st.session_state.get("ctl_x5_brain_pack", False)) else "Available",
        "Best for": "maximum deep learning + brain growth",
        "Recommended action": "Apply Ultimate ML X5 Type + Brain Setup",
    },
    {
        "Layer": "Programming + C++",
        "Status": "Active" if str(st.session_state.get("ctl_operation_mode", "Programming + C++")) == "Programming + C++" else "Ready",
        "Best for": "intensive compile/debug/refactor workloads",
        "Recommended action": "Set mode to Programming + C++ for heavy engineering runs",
    },
    {
        "Layer": "Smart tools architecture",
        "Status": f"{len(st.session_state.get('ctl_smart_tools', []))} selected",
        "Best for": "automation, split routing, and fleet coordination",
        "Recommended action": "Keep chaos-engine + multi-parallel + brain-fusion enabled",
    },
    {
        "Layer": "AIHub bonus + Multi-LLM",
        "Status": "Integrated",
        "Best for": "blended reasoning quality and specialization routing",
        "Recommended action": "Use AIHub Next-Level upgrade for higher LLM blend pressure",
    },
    {
        "Layer": "Clear SQL center",
        "Status": "Integrated",
        "Best for": "storage visibility and evidence confidence",
        "Recommended action": "Use SQL Center one-click setup and design bars",
    },
    {
        "Layer": "Deep learning + brain system",
        "Status": "Integrated",
        "Best for": "long-horizon retention and adaptive memory",
        "Recommended action": "Enable X6 Learning Plus + Auto X10 setup",
    },
]
st.dataframe(ultimate_guide_rows, use_container_width=True, hide_index=True)
st.caption("C++ intensive default recommendation: Programming + C++ mode + Ultimate ML X5 + chaos-engine/multi-parallel/brain-fusion tools.")
with st.expander("Full Hermes Guide (complete quick-reference)", expanded=False):
    st.dataframe(
        [
            {"Step": "1) Pick operation mode", "What to choose": "Programming + C++ for intensive engineering, GUI + Visual for UX polish", "Why it matters": "Sets learning profile, swarm behavior, and pressure deltas"},
            {"Step": "2) Choose Hermes type", "What to choose": "Ultimate ML X5 or Ultimate AIHub Fusion for max depth", "Why it matters": "Defines base strategy, techniques, and specialization identity"},
            {"Step": "3) Enable deep brain packs", "What to choose": "X5 brain pack + X6 learning plus + both-sides training", "Why it matters": "Boosts long-horizon retention and dual-signal adaptation"},
            {"Step": "4) Turn on smart tools", "What to choose": "chaos-engine-lab, multi-parallel-orchestrator, brain-fusion-monitor (+ others as needed)", "Why it matters": "Adds split routing, automation quality, and advanced coordination"},
            {"Step": "5) Run SQL center setup", "What to choose": "One-Click setup, then Ultimate upgrade, then snapshot", "Why it matters": "Stabilizes volume-backed learning evidence and clear SQL telemetry"},
            {"Step": "6) Use AIHub multi-LLM blend", "What to choose": "Reasoning lane for C++, UI/UX lane for visual flow, Security lane for guardrails", "Why it matters": "Improves output quality by specialization-aware model routing"},
            {"Step": "7) Keep auto-learning active", "What to choose": "Auto X10 + periodic pulse/deploy/return cycles", "Why it matters": "Maintains continuous training, adaptation, and fleet readiness"},
        ],
        use_container_width=True,
        hide_index=True,
    )
    st.caption("Best overall preset: use the 'Enable Ultimate + All Options' button, then run SQL Center setup and AIHub next-level upgrade.")

st.markdown("#### X-Everything Smart Mix Guide (best settings by project)")
smart_mix_catalog: Dict[str, Dict[str, Any]] = {
    "Best overall project mix": {
        "mode": "Programming + C++",
        "type": "ultimate-ml-x5",
        "swarm": "multipolar",
        "micro_agents": 224,
        "gaussian_pressure": 0.90,
        "high_level_learning": 0.88,
        "study_areas": ["Security", "Optimization", "AIHub", "Fleet Topology", "Learning Retention", "Truth & Safety", "Cost Efficiency"],
        "tools": ["chaos-engine-lab", "multi-parallel-orchestrator", "brain-fusion-monitor", "sql-pattern-lens", "deployment-flow-router", "security-sentinel"],
        "why": "Best blend for C++ intensity, deep learning, reliable SQL, and safe deployment.",
    },
    "C++ intensive + performance": {
        "mode": "Programming + C++",
        "type": "quantum-cpp-mesh",
        "swarm": "swarm",
        "micro_agents": 240,
        "gaussian_pressure": 0.82,
        "high_level_learning": 0.78,
        "study_areas": ["Optimization", "AIHub", "Fleet Topology", "Cost Efficiency"],
        "tools": ["multi-parallel-orchestrator", "quantized-compression-engine", "parallel-compile-shaper", "llm-latency-balancer", "deployment-flow-router"],
        "why": "Pushes throughput and compile speed while keeping model routing efficient.",
    },
    "UI/UX + SQL clarity": {
        "mode": "GUI + Visual",
        "type": "visual-ux-oracle",
        "swarm": "mesh",
        "micro_agents": 160,
        "gaussian_pressure": 0.74,
        "high_level_learning": 0.84,
        "study_areas": ["AIHub", "Learning Retention", "Movies & Media", "Truth & Safety"],
        "tools": ["ux-clarity-orchestrator", "sql-pattern-lens", "signal-art-synthesizer", "llm-style-harmonizer", "brain-fusion-monitor"],
        "why": "Cleaner interface behavior, stronger SQL visuals, and stable user-facing flow.",
    },
    "Security + reliability": {
        "mode": "Learning Depth",
        "type": "security-fortress-core",
        "swarm": "specialist-mix",
        "micro_agents": 192,
        "gaussian_pressure": 0.86,
        "high_level_learning": 0.92,
        "study_areas": ["Security", "Truth & Safety", "Learning Retention", "Internet Signals"],
        "tools": ["security-sentinel", "truth-safety-guardian", "chaos-engine-lab", "memory-integrity-auditor", "deployment-flow-router"],
        "why": "Prioritizes hardening, safe decisions, and resilient long-horizon behavior.",
    },
}
st.dataframe(
    [
        {
            "Mix": name,
            "Mode": str(cfg.get("mode", "")),
            "Type": str(cfg.get("type", "")),
            "Swarm": str(cfg.get("swarm", "")),
            "Micro agents": int(cfg.get("micro_agents", 160)),
            "Gaussian": float(cfg.get("gaussian_pressure", 0.80)),
            "High-level learning": float(cfg.get("high_level_learning", 0.72)),
            "Why this mix": str(cfg.get("why", "")),
        }
        for name, cfg in smart_mix_catalog.items()
    ],
    use_container_width=True,
    hide_index=True,
)
mix_choice = st.selectbox("Choose smart project mix", list(smart_mix_catalog.keys()), key="ctl_smart_mix_choice")
mix_cfg = smart_mix_catalog.get(mix_choice, {})
st.caption(f"Smart recommendation: {mix_cfg.get('why', 'Balanced operating profile.')}")
if st.button("Apply Selected Smart Mix", use_container_width=True):
    st.session_state["ctl_operation_mode"] = str(mix_cfg.get("mode", "Programming + C++"))
    st.session_state["ctl_hermes_type"] = str(mix_cfg.get("type", "ultimate-ml-x5"))
    st.session_state["ctl_swarm_strategy"] = str(mix_cfg.get("swarm", "hybrid"))
    st.session_state["ctl_micro_agents"] = int(max(16, min(256, int(mix_cfg.get("micro_agents", 160)))))
    st.session_state["ctl_gaussian_pressure"] = float(max(0.40, min(1.00, float(mix_cfg.get("gaussian_pressure", 0.80)))))
    st.session_state["ctl_high_level_learning"] = float(max(0.0, min(1.0, float(mix_cfg.get("high_level_learning", 0.72)))))
    st.session_state["ctl_study_areas"] = list(mix_cfg.get("study_areas", []))
    st.session_state["ctl_smart_tools"] = [t for t in list(mix_cfg.get("tools", [])) if t in SMART_TOOL_CATALOG]
    st.session_state["ctl_x5_brain_pack"] = True
    st.session_state["ctl_x6_learning_pack"] = True
    st.session_state["ctl_both_sides_training"] = True
    st.success(f"Applied smart mix: {mix_choice}")
    st.rerun()

st.subheader("Activity Goal Profile (Fast User Controls)")
entry_defaults = default_user_entry_profile()
goal_profile = st.selectbox(
    "Goal character",
    ["balanced", "speed", "safe", "cost"],
    index=["balanced", "speed", "safe", "cost"].index(str(entry_defaults.get("goal_profile", "balanced"))),
    key="ctl_goal_profile",
)
success_priority = st.slider(
    "Success priority",
    min_value=0.0,
    max_value=1.0,
    value=float(entry_defaults.get("success_priority", 0.72)),
    step=0.01,
    key="ctl_success_priority",
)
wrongness_tolerance = st.slider(
    "Wrongness tolerance",
    min_value=0.0,
    max_value=1.0,
    value=float(entry_defaults.get("wrongness_tolerance", 0.22)),
    step=0.01,
    key="ctl_wrongness_tolerance",
)
group_preference = st.slider(
    "Group analysis weight",
    min_value=0.0,
    max_value=1.0,
    value=float(entry_defaults.get("group_preference", 0.58)),
    step=0.01,
    key="ctl_group_preference",
)
solo_preference = st.slider(
    "Solo analysis weight",
    min_value=0.0,
    max_value=1.0,
    value=float(entry_defaults.get("solo_preference", 0.42)),
    step=0.01,
    key="ctl_solo_preference",
)
dynamic_response = st.slider(
    "Dynamic monitor response",
    min_value=0.0,
    max_value=1.0,
    value=float(entry_defaults.get("dynamic_response", 0.62)),
    step=0.01,
    key="ctl_dynamic_response",
)
activity_profile = {
    "goal_profile": goal_profile,
    "success_priority": success_priority,
    "wrongness_tolerance": wrongness_tolerance,
    "group_preference": group_preference,
    "solo_preference": solo_preference,
    "dynamic_response": dynamic_response,
    "both_sides_training": bool(st.session_state.get("ctl_both_sides_training", True)),
    "x6_learning_pack": bool(st.session_state.get("ctl_x6_learning_pack", True)),
    "smart_tools": list(st.session_state.get("ctl_smart_tools", [])),
}
if st.button("Apply Activity Profile Now", use_container_width=True):
    run_logged_post_action(
        label="gui-activity-profile",
        path="/ingest-signal",
        payload={
            "source": "gui_activity_profile",
            "signal_score": max(0.0, min(1.0, success_priority * 0.7 + (1.0 - wrongness_tolerance) * 0.3)),
            "payload": activity_profile,
            "both_sides_training": bool(st.session_state.get("ctl_both_sides_training", True)),
        },
        success_message="Activity profile applied to active brain.",
        error_prefix="Activity profile push failed",
        timeout=60,
    )

technique_profile = build_technique_profile(
    techniques=techniques,
    swarm_strategy=swarm_strategy,
    micro_agents=micro_agents,
    gaussian_pressure=gaussian_pressure,
    permanent_intelligence=permanent_intelligence,
    high_level_learning=high_level_learning,
)
mode_cfg = OPERATION_MODES.get(str(st.session_state.get("ctl_operation_mode", "Programming + C++")), {})
technique_profile["swarm_strategy"] = str(mode_cfg.get("swarm", technique_profile.get("swarm_strategy", "hybrid")))
technique_profile["micro_agents"] = int(max(16, min(256, int(technique_profile.get("micro_agents", 160)) + int(mode_cfg.get("agents_delta", 0)))))
technique_profile["gaussian_pressure"] = float(max(0.40, min(1.00, float(technique_profile.get("gaussian_pressure", 0.80)) + float(mode_cfg.get("gaussian_delta", 0.0)))))
technique_profile["high_level_learning"] = float(max(0.0, min(1.0, float(technique_profile.get("high_level_learning", 0.72)) + float(mode_cfg.get("learning_delta", 0.0)))))
if bool(st.session_state.get("ctl_x5_brain_pack", False)):
    technique_profile["micro_agents"] = int(max(16, min(256, int(technique_profile.get("micro_agents", 160)) + 40)))
    technique_profile["gaussian_pressure"] = float(max(0.40, min(1.00, float(technique_profile.get("gaussian_pressure", 0.80)) + 0.06)))
    technique_profile["high_level_learning"] = float(max(0.0, min(1.0, float(technique_profile.get("high_level_learning", 0.72)) + 0.14)))
    extra_techniques = list(technique_profile.get("techniques", []))
    if "X5 brain fusion pipeline" not in extra_techniques:
        extra_techniques.append("X5 brain fusion pipeline")
    technique_profile["techniques"] = extra_techniques[:8]
if bool(st.session_state.get("ctl_x6_learning_pack", True)):
    technique_profile["micro_agents"] = int(max(16, min(256, int(technique_profile.get("micro_agents", 160)) + 24)))
    technique_profile["gaussian_pressure"] = float(max(0.40, min(1.00, float(technique_profile.get("gaussian_pressure", 0.80)) + 0.03)))
    technique_profile["high_level_learning"] = float(max(0.0, min(1.0, float(technique_profile.get("high_level_learning", 0.72)) + 0.08)))
    extra_techniques = list(technique_profile.get("techniques", []))
    if "X6 learning extension" not in extra_techniques:
        extra_techniques.append("X6 learning extension")
    technique_profile["techniques"] = extra_techniques[:10]
if bool(st.session_state.get("ctl_auto_x10_setup", True)):
    if "auto_x10_setup_done" not in st.session_state:
        st.session_state["auto_x10_setup_done"] = False
    if not bool(st.session_state.get("auto_x10_setup_done", False)):
        _, auto_err = safe_post(
            "/learning-pulse",
            {
                "specialty": "fleet:auto-x10-setup",
                "steps": 680,
                "candidates": 380,
                "both_sides_training": bool(st.session_state.get("ctl_both_sides_training", True)),
                "x6_learning_pack": bool(st.session_state.get("ctl_x6_learning_pack", True)),
                "sql_signal": 0.97,
                "internet_signal": 0.06 if not OFFLINE_ONLY_MODE else 0.0,
                "llm_signal": 0.95,
                "stability_bias": 0.91,
            },
            timeout=120,
        )
        if auto_err:
            st.warning(f"Auto X10 setup pending: {auto_err}")
        else:
            st.session_state["auto_x10_setup_done"] = True
            st.success("Auto X10 setup applied for training + brain + SQL.")
st.caption(
    "Active upgrades: "
    f"{', '.join(technique_profile['techniques']) if technique_profile['techniques'] else 'standard'} | "
    f"swarm={technique_profile['swarm_strategy']} | micro_agents={technique_profile['micro_agents']} | "
    f"high_level_learning={technique_profile['high_level_learning']:.2f}"
)
st.caption("Agent skill system: 25 total skills, 3 active skills per Hermes unit.")
if "Movies & Media" in study_areas:
    st.caption("Movies/media domain is active: AIHub movie bonus + mesh learning ingestion enabled.")

learned_profile = latest_learned_profile(snapshot)
sync1, sync2, sync3 = st.columns([1.1, 1.1, 2.2])
with sync1:
    if st.button("Send GUI Profile to Fleet", use_container_width=True):
        gui_sync_payload = {
            "source": "gui_profile",
            "signal_score": max(0.0, min(1.0, 0.55 + (technique_profile["high_level_learning"] * 0.25))),
            "payload": {
                "swarm_strategy": technique_profile["swarm_strategy"],
                "micro_agents": technique_profile["micro_agents"],
                "gaussian_pressure": technique_profile["gaussian_pressure"],
                "high_level_learning": technique_profile["high_level_learning"],
                "activity_profile": activity_profile,
                "techniques": technique_profile["techniques"],
                "study_areas": study_areas,
                "both_sides_training": bool(st.session_state.get("ctl_both_sides_training", True)),
                "x6_learning_pack": bool(st.session_state.get("ctl_x6_learning_pack", True)),
                "smart_tools": list(st.session_state.get("ctl_smart_tools", [])),
            },
        }
        _, sync_err = safe_post("/ingest-signal", gui_sync_payload, timeout=60)
        if sync_err:
            st.error(f"Sync failed: {sync_err}")
        else:
            st.success("GUI profile synced to fleet memory.")
with sync2:
    if st.button("Apply Fleet Learned Profile", use_container_width=True):
        if learned_profile:
            st.session_state["ctl_swarm_strategy"] = str(learned_profile.get("swarm_strategy", learned_profile.get("strategy", st.session_state["ctl_swarm_strategy"])))
            micro_val = learned_profile.get("micro_agents", st.session_state["ctl_micro_agents"])
            if isinstance(micro_val, (int, float)):
                st.session_state["ctl_micro_agents"] = int(max(16, min(256, micro_val)))
            gp_val = learned_profile.get("gaussian_pressure", learned_profile.get("dynamic_chaos", st.session_state["ctl_gaussian_pressure"]))
            if isinstance(gp_val, (int, float)):
                st.session_state["ctl_gaussian_pressure"] = float(max(0.40, min(1.00, gp_val)))
            hll_val = learned_profile.get("high_level_learning", st.session_state["ctl_high_level_learning"])
            if isinstance(hll_val, (int, float)):
                st.session_state["ctl_high_level_learning"] = float(max(0.0, min(1.0, hll_val)))
            if isinstance(learned_profile.get("techniques"), list) and learned_profile.get("techniques"):
                st.session_state["ctl_techniques"] = [str(t) for t in learned_profile["techniques"][:6]]
            st.success("Fleet learned profile applied to GUI controls.")
            st.rerun()
        else:
            st.warning("No learned profile found in recent fleet signals.")
with sync3:
    if learned_profile:
        st.caption(
            f"Carryover active: strategy={learned_profile.get('swarm_strategy', learned_profile.get('strategy', 'hybrid'))}, "
            f"high_level_learning={float(learned_profile.get('high_level_learning', 0.0)):.2f}"
        )
    else:
        st.caption("Carryover ready: run an auto cycle to generate learned profile signals.")

st.subheader("Data I/O + Fleet Command Center")
st.markdown(
    "- **Get data** = read-only pull from runtime (snapshot/training/brain status) so you can inspect current state.\n"
    "- **Send data** = write/command push to runtime (signals/deploy/return) so fleet behavior changes immediately."
)
io1, io2, io3, io4 = st.columns(4)
with io1:
    if st.button("Get Fleet Data", use_container_width=True):
        pulled, pull_err = safe_get("/snapshot", timeout=30)
        if pull_err:
            st.error(f"Get fleet data failed: {pull_err}")
        else:
            st.session_state["io_last_data"] = pulled
            st.success("Fleet snapshot loaded.")
with io2:
    if st.button("Get Training + Brain Data", use_container_width=True):
        train_data, train_err = safe_get("/training-status", timeout=30)
        growth_io, growth_io_err = safe_get("/growth-maturity", timeout=40)
        if train_err or growth_io_err:
            st.error(f"Get training/brain data failed: {train_err or growth_io_err}")
        else:
            st.session_state["io_last_data"] = {"training_status": train_data, "growth_maturity": growth_io}
            st.success("Training + brain data loaded.")
with io3:
    if st.button("Send Data Signal", use_container_width=True):
        send_payload = {
            "source": "gui_data_io_send",
            "signal_score": max(0.0, min(1.0, 0.55 + float(technique_profile.get("high_level_learning", 0.0)) * 0.35)),
            "payload": {
                "mode": str(st.session_state.get("ctl_operation_mode", "Programming + C++")),
                "swarm_strategy": str(technique_profile.get("swarm_strategy", "hybrid")),
                "micro_agents": int(technique_profile.get("micro_agents", 160)),
                "gaussian_pressure": float(technique_profile.get("gaussian_pressure", 0.8)),
                "high_level_learning": float(technique_profile.get("high_level_learning", 0.72)),
                "x5_brain_pack": bool(st.session_state.get("ctl_x5_brain_pack", False)),
                "x6_learning_pack": bool(st.session_state.get("ctl_x6_learning_pack", True)),
                "both_sides_training": bool(st.session_state.get("ctl_both_sides_training", True)),
                "smart_tools": list(st.session_state.get("ctl_smart_tools", [])),
            },
        }
        _, send_err = safe_post("/ingest-signal", send_payload, timeout=60)
        if send_err:
            st.error(f"Send data failed: {send_err}")
        else:
            st.success("Data signal sent to fleet.")
with io4:
    if st.button("Send Deploy + Return Cycle", use_container_width=True):
        deploy_result, deploy_err = safe_post(
            "/runtime-orchestrate/deploy",
            {"mode": "deploy", "scope": "batch", "batch_size": 12, "specialty": _specialty_base(), "steps": 260, "candidates": 180, "both_sides_training": bool(st.session_state.get("ctl_both_sides_training", True)), "x6_learning_pack": bool(st.session_state.get("ctl_x6_learning_pack", True))},
            timeout=120,
        )
        return_result, return_err = safe_post(
            "/runtime-orchestrate/return",
            {"mode": "return", "units": 12, "specialty": _specialty_base(), "reason": "gui-data-io-cycle", "both_sides_training": bool(st.session_state.get("ctl_both_sides_training", True)), "x6_learning_pack": bool(st.session_state.get("ctl_x6_learning_pack", True))},
            timeout=120,
        )
        if deploy_err or return_err:
            st.error(f"Deploy/return cycle failed: {deploy_err or return_err}")
        else:
            st.session_state["io_last_data"] = {"deploy": deploy_result, "return": return_result}
            st.success("Deploy + return cycle completed.")
if st.session_state.get("io_last_data") is not None:
    st.text_area("Last Data I/O Result", value=json.dumps(st.session_state.get("io_last_data"), indent=2)[:12000], height=240)

fleet_reward = pull_metric(snapshot, ("avg_reward_score", "reward_score", "reward"), default=0.0)
fleet_truth = pull_metric(snapshot, ("avg_truth_score", "truth_score", "truth"), default=0.0)
fleet_shape = pull_metric(snapshot, ("avg_fleet_shape_score", "fleet_shape_score"), default=0.0)
learning_depth = pull_metric(snapshot, ("learning_steps", "steps", "total_steps"), default=0.0)
fleet_score = max(0.0, min(100.0, ((fleet_reward * 0.35) + (fleet_truth * 0.35) + (fleet_shape * 0.30)) * 100.0))
growth_index = float(growth_data.get("growth_index", 0.0)) if not growth_err else 0.0
knowledge_depth = growth_data.get("knowledge_depth", {}) if isinstance(growth_data, dict) else {}
st.progress(float(max(0.0, min(1.0, avg_progress))), text=f"Fleet Progress: {avg_progress * 100:.1f}%")
g1, g2 = st.columns(2)
g1.metric("Fleet Score", f"{fleet_score:.1f}/100")
g2.metric("Hermes Growth", f"{growth_index * 100:.1f}%")
xp1, xp2, xp3, xp4 = st.columns(4)
with xp1:
    render_xp_bar("Learning XP", min(1.0, learning_depth / 1000.0), "#48C9B0")
with xp2:
    render_xp_bar("Reward XP", fleet_reward, "#58D68D")
with xp3:
    render_xp_bar("Truth XP", fleet_truth, "#5DADE2")
with xp4:
    render_xp_bar("Fleet Shape XP", fleet_shape, "#AF7AC5")

trend1, trend2 = st.columns(2)
with trend1:
    st.caption("AIHub bonus memory (recent)")
    bonus_tail = snapshot.get("aihub_bonus_memory_tail", [])[-20:]
    if bonus_tail:
        st.line_chart(bonus_tail)
with trend2:
    st.caption("Fleet score trend (recent)")
    score_tail = fleet_score_history(snapshot)
    if score_tail:
        st.line_chart(score_tail[-20:])
if isinstance(knowledge_depth, dict):
    st.caption(
        "Knowledge depth: "
        f"bandits={int(knowledge_depth.get('bandit_specialties', 0))} | "
        f"q_states={int(knowledge_depth.get('q_table_states', 0))} | "
        f"beta_priors={int(knowledge_depth.get('beta_priors', 0))} | "
        f"hard_facts={int(knowledge_depth.get('hard_facts', 0))} | "
        f"adaptive_channels={int(knowledge_depth.get('adaptive_dynamic_channels', 0))}"
    )
adaptive_mods = snapshot.get("adaptive_dynamic_modifiers", {}) if isinstance(snapshot, dict) else {}
if isinstance(adaptive_mods, dict) and adaptive_mods:
    st.caption(
        "Adaptive center: "
        f"range={adaptive_mods.get('moving_range_low', 0.0):.2f}-{adaptive_mods.get('moving_range_high', 1.0):.2f}, "
        f"confidence={adaptive_mods.get('confidence_signal', 0.0):.2f}, "
        f"modifier_gain={adaptive_mods.get('modifier_gain', 0.0):.2f}, "
        f"pivot_bias={adaptive_mods.get('pivot_bias', 0.0):.2f}"
    )

summary_left, summary_right = st.columns([2, 1])
with summary_left:
    st.subheader("Fleet Summary")
    st.write(
        f"- Reward quality: **{fleet_reward:.3f}**\n"
        f"- Truth and safety: **{fleet_truth:.3f}**\n"
        f"- Fleet shape signal: **{fleet_shape:.3f}**\n"
        f"- Learning depth: **{int(learning_depth)} steps**"
    )
with summary_right:
    st.subheader("Quick Actions")
    action_mode = st.radio("Action view", ["Simple", "Advanced"], horizontal=True, index=0)
    show_extended_actions = st.checkbox("Show extended deploy controls", value=False)
    deploy_batch = st.slider("Deploy batch size", min_value=1, max_value=50, value=10, step=1)
    st.caption("Simple view keeps the most-used controls only. Advanced view exposes full orchestration actions.")
    st.caption("These actions run immediately.")
    if st.button("Generate Fleet Health Report", use_container_width=True):
        report_prompt = (
            "Create a short fleet health report from current Hermes data with "
            "strengths, risks, and next optimization action."
        )
        chat, chat_err = safe_post(
            "/llm-chat",
            {
                "prompt": report_prompt,
                "system_prompt": "You are Hermes AIHub fleet analyst.",
                "model": _selected_model_override() or None,
                "temperature": 0.2,
                "max_tokens": 800,
            },
        )
        if chat_err:
            st.error(f"Report generation failed: {chat_err}")
        else:
            st.session_state["last_chat"] = chat.get("response_text", "")
            log_text("fleet-health-report", chat)
            st.success("Fleet health report generated.")
    if show_extended_actions:
        if st.button("🚀 Deploy Full Hermes Army", use_container_width=True):
            run_logged_post_action(
                label="deploy-all-hermes",
                path="/runtime-orchestrate/deploy",
                payload={
                    "mode": "deploy",
                    "scope": "all",
                    "batch_size": deploy_batch,
                    "specialty": _specialty_base(),
                    "steps": 240,
                    "candidates": 160,
                    "sql_signal": min(0.99, technique_profile["sql_signal"] + 0.05),
                    "internet_signal": 0.0 if OFFLINE_ONLY_MODE else technique_profile["internet_signal"],
                    "llm_signal": min(0.99, technique_profile["llm_signal"] + 0.05),
                    "stability_bias": min(0.99, technique_profile["stability_bias"] + 0.02),
                },
                success_message="All Hermes units deployed and synced.",
                error_prefix="Deploy orchestration failed",
                timeout=120,
            )
        if st.button("🚚 Deploy Hermes Army Batch", use_container_width=True):
            run_logged_post_action(
                label="deploy-batch-hermes",
                path="/runtime-orchestrate/deploy",
                payload={
                    "mode": "deploy",
                    "scope": "batch",
                    "batch_size": deploy_batch,
                    "specialty": _specialty_base(),
                    "steps": 180,
                    "candidates": max(80, deploy_batch * 6),
                    "sql_signal": min(0.99, technique_profile["sql_signal"] + 0.03),
                    "internet_signal": 0.0 if OFFLINE_ONLY_MODE else technique_profile["internet_signal"],
                    "llm_signal": min(0.99, technique_profile["llm_signal"] + 0.03),
                    "stability_bias": min(0.99, technique_profile["stability_bias"] + 0.02),
                },
                success_message=f"Batch deploy completed for {deploy_batch} Hermes units.",
                error_prefix="Batch deploy failed",
                timeout=120,
            )
        if st.button("↩️ Bring Hermes Army Back", use_container_width=True):
            run_logged_post_action(
                label="return-hermes",
                path="/runtime-orchestrate/return",
                payload={"mode": "return", "specialty": _specialty_base(), "units": deploy_batch, "reason": "gui-return-request", "confidence": 0.88},
                success_message=f"Return signal sent for {deploy_batch} Hermes units.",
                error_prefix="Return action failed",
                timeout=90,
            )
        if st.button("⚡ Permanent Bonus Boost", use_container_width=True):
            boost1, e1 = safe_post(
                "/curate-learning",
                {
                    "sql_signal": min(0.99, technique_profile["sql_signal"] + 0.04),
                    "internet_signal": 0.0 if OFFLINE_ONLY_MODE else (min(0.14, technique_profile["internet_signal"] + 0.01) if USER_ROUTED_INTERNET else min(0.99, technique_profile["internet_signal"] + 0.04)),
                    "llm_signal": min(0.99, technique_profile["llm_signal"] + 0.04),
                    "stability_bias": min(0.99, technique_profile["stability_bias"] + 0.03),
                },
                timeout=90,
            )
            boost2, e2 = safe_post("/dedupe-optimize", {"roots": ["core", "runtime", "src"], "max_file_mb": 8}, timeout=120)
            log_text("permanent-bonus-boost", {"curate_learning": boost1, "dedupe": boost2, "errors": [e1, e2]})
            st.success("Permanent bonus boost tools applied.")
    else:
        st.caption("Extended deploy controls are hidden for cleaner operation.")

if action_mode == "Simple":
    simple1, simple2, simple3 = st.columns(3)
    with simple1:
        if st.button("⚡ One Fusion Run", use_container_width=True):
            result = run_auto_cycle(max_mode=max_mode, technique=technique_profile)
            log_text("full-auto-cycle", result)
            st.success("Fusion run finished.")
    with simple2:
        if st.button("Refresh Fleet Data", use_container_width=True):
            snapshot, snapshot_err = safe_get("/snapshot", timeout=20)
            if snapshot_err:
                st.error(f"Fleet data refresh failed: {snapshot_err}")
            else:
                agent_rows = normalize_agents(snapshot, aihub_bonus)
                log_text("fleet-refresh", snapshot)
                st.success("Fleet data refreshed.")
    with simple3:
        if st.button("Quick Optimize", use_container_width=True):
            optimize, opt_err = safe_post(
                "/optimize-fleet",
                {"specialty": f"{_specialty_base()}:{technique_profile['swarm_strategy']}", "candidates": min(500, (480 if max_mode else 160) + int(technique_profile["micro_agents"] * 0.2))},
                timeout=120,
            )
            if opt_err:
                st.error(f"Optimize failed: {opt_err}")
            else:
                log_text("quick-optimize", optimize)
                st.success("Fleet optimization complete.")
else:
    act1, act2 = st.columns(2)
    with act1:
        if st.button("♾️ Deep Auto Learning Zone", use_container_width=True):
            deep = deep_auto_learning_zone(max_mode=max_mode, study_areas=study_areas, rounds=3 if max_mode else 2, technique=technique_profile)
            log_text("deep-auto-learning-zone", deep)
            st.success("Deep auto-learning completed.")
            st.text_area("Deep Learning Summary", value=json.dumps(deep, indent=2), height=260)
    with act2:
        if st.button("🛰️ Special Fleet Training", use_container_width=True):
            special = run_special_fleet_training(max_mode=max_mode, study_areas=study_areas, technique=technique_profile)
            log_text("special-fleet-training", special)
            st.success("Special fleet training completed.")
            st.text_area("Special Training Result", value=json.dumps(special, indent=2), height=260)

st.subheader("Automatic Learning Zone")
st.markdown(
    "Use this section for the easiest always-on training path: enable auto learning, keep intelligent shuffle on, and use 35-60s interval for stable growth."
)
auto_enabled = st.checkbox("Always run automatic smart learning", value=True)
auto_interval = st.slider("Auto interval (seconds)", min_value=20, max_value=300, value=45, step=5)
intelligent_shuffle = st.checkbox("Intelligent shuffle + adaptive profile each cycle", value=True)
if st.button("Apply Easy Auto Training Profile", use_container_width=True):
    st.session_state["ctl_operation_mode"] = "Learning Depth"
    st.session_state["ctl_x5_brain_pack"] = True
    st.session_state["ctl_x6_learning_pack"] = True
    st.session_state["ctl_auto_x10_setup"] = True
    st.session_state["ctl_both_sides_training"] = True
    st.session_state["ctl_hermes_type"] = "ultimate-ml-x5"
    st.success("Easy auto training profile applied.")
    st.rerun()
if "last_auto_run_ts" not in st.session_state:
    st.session_state["last_auto_run_ts"] = 0.0
now_ts = time.time()
if auto_enabled and (now_ts - float(st.session_state.get("last_auto_run_ts", 0.0))) >= auto_interval:
    auto_profile = dict(technique_profile)
    if intelligent_shuffle and learned_profile:
        learned_hll = float(learned_profile.get("high_level_learning", auto_profile["high_level_learning"]))
        auto_profile["high_level_learning"] = max(0.0, min(1.0, (auto_profile["high_level_learning"] * 0.65) + (learned_hll * 0.35)))
        if isinstance(learned_profile.get("swarm_strategy"), str):
            auto_profile["swarm_strategy"] = learned_profile["swarm_strategy"]
        if isinstance(learned_profile.get("micro_agents"), (int, float)):
            auto_profile["micro_agents"] = int(max(16, min(256, learned_profile["micro_agents"])))
    auto_result = run_auto_cycle(max_mode=max_mode, technique=auto_profile)
    safe_post(
        "/ingest-signal",
        {
            "source": "gui_auto_sync",
            "signal_score": max(0.0, min(1.0, 0.52 + (auto_profile["high_level_learning"] * 0.28))),
            "payload": {
                "swarm_strategy": auto_profile["swarm_strategy"],
                "micro_agents": auto_profile["micro_agents"],
                "gaussian_pressure": auto_profile["gaussian_pressure"],
                "high_level_learning": auto_profile["high_level_learning"],
                "techniques": auto_profile["techniques"],
                "mode": "auto_cycle",
            },
        },
        timeout=60,
    )
    log_text("automatic-learning-zone", auto_result)
    st.session_state["last_auto_run_ts"] = now_ts
    st.info("Automatic smart learning cycle executed.")
else:
    remaining = max(0, auto_interval - int(now_ts - float(st.session_state.get("last_auto_run_ts", 0.0))))
    st.caption(f"Next automatic cycle in ~{remaining}s")

st.subheader("Learning Space (text)")
prompt = st.text_area(
    "Ask Hermes AIHub",
    value="Summarize current fleet state and tell me the next best learning and optimization action.",
    height=120,
)
if st.button("Send to Hermes", use_container_width=True):
    chat, chat_err = safe_post(
        "/llm-chat",
        {
            "prompt": prompt,
            "system_prompt": "You are Hermes AIHub fleet learning assistant.",
            "model": _selected_model_override() or None,
            "temperature": 0.25,
            "max_tokens": 700,
        },
    )
    if chat_err:
        st.error(f"Hermes text request failed: {chat_err}")
    else:
        st.session_state["last_chat"] = chat.get("response_text", "")
        st.session_state["last_chat_optimizer"] = chat.get("provider_response", {}).get("multi_llm_optimizer", {})
        log_text("learning-space-chat", chat)
        st.success("Hermes response ready.")
if st.session_state.get("last_chat", ""):
    st.text_area("Hermes Learning Response", value=st.session_state["last_chat"], height=220)
    opt = st.session_state.get("last_chat_optimizer", {})
    if isinstance(opt, dict) and opt:
        st.caption(
            f"Multi-LLM optimizer: model={opt.get('selected_model')} | "
            f"blend={opt.get('blend_mode')} | "
            f"cost=${float(opt.get('estimated_cost_usd', 0.0)):.4f} | "
            f"speed={float(opt.get('estimated_tokens_per_sec', 0.0)):.1f} tok/s | "
            f"eff={float(opt.get('token_efficiency', 0.0)):.3f}"
        )
        model_rows = []
        for item in opt.get("candidates", []):
            name = str(item.get("model", "unknown"))
            tier = "mini" if "mini" in name else ("full" if "reasoning" in name or "max" in name else "balanced")
            description = (
                "fast lower-cost explorer"
                if tier == "mini"
                else ("deep high-power reasoner" if tier == "full" else "balanced general model")
            )
            model_rows.append(
                {
                    "Model": name,
                    "Tier": tier,
                    "Description": description,
                    "Blend": round(float(item.get("blend_score", 0.0)), 4),
                    "Speed tok/s": round(float(item.get("speed_tokens_per_sec", 0.0)), 1),
                    "Cost/1k": round(float(item.get("cost_per_1k_tokens", 0.0)), 4),
                }
            )
        if model_rows:
            st.caption("AIHub model lineup (mini vs full size):")
            st.dataframe(model_rows, use_container_width=True, hide_index=True)
st.caption("Prompt path: Prompt -> Hermes fleet agents -> learning pulse -> optimization -> bonus + XP")

st.subheader("Local Learning Data (easy)")
exp1, exp2, exp3 = st.columns([1.2, 1.2, 2.2])
with exp1:
    if st.button("Export Full Learning State", use_container_width=True):
        learning_state, ls_err = safe_get("/learning-state", timeout=30)
        if ls_err:
            st.error(f"Export failed: {ls_err}")
        else:
            st.session_state["learning_state_blob"] = json.dumps(learning_state, indent=2)
            st.success("Learning state exported.")
with exp2:
    if st.button("Import Learning State", use_container_width=True):
        raw = st.session_state.get("learning_state_blob", "").strip()
        if not raw:
            st.warning("Paste/export state JSON first.")
        else:
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as exc:
                st.error(f"Invalid JSON: {exc}")
            else:
                imp, imp_err = safe_post("/learning-state/import", parsed, timeout=45)
                if imp_err:
                    st.error(f"Import failed: {imp_err}")
                else:
                    st.success("Learning state imported.")
                    log_text("learning-state-import", imp)
with exp3:
    st.caption("Use this to move full Hermes learning memory locally between runs/machines.")
st.text_area("Learning State JSON", key="learning_state_blob", height=220)

st.subheader("Share to Chat / Export Bundle")
bundle_payload = {
    "snapshot": snapshot if isinstance(snapshot, dict) else {},
    "growth": growth_data if isinstance(growth_data, dict) else {},
    "training_status": training_status if isinstance(training_status, dict) else {},
    "knowledge_mesh_summary": knowledge_mesh.get("summary", {}) if isinstance(knowledge_mesh, dict) else {},
    "unified_config": unified if isinstance(unified, dict) else {},
}
bundle_json = json.dumps(bundle_payload, indent=2)
sb1, sb2 = st.columns([1.2, 2.0])
with sb1:
    st.download_button(
        "Download Hermes Bundle JSON",
        data=bundle_json.encode("utf-8"),
        file_name="hermes_bundle.json",
        mime="application/json",
        use_container_width=True,
    )
with sb2:
    st.caption("Use this bundle for easy sharing, analysis, and replay in other tools/conversations.")
st.text_area("Hermes Bundle (copy/paste here)", value=bundle_json, height=220)

st.subheader("Data Volume Explorer (easy pull + analysis)")
volume_root = resolve_volume_root()
vf1, vf2 = st.columns([2, 1])
with vf1:
    st.caption(f"Volume root: {volume_root}")
with vf2:
    file_limit = st.slider("Volume file rows", min_value=50, max_value=1200, value=300, step=50)
vf3, vf4 = st.columns([1, 1])
with vf3:
    if st.button("Initialize/Repair Volume Layout", use_container_width=True):
        root_out, manifest = initialize_volume_layout(volume_root)
        scan_volume_files.clear()
        read_sql_training_intelligence.clear()
        st.success(f"Volume layout ready at: {root_out}")
        log_text("volume-layout-init", manifest if isinstance(manifest, dict) else {"status": "ok"})
volume_rows = scan_volume_files(volume_root, limit=file_limit)
sql_intel = read_sql_training_intelligence(volume_root)
if not volume_rows:
    st.caption("No files found in volume root yet.")
else:
    summary = volume_health_summary(volume_rows)
    with vf4:
        st.metric("Volume Files", int(summary.get("file_count", 0.0)))
        st.metric("Volume Size (MB)", f"{summary.get('total_mb', 0.0):.2f}")
        st.metric("SQL Pattern", f"{float(sql_intel.get('pattern_score', 0.0)) * 100:.1f}%")
    st.dataframe(
        [
            {
                "Path": row["relative_path"],
                "Size (KB)": round(row["bytes"] / 1024.0, 2),
                "Modified": row["modified"],
            }
            for row in volume_rows
        ],
        use_container_width=True,
        hide_index=True,
    )
    selected_volume_file = st.selectbox(
        "Select volume file",
        options=[row["relative_path"] for row in volume_rows],
        index=0,
    )
    preview_bytes, preview_err = read_volume_file(volume_root, selected_volume_file)
    if preview_err:
        st.warning(preview_err)
    if preview_bytes:
        st.download_button(
            "Download Selected File",
            data=preview_bytes,
            file_name=os.path.basename(selected_volume_file),
            use_container_width=True,
        )
        try:
            preview_text = preview_bytes.decode("utf-8")
        except UnicodeDecodeError:
            preview_text = f"[binary preview] {len(preview_bytes)} bytes"
        st.text_area("Selected File Preview", value=preview_text[:120000], height=220)

render_sql_intelligence_panels(
    sql_intel=sql_intel if isinstance(sql_intel, dict) else {},
    render_xp_bar=render_xp_bar,
    run_logged_post_action=run_logged_post_action,
    high_level_learning=float(st.session_state.get("ctl_high_level_learning", 0.72)),
)

st.subheader("Hermes Fleet Units")
if snapshot_err:
    st.warning(f"Fleet snapshot unavailable: {snapshot_err}")
else:
    d1, d2, d3, d4, d5 = st.columns(5)
    d1.metric("Reward", f"{fleet_reward:.3f}")
    d2.metric("Truth", f"{fleet_truth:.3f}")
    d3.metric("Fleet Shape", f"{fleet_shape:.3f}")
    d4.metric("Hermes Amount", str(total_hermes), delta=f"runtime {runtime_hermes} | target {configured_hermes}")
    d5.metric("Learning Depth", str(int(learning_depth)))
    st.dataframe(
        [
            {
                "Unit": a["symbol"],
                "Hermes": a["name"],
                "Bonus": round(a["bonus"], 4),
                "Progress": f"{a['progress'] * 100:.1f}%",
                "Size": a["size_mode"],
                "Size Detail": a["size_description"],
                "Interaction": a["interaction"],
                "Zone": a["zone"],
                "Specialty": a["specialty"],
                "Thinking": (
                    "Pattern + SQL reasoning"
                    if "sql" in str(a["specialty"]).lower()
                    else ("Visual flow + clarity" if "gui" in str(a["specialty"]).lower() else ("Security guardrails" if "security" in str(a["specialty"]).lower() else "Adaptive fleet planning"))
                ),
                "Good At": (
                    "Data optimization"
                    if "sql" in str(a["specialty"]).lower()
                    else ("UI/UX polish" if "gui" in str(a["specialty"]).lower() else ("Defense + hardening" if "security" in str(a["specialty"]).lower() else "Orchestration + deployment"))
                ),
                "Skills(3)": ", ".join(a["skills"]),
                "Active": "Yes" if a["active"] else "No",
            }
            for a in agent_rows
        ],
        use_container_width=True,
        hide_index=True,
    )
    st.caption("Raw runtime data is hidden by default.")
    with st.expander("Show Raw Data (advanced)"):
        st.json(snapshot)

    st.subheader("Live Fleet Feed")
    st.caption(f"Hermes amount now: {total_hermes} (runtime {runtime_hermes} / target {configured_hermes})")
    recent_events = snapshot.get("recent_events", [])
    if recent_events:
        for event in recent_events[:8]:
            event_type = str(event.get("event_type", "event"))
            ts = float(event.get("ts", 0.0))
            payload = event.get("payload", {})
            st.markdown(f"**{event_type}**  \n`{ts:.0f}`")
            st.code(str(payload)[:900])
    else:
        st.caption("No recent events yet.")

st.subheader("Tips + Tools")
t1, t2, t3 = st.columns(3)
t1.info("Tip: Keep Near Max mode on for stronger fleet adaptation.")
t2.info("Tip: Use Study Areas to steer what Hermes learns next.")
t3.info("Tip: Run Permanent Bonus Boost after major changes.")

if not st.session_state["auto_boot_done"]:
    warm, warm_err = safe_post(
        "/learning-pulse",
        {
            "specialty": _specialty_base(),
            "steps": 260,
            "candidates": 180,
            "both_sides_training": bool(st.session_state.get("ctl_both_sides_training", True)),
            "x6_learning_pack": bool(st.session_state.get("ctl_x6_learning_pack", True)),
        },
        timeout=90,
    )
    if not warm_err:
        log_text("auto-boot-warmstart", warm)
        st.session_state["auto_boot_done"] = True
        st.info("Automatic warm-start completed.")
    else:
        st.warning("Automatic warm-start pending.")

with st.expander("Text Log"):
    for item in st.session_state.get("logs", []):
        st.code(f"{item['label']}: {item['payload']}")

if live_refresh:
    st.caption(f"Live refresh active: updating every {refresh_seconds}s")
    time.sleep(refresh_seconds)
    st.rerun()
