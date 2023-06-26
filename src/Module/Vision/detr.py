import asyncio
import ssl

import cv2
import numpy as np
import torch
from PIL import Image
from transformers import DetrImageProcessor, DetrForObjectDetection

ssl._create_default_https_context = ssl._create_unverified_context


class ObjectDetector:
    def __init__(self):
        self.processor = DetrImageProcessor.from_pretrained("facebook/detr-resnet-50")
        self.model = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-50")
        self.last_detection = None

    async def detect_objects(self, image):
        # preprocess the image for the model
        inputs = self.processor(images=image, return_tensors="pt")

        # run the model on the image
        outputs = self.model(**inputs)

        # convert the model output to COCO API format
        # only keep detections with score > 0.6
        target_sizes = torch.tensor([image.size[::-1]])
        results = self.processor.post_process_object_detection(outputs, target_sizes=target_sizes, threshold=0.6)[0]

        # loop through each detected object and draw a bounding box on the frame
        boxes = []
        for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
            box = [int(i) for i in box.tolist()]
            label_text = self.model.config.id2label[label.item()]
            boxes.append((label_text, score, box))
            self.last_detection = (label_text, score, box)
        return boxes

    async def annotate_frame(self, frame):
        # convert the frame to a PIL image
        image = Image.fromarray(frame)

        # detect objects every 5 frames
        if self.last_detection is None or np.random.rand() < 0.8:
            boxes = await self.detect_objects(image)
        else:
            label_text, score, box = self.last_detection
            boxes = [(label_text, score, box)]

        # draw bounding boxes on the frame
        for label_text, score, box in boxes:
            cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), (0, 255, 0), 2)
            cv2.putText(frame, f"{label_text}: {score:.2f}", (box[0], box[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (0, 255, 0), 2)

        return frame


async def main():
    # set up the webcam
    cap = cv2.VideoCapture(0)

    detector = ObjectDetector()

    i = 0
    while True:
        # capture a frame from the webcam
        ret, frame = cap.read()
        if not ret:
            break

        # skip every other frame
        if i % 2 == 0:
            # annotate the frame with detected objects
            annotated_frame = await detector.annotate_frame(frame)

            # show the annotated frame
            cv2.imshow('Webcam', annotated_frame)

            # break the loop if the 'q' key is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        i += 1

    # release the webcam and close the window
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    asyncio.run(main())
