import subprocess
from time import sleep
import os

from utilities import remove_file


class AudioCapture:
    def __init__(self, file_path):
        self.AUDIO_DEVICES_IDX = None
        self.recording_cmd = None
        self.process = None
        self.file_path = file_path

    def start_recording(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        remove_file(self.file_path)
        self.AUDIO_DEVICES_IDX = "1"
        self.recording_cmd = 'ffmpeg -f avfoundation -capture_cursor 1 -i :"4" -r 12 {}'.format(self.file_path)
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
