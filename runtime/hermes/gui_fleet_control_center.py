import os
import runpy


if __name__ == "__main__":
    target = os.path.join(os.path.dirname(__file__), "apps", "gui_control_center.py")
    runpy.run_path(target, run_name="__main__")
