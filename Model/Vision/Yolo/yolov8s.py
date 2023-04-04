import cv2
import numpy as np
from ultralyticsplus import YOLO, render_result

# load model
model = YOLO('ultralyticsplus/yolov8s')

# set model parameters
model.overrides['conf'] = 0.25  # NMS confidence threshold
model.overrides['iou'] = 0.45  # NMS IoU threshold
model.overrides['agnostic_nms'] = False  # NMS class-agnostic
model.overrides['max_det'] = 1000  # maximum number of detections per image


# open webcam
cap = cv2.VideoCapture(0)

while True:
    # read frame from webcam
    ret, frame = cap.read()

    # run inference
    results = model.predict(frame)
    boxes = results[0].boxes
    labels = {}
    for xyxy, conf, cls in zip(boxes.xyxy, boxes.conf, boxes.cls):
        labels[model.model.names[int(cls)]] = float(conf)

    print(labels)

    # draw bounding boxes on frame
    render = render_result(model=model, image=frame, result=results[0])

    # convert PIL image to numpy array
    render = np.array(render.convert('RGB'))

    cv2.imshow('YOLO Object Detection', render)

    # press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# release webcam and close windows
cap.release()
cv2.destroyAllWindows()
