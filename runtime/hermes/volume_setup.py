import json
import os
import time
from typing import Dict, List, Tuple

VOLUME_SUBDIRS = [
    "training",
    "training/checkpoints",
    "knowledge",
    "knowledge/mesh",
    "exports",
    "logs",
    "cache",
]


def resolve_runtime_volume_root() -> str:
    candidates = [
        os.getenv("HERMES_VOLUME_DATA_PATH", "").strip(),
        "/workspace/runtime/hermes_persist",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "hermes_persist")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "auto")),
    ]
    for path in candidates:
        if path and os.path.exists(path):
            return path
    return candidates[1]


def ensure_runtime_volume_setup(root: str | None = None) -> Tuple[str, Dict[str, object]]:
    base = root or resolve_runtime_volume_root()
    os.makedirs(base, exist_ok=True)
    created: List[str] = []
    for rel in VOLUME_SUBDIRS:
        target = os.path.join(base, rel)
        if not os.path.exists(target):
            os.makedirs(target, exist_ok=True)
            created.append(rel.replace("\\", "/"))
    manifest_path = os.path.join(base, "hermes_volume_manifest.json")
    manifest = {
        "version": 1,
        "root": base,
        "created_unix": time.time(),
        "subdirs": VOLUME_SUBDIRS,
        "created_count": len(created),
        "created_paths": created,
    }
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
    return base, manifest
