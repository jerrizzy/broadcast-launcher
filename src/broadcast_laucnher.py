from launcher import load_config, launch_app, is_app_running_or_window_open
import logging
import time
import devices.camera as camera
from concurrent.futures import ThreadPoolExecutor


class BroadcastLauncher:
    def __init__(self):
        #load_config() returns a dictionary. config["apps"] gives me a list. 
        #The for loop takes one dictionary from that list at a time, 
        #and I use its keys to get the name and path.
        # step 1: read apps.json file and load it into a dictionary
        self.config = load_config()

    def wake_cameras(self):
        # Read the camera configuration from broadcast.json.
        # If "cameras" does not exist, use an empty list instead.
        cameras = self.config.get("cameras", [])

        # convert each cam dictionary from config file
        # into a PTZCamera object
        for camera_config in cameras:
            camera_info = camera.PTZCamera(
                name=camera_config["name"],
                ip=camera_config["ip"],
                port=camera_config.get("port", 1259)  # Default to 1259 if not specified
            )
        
        with ThreadPoolExecutor(max_workers=(len(camera_info))) as executor:
            # Submit one wake_and_wait() job for each camera.
            #
            # executor.submit(...) does NOT wait for the function to finish.
            # Instead, it immediately returns a Future object.
            #
            # A Future represents:
            # "this job is running now, and it will eventually produce
            #  a result or raise an exception."
            #
            # We store each Future as a key and the camera object as its value.
            # That lets us later know which camera belongs to each result.
            futures = {
                executor.submit(
                    camera_info.wake_and_wait, 
                    40, 1): camera 
                    for camera in camera_info
                    }
            # Process each Future as soon as it finishes.
            #
            # The cameras do NOT have to finish in config order.
            # If Right Camera finishes first, we handle Right Camera first.
            for future in as_completed(futures):
                # use the Completed Future to retrieve the camera
                # associated with that job
                camera = futures[future]

                try:
                    # future.result() gives us whatever wake_and_wait()
                    # returned.
                    #
                    # In our case:
                    # True  = camera woke successfully
                    # False = camera did not wake before timeout
                    #
                    # If wake_and_wait() raised an exception,
                    # future.result() will re-raise it here.
                    success = future.result()  # This will block until the job is done

                    logging.info("waking %s", camera.name)

                    if success:
                        logging.info("%s is ready", camera.name)
                    else:
                        logging.error("%s failed to wake", camera.name)
                        
                except Exception as e:
                    logging.error(
                        "%s encountered an error while waking: %s",
                        camera.name, e,
                        error
                    )
            

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
                app["path"],
                app.get("arguments")  # Pass arguments if they exist, otherwise None
            )

            if success:
                logging.info("%s launched successfully", app["name"])
            else:
                logging.error("%s failed to launch", app["name"])

            time.sleep(app.get("delay", 1))# Add a delay between launching apps 