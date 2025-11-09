from pathlib import Path

from lerobot.robots.so101_follower import SO101Follower, SO101FollowerConfig


def main():
    """Connects to the SO101 robotic arm and makes calibration."""
    # Configure the robot
    config = SO101FollowerConfig(
        port="/dev/ttyACM1",
        id="my_follower_robot_arm",
        calibration_dir=Path(".cache/calibration/so101/"),
    )

    print(f"Using calibration directory: {config.calibration_dir}")

    # Connect to the robot
    robot = SO101Follower(config)

    # To calibrate
    print("Robot is connected?", robot.is_connected)
    robot.bus.connect()
    print("Robot is calibrated?", robot.is_calibrated)
    robot.calibrate()


if __name__ == "__main__":
    main()
