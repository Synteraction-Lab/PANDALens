import multiprocessing
import os
import threading
import time
from multiprocessing.managers import BaseManager

from src.Module.Audio.audio_classifier import AudioClassifierRunner
from src.Module.Gaze.gaze_data import GazeData
from src.Module.Vision.Yolo.yolov8s import ObjectDetector

NON_AUDIO_FEEDBACK_DISPLAY_TIME = 1.8

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


class SystemConfig(object):
    def __init__(self):
        self.non_audio_feedback_display_start_time = None
        self.progress_bar_percentage = None
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
        self.previous_interesting_object_time = {}
        self.interesting_object = None
        self.stop_recording_command = False
        self.show_interest_icon = False
        self.last_request_type = None
        self.naive = False
        self.gaze_pos = None
        self.log_path = None
        self.pending_task_list = []
        self.notification_lock = threading.Lock()
        self.cancel_recording_command = False
        self.gpt_response_type = None
        self.latest_moment_list = None

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

    def set_naive(self, naive):
        if naive == "UbiWriter":
            self.naive = False
        else:
            self.naive = True

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
        manager = multiprocessing.Manager()
        self.audio_classifier_results = manager.list([None, None])
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.audio_classifier_runner = AudioClassifierRunner(
            model=os.path.join(project_root, "src", "Module", "Audio", "lite-model_yamnet_classification.tflite"),
            queue=self.audio_classifier_results, device=device)

        multiprocessing.Process(target=self.audio_classifier_runner.run).start()

    def get_bg_audio_analysis(self):
        return self.audio_classifier_runner()

    def get_bg_audio_analysis_result(self):
        score, category_name = None, None
        # while not self.audio_classifier_results.empty():
        score, category_name = self.audio_classifier_results[0], self.audio_classifier_results[1]
        return score, category_name

    def get_bg_audio_interesting_categories(self):
        return interesting_audioset_categories

    def set_vision_analysis(self, record=False):
        BaseManager.register('GazeData', GazeData)
        manager = BaseManager()
        manager.start()
        self.vision_detector = manager.GazeData()
        object_detector = ObjectDetector(simulate=False, cv_imshow=False, record=record)
        self.thread_vision = multiprocessing.Process(target=object_detector.run, args=(self.vision_detector,))
        self.thread_vision.start()

    def set_emotion_classifier(self, emotion_classifier):
        self.emotion_classifier = emotion_classifier

    def detect_audio_feedback_finished(self):
        return self.audio_feedback_finished_playing \
            and self.audio_feedback_to_show is None

    def non_audio_feedback_display_ended(self):
        if self.non_audio_feedback_display_start_time is None:
            return True
        if time.time() - self.non_audio_feedback_display_start_time > NON_AUDIO_FEEDBACK_DISPLAY_TIME:
            self.non_audio_feedback_display_start_time = None
            return True
        else:
            return False

    def start_non_audio_feedback_display(self):
        self.non_audio_feedback_display_start_time = time.time()

    def set_log_path(self, log_path):
        self.log_path = log_path
