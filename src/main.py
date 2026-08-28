from launcher import load_config, launch_app

#load_config() returns a dictionary. config["apps"] gives me a list. 
#The for loop takes one dictionary from that list at a time, 
#and I use its keys to get the name and path.
def main():
    print("Broadcast Launcher Starting...")

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
        print(f"Launching {app['name']} from {app['path']}...")

        #step #3 takes the path from the loop 
        # and passes it to the launch_app function which uses the subprocess library to run the application
        launch_app(app['path'])
    

if __name__ == "__main__":
    main()