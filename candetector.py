import cv2
from ultralytics import YOLO

# --- Camera source ---
# If using an IP Camera app, replace the line below with your stream URL:
# CAMERA_SOURCE = "http://192.168.1.12:8080/video"
CAMERA_SOURCE = 0  # 0 or 1 if using EpocCam as webcam

# --- Load YOLOv8 model ---
# "n" = nano model (fast), you can switch to "s" for more accuracy
model = YOLO("yolov8n.pt")

# --- Open camera ---
cap = cv2.VideoCapture(CAMERA_SOURCE)
if not cap.isOpened():
    print("❌ Could not open camera. Check connection or IP address.")
    exit()

print("✅ Camera stream opened. Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("⚠️ Frame not received.")
        continue

    # --- Run YOLO inference ---
    results = model(frame)
    annotated = frame.copy()

    for box in results[0].boxes:
        cls = int(box.cls[0])
        label = model.names[cls].lower()

        # Filter for likely "can" objects
        if any(k in label for k in ["can", "bottle", "drink", "cup"]):
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            conf = float(box.conf[0])
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 255), 2)
            cv2.putText(annotated, f"{label} ({conf:.2f})", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            cv2.putText(annotated, f"pos: ({cx}, {cy})", (x1, y2 + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            print(f"🧃 Detected {label} at (x={cx}, y={cy}) conf={conf:.2f}")

    cv2.imshow("Can Detector (press 'q' to quit)", annotated)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
