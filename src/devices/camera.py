import socket
import time

class PTZCamera:

    POWER_ON = bytes.fromhex("81 01 04 00 02 FF")
    POWER_INQUIRY = bytes.fromhex("81 09 04 00 FF")

    POWER_ON_RESPONSE = bytes.fromhex("90 50 02 FF")
    POWER_STANDBY_RESPONSE = bytes.fromhex("90 50 03 FF")

    def __init__(self, name, ip, port=1259):
        self.name = name
        self.ip = ip
        self.port = port

    def wake(self):
        """Send VISCA Power on command to the cam"""

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            sock.sendto(self.POWER_ON, (self.ip, self.port))
            return True
        except Exception as e:
            print(f"Failed to wake camera {self.name} at {self.ip}:{self.port}: {e}")
            return False
        
        finally:
            sock.close()
    
    def get_power_state(self):
        """
        Ask the camera for its current power state.

        Returns:
            "on"
            "standby"
            "unknown"
            "offline"
        """
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(2)

            try:
                sock.sendto(
                    self.POWER_INQUIRY,
                    (self.ip, self.port)
                )

                response, address = sock.recvfrom(1024)
                
                print(
                    f"{self.name} replied from {address}: "
                    f"{response.hex(' ').upper()}"
)

            except socket.timeout:
                return "offline"

        if response == self.POWER_ON_RESPONSE:
            return "on"

        if response == self.POWER_STANDBY_RESPONSE:
            return "standby"

        # Firmware quirk: power inquiry not executable while in standby
        if response == bytes.fromhex("90 61 41 FF") or response == bytes.fromhex("90 62 41 FF"):
            return "standby"

        return "unknown"

    def wake_and_wait(self, timeout = 40, interval = 1) -> bool:
        """Check the camera's power state and print it."""
        state = self.get_power_state()
        print(f"{self.name} is currently: {state}")

        if state == "on":
            return True

        self.wake()

        start_time = time.time()

        while time.time() - start_time < timeout:
            time.sleep(interval)

            state = self.get_power_state()

            if state == "on":
                print(f"{self.name} is now: {state}")
                return True

        print(f"{self.name} did not turn on within the timeout period.")
        return False