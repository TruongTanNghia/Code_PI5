import cv2

cap = cv2.VideoCapture(1, cv2.CAP_V4L2)  # d?i s? cho d�ng

if not cap.isOpened():
    print("? OpenCV kh�ng m? du?c camera")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("? Kh�ng d?c du?c frame")
        break

    cv2.imshow("Test", frame)
    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()
