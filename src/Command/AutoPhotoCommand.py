import os
import warnings
from datetime import datetime

import PIL.Image
import cv2
import imquality.brisque as brisque
import numpy as np

from src.Command.Command import Command
from src.Data.SystemConfig import SystemConfig
from src.Module.Vision.utilities import take_picture

warnings.filterwarnings("ignore", category=FutureWarning)


def find_best_quality_img(img_directory, prefix):
    best_quality = float('inf')  # Initialize with infinity; lower score means better quality
    best_img_filename = ''
    best_quality_img = None

    for filename in os.listdir(img_directory):
        if filename.startswith(prefix) and (filename.endswith('.png') or filename.endswith('.jpg')):
            img = PIL.Image.open(os.path.join(img_directory, filename))
            score = brisque.score(img)

            if score < best_quality:  # Lower score is better
                best_quality = score
                best_img_filename = filename
                best_quality_img = img

    return best_img_filename, best_quality, best_quality_img


AUTO_PHOTO_NUM = 3


class AutoPhotoCommand(Command):
    def __init__(self, sys_config):
        super().__init__()
        self.system_config = sys_config

    def execute(self):
        image_folder = self.system_config.get_image_folder()
        now_time = datetime.now().strftime("%H_%M_%S")
        for i in range(AUTO_PHOTO_NUM):
            photo_file_path = os.path.join(image_folder, f'{now_time}_{i}.png')

            if self.system_config.vision_detector.original_frame is not None:
                frame = self.system_config.vision_detector.original_frame.copy()
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:
                frame = take_picture(photo_file_path)

            os.makedirs(os.path.dirname(photo_file_path), exist_ok=True)
            cv2.imwrite(photo_file_path, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

        latest_photo_filename, _, frame = find_best_quality_img(image_folder, prefix=now_time)
        self.system_config.set_latest_photo_file_path(os.path.join(image_folder, latest_photo_filename))

        # remove all the photos other than the best one
        for filename in os.listdir(image_folder):
            if filename.startswith(now_time) and (filename.endswith('.png') or filename.endswith('.jpg')):
                if filename != latest_photo_filename:
                    os.remove(os.path.join(image_folder, filename))

        self.system_config.potential_interested_frame = cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR)
        return frame


def test():
    sys_config = SystemConfig()
    sys_config.set_vision_analysis()

    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    image_folder = os.path.join(project_root, "data", "recordings", "test_data", "auto_image")

    sys_config.image_folder = image_folder

    # Create AutoPhotoCommand object
    auto_photo_cmd = AutoPhotoCommand(sys_config)

    # Execute the command and get the frame with the best quality
    best_frame = auto_photo_cmd.execute()

    # Display the PIL frame
    best_frame.show()


if __name__ == "__main__":
    test()
