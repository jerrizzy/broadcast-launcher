import logging
from pathlib import Path
from launcher import load_config, launch_app

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "broadcast_launcher.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

#load_config() returns a dictionary. config["apps"] gives me a list. 
#The for loop takes one dictionary from that list at a time, 
#and I use its keys to get the name and path.
def main():
    logging.info("Broadcast Launcher Starting...")

    # step 1: read apps.json file and load it into a dictionary
    config = load_config()
    
    # step 2: config['apps] is a list of dictionaries, each dictionary contains the name and path of an application
    # the loop iterates through each disctionary in the list
    for app in config['apps']:
        # Example:
        # app = {
        #     "name": "Chrome",
        #     "path": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        # }
        logging.info("Attempting to launch %s", app['name'])

        #step #3 takes the path from the loop 
        # and passes it to the launch_app function which uses the subprocess library to run the application
        success = launch_app(app['name'], app['path'])

        if success:
            logging.info("%s lauched successfuly", app['name'])
        else:
            logging.error("%s failed to lauch", app['name'])
    

if __name__ == "__main__":
    main()