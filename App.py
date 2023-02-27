import threading
import time
import tkinter as tk
from multiprocessing import Process

import pandas
import pyperclip

from UI.device_panel import DevicePanel, VISUAL_OUTPUT, AUDIO_OUTPUT, CONFIG_FILE_NAME
from UI.widget_generator import get_button

from datetime import datetime
from time import sleep
from pynput import keyboard
import whisper
import ssl
import openai
from AudioCapture import AudioCapture
from Utilities.clipboard import copy_content, get_clipboard_content
from Utilities.utilities import append_data
import os
from pynput.keyboard import Key, Controller, Listener as KeyboardListener
from pynput.mouse import Listener as MouseListener
import pyttsx3

CONCISE_THRESHOLD = 7000

JOURNAL = "journal"
PAPER = "paper_writing"
SELF_REFLECTION = "reflection"
PAPER_REVIEW = "paper_review"

ALL_HISTORY = "all"
AI_HISTORY = "ai"
HUMAN_HISTORY = "human"

ssl._create_default_https_context = ssl._create_unverified_context

audio_file = "command.mp3"
chat_file = "chat_history.txt"
slim_history_file = "slim_history.txt"
task_description_path = os.path.join("data", "task_description")
NEW_ITEM_KEY = 'key.down'
REVISE_KEY = 'key.right'
SUMMARIZE_KEY = 'key.up'

config_path = os.path.join("data", CONFIG_FILE_NAME)


def load_task_description(task_type):
    with open(os.path.join(task_description_path, task_type)) as f:
        task_description = f.read()
        return task_description


def play_audio_response(response):
    response = response.replace("AI:", "")
    speech_engine = pyttsx3.init(debug=True)
    speech_engine.setProperty('rate', 120)
    speech_engine.say(response)
    speech_engine.runAndWait()


def generate_gpt_response(sent_prompt, max_tokens=1000, temperature=0.7):
    try:
        openai.api_key = "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"
        model_engine = "text-davinci-003"
        completion = openai.Completion.create(
            engine=model_engine,
            prompt=sent_prompt,
            max_tokens=max_tokens,
            n=1,
            stop=None,
            temperature=temperature,
        )
        response = completion.choices[0].text
        return response
    except:
        raise Exception


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.wm_attributes("-topmost", True)
        self.init_screen_size = "800x600"

        # Open Setup panel
        DevicePanel(self.root, parent_object_save_command=self.update_config)

        # Set up voice recording
        self.audio_capture = None
        self.is_recording = False

        # Set up conversation history
        self.slim_history = ""
        self.ai_history = ""
        self.human_history = ""
        self.chat_history = ""
        self.stored_text_widget_content = ""

        self.send_history_mode = ALL_HISTORY

        # Set up keyboard and mouse listener
        self.start_listener()

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
        self.chat_history_file_name = os.path.join(self.folder_path, chat_file)
        self.slim_history_file_name = os.path.join(self.folder_path, slim_history_file)
        self.task_type = task_name

        # Set up output modality
        self.output_mode = output_modality
        self.audio_device_idx = audio_device_idx

        # Initiate the conversation
        self.setup_chat_gpt(self.task_type)

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
            self.on_more()
        elif key == Key.down:
            self.on_new()


    def on_release(self, key):
        # Resume Previous conversation
        if key == Key.esc:
            chat_history = None
            if os.path.isfile(self.slim_history_file_name):
                with open(self.slim_history_file_name) as f:
                    chat_history = f.read()
                    print("Resuming the conversation: ", self.slim_history_file_name)
            else:
                with open(self.chat_history_file_name) as f:
                    chat_history = f.read()
                    print("Resuming the conversation: ", self.chat_history_file_name)
            response = self.get_response_from_gpt(command=chat_history,
                                                  prefix="Resume the conversation history (Don't show the timestamp in the following answers)",
                                                  is_stored=False)
            self.store(response)
            self.chat_history = self.chat_history + response
            print(response.lstrip())

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
        print((x,y), pressed)
        if not pressed:
            copy_content()

    def pack_layout(self):
        # set the dimensions of the window to match the screen
        screen_width = self.root.winfo_screenwidth()
        screen_height = int(self.root.winfo_screenheight()/6)
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
        self.notification = tk.Label(self.root, text="Up for summarization, Down for recording, Left for hide/show text, Right for Resize", fg='green', bg='black', font=('Arial', 20))
        self.text_widget.insert(tk.END, "Welcome to use this system to record your idea.")
        self.scrollbar = tk.Scrollbar(self.text_frame, command=self.text_widget.yview, bg='black')
        self.text_widget.config(yscrollcommand=self.scrollbar.set)
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.top_button = get_button(self.manipulation_frame, text="Summarize", fg_color="green",
                                     command=self.on_summarize)
        self.left_button = get_button(self.manipulation_frame, text="Hide", fg_color="green",
                                      command=self.hide_show_text)
        self.right_button = get_button(self.manipulation_frame, text="Resize", fg_color="green", command=self.on_more)
        self.bottom_button = get_button(self.manipulation_frame, text="Record", fg_color="green",
                                        command=self.on_new)
        self.text_frame.grid(row=1, column=1, sticky="NSEW")
        self.notification.pack()
        self.top_button.grid(row=0, column=1, pady=5)
        self.left_button.grid(row=1, column=0, padx=5)
        self.right_button.grid(row=1, column=2, padx=5)
        self.bottom_button.grid(row=2, column=1, pady=5)
        self.manipulation_frame.pack(fill="both", expand=True)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        # self.root.attributes("-fullscreen", True)
        self.root.attributes("-alpha", 0.85)
        self.top_button.grid_forget()
        self.left_button.grid_forget()
        self.right_button.grid_forget()
        self.bottom_button.grid_forget()

    def on_close(self):
        self.root.destroy()
        self.keyboard_listener.stop()

    def on_summarize(self):
        self.notification.config(text="Summarizing...")
        if not self.is_recording:
            command_type = "{} all the items and generate the writing". \
                format("Summarize")
            t = threading.Thread(target=self.thread_summarize, args=(command_type,), daemon=True)
            t.start()

    def thread_summarize(self, command_type):
        response = self.get_response_from_gpt(command="", prefix=command_type)
        self.store(response)
        self.chat_history = self.chat_history + response
        self.render_response(response)
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

    def on_more(self):
        if self.root.attributes('-fullscreen'):
            # If it is, restore the window to its previous size
            self.root.attributes('-fullscreen', False)
            self.root.geometry(self.init_screen_size)

            self.top_button.grid_forget()
            self.left_button.grid_forget()
            self.right_button.grid_forget()
            self.bottom_button.grid_forget()
        else:
            # If it's not, set the window size to the screen size
            self.root.attributes('-fullscreen', True)
            self.top_button.grid(row=0, column=1, pady=5)
            self.left_button.grid(row=1, column=0, padx=5)
            # self.right_button.grid(row=1, column=2, padx=5)
            self.bottom_button.grid(row=2, column=1, pady=5)


    def thread_transcribe_and_render(self, command_type):
        # Transcribe voice command and get response from GPT
        voice_command = self.transcribe_voice_command()
        response = self.get_response_from_gpt(command=voice_command, prefix=command_type)

        # Store response
        self.store(response)
        self.chat_history = self.chat_history + response

        # Render response
        self.render_response(response)
        self.notification.config(text="")

        # Enable new recording
        self.is_recording = False

    def on_new(self):
        if not self.is_recording:
            self.notification.config(text="Reminder: Press \"Bottom\" button again to stop recording!")
            self.bottom_button.configure(text="Stop")
            self.audio_capture = AudioCapture(self.audio_file_name, self.audio_device_idx)
            self.audio_capture.start_recording()
            self.is_recording = True
        else:
            if self.audio_capture is not None:
                self.audio_capture.stop_recording()
                self.notification.config(text="Analyzing...")
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
            self.bottom_button.configure(text="Record")

    def setup_chat_gpt(self, task_type):
        self.task_description = load_task_description(task_type)
        self.chat_history = self.task_description
        self.human_history = self.task_description
        self.ai_history = self.task_description
        _ = self.get_response_from_gpt(self.chat_history, is_stored=False)

    def store(self, text, path=None):
        if path is None:
            path = self.chat_history_file_name
        data = str(datetime.now()) + ": " + text.lstrip() + "\n"
        append_data(path, data)

    def transcribe_voice_command(self):
        # transcribe audio to text
        print("start transcribing")
        model = whisper.load_model("base.en")
        result = model.transcribe(self.audio_file_name)
        command = result['text']
        return command

    def get_response_from_gpt(self, command, is_stored=True, role="Human: ", prefix=""):
        response = ""

        # Set up the prompt
        prompt = role + prefix + " " + command
        if is_stored:
            self.store(prompt)
            print(prompt)
        try:
            self.chat_history = self.chat_history + prompt
            self.human_history = self.human_history + prompt

            sent_prompt = self.chat_history + prompt

            response = generate_gpt_response(sent_prompt)

            self.ai_history = self.ai_history + response
            print("ai:", len(self.ai_history), "human: ", len(self.human_history), "total: ", len(self.chat_history))
            if len(self.chat_history) > CONCISE_THRESHOLD:
                t = threading.Thread(target=self.concise_history, daemon=True)
                t.start()

        except Exception as e:
            print(e)
            response = "No Response from GPT."

            if self.chat_history > CONCISE_THRESHOLD:
                self.chat_history = self.task_description + self.slim_history
                sent_prompt = self.chat_history + prompt
                response = generate_gpt_response(sent_prompt)
        finally:
            return response

    def concise_history(self):
        try:
            # Set up the prompt
            task_type = "concise_history"
            prompt = load_task_description(task_type)
            sent_prompt = prompt + self.slim_history
            if len(sent_prompt) > CONCISE_THRESHOLD:
                sent_prompt = sent_prompt[-CONCISE_THRESHOLD:-1]

            # Generate a response
            response = generate_gpt_response(sent_prompt)
            self.slim_history = self.task_description + response.lstrip()
            self.store(self.slim_history, self.slim_history_file_name)
            print("slim:", self.slim_history)

        except Exception as e:
            print("concise error: ", e)

    def render_response(self, response):
        print(response.lstrip())
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.insert(tk.END, response.lstrip())
        if self.output_mode == AUDIO_OUTPUT:
            p = Process(target=play_audio_response, args=(response,))
            p.start()


if __name__ == '__main__':
    App()
