import os
import runpy
import sys


def run_legacy_alias(app: str) -> None:
    target = os.path.join(os.path.dirname(__file__), "apps", "runtime_entrypoint.py")
    sys.argv = [target, "--app", app]
    runpy.run_path(target, run_name="__main__")
