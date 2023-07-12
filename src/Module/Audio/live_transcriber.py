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

from transformers import pipeline

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
        self.scores = None
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

        # mode is either voice_transcription or emotion_classification
        self.mode = "emotion_classification"

        self.silence_start = None
        self.silence_end = None

        device_index = None

        for index, info in enumerate(sd.query_devices()):
            if info['name'] == self.device_index and info['max_input_channels'] > 0:
                device_index = index
                break

        if device_index is not None:
            self.source = sr.Microphone(sample_rate=16000, device_index=device_index)
        else:
            raise ValueError(f"No input microphone named \"{self.device_index}\" found")

        # self.recorder.adjust_for_ambient_noise(self.source)
        self.audio_model = whisper.load_model(self.model)

        self.temp_file = NamedTemporaryFile().name
        self.transcription = ['']

        self.lock = threading.Lock()

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

                if self.mode == "voice_transcription":
                    with self.lock:
                        result = self.audio_model.transcribe(self.temp_file, fp16=torch.cuda.is_available())
                        text = result['text'].strip()

                        if phrase_complete:
                            self.transcription.append(text)
                        else:
                            self.transcription[-1] = text

                        # os.system('clear' if os.name == 'posix' else 'cls')
                        # for line in self.transcription:
                        #     print(line)
                        print(" ".join(self.transcription))
                else:
                    result = self.audio_model.transcribe(self.temp_file, fp16=torch.cuda.is_available(),
                                                         no_speech_threshold=0.2,
                                                         logprob_threshold=None, )
                    text = result['text'].strip()

                    if phrase_complete:
                        self.transcription.append(text)
                        if text != "":
                            self.analyze_emotion(text)
                        else:
                            self.scores = None
                    else:
                        self.transcription[-1] = text

                    os.system('clear' if os.name == 'posix' else 'cls')
                    # for line in self.transcription:
                    #     print(line)
                    if self.scores:
                        print(f"Sentence: {text}, Joy score: {self.scores['joy']}",
                              f"Surprise score: {self.scores['surprise']}")
                print('', end='', flush=True)

                sleep(0.25)

    def analyze_emotion(self, text):
        classifier = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base",
                              return_all_scores=True)
        # Flattening the data
        data = classifier(text)[0]

        # Create a dictionary to store scores
        score_dict = {}

        # Iterating over the data and storing scores in dictionary
        for d in data:
            score_dict[d['label']] = d['score']

        self.scores = score_dict

    def start(self):
        self.stop_event.clear()
        self.record_thread = threading.Thread(target=self.run)
        self.record_thread.start()

    def stop_transcription_and_start_emotion_classification(self):
        with self.lock:
            final_result = " ".join(self.transcription)
        self.full_text = ""
        self.transcription = ['']
        self.model = "small.en"
        self.mode = "emotion_classification"
        return final_result.strip()

    def stop_emotion_classification_and_start_transcription(self):
        with self.lock:
            self.full_text = ""
            self.transcription = ['']
        self.model = "small.en"
        self.mode = "voice_transcription"

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
