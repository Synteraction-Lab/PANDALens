from src.Action.Action import Action
from src.Command import CommandParser


class FullWritingPendingAction(Action):
    def __init__(self, sys_config):
        super().__init__()
        self.system_config = sys_config

    def execute(self):
        user_request = {"user comments/commands": "Write a full blog based on the previous chat history. ' \
                       'Remember: Return the response **ONLY** in following JSON format: ' \
                       '{\"mode\": \"full\",' \
                       ' \"response\": ' \
                       '\{\"full writing\": ' \
                       '\"[full travel blog content in first person narration]\"\, ' \
                       '\"revised parts\": \"[the newly added or revised content, ' \
                       'return \"None\" when no revision.]\"}}"}

        # send request to GPT
        send_gpt_request_command = CommandParser.parse("send_gpt_request", self.system_config)
        if send_gpt_request_command is not None:
            send_gpt_request_command.execute(user_request)

        return True
