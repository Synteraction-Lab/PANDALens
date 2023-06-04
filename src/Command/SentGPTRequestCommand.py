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
                if "full" in json_response['mode']:
                    text_response = f"Full Writing:\n{json_response['response']['full writing']}\n\n" \
                                    f"Revision:\n{json_response['response']['revised parts']}\n"
                    audio_response = f"Revision: {json_response['response']['revised parts']}"
                elif json_response['mode'] == "authoring":
                    text_response = f"New Note:\n{json_response['response']['summary of newly added content']}\n\n" \
                                    f"Questions:\n{json_response['response']['question to users']}\n"
                    audio_response = f"Questions: {json_response['response']['question to users']}"
        except Exception as e:
            pass

        return text_response, audio_response
