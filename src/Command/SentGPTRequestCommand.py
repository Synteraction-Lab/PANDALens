from src.Command.Command import Command
from src.Utilities.json import detect_json


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
                    text_response = f"Full Writing:\n{full_writing}\n\nRevision:\n{revised_parts}\n"
                    audio_response = f"Here is your full writing: {full_writing}"

                    self.system_config.text_feedback_to_show = text_response
                    self.system_config.audio_feedback_to_show = audio_response

                elif json_response['mode'] == "authoring":
                    question_to_users = json_response['response'].get('question to users')
                    summary_of_new_content = json_response['response'].get('summary of new content')
                    if question_to_users is not None:
                        audio_response = f"May I ask:\n{question_to_users}"
                        if audio_response.strip() == "May I ask:\nNone":
                            audio_response = "I have no question for you. Anything you want to add?"
                        text_response = audio_response
                    elif summary_of_new_content is not None:
                        text_response = f"{summary_of_new_content}"
                        audio_response = text_response

                    self.system_config.audio_feedback_to_show = audio_response
                    self.system_config.notification = {'notif_type': 'text',
                                                       'content': f"{text_response}",
                                                       'position': 'middle-right'}

        except Exception as e:
            print(e)

        return text_response, audio_response
