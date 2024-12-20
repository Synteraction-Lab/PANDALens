from src.Command.Command import Command
from src.Utilities.json import detect_json
import re

MAX_QUESTION_NUMBER = 2


def extract_question_sentences(text):
    # Define a regular expression pattern to match question sentences
    pattern = r"(?:^|(?<=[.!?]))\s*([A-Z][^.!?]*\?\s*)"

    # Use the findall() function from the re module to find all matches
    question_sentences = re.findall(pattern, text)

    question_string = ' '.join(question_sentences)

    return question_string


class SendGPTRequestCommand(Command):
    def __init__(self, sys_config):
        super().__init__()
        self.silence_start_time = None
        self.system_config = sys_config

    def execute(self, user_request):
        gpt = self.system_config.get_GPT()
        response = gpt.process_prompt_and_get_gpt_response(command=str(user_request))

        json_response = detect_json(response)
        text_response = response
        audio_response = response

        try:
            if json_response is not None:
                print(f"mode: {json_response['mode']}")
                print(f"response: {response}\n\n")
                if "full" in json_response['mode']:
                    full_writing = json_response['response'].get('full writing', '')
                    revised_parts = json_response['response'].get('revised parts', '')
                    text_response = f"Full Writing:\n{full_writing}"
                    audio_response = f"Here is your full writing: {full_writing}"

                    self.system_config.text_feedback_to_show = text_response
                    self.system_config.audio_feedback_to_show = audio_response
                    self.system_config.gpt_response_type = "full"
                    with self.system_config.notification_lock:
                        self.system_config.notification = None

                elif "selecting" in json_response['mode']:
                    moment_list = ""
                    for key, val in json_response["response"].items():
                        moment_list += f"{int(key)}. {val}\n"

                    text_response = "Moments:\n" + moment_list
                    audio_response = "Here are the summaries of your moments." + moment_list
                    self.system_config.latest_moment_list = moment_list

                    self.system_config.text_feedback_to_show = text_response
                    self.system_config.audio_feedback_to_show = audio_response
                    self.system_config.gpt_response_type = "selecting"
                    with self.system_config.notification_lock:
                        self.system_config.notification = None

                elif json_response['mode'] == "authoring":
                    question_to_users = json_response['response'].get('question to users')
                    summary_of_new_content = json_response['response'].get('summary of new content')
                    self.system_config.gpt_question_count += 1
                    print("question #:", self.system_config.gpt_question_count)
                    if question_to_users is not None:
                        audio_response = f"{question_to_users}"
                        if audio_response.strip() == "None" or self.system_config.gpt_question_count > MAX_QUESTION_NUMBER:
                            audio_response = None
                            text_response = "I have no question for you. Anything you want to add?"
                        else:
                            text_response = audio_response
                    elif summary_of_new_content is not None:
                        question_to_users = extract_question_sentences(summary_of_new_content).strip()
                        audio_response = f"{question_to_users}"
                        if question_to_users == "" or self.system_config.gpt_question_count > MAX_QUESTION_NUMBER:
                            question_to_users = "I have no question for you. Anything you want to add?"
                            audio_response = None

                        text_response = f"{question_to_users}"

                    with self.system_config.notification_lock:
                        self.system_config.audio_feedback_to_show = audio_response
                        self.system_config.notification = {'notif_type': 'text',
                                                           'content': f"{text_response}",
                                                           'position': 'middle-right'}
                    self.system_config.gpt_response_type = "authoring"

            else:
                with self.system_config.notification_lock:
                    self.system_config.audio_feedback_to_show = audio_response
                    self.system_config.notification = {'notif_type': 'text',
                                                       'content': f"{text_response}",
                                                       'position': 'middle-right'}
                self.system_config.self.gpt_response_type = "authoring"

        except Exception as e:
            print(f"GPT Response Parse Error: {e}")
            self.system_config.audio_feedback_to_show = audio_response
            self.system_config.notification = {'notif_type': 'text',
                                               'content': f"{text_response}",
                                               'position': 'middle-right'}

        return text_response, audio_response
