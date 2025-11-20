import time
import math
from coord_transform import camera_to_robot   # uses full homography

bot = "cherrybot"
DETECTION_FILE = "detected_coords.txt"

# -----------------------------------------------------------
# STACK POSITION SETTINGS (PYRAMIDS UP TO 6 CANS)
# -----------------------------------------------------------

CANHIGHT = 72  # mm  (can height)
Z_PICK = 200
Z_LIFT = 300

# -----------------------------------------------------------
# HELPER: compute pyramid positions for 1–6 cans  # NEW
# -----------------------------------------------------------
def get_stack_positions(num_cans):
    """
    Stacks all cans at y = -300.
    Bottom row starts at x = -100 and goes right with spacing = 70.
    """
    y = -300.0               # fixed row
    spacing = 70.0
    half = spacing / 2

    # Bottom row (max 3 cans)
    bottom = [
        -100.0,
        -100.0 + spacing,
        -100.0 + 2*spacing
    ]  # [-100, -30, 40]

    # Middle row (2 cans)
    center = (bottom[0] + bottom[2]) / 2   # -30
    mid = [
        center - half,   # -65
        center + half    # 5
    ]

    # Top row (1 can)
    top = [center]       # -30

    def z(layer):
        return Z_PICK + layer * CANHIGHT

    n = min(max(num_cans, 0), 6)
    positions = []

    if n == 1:
        positions.append((top[0], y, z(2)))
        return positions

    if n == 2:
        positions.append((mid[0], y, z(1)))
        positions.append((mid[1], y, z(1)))
        return positions

    if n == 3:
        positions.append((bottom[0], y, z(0)))
        positions.append((bottom[1], y, z(0)))
        positions.append((bottom[2], y, z(0)))
        return positions

    if n == 4:
        positions.append((bottom[0], y, z(0)))
        positions.append((bottom[1], y, z(0)))
        positions.append((bottom[2], y, z(0)))
        positions.append((mid[0],    y, z(1)))
        return positions

    if n == 5:
        positions.append((bottom[0], y, z(0)))
        positions.append((bottom[1], y, z(0)))
        positions.append((bottom[2], y, z(0)))
        positions.append((mid[0],    y, z(1)))
        positions.append((mid[1],    y, z(1)))
        return positions

    # full pyramid (3 + 2 + 1)
    positions.append((bottom[0], y, z(0)))
    positions.append((bottom[1], y, z(0)))
    positions.append((bottom[2], y, z(0)))
    positions.append((mid[0],    y, z(1)))
    positions.append((mid[1],    y, z(1)))
    positions.append((top[0],    y, z(2)))

    return positions
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

    x_new = x * math.cos(theta) - y * math.sin(theta)
    y_new = x * math.sin(theta) + y * math.cos(theta)
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
# PICK AND PLACE ONE CAN  (now takes z_stack)  # NEW
# -----------------------------------------------------------
def pick_and_place_can(i, x_robot, y_robot, x_stack, y_stack, z_stack):
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
    print(f"🟢 PLACE CAN {i} at: x={x_stack:.1f}, y={y_stack:.1f}, z={z_stack:.1f}")
    move_to_absolute(x_stack, y_stack, Z_LIFT)
    time.sleep(10)

    # Lower to stacking height for this layer
    move_to_absolute(x_stack, y_stack, z_stack)
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


def config_mode():
    print("\n⚙️ ENTERING CONFIG MODE")
    print("Place 4 cans into the robot's gripper when prompted.\n")

    rotate(45)
    time.sleep(6)

    rotate(45)
    time.sleep(6)

    move_to_absolute(0, -450, 300)
    time.sleep(10)

    for i, (x, y) in enumerate(CONFIG_POSITIONS):
        print(f"\n📍 Preparing position {i+1}: x={x}, y={y}")

        # Move above target
        move_to_absolute(x, y, Z_CONFIG_LIFT)
        time.sleep(5)

        # Lower to place height
        move_to_absolute(x, y, Z_CONFIG_PLACE)
        time.sleep(5)

        # OPEN gripper so you can place a can
        print("🤲 Please place a can into the gripper now.")
        toggle()  # open
        time.sleep(4)

        # CLOSE to hold the can
        toggle()  # close
        time.sleep(3)

        # Lift away
        move_to_absolute(x, y, Z_CONFIG_LIFT)
        time.sleep(5)

        print(f"✔️ Can {i+1} placed at config position.")

    print("\n🎉 CONFIGURATION COMPLETE — 4 CANS ARE PLACED.\n")


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

    # Convert to robot coordinates (keep FILE ORDER)
    detections_robot = [camera_to_robot(u, v) for (u, v) in detections_px]

    num_cans = min(len(detections_robot), 6)
    print(f"\n📦 Number of cans detected: {num_cans}")

    if num_cans == 0:
        print("⚠️ No cans to stack.")
        return

    stack_positions = get_stack_positions(num_cans)

    print("\n📌 DETECTIONS (robot coords, file order):")
    for d in detections_robot[:num_cans]:
        print(f"   x={d[0]:.1f}, y={d[1]:.1f}")

    print("\n🏗️ Using stack layout:")
    for i, (xs, ys, zs) in enumerate(stack_positions):
        print(f"   Slot {i}: x={xs:.1f}, y={ys:.1f}, z={zs:.1f}")

    # Pick & stack cans according to file order and chosen pyramid
    for i in range(num_cans):
        x_r, y_r = detections_robot[i]
        x_stack, y_stack, z_stack = stack_positions[i]
        pick_and_place_can(i, x_r, y_r, x_stack, y_stack, z_stack)

    print("\n🎉 STACKING COMPLETE!\n")


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
print("Commands:\nconnect\nconfig\nauto\nmove_to x y z\nrotate deg\ntoggle\nget_tcp\nlog_off\nexit")

while True:
    cmd = input("\nCommand: ").lower().strip()
    parts = cmd.split()

    if cmd == "connect":
        token = log_on()

    elif cmd == "config":
        config_mode()

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