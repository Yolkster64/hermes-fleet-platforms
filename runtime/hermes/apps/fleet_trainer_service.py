import os
import runpy


if __name__ == "__main__":
    runtime_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    target = os.path.join(runtime_root, "auto_trainer.py")
    runpy.run_path(target, run_name="__main__")
