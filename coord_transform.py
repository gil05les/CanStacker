# ---------------------------------------------
# coord_transform.py — CAMERA → ROBOT transform
# Using 4-point HOMOGRAPHY (perspective correct)
# ---------------------------------------------
import numpy as np
import cv2
from config import CONFIG_POSITIONS



# ---------------------------------------------
# Calibration points
# ---------------------------------------------
# Robot coordinates in mm (Robot moves automatically to these positions in the config mode)
CAN_0_ROBOT, CAN_1_ROBOT, CAN_2_ROBOT, CAN_3_ROBOT = CONFIG_POSITIONS

# Camera pixel coordinates (px) corresponding to the above robot positions (These have to be measured with detection_one_picture.py)
CAN_0_CAMERA = (420.6000, 263.4000)
CAN_1_CAMERA = (281.4000, 256.2000)
CAN_2_CAMERA = (412.2000, 397.8000)
CAN_3_CAMERA = (275.4000, 391.8000)

# ---------------------------------------------
# Build 3×3 homography H  such that:
#   [x, y, 1]^T  =  H  ·  [u, v, 1]^T
# ---------------------------------------------
camera_points = np.array([CAN_0_CAMERA, CAN_1_CAMERA, CAN_2_CAMERA, CAN_3_CAMERA], dtype=np.float32)
robot_points = np.array([CAN_0_ROBOT, CAN_1_ROBOT, CAN_2_ROBOT, CAN_3_ROBOT], dtype=np.float32)

H, _ = cv2.findHomography(camera_points, robot_points)

# ---------------------------------------------
# Convert CAMERA → ROBOT coordinates (u, v)
# ---------------------------------------------
def camera_to_robot(u, v):
    pt = np.array([[u, v, 1]], dtype=np.float32).T
    mapped = H @ pt

    # divide by w to convert from homogeneous
    x = mapped[0] / mapped[2]
    y = mapped[1] / mapped[2]

    return float(x), float(y)
