import cv2
import numpy as np

from config import CAMERA_SOURCE, DETECTION_FILE, FRAME_SIZE, RADIUS_MIN, RADIUS_MAX

def detect_once():
    """Captures one frame, detects cans, returns annotated image and circle list."""
    cap = cv2.VideoCapture(CAMERA_SOURCE)
    if not cap.isOpened():
        print("Could not open camera.")
        exit()

    ret, frame = cap.read()
    cap.release()
    if not ret:
        print("Failed to capture frame.")
        return None, []

    frame = cv2.resize(frame, FRAME_SIZE)
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
        circles = circles[0]
        circles = sorted(circles, key=lambda c: c[0])

        for idx, (x, y, r) in enumerate(circles):
            cv2.circle(annotated, (int(x), int(y)), int(r), (0, 255, 0), 2)
            cv2.circle(annotated, (int(x), int(y)), 3, (0, 0, 255), -1)
            cv2.putText(
                annotated,
                f"CAN {idx}",
                (int(x) - 40, int(y) - int(r) - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

    return annotated, circles if circles is not None else []


def detect_cans():
    print("Starting one-shot can detection.")

    while True:
        annotated, circles = detect_once()

        if annotated is None:
            continue

        cv2.imshow("Detection Preview", annotated)
        print(f"Detected {len(circles)} cans.")
        print("Is the detection good? (y/n) (Not in the terminal window, click on the image window)")

        key = None
        while key not in ["y", "n"]:
            key = chr(cv2.waitKey(0) & 0xFF)

        if key == "y" and len(circles) > 0:
            with open(DETECTION_FILE, "w") as f:
                for idx, (x, y, r) in enumerate(circles):
                    f.write(f"{x:.4f} {y:.4f}\n")
                    print(f"Saved CAN {idx}: {x:.4f}, {y:.4f}")

            print("Detection confirmed. Coordinates saved.")
            break

        else:
            print("Retrying...")
            cv2.destroyWindow("Detection Preview")

    cv2.destroyAllWindows()

if __name__ == "__main__":
    detect_cans()
