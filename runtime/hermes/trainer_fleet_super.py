import os
import runpy
import sys


if __name__ == "__main__":
    target = os.path.join(os.path.dirname(__file__), "apps", "runtime_entrypoint.py")
    sys.argv = [target, "--app", "trainer"]
    runpy.run_path(target, run_name="__main__")
