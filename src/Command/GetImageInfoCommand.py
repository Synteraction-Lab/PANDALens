import io
import time

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
        img = compress_image(self.system_config.latest_photo_file_path)

        try:
            photo_label = get_image_labels(img)
            photo_ocr = get_image_texts(img)
        except Exception as e:
            print("Error in getting image info using Google Vision API: ", e)
            photo_label = None
            photo_ocr = None
        try:
            img.seek(0)
            photo_caption = get_image_caption(img)
        except:
            print("Error in getting image info using Huggingface API.")
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

        return image_info
