import argparse
import os
import runpy


def _runtime_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _normalize_app(app: str) -> str:
    aliases = {
        "gui": "gui",
        "dashboard": "gui",
        "trainer": "trainer",
        "train": "trainer",
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


def run_app(app: str) -> None:
    runpy.run_path(_target_for_app(app), run_name="__main__")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hermes runtime app entrypoint")
    parser.add_argument("--app", choices=["gui", "dashboard", "trainer", "train"], required=True, help="App target to run")
    args = parser.parse_args()
    run_app(args.app)
