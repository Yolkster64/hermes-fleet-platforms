from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


COMPONENT_PATTERNS: dict[str, list[str]] = {
    "winre": [r"\bwinre\b", r"\breagentc\b", r"\bdism\b"],
    "vhdx": [r"\bvhdx\b", r"\bdev\s*drive\b", r"\bbitlocker\b", r"\brefs\b"],
    "security": [r"\bfirewall\b", r"\bentra\b", r"\bpurview\b", r"\bquarantine\b"],
    "networking": [r"\bport\b", r"\bproxy\b", r"\bvpn\b", r"\bethernet\b", r"\bwifi\b"],
    "ai_ml": [r"\bai\b", r"\bml\b", r"\bllm\b", r"\bmeta[- ]learning\b", r"\banomaly\b"],
    "runtime": [r"\bdocker\b", r"\bgui\b", r"\bapi\b", r"\bweb app\b", r"\bhermes\b", r"\baihub\b"],
    "optimization": [r"\bcpu\b", r"\bram\b", r"\bgpu\b", r"\bcompression\b", r"\bthroughput\b"],
}


def classify(text: str) -> list[str]:
    lowered = text.lower()
    tags: list[str] = []
    for tag, patterns in COMPONENT_PATTERNS.items():
        if any(re.search(pattern, lowered) for pattern in patterns):
            tags.append(tag)
    return tags


def parse_transcript(lines: list[str]) -> dict:
    turns: list[dict] = []
    current_role: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_role, current_lines
        if not current_role:
            return
        text = "\n".join(current_lines).strip()
        if text:
            turns.append(
                {
                    "role": current_role,
                    "text": text,
                    "tags": classify(text),
                }
            )
        current_role = None
        current_lines = []

    for raw in lines:
        line = raw.rstrip()
        if line == "You said":
            flush()
            current_role = "user"
            continue
        if line == "Copilot said":
            flush()
            current_role = "assistant"
            continue
        if current_role:
            current_lines.append(line)
    flush()

    user_turns = [t for t in turns if t["role"] == "user"]
    assistant_turns = [t for t in turns if t["role"] == "assistant"]

    requirements: list[dict] = []
    milestones: list[dict] = []
    requirement_frequency: dict[str, int] = {}
    for idx, turn in enumerate(user_turns, start=1):
        first = turn["text"].splitlines()[0][:200].strip()
        requirement_frequency[first] = requirement_frequency.get(first, 0) + 1
        requirements.append(
            {
                "id": f"req-{idx:03d}",
                "summary": first,
                "tags": turn["tags"],
            }
        )
    for idx, turn in enumerate(assistant_turns, start=1):
        first = turn["text"].splitlines()[0][:200]
        milestones.append(
            {
                "id": f"ms-{idx:03d}",
                "summary": first,
                "tags": turn["tags"],
            }
        )

    component_coverage = {k: 0 for k in COMPONENT_PATTERNS}
    for turn in turns:
        for tag in turn["tags"]:
            component_coverage[tag] += 1

    integration_map = {
        "python": [
            "python/x-tier/aihub_control_server.py",
            "python/x-tier/hermes_xcore/*",
            "python/x-tier/aihub_stack/*",
        ],
        "csharp": [
            "src/PolyglotXTier/Program.cs",
            "src/PolyglotXTier/IntegrationHost.cs",
        ],
        "cpp": [
            "cpp/x-tier/main.cpp",
            "cpp/x-tier/secure_runtime_core.*",
        ],
        "powershell": [
            "scripts/x-tier/Build-SuperSystem.ps1",
            "scripts/x-tier/Invoke-AIHubUpgrade.ps1",
            "runtime/hermes/docker-compose.yml",
        ],
    }

    return {
        "summary": {
            "total_turns": len(turns),
            "user_turns": len(user_turns),
            "assistant_turns": len(assistant_turns),
            "line_count": len(lines),
        },
        "component_coverage": component_coverage,
        "requirements": requirements,
        "unique_requirements": [
            {"summary": summary, "count": count}
            for summary, count in sorted(requirement_frequency.items(), key=lambda x: (-x[1], x[0]))
        ],
        "milestones": milestones,
        "integration_map": integration_map,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert WinRE transcript into AIHub integration artifacts.")
    parser.add_argument("--source", required=True, help="Path to transcript text file.")
    parser.add_argument("--output", required=True, help="Destination JSON artifact.")
    args = parser.parse_args()

    source = Path(args.source)
    output = Path(args.output)
    lines = source.read_text(encoding="utf-8", errors="replace").splitlines()
    payload = parse_transcript(lines)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
