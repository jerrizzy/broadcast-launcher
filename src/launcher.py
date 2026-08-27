import os
import sys
import subprocess
from pathlib import Path
import json


def load_config():
    """
    Load configuration settings from a config file.
    """
    config_path = Path(__file__).resolve().parent.parent / "config" / "apps.json"

    with config_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def launch_app(app_path: str) -> bool:
    """Launch an application given its filesystem path.

    Returns True on successful start, False otherwise.
    Works cross-platform: Windows, macOS, Linux.
    """
    try:
        if sys.platform == "darwin":
            subprocess.Popen(["open", app_path])
        elif os.name == "nt":
            # os.startfile raises OSError on failure
            os.startfile(app_path)
        else:
            # Assume a freedesktop-like system
            subprocess.Popen(["xdg-open", app_path])
        return True
    except Exception as e:
        # Keep errors visible for the caller / debugging
        print(f"Failed to launch {app_path}: {e}")
        return False
