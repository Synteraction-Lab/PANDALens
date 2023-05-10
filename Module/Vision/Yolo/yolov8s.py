import urllib

import cv2
import numpy as np
from ultralyticsplus import YOLO, render_result
from Module.Gaze.frame_stream import PupilCamera
import json

import ssl

ssl._create_default_https_context = ssl._create_unverified_context


class ObjectDetector:
    def __init__(self, simulate=False):
        # load model
        self.prev_object = None
        self.model = YOLO('ultralyticsplus/yolov8s')

        # set model parameters
        self.model.overrides['conf'] = 0.3  # NMS confidence threshold
        self.model.overrides['iou'] = 0.5  # NMS IoU threshold
        self.model.overrides['agnostic_nms'] = False  # NMS class-agnostic
        self.model.overrides['max_det'] = 100  # maximum number of detections per image
        self.model.overrides['verbose'] = False  # print all detections

        self.classifier = YOLO('ultralyticsplus/yolov8s-cls')
        self.classifier.overrides['verbose'] = False
        self.classifier.overrides['conf'] = 0.9  # NMS confidence threshold

        self.distance_threshold = 100  # adjust as needed

        # load the mapping file
        self.class_idx = None
        self.map_imagenet_id()

        # open webcam
        self.cap = cv2.VideoCapture(0)

        # Define a threshold for zoom detection
        self.zoom_threshold = 0.1  # adjust as needed

        # Initialize gaze position
        self.gaze_position = (0, 0)  # replace with actual gaze tracking data
        self.fixation_position = (0, 0)
        self.prev_size = 0

        cv2.namedWindow('YOLO Object Detection')
        if simulate:
            cv2.setMouseCallback('YOLO Object Detection', self.mouse_callback)

    def map_imagenet_id(self):
        url = "https://s3.amazonaws.com/deep-learning-models/image-models/imagenet_class_index.json"
        urllib.request.urlretrieve(url, "imagenet_class_index.json")

        # load the mapping file
        with open("imagenet_class_index.json", "r") as f:
            self.class_idx = json.load(f)

    def mouse_callback(self, event, x, y, flags, param):
        # Update gaze_position with cursor position
        if event == cv2.EVENT_MOUSEMOVE:
            # print(x, y)
            self.gaze_position = (x, y)

    def process_frame(self, frame):
        results = self.model.predict(frame)
        boxes = results[0].boxes

        closest_object = None
        closest_distance = float('inf')
        closest_size = 0

        # Sort the boxes by whether they contain gaze_position and their area
        sorted_boxes = sorted(zip(boxes.xyxy, boxes.conf, boxes.cls), key=lambda box: (
            not (box[0][0] <= self.gaze_position[0] <= box[0][2] and box[0][1] <= self.gaze_position[1] <= box[0][3]),
            (box[0][2] - box[0][0]) * (box[0][3] - box[0][1])
        ))

        for xyxy, conf, cls in sorted_boxes:
            object_label = self.model.model.names[int(cls)]
            # # only consider finer classification for objects that are not people
            # if object_label != 'person':
            #     x1, y1, x2, y2 = xyxy
            #     object_image = frame[int(y1):int(y2), int(x1):int(x2)]
            #
            #     # object_label = self.classifier.predict(object_image)'s highest confidence label
            #     probs = self.classifier.predict(object_image)[0].probs
            #     idx = np.argmax(probs)
            #     object_label = self.class_idx[str(int(idx))][1]

            dx = max(xyxy[0] - self.gaze_position[0], 0, self.gaze_position[0] - xyxy[2])
            dy = max(xyxy[1] - self.gaze_position[1], 0, self.gaze_position[1] - xyxy[3])
            distance = np.sqrt(dx ** 2 + dy ** 2)

            if distance < closest_distance:
                closest_object = object_label
                closest_distance = distance
                closest_size = (xyxy[2] - xyxy[0]) * (xyxy[3] - xyxy[1])

        cv2.putText(frame, f"gaze:{self.gaze_position}, distance: {closest_distance},", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

        if closest_distance <= self.distance_threshold and closest_object is not None:
            label_text = f"User is looking at a {closest_object}"
            cv2.putText(frame, label_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

            # Compare sizes only if the current and previous objects are the same
            if self.prev_object == closest_object and closest_size > self.prev_size * (1 + self.zoom_threshold):
                label_text = f"User zoomed in / moved closer to the {closest_object}"
                cv2.putText(frame, label_text, (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 0, 0), 2)

            # Update the previous object and size
            self.prev_object = closest_object
            self.prev_size = closest_size
        else:
            label_text = "User is not looking at any object"
            cv2.putText(frame, label_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)

        render = render_result(model=self.model, image=frame, result=results[0])
        render = np.array(render.convert('RGB'))

        # draw gaze position
        cv2.circle(render, self.gaze_position, 10, (0, 0, 255), 2)

        cv2.imshow('YOLO Object Detection', render)

    def detect_zoom_in_with_pupil_core(self):
        camera = PupilCamera(frame_format="bgr")
        gaze_x, gaze_y = None, None
        fixation_x, fixation_y = None, None
        try:
            while True:
                recent_world = None
                while camera.has_new_data_available():
                    topic, msg = camera.recv_from_sub()

                    if topic == "fixations":
                        # print(
                        #     f"Fixation: Normal Pos: {msg['norm_pos']}, Duration: {msg['duration']}, Confidence: {msg['confidence']}")
                        fixation_x, fixation_y = msg['norm_pos']
                        # map gaze position (percentage) to frame size

                    if topic == "gaze.3d.1.":
                        gaze_x, gaze_y = msg['norm_pos']

                    if topic.startswith("frame.") and msg["format"] != camera.FRAME_FORMAT:
                        print(
                            f"different frame format ({msg['format']}); "
                            f"skipping frame from {topic}"
                        )
                        continue

                    if topic == "frame.world":
                        recent_world = np.frombuffer(
                            msg["__raw_data__"][0], dtype=np.uint8
                        ).reshape(msg["height"], msg["width"], 3)

                if recent_world is not None:
                    frame = recent_world
                    frame_height, frame_width = frame.shape[:2]
                    if fixation_x is not None and fixation_y is not None:
                        fixation_y = 1 - fixation_y
                        self.fixation_position = (int(fixation_x * frame_width), int(fixation_y * frame_height))
                        # print(f"Fixation: {self.fixation_position}")
                    if gaze_x is not None and gaze_y is not None:
                        gaze_y = 1 - gaze_y
                        self.gaze_position = (int(gaze_x * frame_width), int(gaze_y * frame_height))
                        # print(f"Gaze: {self.gaze_position}")

                    self.process_frame(frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        except KeyboardInterrupt:
            pass
        finally:
            cv2.destroyAllWindows()

    def detect_zoom_in(self):
        while True:
            ret, frame = self.cap.read()

            if ret is None:
                continue

            self.process_frame(frame)

            # # press 'q' to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    # Set simulate to False if you use Pupil Core. Set to True to use mouse cursor.
    detector = ObjectDetector(simulate=True)
    detector.detect_zoom_in()
