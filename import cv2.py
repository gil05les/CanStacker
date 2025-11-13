import cv2
import numpy as np
import csv
import time

# --- Configuration ---
CAMERA_SOURCE = 0  # or your IP camera URL
CM_PER_PIXEL = 21 / 367  # = 0.055 cm per pixel
MIN_BLACK_AREA = 1000

# --- Open camera ---
cap = cv2.VideoCapture(CAMERA_SOURCE)
if not cap.isOpened():
    print("❌ Could not open camera.")
    exit()
print("✅ Camera stream opened. Press 'q' to quit.")

# --- Prepare CSV output ---
csv_file = open("detections.csv", mode="w", newline="")
csv_writer = csv.writer(csv_file)
csv_writer.writerow(["timestamp", "type", "x_cm", "y_cm", "size", "confidence"])

while True:
    ret, frame = cap.read()
    if not ret:
        print("⚠️ Frame not received.")
        continue

    frame = cv2.resize(frame, (960, 540))
    annotated = frame.copy()

    FRAME_CENTER_X = frame.shape[1] / 2
    FRAME_CENTER_Y = frame.shape[0] / 2

    # --- Circle detection ---
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.medianBlur(gray, 7)

    circles = cv2.HoughCircles(
        blur,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=50,
        param1=100,
        param2=30,
        minRadius=15,
        maxRadius=150
    )

    if circles is not None:
        circles = np.uint16(np.around(circles))
        for (x, y, r) in circles[0, :]:
            # Convert pixel → cm
            x_cm = (x - FRAME_CENTER_X) * CM_PER_PIXEL
            y_cm = (y - FRAME_CENTER_Y) * CM_PER_PIXEL

            # Draw and label
            cv2.circle(annotated, (x, y), r, (0, 255, 0), 3)
            cv2.circle(annotated, (x, y), 3, (0, 0, 255), -1)
            cv2.putText(annotated, f"circle", (x - 25, y - r - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            print(f"⭕ Circle at ({x_cm:.2f}, {y_cm:.2f}) cm, radius={r}px")
            csv_writer.writerow([time.time(), "circle", x_cm, y_cm, r, 1.0])

    # --- Black object detection ---
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_black = np.array([0, 0, 0])
    upper_black = np.array([180, 255, 70])
    mask_black = cv2.inRange(hsv, lower_black, upper_black)

    kernel = np.ones((7, 7), np.uint8)
    mask_black = cv2.morphologyEx(mask_black, cv2.MORPH_OPEN, kernel)
    mask_black = cv2.morphologyEx(mask_black, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask_black, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < MIN_BLACK_AREA:
            continue

        x, y, w, h = cv2.boundingRect(cnt)
        cx, cy = x + w // 2, y + h // 2

        x_cm = (cx - FRAME_CENTER_X) * CM_PER_PIXEL
        y_cm = (cy - FRAME_CENTER_Y) * CM_PER_PIXEL

        cv2.rectangle(annotated, (x, y), (x + w, y + h), (255, 0, 0), 3)
        cv2.putText(annotated, "black rectangle", (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

        print(f"⬛ Black rectangle at ({x_cm:.2f}, {y_cm:.2f}) cm, area={area}")
        csv_writer.writerow([time.time(), "black_rectangle", x_cm, y_cm, area, 1.0])

    # --- Display ---
    cv2.imshow("Object Detector (press 'q' to quit)", annotated)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

csv_file.close()
cap.release()
cv2.destroyAllWindows()
print("💾 Data saved to detections.csv")
