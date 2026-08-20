import subprocess

def launch_app(app_path: str):
    """
    Launch an application using the operating system.
    """
    subprocess.Popen(["open", app_path])