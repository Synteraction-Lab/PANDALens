import os.path
import threading
import time
import wavio as wv
import whisper
import numpy as np
import sounddevice as sd
from Model.Audio.audio_record import AudioRecord


def show_devices():
    """
    Print a list of available input devices.
    """
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        print(i, device['name'])


class LiveTranscriber:
    def __init__(self, model="base.en", device_index=1, duration=7, silence_threshold=0.01, overlapping_factor=0):
        self.prompt = None
        self.record_thread = None
        self.model = whisper.load_model(model)
        self.device_index = device_index
        self.duration = duration
        self.silence_threshold = silence_threshold
        self.overlapping_factor = overlapping_factor
        self.stop_event = threading.Event()
        self.full_text = ""

        sample_rate = 44100
        device = sd.query_devices(device_index)
        channels = device['max_input_channels']

        # Initialize an AudioRecord instance
        self.audio_record = AudioRecord(channels, sample_rate, int(duration * sample_rate))

    def run(self):
        buffer_size = int(self.duration * self.audio_record.sampling_rate)
        input_length_in_second = float(buffer_size) / self.audio_record.sampling_rate
        interval_between_inference = input_length_in_second * (1 - self.overlapping_factor)
        pause_time = interval_between_inference * 0.1
        last_inference_time = time.time()

        self.audio_record.start_recording()
        self.is_recording = True

        while not self.stop_event.is_set():
            now = time.time()
            diff = now - last_inference_time
            if diff < interval_between_inference:
                time.sleep(pause_time)
                continue
            last_inference_time = now

            data = self.audio_record.read(buffer_size)

            # Check the RMS amplitude to determine if there is silence
            rms = np.sqrt(np.mean(np.square(data)))
            if rms > self.silence_threshold:
                file_path = os.path.join("data", "audio", "recording.wav")
                wv.write(file_path, data, self.audio_record.sampling_rate, sampwidth=2)

                threading.Thread(target=self.transcribe, args=(file_path,)).start()

    def transcribe(self, file_path):
        audio = whisper.load_audio(file_path)
        original_audio = audio
        audio = whisper.pad_or_trim(audio)

        mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
        options = whisper.DecodingOptions(language='en', fp16=False)
        # result = whisper.decode(self.model, mel, options)
        result = self.model.transcribe(
            original_audio,
            no_speech_threshold=0.2,
            logprob_threshold=None,
            verbose=False,
            **options.__dict__
        )
        print(result['text'])
        self.prompt = result['text']
        self.full_text += result['text'] + " "

    def start(self):
        self.stop_event.clear()
        self.record_thread = threading.Thread(target=self.run)
        self.record_thread.start()

    def stop(self):
        self.stop_event.set()
        self.record_thread.join()
        final_result = self.full_text
        self.full_text = ""
        return final_result


if __name__ == '__main__':
    model_path = "base.en"
    device_index = 1
    duration = 7
    silence_threshold = 0.01
    overlapping_factor = 0

    show_devices()

    transcriber = LiveTranscriber(model_path, device_index, duration, silence_threshold, overlapping_factor)
    transcriber.start()
    input("Press Enter to stop recording...")
    print(transcriber.stop())
