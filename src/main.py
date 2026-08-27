from launcher import load_config, launch_app

def main():
    print("Broadcast Launcher Starting...")

    config = load_config()

    for app in config['apps']:
        print(f"Launching {app['name']} from {app['path']}...")
        launch_app(app['path'])
    

if __name__ == "__main__":
    main()