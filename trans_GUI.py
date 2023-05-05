import os
import threading
import tkinter as tk

from Model.Audio.audio_classifier import AudioClassifierRunner
from Model.Audio.live_transcriber import LiveTranscriber, show_devices


class TranscriberGUI:
    def __init__(self):
        self.audio_classifier_runner = AudioClassifierRunner(
            model=os.path.join("Module", "Audio", "lite-model_yamnet_classification.tflite"),
            callback=self.update_score_category)
        self.transcriber = LiveTranscriber(device_index=1)
        self.score = None
        self.category_name = None
        self.create_gui()
        show_devices()

    def create_gui(self):
        self.window = tk.Tk()
        self.window.title("Live Transcription")

        self.score_label = tk.Label(self.window, text=f"Score: {self.score}")
        self.score_label.pack()

        self.category_label = tk.Label(self.window, text=f"Category: {self.category_name}")
        self.category_label.pack()

        self.start_button = tk.Button(self.window, text="Start Recording", command=self.toggle_recording)
        self.start_button.pack()

        self.transcription_text = tk.Text(self.window, width=50, height=10)
        self.transcription_text.pack(fill=tk.BOTH, expand=True)

        self.window.rowconfigure(1, weight=1)
        self.window.columnconfigure(0, weight=1)

    def toggle_recording(self):
        if self.transcriber.stop_event.is_set():
            self.start_button.config(text="Stop Recording")
            self.stop_recording()
        else:
            self.start_button.config(text="Start Recording")
            self.start_recording()

    def update_score_category(self, score, category_name):
        self.score_label.config(text=f"Score: {score}")
        self.category_label.config(text=f"Category: {category_name}")

    def start_recording(self):
        self.start_button.config(text="Stop Recording", command=self.stop_recording)
        self.transcriber.start()
        self.update_transcription()

    def stop_recording(self):
        self.start_button.config(text="Start Recording", command=self.start_recording)
        self.transcriber.stop()

    def update_transcription(self):
        self.transcription_text.delete("1.0", tk.END)
        self.transcription_text.insert(tk.END, self.transcriber.full_text)
        if not self.transcriber.stop_event.is_set():
            self.window.after(100, self.update_transcription)

    def run(self):
        threading.Thread(target=self.audio_classifier_runner.run).start()
        self.window.mainloop()


if __name__ == '__main__':
    gui = TranscriberGUI()

    gui.run()
