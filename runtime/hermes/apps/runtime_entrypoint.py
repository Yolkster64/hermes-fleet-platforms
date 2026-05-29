import argparse
import os
import runpy
import sys


def _runtime_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _normalize_app(app: str) -> str:
    aliases = {
        "gui": "gui",
        "dashboard": "gui",
        "control-center": "gui",
        "trainer": "trainer",
        "train": "trainer",
        "fleet-trainer": "trainer",
    }
    if app not in aliases:
        raise ValueError(f"Unknown app target: {app}")
    return aliases[app]


def _target_for_app(app: str) -> str:
    runtime_root = _runtime_root()
    mapping = {
        "gui": os.path.join(runtime_root, "gui_dashboard.py"),
        "trainer": os.path.join(runtime_root, "auto_trainer.py"),
    }
    return mapping[_normalize_app(app)]


def _bootstrap_runtime_intelligence() -> None:
    runtime_root = _runtime_root()
    if runtime_root not in sys.path:
        sys.path.insert(0, runtime_root)
    try:
        from volume_setup import ensure_runtime_volume_setup
        from training_sql_intel import ensure_training_sql

        volume_root, _manifest = ensure_runtime_volume_setup()
        ensure_training_sql(volume_root)
        print(f"[runtime-entrypoint] volume+sql ready at {volume_root}")
    except Exception as exc:  # pragma: no cover
        print(f"[runtime-entrypoint] bootstrap warning: {exc}")


def run_app(app: str) -> None:
    _bootstrap_runtime_intelligence()
    runpy.run_path(_target_for_app(app), run_name="__main__")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hermes runtime app entrypoint")
    parser.add_argument(
        "--app",
        choices=["gui", "dashboard", "control-center", "trainer", "train", "fleet-trainer"],
        required=True,
        help="App target to run",
    )
    args = parser.parse_args()
    run_app(args.app)
