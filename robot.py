import requests
import time
import math
from coord_transform import camera_to_robot   # uses full homography

bot = "cherrybot"
DETECTION_FILE = "detected_coords.txt"

# -----------------------------------------------------------
# STACK POSITION SETTINGS
# -----------------------------------------------------------

CANHIGHT = 72  # mm (can height)
Z_PICK = 200
Z_LIFT = 300

FIXED_X = -400          # << NEW — all cans stacked at x = -400
ROW_SPACING = 70        # spacing in Y direction


CONFIG_POSITIONS = [
    (0,   -400),
    (100, -400),
    (0,   -300),
    (100, -300)
]

Z_CONFIG_LIFT = 300
Z_CONFIG_PLACE = 200

# -----------------------------------------------------------
# HELPER: compute vertical-line pyramid (1–6 cans)
# -----------------------------------------------------------
def get_stack_positions(num_cans):
    """
    Stacks all cans in a vertical line at x = FIXED_X.
    Spacing only in Y direction.
    """
    base_y = -300
    spacing = ROW_SPACING

    # bottom row (3 cans)
    bottom = [
        base_y - spacing,
        base_y,
        base_y + spacing
    ]

    # middle row (2 cans)
    mid_center = base_y
    mid = [
        mid_center - spacing/2,
        mid_center + spacing/2
    ]

    # top row (1 can)
    top = [mid_center]

    def z(layer):
        return Z_PICK + layer * CANHIGHT

    n = min(max(num_cans, 0), 6)
    pos = []

    if n == 1:
        return [(FIXED_X, top[0], z(2))]

    if n == 2:
        return [
            (FIXED_X, mid[0], z(1)),
            (FIXED_X, mid[1], z(1)),
        ]

    if n == 3:
        return [
            (FIXED_X, bottom[0], z(0)),
            (FIXED_X, bottom[1], z(0)),
            (FIXED_X, bottom[2], z(0)),
        ]

    if n == 4:
        return [
            (FIXED_X, bottom[0], z(0)),
            (FIXED_X, bottom[1], z(0)),
            (FIXED_X, bottom[2], z(0)),
            (FIXED_X, mid[0],    z(1)),
        ]

    if n == 5:
        return [
            (FIXED_X, bottom[0], z(0)),
            (FIXED_X, bottom[1], z(0)),
            (FIXED_X, bottom[2], z(0)),
            (FIXED_X, mid[0],    z(1)),
            (FIXED_X, mid[1],    z(1)),
        ]

    # 6 cans: full vertical pyramid: 3 bottom, 2 mid, 1 top
    return [
        (FIXED_X, bottom[0], z(0)),
        (FIXED_X, bottom[1], z(0)),
        (FIXED_X, bottom[2], z(0)),
        (FIXED_X, mid[0],    z(1)),
        (FIXED_X, mid[1],    z(1)),
        (FIXED_X, top[0],    z(2)),
    ]


# -----------------------------------------------------------
# READ DETECTIONS
# -----------------------------------------------------------
def read_all_detections():
    print("📄 Waiting for detected cans...")

    while True:
        try:
            with open(DETECTION_FILE, "r") as f:
                lines = [l.strip() for l in f.readlines() if l.strip()]

            if not lines:
                continue

            cans_px = []
            for line in lines:
                parts = line.split()
                if len(parts) >= 2:
                    u, v = map(float, parts[:2])
                    cans_px.append((u, v))

            if cans_px:
                print(f"📥 Found {len(cans_px)} detections.")
                return cans_px

        except FileNotFoundError:
            pass

        time.sleep(0.1)


# -----------------------------------------------------------
# MOVEMENT: simple version (you said keep)
# -----------------------------------------------------------
def move_to_absolute(x, y, z, roll=180, pitch=0, yaw=180):
    print(f"🧭 Moving to: x={x}, y={y}, z={z}")
    put_tcp_target(x, y, z, roll, pitch, yaw)


def rotate(angle):
    coords = get_tcp_target()
    if not coords:
        print("⚠ Could not read TCP.")
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
        print("🤏 Closing")
        put_gripper(800)
    else:
        print("👐 Opening")
        put_gripper(630)


# -----------------------------------------------------------
# PICK + PLACE
# -----------------------------------------------------------
def pick_and_place_can(i, x_robot, y_robot, x_stack, y_stack, z_stack):
    print(f"\n🔵 PICK CAN {i} from x={x_robot:.1f}, y={y_robot:.1f}")

    move_to_absolute(x_robot, y_robot, Z_LIFT)
    time.sleep(5)

    move_to_absolute(x_robot, y_robot, Z_PICK)
    time.sleep(5)

    toggle()
    time.sleep(1)

    move_to_absolute(x_robot, y_robot, Z_LIFT)
    time.sleep(10)

    print(f"🟢 PLACE CAN {i} at x={x_stack}, y={y_stack}, z={z_stack}")
    move_to_absolute(x_stack, y_stack, Z_LIFT)
    time.sleep(10)

    move_to_absolute(x_stack, y_stack, z_stack)
    time.sleep(10)

    toggle()
    time.sleep(1)

    move_to_absolute(x_stack, y_stack, Z_LIFT)
    time.sleep(6)


# -----------------------------------------------------------
# AUTO STACK
# -----------------------------------------------------------
def auto_stack():
    print("\n🤖 STARTING AUTO STACK...\n")

    rotate(45); time.sleep(6)
    rotate(45); time.sleep(6)

    move_to_absolute(0, -450, 300)
    time.sleep(10)

    detections = read_all_detections()

    detections_robot = [camera_to_robot(u, v) for (u, v) in detections]

    num_cans = min(len(detections_robot), 6)

    print(f"\n📦 Number of cans: {num_cans}")

    stack_positions = get_stack_positions(num_cans)

    for i in range(num_cans):
        x_r, y_r = detections_robot[i]
        x_s, y_s, z_s = stack_positions[i]
        pick_and_place_can(i, x_r, y_r, x_s, y_s, z_s)

    print("\n🎉 STACKING FINISHED!\n")


# -----------------------------------------------------------
# API COMMUNICATION
# -----------------------------------------------------------
def get_operator():
    url = f"https://api.interactions.ics.unisg.ch/{bot}/operator"
    r = requests.get(url)
    time.sleep(1)
    if r.status_code == 200:
        return r.json()["token"], 200
    return None, r.status_code


def post_operator(name, email):
    url = f"https://api.interactions.ics.unisg.ch/{bot}/operator"
    r = requests.post(url, json={"name": name, "email": email})
    time.sleep(1)
    if r.status_code == 200:
        global token
        token = r.headers["Location"].split("/")[-1]
        return token, 200
    return None, r.status_code


def delete_operator(t):
    url = f"https://api.interactions.ics.unisg.ch/{bot}/operator/" + t
    requests.delete(url)
    time.sleep(1)


def get_tcp_target():
    url = f"https://api.interactions.ics.unisg.ch/{bot}/tcp"
    r = requests.get(url, headers={"Authentication": token})
    time.sleep(1)
    if r.status_code == 200:
        d = r.json()
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
    body = {
        "target": {
            "coordinate": {"x": x, "y": y, "z": z},
            "rotation": {"roll": roll, "pitch": pitch, "yaw": yaw},
        },
        "speed": 50
    }
    print("📤 Sending:", body)
    r = requests.put(url, headers={"Authentication": token}, json=body)
    print("➡ Response:", r.status_code)
    time.sleep(1)


def put_gripper(v):
    url = f"https://api.interactions.ics.unisg.ch/{bot}/gripper"
    requests.put(url, headers={"Authentication": token}, json=v)
    time.sleep(1)


def get_gripper():
    url = f"https://api.interactions.ics.unisg.ch/{bot}/gripper"
    r = requests.get(url, headers={"Authentication": token})
    time.sleep(1)
    if r.status_code == 200:
        return r.json()
    return None


def initialize():
    url = f"https://api.interactions.ics.unisg.ch/{bot}/initialize"
    requests.put(url, headers={"Authentication": token})
    time.sleep(1)


# -----------------------------------------------------------
# COMMAND INTERFACE
# -----------------------------------------------------------
print("Commands:\nconnect\nauto\ntoggle\nmove_to x y z\nrotate deg\nget_tcp\nlog_off\nexit")

while True:
    cmd = input("\nCommand: ").lower().strip()
    parts = cmd.split()

    if cmd == "connect":
        token = log_on()

    elif cmd == "auto":
        auto_stack()

    elif cmd == "toggle":
        toggle()

    elif parts[0] == "move_to":
        move_to_absolute(float(parts[1]), float(parts[2]), float(parts[3]))

    elif parts[0] == "rotate":
        rotate(float(parts[1]))

    elif cmd == "get_tcp":
        print(get_tcp_target())

    elif cmd == "log_off":
        log_off()

    elif cmd == "exit":
        log_off()
        exit()

    else:
        print("Unknown command.")