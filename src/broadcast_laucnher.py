from launcher import load_config, launch_app
import logging
import time


class BroadcastLauncher:
    def __init__(self):
        self.config = load_config()

    def launch_all(self):
        for app in self.config["apps"]:
            logging.info("Attempting to launch %s", app["name"])

            success = launch_app(
                app["name"],
                app["path"]
            )

            if success:
                logging.info("%s launched successfully", app["name"])
            else:
                logging.error("%s failed to launch", app["name"])

            time.sleep(app.get("delay", 1))