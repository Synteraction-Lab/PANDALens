# import json
# import os
# from io import BytesIO
#
# import requests
# from PIL import Image
# from transformers import pipeline
#
# API_TOKEN = os.environ["HUGGINGFACE_API_KEY"]
# headers = {"Authorization": f"Bearer {API_TOKEN}"}
# IMAGE_CLASSIFICATION_API_URL = "https://api-inference.huggingface.co/models/google/vit-base-patch16-224"
# OBJECT_DETECTION_API_URL = "https://api-inference.huggingface.co/models/facebook/detr-resnet-50"
# IMAGE_CAPTION_API_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-large"
#
#
# def compress_image(image_path, max_size=720):
#     image = Image.open(image_path)
#     image.thumbnail((max_size, max_size))
#     compressed_image = BytesIO()
#     image.save(compressed_image, format='JPEG')
#     compressed_image.seek(0)
#     return compressed_image
#
#
# def query(filename, model_url, timeout=4):
#     try:
#         sent_data = compress_image(filename)
#         response = requests.post(model_url, headers=headers, data=sent_data, timeout=timeout)
#         response.raise_for_status()
#         content_type = response.headers.get("Content-Type")
#         if "application/json" in content_type:
#             return json.loads(response.content.decode("utf-8"))
#         else:
#             return {}  # Return an empty dictionary for non-JSON responses
#     except Exception as e:
#         print(f"Error querying model {model_url}: {e}")
#         return {}  # Return an empty dictionary for errors
#
#
# def get_image_caption(image_path):
#     try:
#         response = query(image_path, model_url=IMAGE_CAPTION_API_URL)
#         return response[0]['generated_text']
#     except Exception as e:
#         # image_to_text = pipeline("image-to-text", model="nlpconnect/vit-gpt2-image-captioning")
#         return None
#
#
# if __name__ == '__main__':
#     image_path = "../../../data/test_data/panda.JPG"
#     data = get_image_caption(image_path)
#
#     print(data)


from io import BytesIO
import base64
import requests
import os
from PIL import Image


def compress_image(image_path, max_size=720):
    image = Image.open(image_path)
    image.thumbnail((max_size, max_size))
    compressed_image = BytesIO()
    image.save(compressed_image, format='JPEG')
    compressed_image.seek(0)
    return compressed_image


# Function to encode the image to a base64 string
def encode_image(compressed_image):
    return base64.b64encode(compressed_image.getvalue()).decode('utf-8')


def get_image_caption(image_path):
    # Encode the image
    compressed_image = compress_image(image_path)

    # Encode the compressed image
    base64_image = encode_image(compressed_image)
    api_key = os.environ["OPENAI_API_KEY_U1"]

    # Prepare headers with your OpenAI API Key
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    # Define the payload with the encoded image and your question
    payload = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Generate a brief caption for user's FPV."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 60
    }

    # Make the API request
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

    # Check if the response is successful
    if response.status_code == 200:
        response_data = response.json()
        # Assuming the API returns a field that contains the generated caption
        # You might need to adjust the following line according to the actual structure of the response
        return response_data['choices'][0]['message']['content']
    else:
        print(f"Failed to get caption: {response.text}")
        return None


# Usage
if __name__ == '__main__':
    image_path = "../../../data/test_data/panda.JPG"
    caption = get_image_caption(image_path)
    print(caption)
