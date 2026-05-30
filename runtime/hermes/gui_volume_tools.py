import heapq
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Tuple

import streamlit as st

from training_sql_intel import compute_sql_pattern_intel, ensure_training_sql
from volume_setup import ensure_runtime_volume_setup, resolve_runtime_volume_root

_SCAN_SKIP_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    ".pytest_cache",
    ".mypy_cache",
    ".idea",
    ".vs",
    "bin",
    "obj",
}
_SCAN_SKIP_SUFFIXES = {".pyc", ".tmp", ".lock"}


def resolve_volume_root() -> str:
    return resolve_runtime_volume_root()


@st.cache_data(ttl=4, show_spinner=False)
def scan_volume_files(root: str, limit: int = 500) -> List[Dict[str, object]]:
    max_rows = max(50, min(2000, int(limit)))
    newest_heap: List[Tuple[float, Dict[str, object]]] = []
    if not os.path.exists(root):
        return []
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in _SCAN_SKIP_DIRS]
        for name in files:
            if any(name.endswith(sfx) for sfx in _SCAN_SKIP_SUFFIXES):
                continue
            path = os.path.join(base, name)
            try:
                stat = os.stat(path)
            except OSError:
                continue
            rel = os.path.relpath(path, root).replace("\\", "/")
            row = {
                "relative_path": rel,
                "bytes": int(stat.st_size),
                "modified_unix": float(stat.st_mtime),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            }
            stamp = float(stat.st_mtime)
            if len(newest_heap) < max_rows:
                heapq.heappush(newest_heap, (stamp, row))
            elif stamp > newest_heap[0][0]:
                heapq.heapreplace(newest_heap, (stamp, row))
    newest_heap.sort(key=lambda item: item[0], reverse=True)
    return [row for _, row in newest_heap]


def read_volume_file(root: str, rel_path: str, max_bytes: int = 2_000_000) -> Tuple[bytes, str]:
    target = os.path.abspath(os.path.join(root, rel_path))
    root_abs = os.path.abspath(root)
    if not target.startswith(root_abs):
        return b"", "Invalid path."
    if not os.path.exists(target):
        return b"", "File not found."
    try:
        with open(target, "rb") as fh:
            data = fh.read(max_bytes + 1)
    except OSError as exc:
        return b"", str(exc)
    if len(data) > max_bytes:
        return data[:max_bytes], f"File truncated to {max_bytes} bytes for preview."
    return data, ""


def volume_health_summary(rows: List[Dict[str, object]]) -> Dict[str, float]:
    total_bytes = sum(int(row.get("bytes", 0)) for row in rows)
    return {
        "file_count": float(len(rows)),
        "total_mb": float(total_bytes) / (1024.0 * 1024.0),
        "avg_kb": (float(total_bytes) / 1024.0 / float(len(rows))) if rows else 0.0,
    }


def initialize_volume_layout(root: str | None = None) -> Tuple[str, Dict[str, object]]:
    return ensure_runtime_volume_setup(root=root)


@st.cache_data(ttl=4, show_spinner=False)
def read_sql_training_intelligence(root: str) -> Dict[str, object]:
    try:
        ensure_training_sql(root)
        return compute_sql_pattern_intel(root, lookback=240)
    except (sqlite3.Error, OSError, ValueError) as exc:
        return {"rows": 0, "pattern_score": 0.0, "trend": 0.0, "error": str(exc), "variable_means": {}, "latest_github": {}}
