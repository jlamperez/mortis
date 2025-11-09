# ({"shoulder_pan.pos": -45, "shoulder_lift.pos": -99, "elbow_flex.pos": 0, "wrist_flex.pos": 60, "wrist_roll.pos": 0, "gripper.pos": 60}, 0.5),
import os
import time
from pathlib import Path

from lerobot.robots.so101_follower import SO101Follower, SO101FollowerConfig

HOME_POSE = {
    "shoulder_pan.pos": 0,
    "shoulder_lift.pos": -99,
    "elbow_flex.pos": 97,
    "wrist_flex.pos": 55,
    "wrist_roll.pos": 0,
    "gripper.pos": 0,
}


GESTURES = {
    "idle": [
        (HOME_POSE, 1.0),
    ],
    "wave": [
        ({"wrist_flex.pos": -40}, 0.5),
        ({"shoulder_pan.pos": -5, "shoulder_lift.pos": 75, "elbow_flex.pos": -68}, 1),
        (HOME_POSE, 1.0),
    ],
    "point_left": [
        ({"shoulder_pan.pos": -60, "shoulder_lift.pos": -30, "elbow_flex.pos": -15, "wrist_flex.pos": 42, "wrist_roll.pos": 0, "gripper.pos": 0}, 1),
        ({"wrist_flex.pos": 80}, 0.5),
        ({"wrist_flex.pos": 42}, 0.5),
        ({"wrist_flex.pos": 80}, 0.5),
        (HOME_POSE, 1.0),
    ],
    "point_right": [
        ({"shoulder_pan.pos": 65, "shoulder_lift.pos": -50, "elbow_flex.pos": -5, "wrist_flex.pos": 55, "wrist_roll.pos": 0, "gripper.pos": 0}, 1),
        ({"wrist_flex.pos": 90}, 0.5),
        ({"wrist_flex.pos": 42}, 0.5),
        ({"wrist_flex.pos": 90}, 0.5),
        (HOME_POSE, 1.0),
    ],
    "grab": [
        ({'shoulder_pan.pos': 0, 'shoulder_lift.pos': -2, 'elbow_flex.pos': -8., 'wrist_flex.pos': 55, 'wrist_roll.pos': 0, 'gripper.pos': 0}, 0.8),
        ({"wrist_flex.pos": 80}, 0.5),
        ({"wrist_roll.pos": -45, "gripper.pos": 40}, 1),
        ({"elbow_flex.pos": 30}, 1),
        ({"wrist_roll.pos": 45, "gripper.pos": 10}, 1),
        ({"elbow_flex.pos": -20}, 1),
        (HOME_POSE, 1.0),
    ],
    "drop": [
        ({'shoulder_pan.pos': 0, 'shoulder_lift.pos': 5, 'elbow_flex.pos': 20., 'wrist_flex.pos': 55, 'wrist_roll.pos': 0, 'gripper.pos': 0}, 0.8),
        ({"gripper.pos": 80}, 1),
        ({"gripper.pos": 00}, 1),
        (HOME_POSE, 1.0),
    ],
}


class MortisArm:
    """
    Class to control the Mortis SO101 robotic arm.
    Manages connection, disconnection, and gesture execution.
    """

    def __init__(self, port="/dev/ttyACM1"):
        port = os.getenv("ROBOT_PORT", port)

        config = SO101FollowerConfig(
            port=port,
            id="my_follower_robot_arm",
            calibration_dir=Path(".cache/calibration/so101/"),
        )
        self.robot = SO101Follower(config)
        self.connected = False
        print(f"MortisArm initialized. Port: {port}, Calibration directory: {config.calibration_dir}")

    def connect(self):
        """Connects to the robotic arm."""
        if not self.connected:
            try:
                print("Connecting to Mortis' arm...")
                self.robot.connect()
                self.connected = self.robot.is_connected
                if self.connected:
                    print("✅ Mortis' arm connected.")
                    # Move to the initial position to indicate it's ready
                    self.move_arm("idle")
                else:
                    print("⚠️ Could not connect to Mortis' arm.")
            except Exception as e:
                print(f"🚨 Connection error: {e}")
                self.connected = False

    def disconnect(self):
        """Disconnects the robotic arm."""
        if self.connected:
            print("Disconnecting Mortis' arm...")
            # Move to rest position before disconnecting
            self.move_arm("idle")
            time.sleep(1)
            self.robot.disconnect()
            self.connected = False
            print("Arm disconnected.")

    def move_arm(self, gesture_name: str):
        """
        Executes a sequence of movements (a gesture) by its name.
        If the gesture does not exist, it executes 'idle'.
        """
        if not self.connected:
            print("Arm is not connected. Cannot move.")
            return

        # If the gesture is not defined, return to the neutral position.
        if gesture_name not in GESTURES:
            print(f"Gesture '{gesture_name}' not recognized. Reverting to 'idle'.")
            gesture_name = "idle"

        sequence = GESTURES[gesture_name]
        print(f"Executing gesture: '{gesture_name}'...")

        for action, delay in sequence:
            print(f"  -> Sending action: {action}")
            self.robot.send_action(action)
            time.sleep(delay)

        print(f"Gesture '{gesture_name}' completed.")


if __name__ == "__main__":

    mortis_arm = MortisArm()
    if not mortis_arm.connected:
        mortis_arm.connect()

    mortis_arm.move_arm("drop")

    mortis_arm.disconnect()
