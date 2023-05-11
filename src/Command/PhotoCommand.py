import os
from datetime import datetime
from tkinter import filedialog

import cv2

from src.Command.Command import Command
from src.Module.Vision.utilities import take_picture


class PhotoCommand(Command):
    def __init__(self, sys_config):
        super().__init__()
        self.system_config = sys_config

    def execute(self):
        if self.system_config.get_test_mode():
            # enable users select an image from their local machine
            last_image_folder_in_test_mode = self.system_config.last_image_folder_in_test_mode
            latest_photo_file_path = filedialog.askopenfilename(initialdir=last_image_folder_in_test_mode,
                                                                title="Select image file",
                                                                filetypes=(
                                                                    ("jpg files", "*.jpg"),
                                                                    ("jpeg files", "*.jpeg"),
                                                                    ("png files", "*.png"),
                                                                    ("all files", "*.*")))
            self.system_config.set_latest_photo_file_path(latest_photo_file_path)
            self.system_config.last_image_folder_in_test_mode = os.path.dirname(latest_photo_file_path)
            frame = cv2.imread(latest_photo_file_path)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        else:
            image_folder = self.system_config.get_image_folder()
            latest_photo_file_path = os.path.join(image_folder, f'{datetime.now().strftime("%H_%M_%S")}.png')
            self.system_config.set_latest_photo_file_path(latest_photo_file_path)
            frame = take_picture(latest_photo_file_path)

        return frame

    def undo(self):
        pass
