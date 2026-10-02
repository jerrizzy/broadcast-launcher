import time
import logging
from pathlib import Path
from launcher import load_config, launch_app
from broadcast_laucnher import BroadcastLauncher

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

    launcher = BroadcastLauncher()
    launcher.wake_cameras()
    launcher.launch_all()
    launcher.launch_zoom()
    if launcher.connect_zoom_to_vmix():
        logging.info("vMix Zoom connection workflow completed")
        if launcher.start_vmix_streaming():
            logging.info("vMix streaming workflow completed")
        else:
            logging.error("vMix streaming workflow failed")
    else:
        logging.error("vMix Zoom connection workflow failed")
    

if __name__ == "__main__":
    main()