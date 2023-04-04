from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification
import cv2
import numpy as np

# load the MobileNet model and preprocessor
preprocessor = AutoImageProcessor.from_pretrained("google/mobilenet_v2_1.0_224")
model = AutoModelForImageClassification.from_pretrained("google/mobilenet_v2_1.0_224")

# set up the webcam
cap = cv2.VideoCapture(0)

# loop through each frame of the webcam feed
while True:
    # capture a frame from the webcam
    ret, frame = cap.read()

    # convert the frame to a PIL image
    image = Image.fromarray(frame)

    # preprocess the image for the model
    inputs = preprocessor(images=image, return_tensors="pt")

    # classify the image using the model
    outputs = model(**inputs)
    logits = outputs.logits

    # get the predicted class index, label, and score
    predicted_class_idx = logits.argmax(-1).item()
    predicted_class_label = model.config.id2label[predicted_class_idx]
    predicted_class_score = logits.softmax(-1)[0][predicted_class_idx].item()

    # draw the predicted label and score on the frame
    label_text = f"{predicted_class_label}: {predicted_class_score:.2f}"
    cv2.putText(frame, label_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

    # show the frame with the predicted label and score
    cv2.imshow('Webcam', frame)

    # break the loop if the 'q' key is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# release the webcam and close the window
cap.release()
cv2.destroyAllWindows()
