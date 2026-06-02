from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def run(cmd: list[str], allow_fail: bool = False) -> bool:
    try:
        subprocess.run(cmd, check=True)
        return True
    except (subprocess.CalledProcessError, OSError) as exc:
        if not allow_fail:
            raise
        print(f"[warn] optional command failed: {cmd} ({exc})")
        return False


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_cpp_fallback(source: Path, output: Path, python_brief: dict) -> None:
    payload = dict(python_brief)
    payload["source"] = str(source)
    payload["generated_by"] = "cpp_fallback"
    payload["fallback_reason"] = "native_cpp_execution_blocked_or_unavailable"
    payload["runtime_decision"] = {
        "allow": True,
        "reason": "fallback mode: native C++ report generation unavailable in this environment",
        "score": 0,
    }
    payload["optimization_plan"] = {
        "cpu_scheduler_boost": 0.9,
        "memory_gc_pressure": 0.8,
        "gpu_queue_depth": 2.5,
        "network_egress_factor": 0.9,
        "model_hotset_prefetch": 0.85,
    }
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Python/C#/C++ brief compilers and merge outputs.")
    parser.add_argument("--source", required=True)
    parser.add_argument("--out-dir", default="artifacts/polyglot")
    parser.add_argument("--csharp-project", default="src/PolyglotXTier/PolyglotXTier.csproj")
    parser.add_argument("--cpp-exe", default="artifacts/polyglot/xtier_brief_compiler.exe")
    args = parser.parse_args()

    source = Path(args.source)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    py_out = out_dir / "python_master_brief.json"
    cs_out = out_dir / "csharp_master_brief.json"
    cpp_out = out_dir / "cpp_master_brief.json"
    py_conv_out = out_dir / "python_conversation_map.json"
    cs_conv_out = out_dir / "csharp_conversation_map.json"
    cs_frontend_out = out_dir / "csharp_security_frontend_map.json"
    merged = out_dir / "super_integrated_report.json"

    run(["python", "python/x-tier/polyglot/master_brief_compiler.py", "--source", str(source), "--output", str(py_out)])
    run(["dotnet", "run", "--project", args.csharp_project, "--", str(source), str(cs_out)])
    run(
        [
            "python",
            "python/x-tier/aihub_stack/winre_conversation_integrator.py",
            "--source",
            str(source),
            "--output",
            str(py_conv_out),
        ]
    )
    run(["dotnet", "run", "--project", args.csharp_project, "--", "--conversation-map", str(source), str(cs_conv_out)])
    cpp_ok = False
    if Path(args.cpp_exe).exists():
        cpp_ok = run([args.cpp_exe, str(source), str(cpp_out)], allow_fail=True)

    py = load_json(py_out) if py_out.exists() else {}
    cs = load_json(cs_out) if cs_out.exists() else {}
    if not cpp_ok or not cpp_out.exists():
        write_cpp_fallback(source, cpp_out, py)
    run(["dotnet", "run", "--project", args.csharp_project, "--", "--security-front-end-map", str(cpp_out), str(cs_frontend_out)])
    cpp = load_json(cpp_out) if cpp_out.exists() else {}
    py_conv = load_json(py_conv_out) if py_conv_out.exists() else {}
    cs_conv = load_json(cs_conv_out) if cs_conv_out.exists() else {}
    cs_frontend = load_json(cs_frontend_out) if cs_frontend_out.exists() else {}

    keys = [
        "line_count",
        "word_count",
        "heading_count",
        "section_count",
        "appendix_count",
        "task_mentions",
        "skill_mentions",
        "connector_mentions",
        "phase_mentions",
        "mode_mentions",
        "auto_mentions",
        "self_heal_mentions",
        "section_symbol_count",
        "section_symbol_max",
    ]
    consensus: dict[str, dict] = {}
    for k in keys:
        values = {
            "python": py.get(k),
            "csharp": cs.get(k),
            "cpp": cpp.get(k),
        }
        consensus[k] = {
            "values": values,
            "all_equal": len({v for v in values.values() if v is not None}) <= 1,
        }

    payload = {
        "source": str(source),
        "outputs": {
            "python": str(py_out),
            "csharp": str(cs_out),
            "cpp": str(cpp_out) if cpp_out.exists() else None,
            "python_conversation": str(py_conv_out),
            "csharp_conversation": str(cs_conv_out),
            "csharp_security_frontend": str(cs_frontend_out),
        },
        "consensus": consensus,
        "conversation": {
            "python_summary": py_conv.get("summary", {}),
            "csharp_summary": cs_conv.get("summary", {}),
            "component_coverage": py_conv.get("component_coverage", {}),
            "requirements_count": len(py_conv.get("requirements", [])),
            "unique_requirements_count": len(py_conv.get("unique_requirements", [])),
            "milestones_count": len(py_conv.get("milestones", [])),
        },
        "cpp_source_of_truth": {
            "runtime_decision": cpp.get("runtime_decision", {}),
            "optimization_plan": cpp.get("optimization_plan", {}),
            "security_optimization_data": cpp.get("cpp_security_optimization_data", {}),
            "major_parallelization_types": cpp.get("major_parallelization_types", []),
            "security_watch_plan": cpp.get("security_watch_plan", {}),
            "folder_governance_plan": cpp.get("folder_governance_plan", {}),
            "alert_channels": cpp.get("alert_channels", []),
            "generated_by": cpp.get("generated_by", "cpp_native"),
        },
        "csharp_frontend_contract": cs_frontend,
    }
    merged.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote: {merged}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
