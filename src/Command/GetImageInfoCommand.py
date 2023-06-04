import time

from src.Command.Command import Command
from src.Module.Vision.google_vision import get_image_labels, get_image_texts
from src.Module.Vision.huggingface_query import get_image_caption


class GetImageInfoCommand(Command):
    def __init__(self, sys_config):
        super().__init__()
        self.silence_start_time = None
        self.system_config = sys_config

    def execute(self):
        photo_label = get_image_labels(self.system_config.latest_photo_file_path)
        photo_ocr = get_image_texts(self.system_config.latest_photo_file_path)
        photo_caption = get_image_caption(self.system_config.latest_photo_file_path)
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
