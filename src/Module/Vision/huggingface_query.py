import json
import requests
from transformers import pipeline
import os

API_TOKEN = os.environ["HUGGINGFACE_API_KEY"]
headers = {"Authorization": f"Bearer {API_TOKEN}"}
IMAGE_CLASSIFICATION_API_URL = "https://api-inference.huggingface.co/models/google/vit-base-patch16-224"
OBJECT_DETECTION_API_URL = "https://api-inference.huggingface.co/models/facebook/detr-resnet-50"
IMAGE_CAPTION_API_URL = "https://api-inference.huggingface.co/models/nlpconnect/vit-gpt2-image-captioning"


def query(filename, model_url, timeout=5):
    try:
        with open(filename, "rb") as f:
            sent_data = f.read()
        response = requests.post(model_url, headers=headers, data=sent_data, timeout=timeout)
        response.raise_for_status()
        content_type = response.headers.get("Content-Type")
        if "application/json" in content_type:
            return json.loads(response.content.decode("utf-8"))
        else:
            return {}  # Return an empty dictionary for non-JSON responses
    except Exception as e:
        print(f"Error querying model {model_url}: {e}")
        return {}  # Return an empty dictionary for errors


def get_image_caption(image_path):
    try:
        response = query(image_path, model_url=IMAGE_CAPTION_API_URL)
        return response[0]['generated_text']
    except Exception as e:
        image_to_text = pipeline("image-to-text", model="nlpconnect/vit-gpt2-image-captioning")
        return image_to_text(image_path)[0]['generated_text']


if __name__ == '__main__':
    image_path = "../../../data/test_data/cable.JPG"
    data = get_image_caption(image_path)

    print(data)

# # Run Locally
# from transformers import pipeline
# from PIL import Image
#
# image_to_text = pipeline("image-to-text", model="nlpconnect/vit-gpt2-image-captioning")
#
# image_path = 'party.jpg'
# image = Image.open(image_path)
#
# print(image_to_text(image))
