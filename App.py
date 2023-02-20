import threading
import tkinter as tk
from UI.widget_generator import get_button

from datetime import datetime
from time import sleep
from pynput import keyboard
import whisper
import ssl
import openai
from AudioCapture import AudioCapture
from utilities import append_data
import os
from gtts import gTTS
from playsound import playsound
from pynput.mouse import Listener as MouseListener

JOURNAL = "journal"
PAPER = "paper"
SELF_REFLECTION = "reflection"
VISUAL_OUTPUT = "visual"
AUDIO_OUTPUT = "audio"

ssl._create_default_https_context = ssl._create_unverified_context

audio_file = "command.mp3"
chat_file = "chat_history.txt"
NEW_ITEM_KEY = 'key.down'
REVISE_KEY = 'key.right'
SUMMARIZE_KEY = 'key.up'


class App:
    def __init__(self, user_id="u01", output_mode=VISUAL_OUTPUT, task_type=SELF_REFLECTION):
        self.chat_history = None
        self.is_recording = False
        self.folder_path = os.path.join("data", user_id)
        self.output_mode = output_mode
        self.audio_file_name = os.path.join(self.folder_path, audio_file)
        self.chat_history_file_name = os.path.join(self.folder_path, chat_file)
        self.task_type = task_type

        self.audio_capture = None
        self.setup_chat_gpt(task_type)
        # self.store(response)

        # with keyboard.Listener(on_release=self.on_release) as listener:
        #     listener.join()

        self.root = tk.Tk()
        self.pack_layout()
        self.start_listener()
        self.root.mainloop()

    def start_listener(self):
        self.mouse_listener = MouseListener(
            on_click=self.on_click)
        self.mouse_listener.start()

    def on_click(self, x, y, button, pressed):
        if pressed:
            self.on_clean()

    def pack_layout(self):
        self.root.configure(bg='black')
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(2, weight=1)
        self.root.grid_columnconfigure(1, weight=2)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_rowconfigure(1, weight=2)
        self.text_frame = tk.Frame(self.root)
        self.text_frame.grid(row=1, column=1, sticky="NSEW")
        self.text_frame.grid_columnconfigure(0, weight=1)
        self.text_frame.grid_rowconfigure(0, weight=1)
        self.text_widget = tk.Text(self.text_frame, height=10, width=50, fg='green', bg='black', font=('Arial', 40),
                                   wrap="word")
        self.text_widget.insert(tk.END, "Welcome to use this system to record your idea.")
        self.scrollbar = tk.Scrollbar(self.text_frame, command=self.text_widget.yview)
        self.text_widget.config(yscrollcommand=self.scrollbar.set)
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.top_button = get_button(self.root, text="Summarize", fg_color="green", command=self.on_summarize)
        self.left_button = get_button(self.root, text="Clean", fg_color="green", command=self.on_clean)
        self.right_button = get_button(self.root, text="More", fg_color="green", command=self.on_more)
        self.bottom_button = get_button(self.root, text="New", fg_color="green", command=self.on_new)
        self.text_frame.grid(row=1, column=1, sticky="NSEW")
        self.top_button.grid(row=0, column=1, pady=10)
        self.left_button.grid(row=1, column=0, padx=10)
        self.right_button.grid(row=1, column=2, padx=10)
        self.bottom_button.grid(row=2, column=1, pady=10)
        self.root.bind('<Up>', lambda event: self.top_button.invoke())
        self.root.bind('<Down>', lambda event: self.bottom_button.invoke())
        self.root.bind('<Left>', lambda event: self.left_button.invoke())
        self.root.bind('<Right>', lambda event: self.right_button.invoke())

    def on_summarize(self):
        self.text_widget.insert(tk.END, "\n\nSummarizing...")
        if not self.is_recording:
            command_type = "{} all the items and generate the writing". \
                format("Summarize")
            response = self.get_response_from_gpt(command="", prefix=command_type)
            self.store(response)
            self.chat_history = self.chat_history + response
            self.render_response(response)

    def on_clean(self):
        print("Clean button clicked")
        self.text_widget.delete(1.0, tk.END)

    def on_more(self):
        self.text_widget.insert(tk.END, "\n\nReminder: Press \"Right\" button again to stop recording!")
        if not self.is_recording:
            self.audio_capture = AudioCapture(self.audio_file_name)
            self.audio_capture.start_recording()
            self.is_recording = True
        else:
            if self.audio_capture is not None:
                self.audio_capture.stop_recording()
                sleep(0.5)
            command_type = "I want to elaborate more on this point."
            response = self.transcribe_and_send_to_gpt(command_type)
            self.render_response(response)
            self.is_recording = False

    def on_new(self):
        self.text_widget.insert(tk.END, "\n\nReminder: Press \"Bottom\" button again to stop recording!")
        if not self.is_recording:
            self.audio_capture = AudioCapture(self.audio_file_name)
            self.audio_capture.start_recording()
            self.is_recording = True
        else:
            if self.audio_capture is not None:
                self.audio_capture.stop_recording()
                sleep(0.5)

            command_type = "I want to add a new point: "

            response = self.transcribe_and_send_to_gpt(command_type)
            self.render_response(response)
            self.is_recording = False

    def setup_chat_gpt(self, task_type):
        if task_type == SELF_REFLECTION:
            task_description = 'You are my intelligent diary notebook. ' \
                               'I will have some self-reflections in my everyday activities. ' \
                               'You need to help me summarize my rough self-reflections using the first-person narration.' \
                               'It would be good if you can sometimes help me dig some points further ' \
                               'so that the summarization could be interesting and meaningful to share ' \
                               'I may have three option: 1) start a new reflection item' \
                               '2) elaborate more on the item' \
                               '3) ask you to provide a summary of all the items in the day' \
                               'Everytime, if I do not mention you should provide the whole summary of the day, ' \
                               'you just need to present that single item for me.' \
                               'And at the end of the day, ' \
                               'you need to generate a interesrting diary for my whole day. ' \
                               'I will use the diary for later twitter or blog writing.\n ' \
                               'AI: Great! I\'m excited to be your intelligent diary notebook. ' \
                               'To help you summarize your reflections, ' \
                               'I can ask questions to guide you and help structure your thoughts. ' \
                               'At the end of the day, I will create a summary of your reflections for the day, ' \
                               'so that you can look back at your progress.'
        elif task_type == JOURNAL:
            task_description = 'I am a journalist from New York Times. You are my journal writing assistant.' \
                               'AI: Thank you for trusting me with this important task! How can I help you?' \
                               'Human: I will either ask you to: start to record a new point, elaborate more on the point, ' \
                               'or ask you to provide a summary of all the points and generate a journal in New York Times\' ' \
                               'writing style. Show me a paragraph when I talk about each point and generate a full text' \
                               'when I require a summary. Your job is to help me summarize my rough thoughts and ' \
                               'present them in New York Times\' writing style. ' \
                               'It would be great if you could help me dig deeper into some points, ' \
                               'so that the summarization is interesting and meaningful to post in New York Times. '
        else:
            task_description = "I am a human-computer interaction researcher. You are my writing assistant for academic writing." \
                               "AI: My primary role is to help make your academic writing process efficient, productive, " \
                               "and enjoyable. I can help with grammar, punctuation, flow, accuracy, clarity, " \
                               "and consistency of your writing. I can suggest topic-relevant resources and sources " \
                               "that you may want to consider including in your work. Additionally, upon request, " \
                               "I can provide feedback on the overall structure and content of your paper. " \
                               "Human:  Great. I will either ask you to: start to record a new point, " \
                               "elaborate more on the point, or ask you to provide a summary of all " \
                               "the writing points and generate an introduction for the paper. " \
                               "Show me a paragraph when I talk about each point and generate a full text when " \
                               "I require a summary. It would be great if you could help me dig deeper into some points," \
                               "so that the summarization is interesting and insightful for a paper.  " \
                               "An academic paper usually contains background, issues and research gap, " \
                               "introduction our system, a brief description of the study design & results, " \
                               "what contribution we made. Please guide me or remind me to cover these parts if I miss them." \
                               "\nAI: Certainly! I can help you cover each part and ensure that your academic paper " \
                               "is comprehensive, detailed, and well-structured. " \
                               "When you ask me to start or elaborate on a new point, " \
                               "I can provide guidance and resources to help you understand the topic better, " \
                               "suggest relevant sources for further exploration, and provide examples of how " \
                               "to structure the text for effective communication. For summarization, " \
                               "I can help you review all the points, organize them into distinct categories, " \
                               "and generate an introduction to help the reader understand the main concepts. A" \
                               "dditionally, I can remind you to include background, research gaps, " \
                               "a description of the system, the design and results of any experiments, " \
                               "and the contributions made. I look forward to working with you to create " \
                               "an engaging and informative. \nHuman: I will start now"

        self.chat_history = task_description
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
        openai.api_key = "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"

        # Set up the model and prompt
        model_engine = "text-davinci-003"
        prompt = role + prefix + " " + command
        if is_stored:
            self.store(prompt)
        print(prompt)
        self.chat_history = self.chat_history + prompt

        # Generate a response
        completion = openai.Completion.create(
            engine=model_engine,
            prompt=self.chat_history,
            max_tokens=2048,
            n=1,
            stop=None,
            temperature=0.6,
        )
        response = completion.choices[0].text
        return response

    def render_response(self, response):
        print(response.lstrip())
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.insert(tk.END, response.lstrip())
        if self.output_mode == AUDIO_OUTPUT:
            # response = self.play_audio_response(response)
            t1 = threading.Thread(target=self.play_audio_response, args=(response,), daemon=True)
            t1.start()


    def play_audio_response(self, response):
        response = response.replace("AI:", "")
        voice_response = gTTS(text=response, lang='en', slow=False)
        save_path = os.path.join(self.folder_path, "voice_reponse.mp3")
        voice_response.save(save_path)
        # Playing the converted file
        playsound(save_path)
        return response

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
        App("test", AUDIO_OUTPUT, JOURNAL)
    output_mode = input("Please enter the output mode ({} or {}): ".format(VISUAL_OUTPUT, AUDIO_OUTPUT))
    task_type = input("Please enter the task ({} or {} or {}): ".format(SELF_REFLECTION, JOURNAL, PAPER))
    App(uid, output_mode, task_type)
