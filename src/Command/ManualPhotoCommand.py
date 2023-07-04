import os
import warnings
from datetime import datetime

import cv2

import numpy as np

from src.Command.Command import Command
from src.Module.Vision.utilities import take_picture

warnings.filterwarnings("ignore", category=FutureWarning)


class ManualPhotoCommand(Command):
    def __init__(self, sys_config):
        super().__init__()
        self.system_config = sys_config

    def execute(self):
        print("Manual photo command is executed")
        image_folder = self.system_config.get_image_folder()
        now_time = datetime.now().strftime("%H_%M_%S")

        photo_file_path = os.path.join(image_folder, f'{now_time}.png')

        if self.system_config.vision_detector.original_frame is not None:
            frame = self.system_config.vision_detector.original_frame.copy()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        else:
            frame = take_picture(photo_file_path)

        os.makedirs(os.path.dirname(photo_file_path), exist_ok=True)
        cv2.imwrite(photo_file_path, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

        self.system_config.set_latest_photo_file_path(photo_file_path)

        self.system_config.potential_interested_frame = cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR)
        return frame
        # notification = f"You seem to interested in your front scene. Any comments?"
        # self.system_config.notification = {'notif_type': 'text',
        #                                    'content': notification,
        #                                    'position': 'top-center'}
        # self.system_config.audio_feedback_to_show = notification

        # return frame
