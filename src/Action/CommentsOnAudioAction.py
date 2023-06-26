from src.Action.Action import Action
from src.Command import CommandParser


class CommentsOnAudioAction(Action):
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

        user_request["interested audio"] = self.system_config.interesting_audio

        # send request to GPT
        send_gpt_request_command = CommandParser.parse("send_gpt_request", self.system_config)

        if send_gpt_request_command is not None:
            text_feedback, audio_feedback = send_gpt_request_command.execute(user_request)

            self.system_config.text_feedback_to_show = text_feedback
            self.system_config.audio_feedback_to_show = audio_feedback
            print(f"The text feedback is: {self.system_config.text_feedback_to_show}, "
                  f"and the audio feedback is: {self.system_config.audio_feedback_to_show}")

        return True

