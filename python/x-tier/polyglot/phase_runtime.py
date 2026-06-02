from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class RuntimePaths:
    c_root: Path = Path(r"C:\\")
    d_root: Path = Path(r"D:\\")
    e_root: Path = Path(r"E:\\")
    devdrive: Path = Path(r"D:\\DevDrive")


class PhaseRuntime:
    """
    Python implementation skeleton for the 5-phase local AI super-node build.
    """

    def __init__(self, paths: RuntimePaths | None = None):
        self.paths = paths or RuntimePaths()

    # Phase 1: layout + cache drain
    def phase1_layout(self) -> list[Path]:
        targets = [
            self.paths.devdrive / "src",
            self.paths.devdrive / "pkg",
            self.paths.devdrive / "tools",
            self.paths.devdrive / "ai",
            self.paths.devdrive / "docker",
            self.paths.devdrive / "wsl",
            self.paths.devdrive / "vm",
            self.paths.devdrive / "hermes",
            self.paths.devdrive / "data",
            self.paths.devdrive / "azure",
            self.paths.devdrive / "github",
        ]
        return targets

    def phase1_cache_env(self) -> dict[str, str]:
        return {
            "npm_cache": r"D:\pkg\npm-cache",
            "npm_prefix": r"D:\tools\npm-global",
            "pip_cache": r"D:\pkg\pip-cache",
            "nuget_packages": r"D:\pkg\nuget-global",
            "cargo_home": r"D:\tools\cargo",
            "rustup_home": r"D:\tools\rustup",
        }

    # Phase 2: core toolchain
    def phase2_packages(self) -> list[str]:
        return [
            "git",
            "vscode",
            "gh",
            "az",
            "python3.12",
            "nodejs",
            "dotnet8",
            "powershell7",
            "cuda",
            "docker",
            "wsl2",
        ]

    # Phase 3: AI hub + DB + fleet
    def phase3_data_roots(self) -> list[Path]:
        return [
            self.paths.devdrive / "data" / "raw",
            self.paths.devdrive / "data" / "curated",
            self.paths.devdrive / "data" / "features",
            self.paths.devdrive / "data" / "sql",
            self.paths.devdrive / "ai" / "models",
            self.paths.devdrive / "ai" / "embeddings",
            self.paths.devdrive / "ai" / "runs",
            self.paths.devdrive / "hermes" / "runtime",
            self.paths.devdrive / "hermes" / "nodes",
            self.paths.devdrive / "hermes" / "models",
            self.paths.devdrive / "hermes" / "logs",
            self.paths.devdrive / "hermes" / "sql",
            self.paths.devdrive / "hermes" / "vectors",
        ]

    # Phase 4: pattern engine
    def phase4_feature_columns(self) -> list[str]:
        return [
            "tokens_in",
            "tokens_out",
            "latency_ms",
            "tokens_total",
            "throughput",
            "success",
            "task_complexity",
            "input_length",
            "time_of_day_bucket",
        ]

    # Phase 5: security modes
    def phase5_modes(self) -> dict[str, dict]:
        return {
            "C": {"inbound": "block", "outbound": "allow", "profile": "dev"},
            "B": {"inbound": "block", "outbound": "allow_limited", "profile": "balanced"},
            "A": {"inbound": "block", "outbound": "block_default", "profile": "paranoid"},
        }

    def summarize(self) -> dict:
        return {
            "phase1_dirs": [str(p) for p in self.phase1_layout()],
            "phase1_cache_env": self.phase1_cache_env(),
            "phase2_packages": self.phase2_packages(),
            "phase3_data_roots": [str(p) for p in self.phase3_data_roots()],
            "phase4_feature_columns": self.phase4_feature_columns(),
            "phase5_modes": self.phase5_modes(),
        }


def render_lines(values: Iterable[str]) -> str:
    return "\n".join(f"- {v}" for v in values)

