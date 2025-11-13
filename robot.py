import requests
import time
import math
from coord_transform import camera_to_robot   # NEW: uses full homography

bot = "cherrybot"
DETECTION_FILE = "detected_coords.txt"

# -----------------------------------------------------------
# STACK POSITION SETTINGS (BOTTOM, BOTTOM, TOP)
# -----------------------------------------------------------

STACK_POSITIONS = [
    (0,   -350),   # bottom-left can
    (70,  -350),   # bottom-right can
    (35,  -350)    # top can (middle)
]

# Z heights
Z_PICK = 200
Z_LIFT = 300
Z_TOP = 240     # slightly higher so top can doesn't crash


# -----------------------------------------------------------
# READ ALL DETECTED CANS FROM FILE
# -----------------------------------------------------------
def read_all_detections():
    print("📄 Waiting for detected cans...")

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
                print(f"📥 Found {len(cans_px)} detections.")
                return cans_px

        except FileNotFoundError:
            pass

        time.sleep(0.1)


# -----------------------------------------------------------
# MOVEMENT FUNCTIONS
# -----------------------------------------------------------
def move_to_absolute(x, y, z, roll=180, pitch=0, yaw=180):
    print(f"🧭 Moving to: x={x}, y={y}, z={z}")
    put_tcp_target(x, y, z, roll, pitch, yaw)


def rotate(angle):
    coords = get_tcp_target()
    if not coords:
        print("⚠️ Could not read TCP.")
        return

    x, y, z, roll, pitch, yaw = coords
    theta = math.radians(-angle)

    x_new = x*math.cos(theta) - y*math.sin(theta)
    y_new = x*math.sin(theta) + y*math.cos(theta)
    yaw_new = yaw - angle

    put_tcp_target(x_new, y_new, z, roll, pitch, yaw_new)
    print(f"🔄 Rotated {angle}°")


# -----------------------------------------------------------
# GRIPPER
# -----------------------------------------------------------
def toggle():
    g = get_gripper()
    if g == 630:
        print("🤏 Closing gripper")
        put_gripper(800)
    else:
        print("👐 Opening gripper")
        put_gripper(630)


# -----------------------------------------------------------
# PICK AND PLACE ONE CAN
# -----------------------------------------------------------
def pick_and_place_can(i, x_robot, y_robot, x_stack, y_stack):
    print(f"\n🔵 PICK CAN {i} at: x={x_robot:.1f}, y={y_robot:.1f}")

    # Move above can
    move_to_absolute(x_robot, y_robot, Z_LIFT)
    time.sleep(5)

    # Lower to pick height
    move_to_absolute(x_robot, y_robot, Z_PICK)
    time.sleep(5)

    # Grab
    toggle()
    time.sleep(1)

    # Lift upwards
    move_to_absolute(x_robot, y_robot, Z_LIFT)
    time.sleep(10)

    # Move above stack position
    print(f"🟢 PLACE CAN {i} at: x={x_stack:.1f}, y={y_stack:.1f}")
    move_to_absolute(x_stack, y_stack, Z_LIFT)
    time.sleep(10)

    # Lower to stacking height
    if i == 2:
        move_to_absolute(x_stack, y_stack, Z_TOP)
    else:
        move_to_absolute(x_stack, y_stack, Z_PICK)
    time.sleep(10)

    # Release
    toggle()
    time.sleep(1)

    # Lift away
    move_to_absolute(x_stack, y_stack, Z_LIFT)
    time.sleep(6)


# -----------------------------------------------------------
# LOGIN / ROBOT API WRAPPERS
# -----------------------------------------------------------
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


def log_off():
    delete_operator(token)
    print("Logged off.")


# -----------------------------------------------------------
# MAIN AUTO STACK SEQUENCE
# -----------------------------------------------------------
def auto_stack():
    print("\n🤖 STARTING AUTO STACKING...\n")

    rotate(45)
    time.sleep(6)

    rotate(45)
    time.sleep(6)

    move_to_absolute(0, -450, 300)
    time.sleep(10)

    # Read all detected cans from file
    detections_px = read_all_detections()

    # Convert to robot coordinates
    detections_robot = [camera_to_robot(u, v) for (u, v) in detections_px]

    # Sort left → right (x coordinate)
    detections_robot.sort(key=lambda p: p[0])

    print("\n📌 SORTED DETECTIONS (robot coords):")
    for d in detections_robot:
        print(f"   x={d[0]:.1f}, y={d[1]:.1f}")

    # Pick & stack the first 3 cans
    for i, (x_r, y_r) in enumerate(detections_robot[:3]):
        x_stack, y_stack = STACK_POSITIONS[i]
        pick_and_place_can(i, x_r, y_r, x_stack, y_stack)

    print("\n🎉 STACKING COMPLETE! A 3-CAN TOWER WAS BUILT.\n")


# -----------------------------------------------------------
# API COMMUNICATION (UNCHANGED)
# -----------------------------------------------------------
def get_operator():
    url = f"https://api.interactions.ics.unisg.ch/{bot}/operator"
    response = requests.get(url)
    time.sleep(1)

    if response.status_code == 200:
        data = response.json()
        return data["token"], 200
    return None, response.status_code


def post_operator(name, email):
    url = f"https://api.interactions.ics.unisg.ch/{bot}/operator"
    response = requests.post(url, json={"name": name, "email": email})
    time.sleep(1)

    if response.status_code == 200:
        global token
        token = response.headers["Location"].split("/")[-1]
        return token, 200
    return 0, response.status_code


def delete_operator(token_delete):
    url = f"https://api.interactions.ics.unisg.ch/{bot}/operator/" + token_delete
    requests.delete(url)
    time.sleep(1)


def get_tcp_target():
    url = f"https://api.interactions.ics.unisg.ch/{bot}/tcp"
    headers = {"Authentication": token}
    response = requests.get(url, headers=headers)
    time.sleep(1)

    if response.status_code == 200:
        d = response.json()
        return (
            d["coordinate"]["x"],
            d["coordinate"]["y"],
            d["coordinate"]["z"],
            d["rotation"]["roll"],
            d["rotation"]["pitch"],
            d["rotation"]["yaw"],
        )
    return None


def put_tcp_target(x, y, z, roll, pitch, yaw):
    url = f"https://api.interactions.ics.unisg.ch/{bot}/tcp/target"
    headers = {"Authentication": token}

    data = {
        "target": {
            "coordinate": {"x": x, "y": y, "z": z},
            "rotation": {"roll": roll, "pitch": pitch, "yaw": yaw},
        },
        "speed": 50
    }

    print(f"📡 Sending move: {data}")
    response = requests.put(url, headers=headers, json=data)
    print(f"➡️ Response: {response.status_code}")
    time.sleep(1)


def put_gripper(param):
    url = f"https://api.interactions.ics.unisg.ch/{bot}/gripper"
    headers = {"Authentication": token}
    requests.put(url, headers=headers, json=param)
    time.sleep(1)


def get_gripper():
    url = f"https://api.interactions.ics.unisg.ch/{bot}/gripper"
    headers = {"Authentication": token}
    r = requests.get(url, headers=headers)
    time.sleep(1)

    if r.status_code == 200:
        return r.json()
    return None


def initialize():
    url = f"https://api.interactions.ics.unisg.ch/{bot}/initialize"
    headers = {"Authentication": token}
    requests.put(url, headers=headers)
    time.sleep(1)


# -----------------------------------------------------------
# COMMAND INTERFACE
# -----------------------------------------------------------
print("Commands:\nconnect\nauto\nmove_to x y z\nrotate deg\ntoggle\nget_tcp\nlog_off\nexit")

while True:
    cmd = input("\nCommand: ").lower().strip()
    parts = cmd.split()

    if cmd == "connect":
        token = log_on()

    elif cmd == "auto":
        auto_stack()

    elif parts[0] == "move_to":
        move_to_absolute(float(parts[1]), float(parts[2]), float(parts[3]))

    elif parts[0] == "rotate":
        rotate(float(parts[1]))

    elif cmd == "toggle":
        toggle()

    elif cmd == "get_tcp":
        print(get_tcp_target())

    elif cmd == "log_off":
        log_off()

    elif cmd == "exit":
        log_off()
        exit()

    else:
        print("Unknown command.")
