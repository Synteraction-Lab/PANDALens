import os
from time import sleep

import pyaudio
import wave

from utilities import remove_file


class AudioCapture:
    def __init__(self, file_path):
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 2
        self.RATE = 44100
        self.WAVE_OUTPUT_FILENAME = file_path
        self.is_recording = False

        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=self.FORMAT,
                                  channels=self.CHANNELS,
                                  rate=self.RATE,
                                  input=True,
                                  frames_per_buffer=self.CHUNK)

    def start_recording(self):
        os.makedirs(os.path.dirname(self.WAVE_OUTPUT_FILENAME), exist_ok=True)
        remove_file(self.WAVE_OUTPUT_FILENAME)
        print("* recording")
        self.frames = []
        self.is_recording = True
        while self.is_recording:
            data = self.stream.read(self.CHUNK)
            self.frames.append(data)

    def stop_recording(self):
        print("* done recording")
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

        wf = wave.open(self.WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        self.is_recording = False


if __name__ == '__main__':
    screen_capture = AudioCapture("data/output.wav")
    screen_capture.start_recording()
    sleep(10)
    screen_capture.stop_recording()
