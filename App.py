import threading
import time
import tkinter as tk
from multiprocessing import Process

import pandas
import pyperclip

from Model.GPT import GPT

from UI.device_panel import DevicePanel
from Utilities.constant import VISUAL_OUTPUT, AUDIO_OUTPUT, audio_file, chat_file, slim_history_file, config_path
from UI.widget_generator import get_button

from time import sleep
import whisper

from Model.AudioCapture import AudioCapture
from Utilities.clipboard import copy_content, get_clipboard_content

import os
from pynput.keyboard import Key, Controller, Listener as KeyboardListener
from pynput.mouse import Listener as MouseListener
import pyttsx3


def play_audio_response(response):
    response = response.replace("AI:", "")
    speech_engine = pyttsx3.init(debug=True)
    speech_engine.setProperty('rate', 120)
    speech_engine.say(response)
    speech_engine.runAndWait()


class App:
    def __init__(self):
        self.audio_file_name = None
        self.folder_path = None
        self.GPT = None
        self.root = tk.Tk()
        self.root.wm_attributes("-topmost", True)
        self.init_screen_size = "800x600"

        # Open Setup panel
        DevicePanel(self.root, parent_object_save_command=self.update_config)

        # Set up voice recording
        self.audio_capture = None
        self.is_recording = False

        # Set up keyboard and mouse listener
        self.start_listener()

        self.voice_feedback_process = None

        # Pack and run the main UI
        self.pack_layout()

        self.root.mainloop()

    def update_config(self):
        if not os.path.isfile(config_path):
            pid_num = os.path.join("p1", "01")
            task_name = "paper_review"
            output_modality = AUDIO_OUTPUT
            audio_device_idx = 0
        else:
            try:
                df = pandas.read_csv(config_path)
                pid_num = df[df['item'] == 'pid']['details'].item()
                task_name = df[df['item'] == 'task']['details'].item()
                output_modality = df[df['item'] == 'output']['details'].item()
                audio_device_idx = df[df['item'] == 'audio_device']['details'].item()
            except:
                pid_num = os.path.join("p1", "01")
                task_name = "paper_review"
                output_modality = AUDIO_OUTPUT
                audio_device_idx = 0
                print("Config file has an error!")

        # Set up path
        self.folder_path = os.path.join(os.path.join("data", "recordings"), pid_num)
        self.audio_file_name = os.path.join(self.folder_path, audio_file)
        chat_history_file_name = os.path.join(self.folder_path, chat_file)
        slim_history_file_name = os.path.join(self.folder_path, slim_history_file)

        self.GPT = GPT(chat_history_file_name=chat_history_file_name,
                       slim_history_file_name=slim_history_file_name)

        # Initiate the conversation
        self.GPT.setup_chat_gpt(task_name)

        # Set up output modality
        self.output_mode = output_modality
        self.audio_device_idx = audio_device_idx

        pyperclip.copy('')

    def on_press(self, key):
        if str(key) == "'.'":
            keyboard = Controller()
            keyboard.press(Key.cmd)
            keyboard.press(Key.tab)
            keyboard.release(Key.tab)
            keyboard.release(Key.cmd)
        elif key == Key.left:
            self.hide_show_text()
        elif key == Key.up:
            self.on_summarize()
        elif key == Key.right:
            self.on_new()
        elif key == Key.down:
            self.on_resize()

    def on_release(self, key):
        # Resume Previous conversation
        try:
            if key == Key.esc:
                self.GPT.resume_stored_history()
        except Exception as e:
            print(e)

    def start_listener(self):
        # self.root.bind("<Button-1>", self.on_click)
        self.mouse_listener = MouseListener(on_click=self.on_click)
        self.keyboard_listener = KeyboardListener(
            on_press=self.on_press, on_release=self.on_release)
        self.mouse_listener.start()
        time.sleep(0.1)
        self.keyboard_listener.start()

    def on_click(self, x, y, button, pressed):
        # self.hide_show_text()
        if not pressed:
            copy_content()

    def pack_layout(self):
        # set the dimensions of the window to match the screen
        screen_width = self.root.winfo_screenwidth()
        screen_height = int(self.root.winfo_screenheight() / 6)
        self.init_screen_size = f"{screen_width}x{screen_height}+0+0"
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")

        self.root.configure(bg='black')
        self.is_hidden_text = False
        self.manipulation_frame = tk.Frame(self.root, bg='black')
        self.manipulation_frame.grid_columnconfigure(0, weight=0)
        self.manipulation_frame.grid_columnconfigure(2, weight=1)
        self.manipulation_frame.grid_columnconfigure(1, weight=2)
        self.manipulation_frame.grid_rowconfigure(0, weight=0)
        self.manipulation_frame.grid_rowconfigure(2, weight=1)
        self.manipulation_frame.grid_rowconfigure(1, weight=2)
        self.text_frame = tk.Frame(self.manipulation_frame, bg='black', background="black")
        self.text_frame.grid(row=1, column=1, sticky="NSEW")
        self.text_frame.grid_columnconfigure(0, weight=1)
        self.text_frame.grid_rowconfigure(0, weight=1)
        self.text_widget = tk.Text(self.text_frame, height=10, width=50, fg='green', bg='black', font=('Arial', 40),
                                   spacing1=10, spacing2=20, wrap="word")
        self.last_y = None
        self.notification = tk.Label(self.root,
                                     text="Use Arrows on your keyboard to manipulate: Up for Summarization, Right for Recording, Left for Hide/Show text, Down for Resize",
                                     fg='green', bg='black', font=('Arial', 20))
        self.text_widget.insert(tk.END, "Welcome to use this system to record your idea.")
        self.scrollbar = tk.Scrollbar(self.text_frame, command=self.text_widget.yview, bg='black')
        self.text_widget.config(yscrollcommand=self.scrollbar.set)
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.top_button = get_button(self.manipulation_frame, text="Summarize", fg_color="green",
                                     command=self.on_summarize)
        self.left_button = get_button(self.manipulation_frame, text="Hide", fg_color="green",
                                      command=self.hide_show_text)
        self.resize_button = get_button(self.manipulation_frame, text="Resize", fg_color="green", command=self.on_resize)
        self.record_button = get_button(self.manipulation_frame, text="Record", fg_color="green",
                                        command=self.on_new)
        self.text_frame.grid(row=1, column=1, sticky="NSEW")
        self.notification.pack()
        self.top_button.grid(row=0, column=1, pady=5)
        self.left_button.grid(row=1, column=0, padx=5)
        self.record_button.grid(row=1, column=2, padx=5)
        self.resize_button.grid(row=2, column=1, pady=5)
        self.manipulation_frame.pack(fill="both", expand=True)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        # self.root.attributes("-fullscreen", True)
        self.root.attributes("-alpha", 0.95)
        self.top_button.grid_forget()
        self.left_button.grid_forget()
        self.resize_button.grid_forget()
        self.record_button.grid_forget()

    def on_close(self):
        self.root.destroy()
        self.keyboard_listener.stop()

    def on_summarize(self):
        self.determinate_voice_feedback_process()
        self.notification.config(text="Summarizing...")
        if not self.is_recording:
            command_type = "{} all the items and generate the writing". \
                format("Summarize")
            t = threading.Thread(target=self.thread_summarize, args=(command_type,), daemon=True)
            t.start()

    def determinate_voice_feedback_process(self):
        if self.voice_feedback_process is not None:
            self.voice_feedback_process.terminate()

    def thread_summarize(self, command_type):
        response = self.GPT.process_prompt_and_get_gpt_response(command="", prefix=command_type)
        self.render_response(response, self.output_mode)
        self.notification.config(text="")

    def hide_show_text(self):
        if not self.is_hidden_text:
            self.stored_text_widget_content = self.text_widget.get("1.0", tk.END)
            self.text_widget.delete(1.0, tk.END)
            self.left_button.configure(text="Show")
        else:
            self.text_widget.delete(1.0, tk.END)
            self.text_widget.insert(tk.END, self.stored_text_widget_content)
            self.left_button.configure(text="Hide")
        self.is_hidden_text = not self.is_hidden_text

    def on_resize(self):
        if self.root.attributes('-fullscreen'):
            # If it is, restore the window to its previous size
            self.root.attributes('-fullscreen', False)
            self.root.geometry(self.init_screen_size)

            self.top_button.grid_forget()
            self.left_button.grid_forget()
            self.resize_button.grid_forget()
            self.record_button.grid_forget()
        else:
            # If it's not, set the window size to the screen size
            self.root.attributes('-fullscreen', True)
            self.top_button.grid(row=0, column=1, pady=5)
            self.left_button.grid(row=1, column=0, padx=5)
            self.resize_button.grid(row=2, column=1, padx=5)
            self.record_button.grid(row=1, column=2, pady=5)

    def thread_transcribe_and_render(self, command_type):
        # Transcribe voice command and get response from GPT
        voice_command = self.transcribe_voice_command()
        self.notification.config(text="Analyzing...")
        response = self.GPT.process_prompt_and_get_gpt_response(command=voice_command, prefix=command_type)

        # Render response
        self.render_response(response, self.output_mode)
        self.notification.config(text="")

        # Enable new recording
        self.is_recording = False

    def on_new(self):
        self.determinate_voice_feedback_process()
        if not self.is_recording:
            self.notification.config(text="Reminder: Press \"Right\" button again to stop recording!")
            self.record_button.configure(text="Stop")
            self.audio_capture = AudioCapture(self.audio_file_name, self.audio_device_idx)
            self.audio_capture.start_recording()
            self.is_recording = True
        else:
            if self.audio_capture is not None:
                self.audio_capture.stop_recording()
                sleep(0.5)

            # command_type = "I want to add a new point: "
            content = get_clipboard_content()
            command_type = ""
            if content is not None and content != '':
                command_type = "For this part written in the paper: '{}', I want comment that: ".format(content)
                print(command_type)

            t = threading.Thread(target=self.thread_transcribe_and_render, args=(command_type,), daemon=True)
            t.start()
            pyperclip.copy('')
            self.record_button.configure(text="Record")

    def transcribe_voice_command(self):
        # transcribe audio to text
        self.notification.config(text="start transcribing")
        model = whisper.load_model("base.en")
        result = model.transcribe(self.audio_file_name)
        command = result['text']
        self.render_response(command, VISUAL_OUTPUT)
        return command

    def render_response(self, response, output_mode):
        print(response.lstrip())
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.insert(tk.END, response.lstrip())
        if output_mode == AUDIO_OUTPUT:
            self.voice_feedback_process = Process(target=play_audio_response, args=(response,))
            self.voice_feedback_process.start()


if __name__ == '__main__':
    App()
