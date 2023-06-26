import cv2


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

    # original_frame = frame.copy()

    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # release the camera and close the window
    cap.release()

    # return the captured frame
    return frame


def compare_histograms(image1, image2):
    hist1 = cv2.calcHist([image1], [0], None, [256], [0, 256])
    hist2 = cv2.calcHist([image2], [0], None, [256], [0, 256])
    return cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
