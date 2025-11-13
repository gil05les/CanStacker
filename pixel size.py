import cv2

points = []

def click_event(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append((x, y))
        if len(points) == 2:
            (x1, y1), (x2, y2) = points
            dist = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
            print(f"Pixel distance: {dist:.1f}px")
            points.clear()

cap = cv2.VideoCapture(0)
print("Click on the left and right edges of the paper.")
while True:
    ret, frame = cap.read()
    if not ret:
        break
    cv2.imshow("Click two edges of paper (q to quit)", frame)
    cv2.setMouseCallback("Click two edges of paper (q to quit)", click_event)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
cap.release()
cv2.destroyAllWindows()
