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
# 3-can stack (two-base + one top)
STACK_POSITIONS_3 = [
    (0, -400),    # base left
    (70, -400),   # base right
    (35, -400),   # top center
]

# 6-can pyramid stack (three base, two mid, one top)
STACK_POSITIONS_6 = [
    (0, -400),   # base far left
    (70, -400),    # base center
    (140, -400),   # base far right
    (35, -400),     # middle left
    (105, -400),    # middle right
    (70, -400),    # top center
]

# Backward-compatible alias for existing 3-can stack
STACK_POSITIONS = STACK_POSITIONS_3

CAN_HEIGHT = 72
Z_PICK = 200
Z_LIFT = 300
Z_2ND_ROW = Z_PICK + CAN_HEIGHT
Z_TOP_ROW = Z_PICK + 2 * CAN_HEIGHT

# Z targets for stack layouts
STACK_Z_TARGETS_3 = [Z_PICK, Z_PICK, Z_2ND_ROW]
STACK_Z_TARGETS_6 = [Z_PICK, Z_PICK, Z_PICK, Z_2ND_ROW, Z_2ND_ROW, Z_TOP_ROW]

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
