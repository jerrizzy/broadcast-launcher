from launcher import load_config, launch_app, is_app_running_or_window_open
import logging
import time


class BroadcastLauncher:
    def __init__(self):
        #load_config() returns a dictionary. config["apps"] gives me a list. 
        #The for loop takes one dictionary from that list at a time, 
        #and I use its keys to get the name and path.
        # step 1: read apps.json file and load it into a dictionary
        self.config = load_config()

    def launch_all(self):

        # step 2: config['apps] is a list of dictionaries, each dictionary contains the name and path of an application
        # the loop iterates through each disctionary in the list
        for app in self.config["apps"]:
        # Example:
        # app = {
        #     "name": "Chrome",
        #     "path": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        # }
            if is_app_running_or_window_open(app):
                logging.info("%s is already running or window is open", 
                app["name"])
                continue  # Skip launching this app if it's already running or window is open

            logging.info("Attempting to launch %s", app["name"])

            #step #3 takes the path from the loop 
            # and passes it to the launch_app function which uses the subprocess library to run the applicat
            success = launch_app(
                app["name"],
                app["path"]
            )

            if success:
                logging.info("%s launched successfully", app["name"])
            else:
                logging.error("%s failed to launch", app["name"])

            time.sleep(app.get("delay", 1))# Add a delay between launching apps 