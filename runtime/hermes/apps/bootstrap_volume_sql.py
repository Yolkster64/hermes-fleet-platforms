import os
import sys


def _runtime_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def main() -> int:
    runtime_root = _runtime_root()
    if runtime_root not in sys.path:
        sys.path.insert(0, runtime_root)
    try:
        from training_sql_intel import ensure_training_sql
        from volume_setup import ensure_runtime_volume_setup

        volume_root, manifest = ensure_runtime_volume_setup()
        db_path = ensure_training_sql(volume_root)
        print(
            f"[bootstrap-volume-sql] ready root={volume_root} db={db_path} "
            f"created={int(manifest.get('created_count', 0)) if isinstance(manifest, dict) else 0}"
        )
        return 0
    except Exception as exc:
        print(f"[bootstrap-volume-sql] warning: {exc}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
