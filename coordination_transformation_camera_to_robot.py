# ---------------------------------------------
# coordination_transformation_camera_to_robot.py
# CAMERA → ROBOT transform using 4-point HOMOGRAPHY
# ---------------------------------------------
import numpy as np
import cv2
from config import CONFIG_POSITIONS


# ---------------------------------------------
# Calibration points
# ---------------------------------------------
# Robot coordinates in mm (robot moves automatically to these positions in the config mode)
CAN_0_ROBOT, CAN_1_ROBOT, CAN_2_ROBOT, CAN_3_ROBOT = CONFIG_POSITIONS

# Camera pixel coordinates (px) corresponding to the above robot positions (measure with detect_single_frame.py)
CAN_0_CAMERA = (427.8000, 238.2000)
CAN_1_CAMERA = (288.6000, 233.4000)
CAN_2_CAMERA = (425.4000, 375.0000)
CAN_3_CAMERA = (285.0000 , 371.4000)


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
