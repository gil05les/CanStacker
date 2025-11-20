import cv2
import numpy as np
from collections import defaultdict, deque

OUTPUT_FILE = "detected_coords.txt"
CAMERA_SOURCE = 0

# Expected radius range for cans
RADIUS_MIN = 39
RADIUS_MAX = 44

# Number of frames to average per can
BUFFER_SIZE = 200

# Dictionary of buffers: { index: deque }
buffers = defaultdict(lambda: deque(maxlen=BUFFER_SIZE))

cap = cv2.VideoCapture(CAMERA_SOURCE)
if not cap.isOpened():
    print("❌ Could not open camera.")
    exit()

print("🎯 Multi-can detection active — each can needs 200 detections.")

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    frame = cv2.resize(frame, (960, 540))
    annotated = frame.copy()

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.medianBlur(gray, 7)

    circles = cv2.HoughCircles(
        blur,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=60,
        param1=100,
        param2=30,
        minRadius=RADIUS_MIN,
        maxRadius=RADIUS_MAX
    )

    if circles is not None:
        circles = np.uint16(np.around(circles))[0]

        # Sort left → right so cans always get consistent indices
        circles = sorted(circles, key=lambda c: c[0])

        for idx, (x, y, r) in enumerate(circles):

            # --- Draw circle ---
            cv2.circle(annotated, (x, y), r, (0, 255, 0), 2)
            cv2.circle(annotated, (x, y), 3, (0, 0, 255), -1)

            # --- Label CAN ID ---
            label = f"CAN {idx}"
            cv2.putText(
                annotated,
                label,
                (x - 40, y - r - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

            # Add coordinates to buffer
            buffers[idx].append((x, y))

            print(f"Can {idx}: {len(buffers[idx])}/200 samples   Latest=({x}, {y})")

    # Draw count of detected cans
    cv2.putText(
        annotated,
        f"Cans detected: {len(buffers)}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (0, 255, 255),
        2
    )

    cv2.imshow("Multi-can Detector", annotated)

    # Check if ALL cans reached 200 samples
    if len(buffers) > 0 and all(len(buffers[i]) == BUFFER_SIZE for i in buffers.keys()):
        print("\n🎉 All cans reached 200 samples! Writing to file...")

        with open(OUTPUT_FILE, "w") as f:
            for i in sorted(buffers.keys()):
                xs = [p[0] for p in buffers[i]]
                ys = [p[1] for p in buffers[i]]
                avg_x = np.mean(xs)
                avg_y = np.mean(ys)
                f.write(f"{avg_x:.1f} {avg_y:.1f}\n")

                print(f"📝 CAN {i} averaged pixel coords: {avg_x:.1f}, {avg_y:.1f}")

        print("🛑 Detection completed — exiting.\n")
        break

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("\n🛑 Detection aborted.")
        break

cap.release()
cv2.destroyAllWindows()
