import concurrent.futures

from src.Command.Command import Command
from src.Module.Vision.google_vision import get_image_labels, get_image_texts
from src.Module.Vision.huggingface_query import get_image_caption

from io import BytesIO

from PIL import Image

MAX_SIZE = 720


def compress_image(image_path, max_size=MAX_SIZE):
    image = Image.open(image_path)
    image.thumbnail((max_size, max_size))
    compressed_image = BytesIO()
    image.save(compressed_image, format='JPEG')
    return compressed_image


class GetImageInfoCommand(Command):
    def __init__(self, sys_config):
        super().__init__()
        self.silence_start_time = None
        self.system_config = sys_config

    def execute(self):
        try:
            img = compress_image(self.system_config.latest_photo_file_path)
        except Exception as e:
            print(e)
            image_info = {"error": "Image is not found"}
            self.system_config.image_info_dict[self.system_config.latest_photo_file_path] = image_info
            return image_info

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_label = executor.submit(get_image_labels, img)
            future_to_ocr = executor.submit(get_image_texts, img)
            img.seek(0)
            future_to_caption = executor.submit(get_image_caption, img)

            try:
                photo_label = future_to_label.result()
            except Exception as e:
                print("Error in getting image info using Google Vision API: ", e)
                photo_label = None

            try:
                photo_ocr = future_to_ocr.result()
            except Exception as e:
                print("Error in getting image info using Google Vision API: ", e)
                photo_ocr = None

            try:
                photo_caption = future_to_caption.result()
            except Exception as e:
                print("Error in getting image info using Huggingface API: ", e)
                photo_caption = None

        image_info = {}

        moment_idx = self.system_config.get_moment_idx()
        moment_idx += 1
        self.system_config.set_moment_idx(moment_idx)
        image_info["no."] = moment_idx

        if photo_label is not None:
            image_info["photo_label"] = photo_label.rstrip()
        if photo_ocr is not None:
            image_info["photo_ocr"] = photo_ocr.rstrip()
        if photo_caption is not None:
            image_info["photo_caption"] = photo_caption.rstrip()

        self.system_config.image_info_dict[self.system_config.latest_photo_file_path] = image_info

        return image_info
