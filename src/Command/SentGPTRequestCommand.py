from src.Command.Command import Command
from src.Utilities.json import detect_json
import json


class SendGPTRequestCommand(Command):
    def __init__(self, sys_config):
        super().__init__()
        self.silence_start_time = None
        self.system_config = sys_config

    def execute(self, user_request):
        gpt = self.system_config.get_GPT()
        response = gpt.process_prompt_and_get_gpt_response(command=str(user_request))

        json_response = detect_json(response)
        json_dict = json.loads(response)
        text_response = response
        audio_response = response

        try:
            if json_response is not None:
                print(f"mode: {json_response['mode']}")
                if "full" in json_response['mode']:
                    text_response = f"Full Writing:\n{json_response['response']['full writing']}\n\n" \
                                    f"Revision:\n{json_response['response']['revised parts']}\n"
                    audio_response = f"Here is your full writing: {json_response['response']['full writing']}"

                    self.system_config.text_feedback_to_show = text_response
                    self.system_config.audio_feedback_to_show = audio_response

                elif json_response['mode'] == "authoring":
                    # text_response = f"Questions:\n{json_response['response']['question to users']}\n"
                    # f"New Note:\n{json_response['response']['summary of newly added content']}\n\n" \

                    audio_response = f"May I ask:\n {json_response['response']['question to users']}"
                    if audio_response.strip() == "May I ask:\n None":
                        audio_response = "I have no questions for you. Anything you want to add?"
                    text_response = audio_response

                    self.system_config.audio_feedback_to_show = audio_response
                    self.system_config.notification = {'notif_type': 'text',
                                                       'content': f"{text_response}",
                                                       'position': 'middle-right'}
                    
                elif json_response['mode'] == "selecting":
                    text_response = f"Moments:\n {json_response['response']}"
                    # self.system_config.notification = {'notif_type': 'text',
                    #                                    'content': f"{text_response}\n",
                    #                                    'position': 'middle-right'}
                    
                    # for i in range(len(json_response['response'])):
                    #     text_response += f"{i+1}: {json_response['response'][str(i)]}\n"
                        
               
                    audio_response = "Here are the summaries of your moments."
                    # self.system_config.text_feedback_to_show = text_response
                    # self.system_config.audio_feedback_to_show = audio_response

                    



        except Exception as e:
            print(e)

        return text_response, audio_response
