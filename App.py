import subprocess
import threading
import tkinter as tk
from multiprocessing import Process

from UI.widget_generator import get_button

from datetime import datetime
from time import sleep
from pynput import keyboard
import whisper
import ssl
import openai
from AudioCapture import AudioCapture
from utilities import append_data, remove_file
import os
from gtts import gTTS
from playsound import playsound
from pynput.mouse import Listener as MouseListener
from pynput.keyboard import Key, Controller, Listener as KeyboardListener
import pyttsx3

CONCISE_THRESHOLD = 8000

JOURNAL = "journal"
PAPER = "paper"
SELF_REFLECTION = "reflection"
PAPER_REVIEW = "paper_review"
VISUAL_OUTPUT = "visual"
AUDIO_OUTPUT = "audio"

ALL_HISTORY = "all"
AI_HISTORY = "ai"
HUMAN_HISTORY = "human"

ssl._create_default_https_context = ssl._create_unverified_context

audio_file = "command.mp3"
chat_file = "chat_history.txt"
task_description_path = os.path.join("data", "task_description")
NEW_ITEM_KEY = 'key.down'
REVISE_KEY = 'key.right'
SUMMARIZE_KEY = 'key.up'


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


class App:
    def __init__(self, user_id="u01", output_mode=VISUAL_OUTPUT, task_type=SELF_REFLECTION):
        self.slim_history = ""
        self.ai_history = ""
        self.human_history = ""
        self.chat_history = ""
        self.stored_text_widget_content = ""
        self.is_recording = False
        self.folder_path = os.path.join(os.path.join("data", "recordings"), user_id)
        self.output_mode = output_mode
        self.audio_file_name = os.path.join(self.folder_path, audio_file)
        self.chat_history_file_name = os.path.join(self.folder_path, chat_file)
        self.task_type = task_type
        self.send_history_mode = ALL_HISTORY

        self.audio_capture = None
        self.setup_chat_gpt(task_type)

        # with keyboard.Listener(on_release=self.on_release) as listener:
        #     listener.join()

        self.root = tk.Tk()
        self.pack_layout()
        self.start_listener()
        self.root.mainloop()

    def on_press(self, key):
        if str(key) == "'.'":
            keyboard = Controller()
            keyboard.press(Key.cmd)
            keyboard.press(Key.tab)
            keyboard.release(Key.tab)
            keyboard.release(Key.cmd)

    def start_listener(self):
        self.root.bind("<Button-1>", self.on_click)
        # self.mouse_listener = MouseListener(
        #     on_click=self.on_click)
        # self.mouse_listener.start()
        self.keyboard_listener = KeyboardListener(
            on_press=self.on_press)
        self.keyboard_listener.start()

    def on_mouse_move(self, event):
        cur_y = event.y
        if self.last_y is not None:
            if cur_y < self.last_y:
                # mouse moved up
                self.text_widget.yview_scroll(-1, "units")
            elif cur_y > self.last_y:
                # mouse moved down
                self.text_widget.yview_scroll(1, "units")
        self.last_y = cur_y

    def on_click(self, *args):
        self.hide_show_text()

    def pack_layout(self):
        self.root.configure(bg='black')
        self.is_hidden_text = False
        self.manipulation_frame = tk.Frame(self.root, bg='black')
        self.manipulation_frame.grid_columnconfigure(0, weight=0)
        self.manipulation_frame.grid_columnconfigure(2, weight=1)
        self.manipulation_frame.grid_columnconfigure(1, weight=2)
        self.manipulation_frame.grid_rowconfigure(0, weight=0)
        self.manipulation_frame.grid_rowconfigure(2, weight=1)
        self.manipulation_frame.grid_rowconfigure(1, weight=2)
        self.text_frame = tk.Frame(self.manipulation_frame)
        self.text_frame.grid(row=1, column=1, sticky="NSEW")
        self.text_frame.grid_columnconfigure(0, weight=1)
        self.text_frame.grid_rowconfigure(0, weight=1)
        self.text_widget = tk.Text(self.text_frame, height=10, width=50, fg='green', bg='black', font=('Arial', 40),
                                   spacing1=10, spacing2=20, wrap="word")
        self.text_widget.bind("<Motion>", self.on_mouse_move)
        self.last_y = None
        self.notification = tk.Label(self.root, text="", fg='green', bg='black', font=('Arial', 20))
        self.text_widget.insert(tk.END, "Welcome to use this system to record your idea.")
        self.scrollbar = tk.Scrollbar(self.text_frame, command=self.text_widget.yview)
        self.text_widget.config(yscrollcommand=self.scrollbar.set)
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.top_button = get_button(self.manipulation_frame, text="Summarize", fg_color="green",
                                     command=self.on_summarize)
        self.left_button = get_button(self.manipulation_frame, text="Hide", fg_color="green",
                                      command=self.hide_show_text)
        self.right_button = get_button(self.manipulation_frame, text="More", fg_color="green", command=self.on_more)
        self.bottom_button = get_button(self.manipulation_frame, text="Recording", fg_color="green",
                                        command=self.on_new)
        self.text_frame.grid(row=1, column=1, sticky="NSEW")
        self.notification.pack()
        self.top_button.grid(row=0, column=1, pady=10)
        self.left_button.grid(row=1, column=0, padx=10)
        # self.right_button.grid(row=1, column=2, padx=10)
        self.bottom_button.grid(row=2, column=1, pady=10)
        self.manipulation_frame.pack(fill="both", expand=True)
        self.root.bind('<Up>', lambda event: self.top_button.invoke())
        self.root.bind('<Down>', lambda event: self.bottom_button.invoke())
        self.root.bind('<Left>', lambda event: self.left_button.invoke())
        # self.root.bind('<Right>', lambda event: self.right_button.invoke())
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # set the dimensions of the window to match the screen
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

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

    # def on_clean(self):
    #     print("Clean button clicked")
    #     self.text_widget.delete(1.0, tk.END)
    def hide_show_text(self):
        if not self.is_hidden_text:
            self.stored_text_widget_content = self.text_widget.get("1.0", tk.END)
            self.text_widget.delete(1.0, tk.END)
            # self.text_widget.pack_forget()
            self.left_button.configure(text="Show")
        else:
            self.text_widget.delete(1.0, tk.END)
            self.text_widget.insert(tk.END, self.stored_text_widget_content)
            # self.text_widget.pack(fill="both", expand=True, padx=10, pady=10)
            self.left_button.configure(text="Hide")
        self.is_hidden_text = not self.is_hidden_text

    def on_more(self):
        if not self.is_recording:
            self.notification.config(text="Reminder: Press \"Right\" button again to stop recording!")
            self.audio_capture = AudioCapture(self.audio_file_name)
            self.audio_capture.start_recording()
            self.is_recording = True
        else:
            if self.audio_capture is not None:
                self.audio_capture.stop_recording()
                self.notification.config(text="Analyzing...")
                sleep(0.5)
            command_type = "I want to elaborate more on this point."
            t = threading.Thread(target=self.thread_transcribe_and_render, args=(command_type,), daemon=True)
            t.start()

    def thread_transcribe_and_render(self, command_type):
        response = self.transcribe_and_send_to_gpt(command_type)
        self.render_response(response)
        self.notification.config(text="")
        self.is_recording = False

    def on_new(self):
        if not self.is_recording:
            self.notification.config(text="Reminder: Press \"Bottom\" button again to stop recording!")
            self.audio_capture = AudioCapture(self.audio_file_name)
            self.audio_capture.start_recording()
            self.is_recording = True
        else:
            if self.audio_capture is not None:
                self.audio_capture.stop_recording()
                self.notification.config(text="Analyzing...")
                sleep(0.5)

            # command_type = "I want to add a new point: "
            command_type = ""

            t = threading.Thread(target=self.thread_transcribe_and_render, args=(command_type,), daemon=True)
            t.start()

    def setup_chat_gpt(self, task_type):
        self.task_description = load_task_description(task_type)
        self.chat_history = self.task_description
        self.human_history = self.task_description
        self.ai_history = self.task_description
        _ = self.get_response_from_gpt(self.chat_history, is_stored=False)

    def store(self, text):
        data = str(datetime.now()) + ": " + text.lstrip() + "\n"
        append_data(self.chat_history_file_name, data)

    def transcribe_and_send_to_gpt(self, command_type=None):
        # transcribe audio to text
        print("start transcribing")
        model = whisper.load_model("base.en")
        result = model.transcribe(self.audio_file_name)
        command = result['text']

        response = self.get_response_from_gpt(command=command, prefix=command_type)
        self.store(response)
        self.chat_history = self.chat_history + response
        return response

    def get_response_from_gpt(self, command, is_stored=True, role="Human: ", prefix=""):
        # Define OpenAI API key
        response = ""
        try:
            openai.api_key = "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"

            # Set up the model and prompt
            model_engine = "text-davinci-003"
            prompt = role + prefix + " " + command
            if is_stored:
                self.store(prompt)
            print(prompt)
            self.chat_history = self.chat_history + prompt
            self.human_history = self.human_history + prompt

            if self.send_history_mode == ALL_HISTORY:
                sent_prompt = self.chat_history + prompt
            elif self.send_history_mode == AI_HISTORY:
                sent_prompt = self.ai_history + prompt
            else:
                sent_prompt = self.human_history + prompt

            # Generate a response
            completion = openai.Completion.create(
                engine=model_engine,
                prompt=sent_prompt,
                max_tokens=1024,
                n=1,
                stop=None,
                temperature=0.6,
            )
            response = completion.choices[0].text

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
            # self.send_history_mode = AI_HISTORY
        finally:
            return response

    def concise_history(self):
        response = ""
        try:
            openai.api_key = "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"

            # Set up the model and prompt
            model_engine = "text-davinci-003"

            prompt = load_task_description(task_type)
            sent_prompt = prompt + self.chat_history

            # Generate a response
            completion = openai.Completion.create(
                engine=model_engine,
                prompt=sent_prompt,
                max_tokens=1024,
                n=1,
                stop=None,
                temperature=0.6,
            )
            response = completion.choices[0].text
            self.slim_history = self.task_description + response.lstrip()
            print(self.slim_history)

        except Exception as e:
            print(e)
            self.send_history_mode = AI_HISTORY


    def render_response(self, response):
        print(response.lstrip())
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.insert(tk.END, response.lstrip())
        if self.output_mode == AUDIO_OUTPUT:
            p = Process(target=play_audio_response, args=(response,))
            p.start()

    def on_release(self, key):
        # Resume Previous conversation
        if key == keyboard.Key.esc:
            chat_history = None
            print("Resuming the conversation: ", self.chat_history_file_name)
            with open(self.chat_history_file_name) as f:
                chat_history = f.read()
            response = self.get_response_from_gpt(command=chat_history,
                                                  prefix="Resume the conversation history (Don't show the timestamp in the following answers)",
                                                  is_stored=False)
            self.store(response)
            self.chat_history = self.chat_history + response
            print(response.lstrip())


if __name__ == '__main__':
    uid = input("Please enter the user id: ")
    if uid == "test":
        App("test", AUDIO_OUTPUT, PAPER_REVIEW)
    else:
        output_mode = input("Please enter the output mode ({} or {}): ".format(VISUAL_OUTPUT, AUDIO_OUTPUT))
        task_type = input(
            "Please enter the task ({} or {} or {} or others (create a .txt file under data/task_description and add the description first.): ".format(
                SELF_REFLECTION, JOURNAL, PAPER_REVIEW))
        App(uid, output_mode, task_type)
