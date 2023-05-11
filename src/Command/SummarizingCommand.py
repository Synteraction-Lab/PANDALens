from src.Command.Command import Command
from src.Utilities.json import detect_json


class SummarizingCommand(Command):
    def __init__(self, sys_config):
        super().__init__()
        self.system_config = sys_config

    def execute(self):
        gpt = self.system_config.get_GPT()
        command_type = '{"User Command": "Write a full blog based on the previous chat history. ' \
                       'Remember: Return the response **ONLY** in following JSON format: ' \
                       '{\"mode\": \"full\",' \
                       ' \"response\": ' \
                       '\{ \"full writing\": ' \
                       '\"[full travel blog content in first person narration]\"\, ' \
                       '\"revised parts\": \"[the newly added or revised content, ' \
                       'return \"None\" when no revision.]\" } }"'
        response = gpt.process_prompt_and_get_gpt_response(command=command_type)

        json_response = detect_json(response)

        try:
            if json_response is not None:
                response = f"Full Writing:\n{json_response['response']['full writing']}\n\n" \
                           f"Revision:\n{json_response['response']['revised parts']}\n"
        except Exception as e:
            pass

        return response

    def undo(self):
        pass