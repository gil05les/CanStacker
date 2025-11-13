# ---------------------------------------------
# coord_transform.py — CAMERA → ROBOT transform
# Using 4-point HOMOGRAPHY (perspective correct)
# ---------------------------------------------
import numpy as np
import cv2

# ---------------------------------------------
# Calibration points
# ---------------------------------------------
# Robot coordinates in mm
CAN_A_R = (-200.0, -300.0)
CAN_B_R = (100.0, -300.0)
CAN_C_R = (-200.0, -450.0)
CAN_D_R = (100.0, -450.0)

# Camera pixel coordinates (px)
CAN_A_C = (194.7, 469.3)
CAN_B_C = (154.4,  86.0)
CAN_C_C = (377.1, 439.6)
CAN_D_C = (336.7,  85.0)

# ---------------------------------------------
# Build 3×3 homography H  such that:
#   [x, y, 1]^T  =  H  ·  [u, v, 1]^T
# ---------------------------------------------
src_pts = np.array([CAN_A_C, CAN_B_C, CAN_C_C, CAN_D_C], dtype=np.float32)
dst_pts = np.array([CAN_A_R, CAN_B_R, CAN_C_R, CAN_D_R], dtype=np.float32)

H, _ = cv2.findHomography(src_pts, dst_pts)


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
