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


LOW_INTELLIGENCE = "low"
HIGH_INTELLIGENCE = "high"
VISUAL_OUTPUT = "visual"
AUDIO_OUTPUT = "audio"

ssl._create_default_https_context = ssl._create_unverified_context

audio_file = "command.mp3"
chat_file = "chat_history.txt"
NEW_ITEM_KEY = 'key.down'
REVISE_KEY = 'key.right'
SUMMARIZE_KEY = 'key.up'


class App:
    def __init__(self, user_id="u01", output_mode=VISUAL_OUTPUT, level=HIGH_INTELLIGENCE):
        self.chat_history = None
        self.is_recording = False
        self.folder_path = os.path.join("data", user_id)
        self.output_mode = output_mode
        self.audio_file_name = os.path.join(self.folder_path, audio_file)
        self.chat_history_file_name = os.path.join(self.folder_path, chat_file)
        self.intelligent_level = level

        self.audio_capture = None
        self.setup_chat_gpt(level)
        # self.store(response)

        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            listener.join()

    def setup_chat_gpt(self, level):
        if level == HIGH_INTELLIGENCE:
            task_description = 'You are my intelligent diary notebook. ' \
                               'I will have some self-reflections in my everyday activities. ' \
                               'You need to help me summarize my rough self-reflections using the first-person narration. ' \
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
        else:
            task_description = 'You are my intelligent diary notebook. ' \
                               'I will have some self-reflections in my everyday activities. ' \
                               'You are an AI assistant that can help me correct' \
                               ' the language issues of my self-reflection. ' \
                               'Note: You only proofread my speech. e.g., ' \
                               'grammar mistakes and you can delete some useless words, e.g., Interjections. ' \
                               'You are not allowed to revise and concise my speaking. ' \
                               'You remember all the corrected self-reflection.' \
                               'Everytime, if I do not mention you should provide the whole summary of the day, ' \
                               'you just need to present that single item for me.' \
                               'And at the end of the day, you can show me what I said for the day ' \
                               'using first-person narration. ' \
                               '\nAI: I understand, I will be your AI assistant' \
                               ' to help you proofread your self-reflections. ' \
                               'I will identify and correct any grammar mistakes ' \
                               'and delete any interjections from your reflections. ' \
                               'I will not revise or condense the reflections in any way. ' \
                               'I will remember all the corrected self-reflection.' \
                               'At the end of each day, I will present you with a record of ' \
                               'your self-reflections using first-person narration for that day.'
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
            temperature=0.7,
        )
        response = completion.choices[0].text
        return response

    def on_press(self, key):
        try:
            if (not self.is_recording) and str(key).strip("''").lower() == SUMMARIZE_KEY:
                command_type = "{} all the items using first-person narrative.". \
                    format("Summarize" if self.intelligent_level == HIGH_INTELLIGENCE
                           else "List (but don't revise or condense)")
                response = self.get_response_from_gpt(command="", prefix=command_type)
                self.store(response)
                self.chat_history = self.chat_history + response
                self.render_response(response)

            if str(key).strip("''").lower() == NEW_ITEM_KEY or str(key).strip("''").lower() == REVISE_KEY:
                if not self.is_recording:
                    self.audio_capture = AudioCapture(self.audio_file_name)
                    self.audio_capture.start_recording()
                    self.is_recording = True
                else:
                    if self.audio_capture is not None:
                        self.audio_capture.stop_recording()
                        sleep(0.5)
                    command_type = None
                    if str(key).strip("''").lower() == NEW_ITEM_KEY:
                        command_type = "I want to add a new self-reflection: "
                    elif str(key).strip("''").lower() == REVISE_KEY:
                        if self.intelligent_level == HIGH_INTELLIGENCE:
                            command_type = "I want to elaborate more on this topic."
                        elif self.intelligent_level == LOW_INTELLIGENCE:
                            command_type = "Not correct. I want to clarify that: "
                    response = self.transcribe_and_send_to_gpt(command_type)
                    self.render_response(response)
                    self.is_recording = False
        except Exception as e:
            print(e)

    def render_response(self, response):
        if self.output_mode == AUDIO_OUTPUT:
            response = response.replace("AI:", "")
            voice_response = gTTS(text=response, lang='en', slow=False)
            save_path = os.path.join(self.folder_path, "voice_reponse.mp3")
            voice_response.save(save_path)
            # Playing the converted file
            playsound(save_path)

        print(response.lstrip())

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
    output_mode = input("Please enter the output mode ({} or {}): ".format(VISUAL_OUTPUT, AUDIO_OUTPUT))
    intelligence_level = input("Please enter the AI intelligence level ({} or {}): ".format(HIGH_INTELLIGENCE,
                                                                                            LOW_INTELLIGENCE))
    App(uid, output_mode, intelligence_level)
