import subprocess
from pathlib import Path
import json

# this function points to the config file and loads it into a dictionary
# the .open() method opens the file in read mode and the encoding is set to utf-8
# it turns into a dictionary with this line: return json.load(file)
def load_config():
    """
    Load configuration settings from a config file.
    """
    config_path = Path(__file__).resolve().parent.parent / "config" / "apps.json"

    with config_path.open("r", encoding="utf-8") as file:
        return json.load(file)

# this function launches an application given its path
# it uses the subprocess library to run the application in a new process
def launch_app(app_name: str, app_path: str):
    """
    attempt to launch an application.
    Returns True when successful and False when unsuccessful.
    """
    try:
        subprocess.Popen([app_path])
        return True

    except FileNotFoundError:
        return False

    except Exception as error:
        return False
