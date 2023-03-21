import time
from datetime import datetime

import cv2
import numpy as np
from PIL import ImageGrab


def is_image_blurry(image, threshold=1.5):
    """
    Determines whether an image is blurry.

    Args:
        image (str): The image.
        threshold (float): The threshold value for blur. Default is 1.5.

    Returns:
        bool: True if the image is blurry, False otherwise.
    """
    # Convert image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian blur
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # Calculate the Laplacian operator
    laplacian = cv2.Laplacian(blur, cv2.CV_64F)

    # Calculate the gradient value of the image
    sobel = cv2.convertScaleAbs(laplacian)

    # Calculate the average grayscale value of the image
    mean = cv2.mean(sobel)[0]

    print(mean)
    # Determine if the image is blurry
    if mean < threshold:
        return True
    else:
        return False


def get_object_box(detection, height, width):
    center_x = int(detection[0] * width)
    center_y = int(detection[1] * height)
    w = int(detection[2] * width)
    h = int(detection[3] * height)
    x = int(center_x - w / 2)
    y = int(center_y - h / 2)
    return h, w, x, y


class ObjectDetector:
    def __init__(self, model_cfg_path, model_weight_path, labels_path, interests):
        self.previous_interested_object_set = {}
        # Load the YOLOv3 object detection model
        self.net = cv2.dnn.readNet(model_cfg_path, model_weight_path)

        # Load the labels from the coco.names file
        with open(labels_path, 'r') as f:
            self.classes = [line.strip() for line in f.readlines()]

        # Define empty dictionary to hold colors for each detected object
        self.colors = {}

        # Define the user's interests
        self.interests = interests
        self.interest_labels = [self.classes[i] for i in interests]
        print("Your interests include: ", self.interest_labels)

    def detect(self, image):
        # Prepare the frame for object detection
        interested_classes = []

        original_image = image
        image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
        height, width, _ = image.shape
        blob = cv2.dnn.blobFromImage(image, 1 / 255, (416, 416), (0, 0, 0), swapRB=True, crop=False)

        # Set the input to the YOLOv3 model
        self.net.setInput(blob)

        # Run object detection on the frame
        layerOutputs = self.net.forward(self.net.getUnconnectedOutLayersNames())

        # Process the output and draw bounding boxes around detected objects
        boxes = []
        confidences = []
        class_ids = []
        for output in layerOutputs:
            for detection in output:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > 0.5:
                    h, w, x, y = get_object_box(detection, height, width)
                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)

        # Apply non-maximum suppression to remove overlapping boxes
        indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

        # Draw the remaining boxes and labels on the frame
        for i in range(len(boxes)):
            if i in indexes:
                x, y, w, h = boxes[i]
                label = self.classes[class_ids[i]]
                if label not in self.colors:
                    self.colors[label] = np.random.uniform(0, 255, size=(3,))
                color = self.colors[label]
                if class_ids[i] in self.interests:
                    interested_classes.append(class_ids[i])
                    label += " (Interest detected)"
                    cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)
                    cv2.putText(image, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                    cv2.imshow("interested_frame", image)

        if is_image_blurry(original_image):
            return

        if self.check_new_interested_object(interested_classes):
            cv2.imwrite(f'{datetime.now().strftime("%H_%M_%S")}_'
                        f'{[self.classes[i] for i in set(interested_classes)]}.png', image)

        return image

    def check_new_interested_object(self, interested_classes):
        current_frame_interested_set = set(sorted(interested_classes))
        if not set(current_frame_interested_set).issubset(self.previous_interested_object_set) \
                and current_frame_interested_set != set():
            self.previous_interested_object_set = current_frame_interested_set
            print(current_frame_interested_set)
            return True
        return False


if __name__ == '__main__':
    # Define the video capture device (use 0 for default)
    cap = cv2.VideoCapture(0)

    # Define the user's interests (modify this list based on the user's input)
    interests = [14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]

    # Create an instance of the ObjectDetector class
    detector = ObjectDetector('yolov3.cfg', 'yolov3.weights', 'coco.names', interests)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')

    # Get the frame rate of the input video
    fps = 8

    # Define the video writer object with output file name, codec, fps, and frame size
    out = cv2.VideoWriter('output.mp4', fourcc, fps, (int(cap.get(3)), int(cap.get(4))))

    frame_count = 0
    start_time = time.time()

    # Loop through the frames in the video stream
    while True:
        # Capture frame-by-frame
        ret, img = cap.read()

        if ret:
            frame_count += 1

            if frame_count % 4 == 0:
            # Detect objects in the frame
                img = detector.detect(img)

            # Write the output frame to the video file
            out.write(img)

            # # Display the resulting frame
            # cv2.imshow('frame', output_img)


            elapsed_time = time.time() - start_time
            fps = frame_count / elapsed_time
            print(f'Realtime FPS: {fps:.2f}')

            # Exit the loop when 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    out.release()
    cv2.destroyAllWindows()
