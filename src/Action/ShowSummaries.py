from src.Action.Action import Action
from src.Command import CommandParser


class ShowSummariesAction(Action):
    def __init__(self, sys_config):
        super().__init__()
        self.system_config = sys_config

    def execute(self):
        self.system_config.notification = {'notif_type': 'processing_icon',
                                           'position': 'middle-right'}

        user_request = {"System": "List all the moments' summary. To do so, "
                                  "combine the points that belong to the same moment. "
                                  "Note: each summary item should be very concise "
                                  "and written within few words.\n"
                                  "Return the response **ONLY** in JSON format, "
                                  "with the following structure: "
                                  '{\"mode\": \"selecting\",'
                                  ' \"response\": '
                                  '\{\"1\": '
                                  '\"[One sentence summary for moment 1]\"\, '
                                  '\"2\": \"[One sentence summary for moment 2]\"}}'}

        self.system_config.last_request_type = "selecting"

        # send request to GPT
        send_gpt_request_command = CommandParser.parse("send_gpt_request", self.system_config)
        if send_gpt_request_command is not None:
            send_gpt_request_command.execute(user_request)
            # self.system_config.text_feedback_to_show = text_feedback
            # self.system_config.audio_feedback_to_show = audio_feedback

        return True
