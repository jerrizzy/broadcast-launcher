from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import time

from devices.camera import PTZCamera
from launcher import (
    connect_vmix_zoom,
    is_app_running_or_window_open,
    launch_app,
    launch_zoom_meeting,
    load_config,
    start_vmix_streaming,
    wait_for_vmix_api,
)


class BroadcastLauncher:
    def __init__(self):
        self.config = load_config()

    def wake_cameras(self):
        cameras = [
            PTZCamera(
                name=camera_config["name"],
                ip=camera_config["ip"],
                port=camera_config.get("port", 1259),
            )
            for camera_config in self.config.get("cameras", [])
        ]

        if not cameras:
            logging.info("No cameras are configured")
            return

        with ThreadPoolExecutor(max_workers=len(cameras)) as executor:
            futures = {
                executor.submit(camera.wake_and_wait, 40, 1): camera
                for camera in cameras
            }

            for future in as_completed(futures):
                camera = futures[future]
                try:
                    if future.result():
                        logging.info("%s is ready", camera.name)
                    else:
                        logging.error("%s failed to wake", camera.name)
                except Exception as error:
                    logging.exception(
                        "%s encountered an error while waking: %s",
                        camera.name,
                        error,
                    )

    def launch_all(self):
        for app in self.config["apps"]:
            app_name = app["name"]

            if app_name.lower() == "zoom":
                logging.info("Deferring Zoom meeting launch until after vMix connects")
                continue

            if is_app_running_or_window_open(app):
                logging.info("%s is already running or window is open", app_name)
                continue

            logging.info("Attempting to launch %s", app_name)
            if launch_app(app_name, app["path"], app.get("arguments")):
                logging.info("%s launched successfully", app_name)
            else:
                logging.error("%s failed to launch", app_name)

            time.sleep(app.get("delay", 1))

    def launch_zoom(self):
        zoom_config = next(
            (
                app
                for app in self.config["apps"]
                if app["name"].lower() == "zoom"
            ),
            None,
        )
        if zoom_config is None:
            logging.error("Zoom settings not found in application configuration")
            return False

        if is_app_running_or_window_open(zoom_config):
            logging.info("Zoom meeting window is already open")
            return True

        logging.info("Opening configured Zoom meeting")
        if not launch_zoom_meeting(
            zoom_config["path"],
            zoom_config["window_title"],
        ):
            logging.error("Zoom meeting did not open successfully")
            return False

        logging.info("Zoom meeting opened successfully")
        time.sleep(zoom_config.get("delay", 1))
        return True

    def connect_zoom_to_vmix(self):
        zoom_config = next(
            (
                app
                for app in self.config["apps"]
                if app["name"].lower() == "zoom"
            ),
            None,
        )
        if zoom_config is None:
            logging.error("Zoom settings not found in application configuration")
            return False

        if not wait_for_vmix_api():
            return False

        return connect_vmix_zoom(
            meeting_id=zoom_config["meeting_id"],
            password=zoom_config["password"],
            input_title=zoom_config.get("vmix_input_title"),
        )

    def start_vmix_streaming(self):
        return start_vmix_streaming()
