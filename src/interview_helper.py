import os
import ssl
from datetime import datetime

import openai
import pyttsx3
import whisper

from src.Storage.writer import append_json_data

LOW_INTELLIGENCE = "low"
HIGH_INTELLIGENCE = "high"
VISUAL_OUTPUT = "visual"
AUDIO_OUTPUT = "audio"

ssl._create_default_https_context = ssl._create_unverified_context

audio_file = "interview.m4a"
interview_file = "interview.txt"


def play_audio_response(response):
    response = response.replace("AI:", "")
    speech_engine = pyttsx3.init(debug=True)
    speech_engine.setProperty('rate', 120)
    speech_engine.say(response)
    speech_engine.runAndWait()


class App:
    def __init__(self, user_id="u01", level=HIGH_INTELLIGENCE):
        self.is_recording = False
        self.folder_path = os.path.join("../data", user_id)
        self.audio_file_name = os.path.join(self.folder_path, audio_file)
        self.interview_file_name = os.path.join(self.folder_path, interview_file)
        self.intelligent_level = level

        self.task = 'You are my intelligent assistant for helping me code the interview script. I will provide the interview script in the following request later, which contains the questions and participants\' answers. You need to help me list the questions and answers and also give me a summary.'

        self.chat_history = self.task

        _ = self.get_response_from_gpt(self.chat_history, is_stored=False)
        self.transcribe_and_send_to_gpt()
        self.output = VISUAL_OUTPUT

    def store(self, text):
        data = str(datetime.now()) + ": " + text.lstrip() + "\n"
        append_json_data(self.interview_file_name, data)

    def transcribe_and_send_to_gpt(self, command_type=None):
        # transcribe audio to text
        print("start transcribing")
        model = whisper.load_model("base.en")
        result = model.transcribe(self.audio_file_name)
        command = result['text']
        self.store(command)

        response = self.get_response_from_gpt(command=command)
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
            temperature=0.7,
        )
        response = completion.choices[0].text
        return response

    def render_response(self, response):
        if self.output_mode == AUDIO_OUTPUT:
            response = response.replace("AI:", "")
            play_audio_response(response)
        else:
            print(response.lstrip())


if __name__ == '__main__':
    uid = input("Please enter the user id: ")
    App(uid)
