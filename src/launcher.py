import subprocess
from pathlib import Path
import json
import psutil
import win32gui
import os
import time
import logging
import requests
import xml.etree.ElementTree as ET
from pywinauto import Desktop

VMIX_API_URL = "http://127.0.0.1:8088/api/"

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

def wait_for_window(window_title: str, timeout: int = 30) -> bool:
    start_time = time.monotonic()
    while time.monotonic() - start_time < timeout:
        if is_window_open(window_title):
            return True
        time.sleep(1)
    return False


def launch_zoom_meeting(meeting_uri: str, window_title: str) -> bool:
    try:
        os.startfile(meeting_uri)
    except OSError as error:
        logging.error(
            "Could not open the Zoom meeting link (%s)",
            type(error).__name__,
        )
        return False

    if not wait_for_window(window_title):
        logging.error(
            "Zoom meeting window '%s' did not appear before timeout",
            window_title,
        )
        return False

    logging.info("Zoom meeting window '%s' appeared", window_title)
    return True


# this function launches an application given its path
# it uses the subprocess library to run the application in a new process
def launch_app(app_name: str, app_path: str, arguments=None):
    """
    attempt to launch an application.
    Returns True when successful and False when unsuccessful.
    """
    command = [app_path]

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


def grant_zoom_streaming_permission(timeout: int = 20) -> bool:
    """
    Wait for Zoom's livestream permission window and click
    the "Grant permission" button.

    Zoom exposes the permission popup as a Win32 window, but the
    buttons inside the popup are custom-drawn. Because there is no
    accessible child Button control, we click a known position
    relative to the permission window.

    Returns:
        True:
            The permission window was found, the click was sent,
            and the permission window disappeared.

        False:
            The permission window did not appear within the timeout,
            or the window remained after attempting the click.
    """

    # This is the Win32 class Zoom uses for the livestream
    # permission request window.
    permission_class = "zLocalLivingPermissionRequestWndClass"

    # Coordinates are relative to the permission window itself.
    #
    # During testing, the popup measured 500 x 262 pixels and the
    # center of "Grant permission" was approximately (310, 191).
    grant_coordinates = (310, 191)

    start_time = time.time()

    logging.info(
        "Waiting for Zoom livestream permission request"
    )

    # Keep checking until either:
    #
    #   1. Zoom displays the permission window
    #   2. our timeout expires
    #
    while time.time() - start_time < timeout:

        permission_window = Desktop(
            backend="win32"
        ).window(
            class_name=permission_class
        )

        if permission_window.exists():

            logging.info(
                "Zoom livestream permission window detected"
            )

            try:
                window = permission_window.wrapper_object()

                # Click the location of "Grant permission".
                #
                # These coordinates are relative to the popup,
                # so the popup can move around the desktop without
                # changing where we click inside it.
                window.click_input(
                    coords=grant_coordinates
                )

                logging.info(
                    "Clicked Zoom Grant permission"
                )

            except RuntimeError as error:
                if "Not enough rights" in str(error):
                    logging.error(
                        "Cannot grant Zoom streaming permission because "
                        "the launcher lacks permission to interact with Zoom. "
                        "Run the launcher from an elevated terminal."
                    )
                else:
                    logging.exception(
                        "Failed to click Zoom Grant permission: %s",
                        error
                    )
                return False

            except Exception as error:
                logging.exception(
                    "Failed to click Zoom Grant permission: %s",
                    error
                )
                return False

            # Clicking the coordinates isn't enough to prove the
            # permission was accepted.
            #
            # Wait briefly for Zoom to close the permission window.
            disappearance_start = time.time()

            while time.time() - disappearance_start < 5:

                if not permission_window.exists():
                    logging.info(
                        "Zoom livestream permission was granted"
                    )
                    return True

                time.sleep(0.5)

            logging.error(
                "Zoom permission window remained after click"
            )
            return False

        # Don't continuously hammer Windows while waiting.
        time.sleep(0.5)

    logging.error(
        "Zoom livestream permission window did not appear "
        "within %s seconds",
        timeout
    )

    return False


def wait_for_vmix_api(timeout: int = 30, interval: float = 1) -> bool:
    """Wait until the local vMix API responds successfully."""
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        try:
            response = requests.get(VMIX_API_URL, timeout=2)
            response.raise_for_status()
            logging.info("vMix API is ready")
            return True
        except requests.RequestException:
            time.sleep(min(interval, max(0, deadline - time.monotonic())))

    logging.error("vMix API did not become ready within %s seconds", timeout)
    return False


def get_vmix_state():
    """Return the current vMix API state, or None if it cannot be read."""
    try:
        response = requests.get(VMIX_API_URL, timeout=5)
        response.raise_for_status()
        return ET.fromstring(response.content)
    except (requests.RequestException, ET.ParseError) as error:
        logging.error("Could not read vMix API state (%s)", type(error).__name__)
        return None


def resolve_vmix_zoom_input(input_title: str | None = None) -> int | None:
    """Find the Zoom input by type, independent of its current position."""
    state = get_vmix_state()
    if state is None:
        return None

    zoom_inputs = [
        input_element
        for input_element in state.findall("./inputs/input")
        if input_element.get("type", "").casefold() == "zoom"
    ]

    if input_title:
        zoom_inputs = [
            input_element
            for input_element in zoom_inputs
            if input_element.get("title") == input_title
        ]

    if len(zoom_inputs) != 1:
        titles = [item.get("title", "<untitled>") for item in zoom_inputs]
        if not zoom_inputs:
            logging.error(
                "Could not find a matching Zoom input in vMix"
                + (f" with title {input_title!r}" if input_title else "")
            )
        else:
            logging.error(
                "Found multiple Zoom inputs in vMix; set vmix_input_title "
                "to select one: %s",
                ", ".join(titles),
            )
        return None

    try:
        return int(zoom_inputs[0].get("number", ""))
    except ValueError:
        logging.error("The matching vMix Zoom input has no valid input number")
        return None


def connect_vmix_zoom(
    meeting_id: str,
    password: str,
    input_title: str | None = None,
) -> bool:
    """
    Tell vMix to connect its Zoom input to a meeting.

    After vMix requests access to the Zoom meeting, Zoom displays
    a livestream permission request. This function then waits for
    that request and grants permission.

    Returns True only if both stages succeed.
    """

    input_number = resolve_vmix_zoom_input(input_title)
    if input_number is None:
        return False

    params = {
        "Function": "ZoomJoinMeeting",
        "Input": input_number,
        "Value": f"{meeting_id},{password}"
    }

    logging.info(
        "Requesting vMix Zoom connection for input %s",
        input_number
    )

    try:
        response = requests.get(
            VMIX_API_URL,
            params=params,
            timeout=10
        )

        response.raise_for_status()

    except requests.RequestException as error:
        logging.error(
            "vMix Zoom API request failed (%s)",
            type(error).__name__,
        )
        return False

    logging.info(
        "vMix accepted ZoomJoinMeeting request"
    )

    # vMix has now initiated the Zoom connection.
    #
    # Zoom should respond by displaying its livestream
    # permission request. Wait for that popup and approve it.
    if not grant_zoom_streaming_permission(timeout=60):
        logging.error(
            "Could not grant Zoom streaming permission"
        )
        return False

    logging.info(
        "vMix Zoom permission workflow completed"
    )

    return True


def start_vmix_streaming(timeout: int = 15, interval: float = 1) -> bool:
    """Start all configured vMix streams and verify streaming becomes active."""
    state = get_vmix_state()
    if state is None:
        return False

    streaming_state = state.findtext("streaming", default="False")
    if streaming_state.casefold() == "true":
        logging.info("vMix is already streaming")
        return True

    try:
        response = requests.get(
            VMIX_API_URL,
            params={"Function": "StartStreaming"},
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        logging.error(
            "vMix StartStreaming request failed (%s)",
            type(error).__name__,
        )
        return False

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        state = get_vmix_state()
        if state is not None and state.findtext(
            "streaming", default="False"
        ).casefold() == "true":
            logging.info("vMix streaming started")
            return True
        time.sleep(min(interval, max(0, deadline - time.monotonic())))

    logging.error(
        "vMix did not report streaming active within %s seconds",
        timeout,
    )
    return False