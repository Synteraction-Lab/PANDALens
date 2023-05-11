import urllib
from collections import deque

import cv2
import numpy as np
from ultralyticsplus import YOLO, render_result
from src.Module.Gaze.frame_stream import PupilCamera
import json

import ssl

ssl._create_default_https_context = ssl._create_unverified_context


class ObjectDetector:
    def __init__(self, simulate=False):
        # load model
        self.frame_height = None
        self.frame_width = None
        self.GAZE_SLIDE_WINDOW_SIZE = 10  # Adjust the size according to your frame rate (e.g., 30 FPS = 45 for 1.5 seconds)
        self.gaze_positions_window = deque(maxlen=self.GAZE_SLIDE_WINDOW_SIZE)
        self.fixation_detected = False

        self.prev_object = None
        self.model = YOLO('ultralyticsplus/yolov8s')

        # set model parameters
        self.model.overrides['conf'] = 0.3  # NMS confidence threshold
        self.model.overrides['iou'] = 0.1  # NMS IoU threshold
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

    def detect_fixation(self):
        if self.frame_height is None or self.frame_width is None:
            return
        frame_height, frame_width = self.frame_height, self.frame_width
        threshold = 0.1 * min(frame_width, frame_height)

        self.gaze_positions_window.append(self.gaze_position)

        if len(self.gaze_positions_window) < self.GAZE_SLIDE_WINDOW_SIZE:
            return

        x_positions, y_positions = zip(*self.gaze_positions_window)
        min_x, max_x = min(x_positions), max(x_positions)
        min_y, max_y = min(y_positions), max(y_positions)

        area_width = max_x - min_x
        area_height = max_y - min_y

        self.fixation_detected = area_width <= threshold and area_height <= threshold

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
        #
        frame = self.find_gaze_object(frame)

        # draw gaze position
        cv2.circle(frame, self.gaze_position, 10, (0, 0, 255), 2)
        # draw yellow fixation position
        cv2.circle(frame, self.fixation_position, 10, (0, 255, 255), 3)

        cv2.imshow('YOLO Object Detection', frame)

    def find_gaze_object(self, frame):
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
        frame = np.array(render.convert('RGB'))
        # self.detect_fixation()
        if self.fixation_detected:
            cv2.putText(frame, "Fixation Detected", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        return frame

    def detect_zoom_in_with_pupil_core(self):
        camera = PupilCamera(frame_format="bgr")
        try:
            while True:
                recent_world = None
                gaze_x, gaze_y = None, None
                gaze_x_list = []
                gaze_y_list = []
                fixation_x, fixation_y = None, None
                # self.gaze_position = None
                fixation_conf = 0
                gaze_timestamp = None
                frame_timestamp = None
                while camera.has_new_data_available():
                    topic, msg = camera.recv_from_sub()
                    # print(topic)

                    # if topic.startswith("frame.") and msg["format"] != camera.FRAME_FORMAT:
                    #     print(
                    #         f"different frame format ({msg['format']}); "
                    #         f"skipping frame from {topic}"
                    #     )
                    #     continue

                    if topic == "fixations":
                        if msg["confidence"] > fixation_conf:
                            fixation_conf = msg["confidence"]
                            fixation_x, fixation_y = msg['norm_pos']
                    elif topic == "gaze.3d.01.":
                        # if msg['confidence'] > 0.1:
                        gaze_x, gaze_y = msg['norm_pos']
                        gaze_x_list.append(gaze_x)
                        gaze_y_list.append(gaze_y)


                    elif topic == "frame.world":
                        recent_world = np.frombuffer(
                            msg["__raw_data__"][0], dtype=np.uint8
                        ).reshape(msg["height"], msg["width"], 3)
                if recent_world is not None:
                    frame = recent_world
                    frame_height, frame_width = frame.shape[:2]
                    self.frame_height = frame_height
                    self.frame_width = frame_width
                    if fixation_x is not None and fixation_y is not None:
                        fixation_y = 1 - fixation_y
                        self.fixation_position = (int(fixation_x * frame_width), int(fixation_y * frame_height))
                        # print(f"Fixation: {self.fixation_position}")
                    if gaze_x is not None and gaze_y is not None:
                        gaze_x = float(np.array(gaze_x_list).mean())
                        gaze_y = 1 - float(np.array(gaze_y_list).mean())
                        self.gaze_position = (int(gaze_x * frame_width), int(gaze_y * frame_height))
                        # print(f"Gaze: {self.gaze_position} Conf: {conf}")
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
    detector.detect_zoom_in_with_pupil_core()
