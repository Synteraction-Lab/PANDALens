import cv2
import os


def take_picture(save_path=None):
    # create a VideoCapture object to access the camera
    cap = cv2.VideoCapture(0)

    # check if camera is opened successfully
    if not cap.isOpened():
        print("Error opening camera")
        return None

    # read a frame from the camera
    ret, frame = cap.read()

    # check if frame is captured successfully
    if not ret:
        print("Error capturing frame")
        return None

    original_frame = frame.copy()

    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # frame[:, :, 2] = np.clip(frame[:, :, 2] * 0.8, 0, 255).astype(np.uint8)

    if save_path is not None:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        cv2.imwrite(save_path, original_frame)

    # release the camera and close the window
    cap.release()

    # return the captured frame
    return frame
