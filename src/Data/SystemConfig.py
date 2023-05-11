import os


class SystemConfig:
    def __init__(self):
        self.final_transcription = ""
        self.previous_transcription = ""
        self.picture_window_status = False
        self.audio_file_name = None
        self.folder_path = None
        self.GPT = None
        self.is_recording = False
        self.voice_feedback_process = None
        self.moment_idx = 0
        self.image_folder = None
        self.transcriber = None
        self.test_mode = False
        self.latest_photo_file_path = None
        self.last_image_folder_in_test_mode = "/"

    def get_final_transcription(self):
        return self.final_transcription

    def set_final_transcription(self, final_transcription):
        self.final_transcription = final_transcription

    def get_previous_transcription(self):
        return self.previous_transcription

    def set_previous_transcription(self, previous_transcription):
        self.previous_transcription = previous_transcription

    def get_picture_window_status(self):
        return self.picture_window_status

    def set_picture_window_status(self, picture_window_status):
        self.picture_window_status = picture_window_status

    def get_audio_file_name(self):
        return self.audio_file_name

    def set_audio_file_name(self, audio_file_name):
        self.audio_file_name = audio_file_name

    def get_folder_path(self):
        return self.folder_path

    def set_folder_path(self, folder_path):
        self.folder_path = folder_path

    def get_GPT(self):
        return self.GPT

    def set_GPT(self, gpt, task_name):
        self.GPT = gpt
        # Initiate the conversation
        self.GPT.setup_chat_gpt(task_name)

    def get_is_recording(self):
        return self.is_recording

    def set_is_recording(self, is_recording):
        self.is_recording = is_recording

    def get_voice_feedback_process(self):
        return self.voice_feedback_process

    def set_voice_feedback_process(self, voice_feedback_process):
        self.voice_feedback_process = voice_feedback_process

    def get_moment_idx(self):
        return self.moment_idx

    def set_moment_idx(self, moment_idx):
        self.moment_idx = moment_idx

    def get_image_folder(self):
        return self.image_folder

    def set_image_folder(self, image_folder):
        self.image_folder = image_folder

    def get_transcriber(self):
        return self.transcriber

    def set_transcriber(self, transcriber):
        self.transcriber = transcriber

    def get_test_mode(self):
        return self.test_mode

    def set_test_mode(self, test_mode):
        self.test_mode = test_mode

    def get_latest_photo_file_path(self):
        return self.latest_photo_file_path

    def set_latest_photo_file_path(self, image_path):
        self.latest_photo_file_path = image_path
