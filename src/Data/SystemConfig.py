import multiprocessing
import os
import threading

from src.Module.Audio.audio_classifier import AudioClassifierRunner
from src.Module.Vision.Yolo.yolov8s import ObjectDetector

interesting_audioset_categories = [
    'Music',
    # 'Speech',
    'Animal',
    'Vehicle',
    'Natural sounds',
    # 'Human sounds',
    'Musical instrument',
    'Laughter',
    'Thunderstorm',
    'Fireworks',
    'Applause',
    'Babies crying',
    'Footsteps',
    'Water sounds',
    'Wind',
    # 'Typing',
    'Door',
    'Bird',
    'Dog',
    'Cat',
    'Alarm',
    'Phone ring',
    'Chainsaw',
    'Rain',
    'Ocean waves',
    'Train',
    'Airplane',
    'Helicopter',
    'Car',
    'Motorcycle',
    'Bicycle',
    'Siren',
    'Church bells',
    'Clock alarm',
    'Cooking and kitchen sounds',
    'Computer keyboard',
    'Camera shutter',
    'Crackling fire',
    'Screaming',
    'Whispering',
    'Guitar',
    'Piano',
    'Violin',
    'Drum',
    'Trumpet',
    'Saxophone',
    'Harmonica',
    'Cello',
    'Choir singing',
    'Rapping',
    'Beatboxing',
    'Humming'
]


class SystemConfig:
    def __init__(self):
        self.vision_detector = None
        self.audio_classifier_runner = None
        self.audio_classifier_results = None
        self.previous_interesting_audio = None
        self.interesting_audio_for_recording = None
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
        self.interesting_audio = None
        self.user_behavior = None
        self.user_behavior_when_recording = None
        self.previous_interesting_audio_time = {}
        self.emotion_classifier = None
        self.previous_emotion_scores = None
        self.potential_interested_frame = None
        self.frame_shown_in_picture_window = None
        self.text_feedback_to_show = None
        self.audio_feedback_to_show = None
        self.notification = None
        self.audio_feedback_finished_playing = True

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

    def set_bg_audio_analysis(self, device):
        self.audio_classifier_results = multiprocessing.Queue()
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.audio_classifier_runner = AudioClassifierRunner(
            model=os.path.join(project_root, "src", "Module", "Audio", "lite-model_yamnet_classification.tflite"),
            queue=self.audio_classifier_results, device=device)

        multiprocessing.Process(target=self.audio_classifier_runner.run).start()

    def get_bg_audio_analysis(self):
        return self.audio_classifier_runner()

    def get_bg_audio_analysis_result(self):
        score, category_name = None, None
        while not self.audio_classifier_results.empty():
            score, category_name = self.audio_classifier_results.get()
        return score, category_name

    def get_bg_audio_interesting_categories(self):
        return interesting_audioset_categories

    def set_vision_analysis(self):
        self.vision_detector = ObjectDetector(simulate=False, cv_imshow=False)
        self.thread_vision = threading.Thread(target=self.vision_detector.run).start()

    def set_emotion_classifier(self, emotion_classifier):
        self.emotion_classifier = emotion_classifier

