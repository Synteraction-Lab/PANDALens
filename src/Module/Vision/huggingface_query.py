import json
import os
from io import BytesIO

import requests
from PIL import Image
from transformers import pipeline

API_TOKEN = os.environ["HUGGINGFACE_API_KEY"]
headers = {"Authorization": f"Bearer {API_TOKEN}"}
IMAGE_CLASSIFICATION_API_URL = "https://api-inference.huggingface.co/models/google/vit-base-patch16-224"
OBJECT_DETECTION_API_URL = "https://api-inference.huggingface.co/models/facebook/detr-resnet-50"
IMAGE_CAPTION_API_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large"


def compress_image(image_path, max_size=720):
    image = Image.open(image_path)
    image.thumbnail((max_size, max_size))
    compressed_image = BytesIO()
    image.save(compressed_image, format='JPEG')
    compressed_image.seek(0)
    return compressed_image


def query(filename, model_url, timeout=3.5):
    try:
        sent_data = compress_image(filename)
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
        # image_to_text = pipeline("image-to-text", model="nlpconnect/vit-gpt2-image-captioning")
        return None


if __name__ == '__main__':
    image_path = "../../../data/test_data/panda.JPG"
    data = get_image_caption(image_path)

    print(data)
