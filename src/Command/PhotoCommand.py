import os
from datetime import datetime

import cv2
import numpy as np

from src.Command.Command import Command
from src.Module.Vision.utilities import take_picture
from src.Utilities.image_processor import store_img


class PhotoCommand(Command):
    def __init__(self, sys_config):
        super().__init__()
        self.system_config = sys_config

    def execute(self):
        try:
            print("Pending photo command is executed")
            image_folder = self.system_config.get_image_folder()
            now_time = datetime.now().strftime("%H_%M_%S")

            photo_file_path = os.path.join(image_folder, f'{now_time}.png')

            original_frame = self.system_config.vision_detector.get_original_frame()

            if original_frame:
                frame = cv2.cvtColor(original_frame, cv2.COLOR_BGR2RGB)
            else:
                frame = take_picture()
                original_frame = cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR)

            store_img(photo_file_path, frame)
            return original_frame
        except:
            print("Manual photo command is not executed")
            return None
