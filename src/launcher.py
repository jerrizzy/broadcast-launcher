import subprocess
from pathlib import Path
import json
import psutil
import win32gui
import os
from pywinauto import Desktop
import time
import logging

# this function points to the config file and loads it into a dictionary
# the .open() method opens the file in read mode and the encoding is set to utf-8
# it turns into a dictionary with this line: return json.load(file)
def load_config():
    """
    Load configuration settings from a config file.
    """
    config_path = Path(__file__).resolve().parent.parent / "config" / "broadcast.json"

    with config_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def is_app_running(process_name: str) -> bool:
    """Return True if a process with that name is running already"""
    for process in psutil.process_iter(['name']):
        if process.info['name'] and process.info['name'].lower() == process_name.lower():
            return True
    return False

def is_window_open(title_contains: str) -> bool:
    """Return True if a visible top level window contains the given text in its window title"""
    found = False

    def callback(hwnd, _):
        nonlocal found
        if not win32gui.IsWindowVisible(hwnd):
            return True  # Continue enumeration

        window_title = win32gui.GetWindowText(hwnd)

        if title_contains.lower() in window_title.lower():
            found = True

    win32gui.EnumWindows(callback, None)
    return found

def is_app_running_or_window_open(app: dict) -> bool:
    """Dtermime whether on applicationis already running
    using the detection strategy defined in config."""
    detection = app.get("detection", "process")
    if detection == "process":
        process_name = app.get("process_name")

        if not process_name:
            return False  # No process name provided, cannot check
        
        return is_app_running(process_name)
    
    if detection == "window":
        window_title = app.get("window_title")

        if not window_title:
            return False  # No window title provided, cannot check
        
        return is_window_open(window_title)
    
    return False  # Unknown detection strategy

def join_zoom_meeting(window_title: str) -> bool:
    """
    Find the Zoom Join button and invoke it.

    Returns:
        True  - Join button successfully invoked.
        False - Join button could not be found or clicked.
    """

    try:
        window = Desktop(backend="uia").window(
            title=window_title
        )

        join_button = window.child_window(
            title="Join",
            control_type="Button"
        )

        join_button.invoke()

        return True

    except Exception:
        return False

def wait_for_window(window_title: str, timeout: int = 30) -> bool:
    """
    Wait until a window appears.

    This function repeatedly checks whether a window
    with the given title exists.

    It returns immediately when the window is found.

    Returns:
        True  - Window found before timeout.
        False - Window never appeared.
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:

            window = Desktop(
                backend="uia").window(
                title=window_title
                )
            
            if window.exists():
                return True

        except Exception:
            pass

        time.sleep(1)

    return False


# this function launches an application given its path
# it uses the subprocess library to run the application in a new process
def launch_app(app_name: str, app_path: str, window_title: str, arguments=None):
    """
    attempt to launch an application.
    Returns True when successful and False when unsuccessful.
    """
    command = [app_path]

    if app_path.startswith("zoommtg://"):
        os.startfile(app_path)

        if wait_for_window(window_title):
            if join_zoom_meeting(window_title):
                logging.info("Zoom meeting joined successfully")
            else:
                logging.error("Join button not found")
        return True

    if arguments:
        command.extend(arguments)

    try:
        subprocess.Popen(command)
        return True

    except FileNotFoundError:
        return False

    except Exception as error:
        print(f"{app_name}: {error}")
        return False
