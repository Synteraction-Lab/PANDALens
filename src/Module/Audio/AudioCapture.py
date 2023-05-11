import subprocess
from time import sleep
import os

from src.Utilities.file import remove_file, get_system_name


class AudioCapture:
    def __init__(self, file_path, audio_idx):
        self.AUDIO_DEVICES_IDX = audio_idx
        self.recording_cmd = None
        self.process = None
        self.file_path = file_path

    def start_recording(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        remove_file(self.file_path)

        if get_system_name() == "Windows":
            self.recording_cmd = 'ffmpeg -f dshow -i audio="{}" {}'.format(
                self.AUDIO_DEVICES_IDX, self.file_path)

        elif get_system_name() == "Darwin":
            self.recording_cmd = 'ffmpeg -f avfoundation -i :"{}" {}'.format(
                self.AUDIO_DEVICES_IDX, self.file_path)

        self.process = subprocess.Popen(self.recording_cmd, stdin=subprocess.PIPE, shell=True)

    def stop_recording(self):
        self.process.stdin.write('q'.encode("GBK"))
        self.process.communicate()
        self.process.wait()


if __name__ == '__main__':
    screen_capture = AudioCapture()
    screen_capture.start_recording()
    sleep(10)
    screen_capture.stop_recording()
