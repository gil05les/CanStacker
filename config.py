"""Shared configuration for detection and robot interaction."""

# Camera / detection
CAMERA_SOURCE = 0
DETECTION_FILE = "detected_coords.txt"
FRAME_SIZE = (960, 540)
RADIUS_MIN = 39
RADIUS_MAX = 44

# Robot identifiers
BOT_NAME = "cherrybot"

# Positions (mm)
STACK_POSITIONS = [
    (0, -400),
    (70, -400),
    (35, -400),
]

CAN_HEIGHT = 72
Z_PICK = 200
Z_LIFT = 300
Z_2ND_ROW = Z_PICK + CAN_HEIGHT

CONFIG_POSITIONS = [
    (0, -400),
    (100, -400),
    (0, -300),
    (100, -300),
]

# Named robot coordinates for the four calibration/placement cans (aliases)
CAN_0_ROBOT, CAN_1_ROBOT, CAN_2_ROBOT, CAN_3_ROBOT = CONFIG_POSITIONS

# Gripper values
GRIPPER_OPEN = 800
GRIPPER_CLOSE = 630
