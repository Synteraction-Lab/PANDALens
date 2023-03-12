import cv2
import numpy as np


class ObjectDetector:
    def __init__(self, model_cfg_path, model_weight_path, labels_path, interests):
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
        print("Your interests include:")
        print(self.interest_labels)

    def detect(self, image):
        # Prepare the frame for object detection
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
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)
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
                    label += " (Interest detected)"
                cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)
                cv2.putText(image, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

        return image


# Define the video capture device (use 0 for default)
cap = cv2.VideoCapture(0)

# Define the user's interests (modify this list based on the user's input)
interests = [14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]

# Create an instance of the ObjectDetector class
detector = ObjectDetector('yolov3.cfg', 'yolov3.weights', 'coco.names', interests)

# Loop through the frames in the video stream
while True:
    # Capture frame-by-frame
    ret, img = cap.read()

    if ret:
        # Detect objects in the frame
        output_img = detector.detect(img)

        # Display the resulting frame
        cv2.imshow('frame', output_img)

        # Exit the loop when 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
