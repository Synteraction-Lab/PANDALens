import os.path
import ssl
import threading

import numpy as np
import sounddevice as sd

import io
import os
import speech_recognition as sr
import whisper
import torch

from datetime import datetime, timedelta
from queue import Queue
from tempfile import NamedTemporaryFile
from time import sleep

ssl._create_default_https_context = ssl._create_unverified_context


def show_devices():
    """
    Print a list of available input devices.
    """
    devices = sd.query_devices()
    input_devices = [device for device in devices if device['max_input_channels'] > 0]
    print(input_devices)


def get_recording_devices():
    devices = sd.query_devices()
    input_devices = [device for device in devices if device['max_input_channels'] > 0]
    return input_devices


class LiveTranscriber:
    def __init__(self, model="small.en", device_index='MacBook Pro Microphone', silence_threshold=0.02):
        self.stop_listening = None
        self.model = model
        self.device_index = device_index
        self.phrase_timeout = 3
        self.record_timeout = 2
        self.silence_threshold = silence_threshold
        self.stop_event = threading.Event()
        self.stop_event.set()
        self.full_text = ""

        self.recorder = sr.Recognizer()
        self.recorder.energy_threshold = 1000
        self.recorder.dynamic_energy_threshold = False

        self.silence_start = None
        self.silence_end = None

        mic_name = sd.query_devices(self.device_index)['name']
        for index, name in enumerate(sr.Microphone.list_microphone_names()):
            if mic_name in name:
                self.source = sr.Microphone(sample_rate=16000, device_index=index)
                break
        else:
            raise ValueError(f"No microphone named \"{mic_name}\" found")

        # self.recorder.adjust_for_ambient_noise(self.source)
        self.audio_model = whisper.load_model(self.model)

        self.temp_file = NamedTemporaryFile().name
        self.transcription = ['']

        with self.source:
            self.recorder.adjust_for_ambient_noise(self.source)

        self.data_queue = Queue()

    def rms(self, data):
        """
        Calculates the root mean square of the audio data.
        """
        audio_data = np.frombuffer(data, dtype=np.int16)
        return np.sqrt(np.mean(np.square(audio_data)))

    def record_callback(self, _, audio: sr.AudioData) -> None:
        data = audio.get_raw_data()
        self.data_queue.put(data)

    def run(self):
        last_sample = bytes()
        phrase_time = None

        self.stop_listening = self.recorder.listen_in_background(self.source, self.record_callback,
                                                                 phrase_time_limit=self.record_timeout)

        while not self.stop_event.is_set():
            now = datetime.utcnow()
            if not self.data_queue.empty():
                phrase_complete = False
                if phrase_time and now - phrase_time > timedelta(seconds=self.phrase_timeout):
                    last_sample = bytes()
                    phrase_complete = True
                phrase_time = now

                while not self.data_queue.empty():
                    data = self.data_queue.get()
                    last_sample += data

                audio_data = sr.AudioData(last_sample, self.source.SAMPLE_RATE, self.source.SAMPLE_WIDTH)
                wav_data = io.BytesIO(audio_data.get_wav_data())

                with open(self.temp_file, 'w+b') as f:
                    f.write(wav_data.read())

                result = self.audio_model.transcribe(self.temp_file, fp16=torch.cuda.is_available())
                text = result['text'].strip()

                if phrase_complete:
                    self.transcription.append(text)
                else:
                    self.transcription[-1] = text

                os.system('clear' if os.name == 'posix' else 'cls')
                for line in self.transcription:
                    print(line)
                print('', end='', flush=True)

                sleep(0.25)

    def start(self):
        self.stop_event.clear()
        self.record_thread = threading.Thread(target=self.run)
        self.record_thread.start()

    def stop(self):
        self.stop_event.set()
        self.stop_listening(wait_for_stop=False)
        self.record_thread.join()
        final_result = " ".join(self.transcription)
        self.full_text = ""
        self.transcription = ['']
        return final_result


if __name__ == '__main__':
    transcriber = LiveTranscriber()
    transcriber.start()
    input("Press enter to stop")
    print(transcriber.stop())
