
import cv2

RTSP_URL = "rtsp://192.168.0.100"

# You can pass cv2.CAP_FFMPEG to force ffmpeg backend on some builds
cap = cv2.VideoCapture(RTSP_URL, cv2.CAP_FFMPEG)

if not cap.isOpened():
    raise RuntimeError("Could not open RTSP stream")

while True:
    ok, frame = cap.read()
    if not ok:
        print("Frame grab failed, retrying...")
        # A short wait helps when network hiccups occur
        if cv2.waitKey(30) == 27:
            break
        continue

    cv2.imshow("RTSP Stream (q to quit)", frame)
    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()