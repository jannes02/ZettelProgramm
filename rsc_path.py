import sys
import os
from pathlib import Path

LAUNCH_MODE = "prod" #"dev" "portable" "prod"

def rsc_path(relative_path: str) -> str:
    if LAUNCH_MODE == "prod":
        base_path = Path(os.environ["APPDATA"]) / "HausDerWissenschaft"
    elif getattr(sys, "frozen", False):
        base_path = sys._MEIPASS   # PyInstaller Temp-Dir
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, "rsc", relative_path)
