from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


WORD_RE = re.compile(r"\b[\w'-]+\b")
NUMBERED_RE = re.compile(r"^\d+(\.\d+)*\s+[—-]\s+")
TABLE_LIKE_RE = re.compile(r"\s{2,}")
SECTION_SYMBOL_RE = re.compile(r"§\s*(\d+)")


def compile_master_brief(source: Path, output: Path) -> None:
    lines = source.read_text(encoding="utf-8", errors="replace").splitlines()
    headings: list[str] = []
    section_count = 0
    appendix_count = 0
    numbered_heading_count = 0
    table_like_lines = 0
    word_count = 0
    task_mentions = 0
    skill_mentions = 0
    connector_mentions = 0
    phase_mentions = 0
    complete_marks = 0
    pending_marks = 0
    failed_marks = 0
    section_symbol_count = 0
    section_symbol_max = 0
    mode_mentions = 0
    auto_mentions = 0
    self_heal_mentions = 0

    for raw in lines:
        text = raw.strip()
        if not text:
            continue

        lowered = text.lower()
        words = WORD_RE.findall(lowered)
        word_count += len(words)

        if lowered.startswith("section "):
            headings.append(text)
            section_count += 1
        elif lowered.startswith("appendix "):
            headings.append(text)
            appendix_count += 1
        elif NUMBERED_RE.match(text):
            headings.append(text)
            numbered_heading_count += 1

        if TABLE_LIKE_RE.search(raw):
            table_like_lines += 1

        task_mentions += lowered.count("task")
        skill_mentions += lowered.count("skill")
        connector_mentions += lowered.count("connector")
        phase_mentions += lowered.count("phase")

        complete_marks += raw.count("✅")
        pending_marks += raw.count("⏳")
        failed_marks += raw.count("❌")
        mode_mentions += lowered.count("-mode")
        auto_mentions += lowered.count("auto")
        self_heal_mentions += lowered.count("self-heal") + lowered.count("self heal")

        for match in SECTION_SYMBOL_RE.finditer(raw):
            section_symbol_count += 1
            section_symbol_max = max(section_symbol_max, int(match.group(1)))

    payload = {
        "source": str(source),
        "line_count": len(lines),
        "word_count": word_count,
        "heading_count": len(headings),
        "section_count": section_count,
        "appendix_count": appendix_count,
        "numbered_heading_count": numbered_heading_count,
        "table_like_line_count": table_like_lines,
        "task_mentions": task_mentions,
        "skill_mentions": skill_mentions,
        "connector_mentions": connector_mentions,
        "phase_mentions": phase_mentions,
        "status_marks": {
            "complete": complete_marks,
            "pending": pending_marks,
            "failed": failed_marks,
        },
        "section_symbol_count": section_symbol_count,
        "section_symbol_max": section_symbol_max,
        "mode_mentions": mode_mentions,
        "auto_mentions": auto_mentions,
        "self_heal_mentions": self_heal_mentions,
        "headings": headings,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile Copilot master brief into structured JSON.")
    parser.add_argument("--source", required=True, help="Path to source brief text file.")
    parser.add_argument("--output", required=True, help="Path to output JSON file.")
    args = parser.parse_args()
    compile_master_brief(Path(args.source), Path(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
