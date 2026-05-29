import os
from datetime import datetime
from typing import Dict, List, Tuple


def resolve_volume_root() -> str:
    candidates = [
        os.getenv("HERMES_VOLUME_DATA_PATH", "").strip(),
        "/workspace/runtime/hermes_persist",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "hermes_persist")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "auto")),
    ]
    for path in candidates:
        if path and os.path.exists(path):
            return path
    return "/workspace/runtime/hermes_persist"


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
