from src.Action.Action import Action
from src.Command import CommandParser


class ShowSummariesAction(Action):
    def __init__(self, sys_config):
        super().__init__()
        self.system_config = sys_config

    def execute(self):
        user_request = {"user comments/commands": "List all the moments' summary. "  \
                        "Return the response **ONLY** in JSON format, "
                                                "with the following structure: "
                                                '{\"mode\": \"selecting\",' \
                                                ' \"response\": ' \
                                                '\{\"1\": ' \
                                                '\"[One sentence summary for moment 1]\"\, ' \
                                                '\"2\": \"[One sentence summary for moment 2]\"}}'
                                                } 
                                                  
        # send request to GPT
        send_gpt_request_command = CommandParser.parse("send_gpt_request", self.system_config)
        if send_gpt_request_command is not None:
            text_feedback, audio_feedback = send_gpt_request_command.execute(user_request)
            self.system_config.text_feedback_to_show = text_feedback
            self.system_config.audio_feedback_to_show = audio_feedback

        return True
