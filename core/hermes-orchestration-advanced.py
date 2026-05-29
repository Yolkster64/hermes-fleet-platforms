import os
import runpy


if __name__ == "__main__":
    os.environ.setdefault("HERMES_MAX_MODE", "true")
    target = os.path.join(os.path.dirname(__file__), "hermes_super_orchestrator.py")
    runpy.run_path(target, run_name="__main__")
