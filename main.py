import requests
import time
import math

from coordination_transformation_camera_to_robot import camera_to_robot
from detect_single_frame import detect_cans
from config import BOT_NAME, CONFIG_POSITIONS, DETECTION_FILE, GRIPPER_CLOSE, GRIPPER_OPEN, STACK_POSITIONS_3, STACK_POSITIONS_6, STACK_Z_TARGETS_3, STACK_Z_TARGETS_6, Z_LIFT, Z_LIFT_FINISHED, Z_PICK
from robot_client import token, get_operator, post_operator, delete_operator, get_tcp_target, put_tcp_target, put_gripper, get_gripper, initialize

bot = BOT_NAME
token = None


def read_all_detections():
    print("Waiting for detected cans...")

    while True:
        try:
            with open(DETECTION_FILE, "r") as f:
                lines = [l.strip() for l in f.readlines() if l.strip()]

            if len(lines) == 0:
                continue

            cans_px = []
            for line in lines:
                parts = line.split()
                if len(parts) >= 2:
                    u, v = map(float, parts[:2])
                    cans_px.append((u, v))

            if len(cans_px) >= 1:
                print(f"Found {len(cans_px)} detections.")
                return cans_px

        except FileNotFoundError:
            pass

        time.sleep(0.1)


def move_to_absolute(x, y, z, roll=180, pitch=0, yaw=180):
    print(f"Moving to: x={x}, y={y}, z={z}")
    put_tcp_target(x, y, z, roll, pitch, yaw)


def rotate(angle):
    coords = get_tcp_target()
    if not coords:
        print("Could not read TCP.")
        return

    x, y, z, roll, pitch, yaw = coords
    theta = math.radians(-angle)

    x_new = x * math.cos(theta) - y * math.sin(theta)
    y_new = x * math.sin(theta) + y * math.cos(theta)
    yaw_new = yaw - angle

    put_tcp_target(x_new, y_new, z, roll, pitch, yaw_new)
    print(f"Rotated {angle} degrees")


def toggle():
    g = get_gripper()
    if g == GRIPPER_CLOSE:
        print("Opening gripper")
        put_gripper(GRIPPER_OPEN)
    else:
        print("Closing gripper")
        put_gripper(GRIPPER_CLOSE)


def pick_and_place_can(i, x_robot, y_robot, x_stack, y_stack, z_target, lift_height=Z_LIFT):
    print(f"Picking can {i} at {x_robot:.1f}, {y_robot:.1f}")

    move_to_absolute(x_robot, y_robot, lift_height)
    time.sleep(5)

    move_to_absolute(x_robot, y_robot, Z_PICK)
    time.sleep(5)

    toggle()
    time.sleep(1)

    move_to_absolute(x_robot, y_robot, lift_height)
    time.sleep(10)

    print(f"Placing can {i} at {x_stack}, {y_stack} (z target {z_target})")
    move_to_absolute(x_stack, y_stack, lift_height)
    time.sleep(10)

    move_to_absolute(x_stack, y_stack, z_target)
    time.sleep(10)

    toggle()
    time.sleep(1)

    move_to_absolute(x_stack, y_stack, lift_height)
    time.sleep(6)


def log_on():
    tok, code = get_operator()
    if tok:
        delete_operator(tok)

    name = "Can Stacker"
    email = ".@student.unisg.ch"
    new_tok, code = post_operator(name, email)

    initialize()

    if code == 200:
        print(f"Connected to {bot}")
        return new_tok
    else:
        print("Failed to connect")
        return None


def log_off():
    if token:
        delete_operator(token)
        print("Logged off.")


def lift_and_log_off():
    """Move robot up to finish height before logging off."""
    coords = get_tcp_target()
    if coords:
        x, y, _, roll, pitch, yaw = coords
        move_to_absolute(x, y, Z_LIFT_FINISHED, roll, pitch, yaw)
        time.sleep(6)
    else:
        print("Could not read TCP before lift; skipping move up.")
    log_off()


def config_mode():
    print("Entering config mode")
    print("Place 4 cans into the robot's gripper when prompted.")

    g = get_gripper()
    if g != GRIPPER_OPEN:
        print("Opening gripper")
        put_gripper(GRIPPER_OPEN)

    rotate(45)
    time.sleep(6)

    rotate(45)
    time.sleep(6)

    move_to_absolute(0, -450, 300)
    time.sleep(10)

    for i, (x, y) in enumerate(CONFIG_POSITIONS):
        print(f"Preparing position {i+1}: {x}, {y}")

        move_to_absolute(x, y, Z_LIFT)
        time.sleep(5)

        move_to_absolute(x, y, Z_PICK)
        time.sleep(5)

        print("Place a can into the gripper now.")
        toggle()
        time.sleep(4)

        toggle()
        time.sleep(3)

        move_to_absolute(x, y, Z_LIFT)
        time.sleep(5)

        print(f"Can {i+1} placed.")

    print("Configuration mode complete. You can now run detection to detect the cans position. Add them to coordination_transformation_camera_to_robot.py as CAN_0_CAMERA, etc.")


def auto_stack():
    print("Starting auto stacking")

    g = get_gripper()
    if g != GRIPPER_OPEN:
        print("Opening gripper")
        put_gripper(GRIPPER_OPEN)

    rotate(45)
    time.sleep(6)

    rotate(45)
    time.sleep(6)

    move_to_absolute(0, -450, 300)
    time.sleep(10)

    detections_px = read_all_detections()
    detections_px_sorted = sorted(detections_px, key=lambda p: p[0])  # left -> right

    if len(detections_px_sorted) < 3:
        print("Not enough cans detected (need at least 3). Aborting stacking.")
        return

    if len(detections_px_sorted) >= 6:
        selected_px = detections_px_sorted[:6]
        stack_positions = STACK_POSITIONS_6
        z_targets = STACK_Z_TARGETS_6
        print("Using 2-row layout (6 cans).")
    else:
        selected_px = detections_px_sorted[:3]
        stack_positions = STACK_POSITIONS_3
        z_targets = STACK_Z_TARGETS_3
        print("Using single-row layout (3 cans). Extra detections ignored." if len(detections_px_sorted) > 3 else "Using single-row layout (3 cans).")

    detections_robot = [camera_to_robot(u, v) for (u, v) in selected_px]

    print("Detections (robot coordinates, file order):")
    for d in detections_robot:
        print(f"x={d[0]:.1f}, y={d[1]:.1f}")

    total_cans = len(detections_robot)
    for i, ((x_r, y_r), (x_stack, y_stack), z_target) in enumerate(zip(detections_robot, stack_positions, z_targets)):
        travel_lift = Z_LIFT_FINISHED if (total_cans == 6 and i == 5) else Z_LIFT
        pick_and_place_can(i, x_r, y_r, x_stack, y_stack, z_target, lift_height=travel_lift)

    print("Stacking complete.")
    lift_and_log_off()


def main():
    global token

    print("Connecting automatically to " + bot + "...")
    token = log_on()

    while True:
        print("\nCommands:\n- config\n- detect\n- stack\n- toggle\n- exit\n")

        cmd = input("Command: ").lower().strip()

        if cmd == "config":
            config_mode()

        elif cmd == "detect":
            detect_cans()

        elif cmd == "stack":
            print("Running automatic detection")
            detect_cans()
            print("Detection completed. Starting auto stacking.")
            auto_stack()

        elif cmd == "toggle":
            toggle()

        elif cmd == "exit":
            log_off()
            exit()

        else:
            print("Unknown command.")


if __name__ == "__main__":
    main()
