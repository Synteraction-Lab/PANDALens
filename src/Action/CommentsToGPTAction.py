from src.Action.Action import Action
from src.Command import CommandParser


class CommentsToGPTAction(Action):
    def __init__(self, sys_config):
        super().__init__()
        self.system_config = sys_config

    def execute(self):
        user_request = {}

        # transcribe voice
        transcribe_command = CommandParser.parse("transcribe_voice", self.system_config)
        if transcribe_command is not None:
            voice_transcription = transcribe_command.execute()
            if voice_transcription == "":
                return False
            user_request["user_voice_transcription"] = voice_transcription

        if self.system_config.last_request_type == "selecting":
            user_request["user command"] = 'Based on the my selected moments mentioned in "user_voice_transcription", ' \
                                           'generate a full travel blog that ' \
                                           '**Only includes the contents that I select** ' \
                                           'in the following JSON format: ' \
                                           '{"mode": "full",' \
                                           ' "response": ' \
                                           '{"full writing": ' \
                                           '"[full travel blog content in first person narration]", ' \
                                           '"revised parts": "[the newly added or revised content, ' \
                                           'return \"None\" when no revision.]"}'
            self.system_config.last_request_type = "full"

        # send request to GPT
        send_gpt_request_command = CommandParser.parse("send_gpt_request", self.system_config)
        if send_gpt_request_command is not None:
            text_feedback, audio_feedback = send_gpt_request_command.execute(user_request)
            # self.system_config.text_feedback_to_show = text_feedback
            # self.system_config.audio_feedback_to_show = audio_feedback

        return True


