from datetime import datetime

from src.Action.Action import Action
from src.Command import CommandParser
from src.Utilities.location import get_current_location


class CommentsOnPhotoAction(Action):
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

        if not self.system_config.naive:
            # get image info
            get_image_info_command = CommandParser.parse("get_image_info", self.system_config)
            try:
                if get_image_info_command is not None:
                    image_info = get_image_info_command.execute()
                    user_request["image_info"] = image_info
            except Exception as e:
                print("Error: cannot get image info", e)


            # get location & time
            try:
                user_request["location"] = get_current_location()
            except Exception as e:
                print("Error: cannot get location", e)

            user_request["time"] = datetime.now().strftime("%Y/%m/%d, %H:%M")

            # get background audio
            audio = self.system_config.get_bg_audio_analysis_result()
            if audio is not None:
                user_request["background audio"] = audio

            # get user behavior
            if self.system_config.user_behavior_when_recording is not None:
                user_behavior = self.system_config.user_behavior_when_recording
                self.system_config.user_behavior_when_recording = None
                user_request["user_behavior"] = user_behavior

        # send request to GPT
        send_gpt_request_command = CommandParser.parse("send_gpt_request", self.system_config)
        if send_gpt_request_command is not None:
            text_feedback, audio_feedback = send_gpt_request_command.execute(user_request)

            # self.system_config.text_feedback_to_show = text_feedback
            # self.system_config.audio_feedback_to_show = audio_feedback
            print(f"The text feedback is: {self.system_config.text_feedback_to_show}, "
                  f"and the audio feedback is: {self.system_config.audio_feedback_to_show}")

        return True

