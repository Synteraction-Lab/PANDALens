from datetime import datetime

from src.Action.Action import Action
from src.Command import CommandParser
from src.Utilities.location import get_current_location


class CommentsOnGPTResponseAction(Action):
    def __init__(self, sys_config):
        super().__init__()
        self.system_config = sys_config

    def execute(self):
        user_request = {}

        # transcribe voice
        transcribe_command = CommandParser.parse("transcribe_voice", self.system_config)
        if transcribe_command is not None:
            voice_transcription = transcribe_command.execute()
            user_request["user_voice_transcription"] = voice_transcription

        # send request to GPT
        send_gpt_request_command = CommandParser.parse("send_gpt_request", self.system_config)
        if send_gpt_request_command is not None:
            text_feedback, audio_feedback = send_gpt_request_command.execute(user_request)
            self.system_config.text_feedback_to_show = text_feedback
            self.system_config.audio_feedback_to_play = audio_feedback


