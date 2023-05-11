from src.Command.Command import Command
from src.Module.Vision.google_vision import get_image_labels
from src.Module.Vision.huggingface_query import get_image_caption
from src.Utilities.json import detect_json


class NewRecordingCommand(Command):
    def __init__(self, sys_config):
        super().__init__()
        self.system_config = sys_config

    def execute(self):
        audio = None
        user_behavior = None

        prompt = {}
        if self.system_config.picture_window_status:
            moment_idx = self.system_config.get_moment_idx()
            moment_idx += 1
            self.system_config.set_moment_idx(moment_idx)
            prompt["no"] = moment_idx
            photo_label = get_image_labels(self.system_config.latest_photo_file_path)
            photo_caption = get_image_caption(self.system_config.latest_photo_file_path)
            if photo_label is not None:
                prompt["photo_label"] = photo_label.rstrip()
            if photo_caption is not None:
                prompt["photo_caption"] = photo_caption.rstrip()

            self.system_config.picture_window_status = False

            if self.system_config.test_mode:
                audio = input("Please input the simulated audio in the environment here: ")
                user_behavior = input("Please input the simulated user behavior in the environment here: ")

        if audio is not None:
            prompt["audio"] = audio
        if user_behavior is not None:
            prompt["user_behavior"] = user_behavior

        # Transcribe voice command and get response from GPT
        voice_command = self.system_config.final_transcription
        prompt["user comments/commands"] = voice_command

        gpt = self.system_config.get_GPT()
        response = gpt.process_prompt_and_get_gpt_response(command=str(prompt))

        json_response = detect_json(response)

        try:
            if json_response is not None:
                response = f"New Note:\n{json_response['response']['summary of newly added content']}\n\n" \
                           f"Questions:\n{json_response['response']['question to users']}\n"
        except Exception as e:
            pass

        return response

    def undo(self):
        pass
