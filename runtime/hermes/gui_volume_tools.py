import os
from datetime import datetime
from typing import Dict, List, Tuple

from volume_setup import ensure_runtime_volume_setup, resolve_runtime_volume_root


def resolve_volume_root() -> str:
    return resolve_runtime_volume_root()


def scan_volume_files(root: str, limit: int = 500) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    if not os.path.exists(root):
        return rows
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", "node_modules"}]
        for name in files:
            path = os.path.join(base, name)
            try:
                stat = os.stat(path)
            except OSError:
                continue
            rel = os.path.relpath(path, root).replace("\\", "/")
            rows.append(
                {
                    "relative_path": rel,
                    "bytes": int(stat.st_size),
                    "modified_unix": float(stat.st_mtime),
                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
    rows.sort(key=lambda r: float(r["modified_unix"]), reverse=True)
    return rows[: max(50, min(2000, int(limit)))]


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
