import os.path
import threading
import time
import wavio as wv
import whisper
import numpy as np
import sounddevice as sd
from src.Module.Audio.audio_record import AudioRecord
from queue import Queue
import ssl

ssl._create_default_https_context = ssl._create_unverified_context


def show_devices():
    """
    Print a list of available input devices.
    """
    devices = sd.query_devices()
    print(devices)


class LiveTranscriber:
    def __init__(self, model="small.en", device_index=1, duration=60, silence_threshold=0.02, overlapping_factor=0):
        self.prompt = None
        self.record_thread = None
        self.model = whisper.load_model(model)
        self.device_index = device_index
        self.duration = duration
        self.silence_threshold = silence_threshold
        self.overlapping_factor = overlapping_factor
        self.stop_event = threading.Event()
        self.full_text = ""
        self.transcription_queue = Queue()

        self.transcribe_lock = threading.Lock()

        device = sd.query_devices(device_index)
        channels = device['max_input_channels']
        sample_rate = int(device['default_samplerate'])

        # Initialize an AudioRecord instance
        self.audio_record = AudioRecord(channels, sample_rate, int(duration * sample_rate))

    def run(self):

        self.audio_record.start_recording()
        self.is_recording = True

        dir_path = os.path.join("data", "audio")
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)

        idx = 0
        recording_started = False
        recording_start_time = 0

        # stored_previous_audio = None

        recording_thread_start_time_now = time.time()

        while not self.stop_event.is_set():
            now = time.time()

            if now - recording_thread_start_time_now < 1:
                time.sleep(1)
                continue

            previous_1s_audio = self.audio_record.read(self.audio_record.sampling_rate * 1)

            # Check the RMS amplitude to determine if there is silence
            rms = np.sqrt(np.mean(np.square(previous_1s_audio)))

            diff_since_start = now - recording_start_time

            if (rms <= self.silence_threshold or diff_since_start >= self.duration - 1) and recording_started:
                # Save and transcribe the recorded data
                recording_started = False

                buffer_size = int((diff_since_start + 1) * self.audio_record.sampling_rate)
                data = self.audio_record.read(buffer_size)

                # data = np.concatenate((stored_previous_audio, data))

                idx += 1
                idx %= 2
                file_path = os.path.join(dir_path, f"recording{idx}.wav")
                wv.write(file_path, data, self.audio_record.sampling_rate, sampwidth=2)

                threading.Thread(target=self.transcribe, args=(file_path,)).start()

            elif rms > self.silence_threshold and not recording_started:
                # Start recording
                recording_started = True
                recording_start_time = now
                # stored_previous_audio = previous_1s_audio

    def transcribe(self, file_path):
        # print("Transcribing...")
        audio = whisper.load_audio(file_path)
        original_audio = audio
        # audio = whisper.pad_or_trim(audio)
        #
        # mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
        options = whisper.DecodingOptions(language='en', fp16=False, prompt=self.prompt)

        # require the lock here
        with self.transcribe_lock:
            result = self.model.transcribe(
                original_audio,
                no_speech_threshold=0.2,
                logprob_threshold=None,
                verbose=False,
                **options.__dict__
            )
            self.prompt = result['text']
            self.full_text += result['text'] + " "
            # self.transcription_queue.put(result['text'])
            print(result['text'])

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
    show_devices()
    device_index = int(input("Enter device index: "))
    duration = 60
    silence_threshold = 0.01
    overlapping_factor = 0

    transcriber = LiveTranscriber(model_path, device_index, duration, silence_threshold, overlapping_factor)
    transcriber.start()
    input("Press Enter to stop recording...")
    print(transcriber.stop())
