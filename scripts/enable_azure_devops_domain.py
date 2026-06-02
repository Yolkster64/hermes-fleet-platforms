#!/usr/bin/env python3
"""
Enable Azure DevOps MCP domain defaults in .mcp.json.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ALLOWED_DOMAINS = {
    "core",
    "work",
    "work-items",
    "search",
    "test-plans",
    "repositories",
    "wiki",
    "pipelines",
    "advanced-security",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Set the default enabled Azure DevOps MCP domain in .mcp.json."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(".mcp.json"),
        help="Path to .mcp.json (default: .mcp.json in current directory).",
    )
    parser.add_argument(
        "--domain",
        default="core",
        help="Domain to enable by default (default: core).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    domain = args.domain.strip().lower()
    if domain not in ALLOWED_DOMAINS:
        allowed = ", ".join(sorted(ALLOWED_DOMAINS))
        raise ValueError(f"Invalid domain '{args.domain}'. Allowed values: {allowed}")

    if not args.config.exists():
        raise FileNotFoundError(f"Config file not found: {args.config}")

    data = json.loads(args.config.read_text(encoding="utf-8"))
    inputs = data.get("inputs", [])
    arg20 = next((item for item in inputs if item.get("id") == "arg20"), None)
    if arg20 is None:
        raise KeyError("Could not find input id 'arg20' in .mcp.json")

    arg20["default"] = domain
    args.config.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"Enabled Azure DevOps MCP domain default: {domain}")
    print(f"Updated: {args.config}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
