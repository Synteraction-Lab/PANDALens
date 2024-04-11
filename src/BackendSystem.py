import os
import time

import cv2
import numpy as np

from src.Command.PhotoCommand import PhotoCommand
from src.Data.SystemConfig import SystemConfig
from src.Data.SystemStatus import SystemStatus
from src.Module.Audio.live_transcriber import LiveTranscriber
from src.Module.LLM.GPT import GPT
from src.Module.Vision.utilities import compare_histograms
from src.Storage.writer import log_manipulation, remove_file_async
from src.Action import ActionParser

import warnings

from src.Utilities.constant import chat_file, slim_history_file

SILENCE_THRESHOLD = 8

warnings.filterwarnings("ignore", category=UserWarning)


def calculate_dynamic_threshold(last_interested_frame_sim):
    BASE_THRESHOLD = 15  # set your base threshold value here
    THRESHOLD_FACTOR = 200  # set your factor for adjusting threshold here

    threshold = BASE_THRESHOLD + (last_interested_frame_sim * last_interested_frame_sim * THRESHOLD_FACTOR)
    return threshold


class BackendSystem:
    def __init__(self, system_config):
        self.user_confirm_move_to_another_place = False
        self.last_gaze_detection_time = 0
        self.previous_sentiment_scores = None
        self.user_explicit_input = None
        self.silence_start_time = None
        self.simulated_fixation = False
        self.zoom_in = None
        self.previous_vision_frame = None
        self.previous_norm_pos = None
        self.system_config = system_config
        self.system_status = SystemStatus()
        self.log_path = self.system_config.log_path
        self.prev_state = None

    def run(self):
        while True:
            # Get the current state
            current_state = self.system_status.get_current_state()
            # self.system_config.gaze_pos = self.system_config.vision_detector.get_norm_gaze_position()
            if current_state != self.prev_state:
                self.prev_state = current_state
                print("Current state: " + current_state)

            if self.detect_user_explicit_input():
                if self.user_explicit_input == 'voice_comment':
                    self.system_status.set_state('comments_to_gpt')
                    action = self.system_status.get_current_state()
                    success = ActionParser.parse(action, self.system_config).execute()
                    if not success:
                        self.system_status.set_state("init")
                        with self.system_config.notification_lock:
                            if self.system_config.cancel_recording_command:
                                self.system_config.cancel_recording_command = False
                            else:
                                self.system_config.notification = None
                        transcriber = self.system_config.get_transcriber()
                        if transcriber is not None:
                            transcriber.stop_transcription_and_start_emotion_classification()
                        self.system_config.text_feedback_to_show = ""
                elif self.user_explicit_input == 'take_photo':
                    # with self.system_config.notification_lock:
                    #     self.system_config.notification = {'notif_type': 'processing_icon',
                    #                                        'position': 'middle-right'}

                    self.system_status.set_state('manual_photo_comments_pending')
                    ActionParser.parse('manual_photo_comments_pending', self.system_config).execute()
                    with self.system_config.notification_lock:
                        self.system_config.notification = {'notif_type': 'picture',
                                                           'content': self.system_config.potential_interested_frame,
                                                           'position': 'middle-right'}
                    self.system_config.start_non_audio_feedback_display()
                elif self.user_explicit_input == 'full_writing':
                    with self.system_config.notification_lock:
                        self.system_config.notification = {'notif_type': 'processing_icon',
                                                           'position': 'middle-right'}
                    self.system_status.set_state('full_writing_pending')
                    action = self.system_status.get_current_state()
                    ActionParser.parse(action, self.system_config).execute()
                elif self.user_explicit_input == 'select':
                    with self.system_config.notification_lock:
                        self.system_config.notification = {'notif_type': 'processing_icon',
                                                           'position': 'middle-right'}
                    self.system_status.set_state('select_moments')
                    action = self.system_status.get_current_state()
                    ActionParser.parse(action, self.system_config).execute()
                elif self.user_explicit_input == "terminate_waiting_for_user_response":
                    with self.system_config.notification_lock:
                        self.system_config.notification = None
                    self.system_status.set_state("init")
                    self.silence_start_time = None
                    transcriber = self.system_config.get_transcriber()
                    if transcriber is not None:
                        transcriber.stop_transcription_and_start_emotion_classification()

                self.user_explicit_input = None
                continue

            if current_state == 'init':
                if not self.system_config.naive:
                    self.system_config.gpt_question_count = 0
                    emotion_classifier = self.system_config.get_transcriber()
                    if emotion_classifier is not None:
                        if emotion_classifier.stop_event.is_set():
                            emotion_classifier.start()
                            emotion_classifier.stop_transcription_and_start_emotion_classification()

                    # Processing pending task first
                    if self.system_config.pending_task_list:
                        photo, photo_file_path = self.system_config.pending_task_list.pop(0)
                        time.sleep(0.5)
                        with self.system_config.notification_lock:
                            self.system_config.notification = {'notif_type': 'picture',
                                                               'content': photo,
                                                               'position': 'middle-right'}
                        self.system_config.set_latest_photo_file_path(photo_file_path)
                        self.system_status.set_state('photo_comments_pending')

                    # Detect implicit input
                    if self.detect_gaze_and_zoom_in():
                        with self.system_config.notification_lock:
                            self.system_config.notification = {
                                'notif_type': 'fpv_photo_icon',
                                'position': 'top-right'
                            }
                        self.system_status.trigger('gaze')
                        action = self.system_status.get_current_state()
                        ActionParser.parse(action, self.system_config).execute()
                    elif self.detect_interested_audio():
                        self.system_status.set_state('audio_comments_pending')
                        log_manipulation(self.log_path, f"interested_audio: {self.system_config.interesting_audio}")
                        action = self.system_status.get_current_state()
                        ActionParser.parse(action, self.system_config).execute()
                    elif self.detect_interested_object():
                        self.system_status.set_state('manual_photo_comments_pending')
                        log_manipulation(self.log_path, f"interested_object: {self.system_config.interesting_object}")
                        action = self.system_status.get_current_state()
                        ActionParser.parse(action, self.system_config).execute()

                        with self.system_config.notification_lock:
                            self.system_config.notification = {'notif_type': 'like_object_icon',
                                                               'label': self.system_config.interesting_object,
                                                               'position': 'middle-right'}
                        self.system_config.start_non_audio_feedback_display()
                    elif self.detect_positive_tone():
                        self.system_status.set_state('manual_photo_comments_pending')
                        log_manipulation(self.log_path, "positive_tone")
                        action = self.system_status.get_current_state()
                        ActionParser.parse(action, self.system_config).execute()

                        with self.system_config.notification_lock:
                            self.system_config.notification = {'notif_type': 'like_icon', 'position': 'middle-right'}
                        self.system_config.start_non_audio_feedback_display()


                # else:

            elif current_state == 'photo_pending':
                if self.detect_user_move_to_another_place():
                    self.system_status.trigger('move_to_another_place')
                    log_manipulation(self.log_path, "move_to_another_place")
                    action = self.system_status.get_current_state()
                    ActionParser.parse(action, self.system_config).execute()
            elif current_state in ['photo_comments_pending', 'manual_photo_comments_pending', 'audio_comments_pending'] \
                    or (current_state == 'show_gpt_response' and self.system_config.gpt_response_type == "authoring"):
                if self.system_config.detect_audio_feedback_finished():
                    if self.detect_user_speak() and self.system_config.non_audio_feedback_display_ended():
                        self.system_config.text_feedback_to_show = ""
                        self.system_status.trigger('speak')
                        action = self.system_status.get_current_state()
                        success = ActionParser.parse(action, self.system_config).execute()
                        if not success:
                            self.system_status.set_state("init")

                            with self.system_config.notification_lock:
                                if self.system_config.cancel_recording_command:
                                    self.system_config.cancel_recording_command = False
                                else:
                                    self.system_config.notification = None
                            transcriber = self.system_config.get_transcriber()
                            if transcriber is not None:
                                transcriber.stop_transcription_and_start_emotion_classification()
                        self.silence_start_time = None

                    elif self.detect_user_ignore():
                        transcriber = self.system_config.get_transcriber()
                        if transcriber is not None:
                            transcriber.stop_transcription_and_start_emotion_classification()
                        self.system_status.trigger('ignore')
                        log_manipulation(self.log_path, "ignore")
                        with self.system_config.notification_lock:
                            self.system_config.notification = None
                        self.system_config.text_feedback_to_show = ""
                        self.silence_start_time = None
                else:
                    self.silence_start_time = None
            elif current_state in ['comments_on_photo', 'comments_to_gpt', 'full_writing_pending',
                                   'comments_on_audio', 'select_moments']:
                if self.detect_gpt_response():
                    # self.system_config.notification = None
                    self.system_status.trigger('gpt_generate_response')
                    action = self.system_status.get_current_state()
                    ActionParser.parse(action, self.system_config).execute()

    def take_user_explict_input(self, user_input):
        self.system_status.trigger(user_input)
        action = self.system_status.get_current_state()
        ActionParser.parse(action, self.system_config).execute()

    def detect_gaze_and_zoom_in(self):
        previous_frame_sim = 0
        last_interested_frame_sim = 0
        zoom_in = self.system_config.vision_detector.get_zoom_in()
        closest_object = self.system_config.vision_detector.get_closest_object()
        person_count = self.system_config.vision_detector.get_person_count()
        fixation_detected = self.system_config.vision_detector.get_fixation_detected()
        current_frame = self.system_config.vision_detector.get_original_frame()
        norm_pos = self.system_config.vision_detector.get_norm_gaze_position()
        self.system_config.gaze_pos = norm_pos

        if self.simulated_fixation:
            self.simulated_fixation = False
            fixation_detected = True
            norm_pos = (0.5, 0.5)

        if self.previous_norm_pos == norm_pos:
            return False

        self.previous_norm_pos = norm_pos

        if self.system_config.potential_interested_frame is not None:
            last_interested_frame_sim = compare_histograms(self.system_config.potential_interested_frame, current_frame)

        not_similar_frame = last_interested_frame_sim < 0.6

        print(f"Zoom in: {zoom_in}, fixation: {fixation_detected}, "
              f"last_interested_frame_sim: {last_interested_frame_sim}, "
              f"not_similar_frame: {not_similar_frame}")

        if (zoom_in or fixation_detected) and not_similar_frame and norm_pos is not None:
            now = time.time()
            dynamic_threshold = calculate_dynamic_threshold(last_interested_frame_sim)
            if now - self.last_gaze_detection_time > dynamic_threshold:
                # Conditions to determine the user's behavior
                if zoom_in and fixation_detected:
                    self.system_config.user_behavior = f"Moving close to and looking at: {closest_object}"
                elif zoom_in:
                    self.system_config.user_behavior = f"Moving close to: {closest_object}"
                elif fixation_detected:
                    self.system_config.user_behavior = f"Looking at: {closest_object}"

                log_manipulation(self.log_path, self.system_config.user_behavior)
                self.previous_vision_frame = current_frame
                self.system_config.potential_interested_frame = current_frame
                self.last_gaze_detection_time = now
                return True
        self.previous_vision_frame = current_frame
        return False

    def detect_user_move_to_another_place(self):
        if self.user_confirm_move_to_another_place:
            self.user_confirm_move_to_another_place = False
            with self.system_config.notification_lock:
                self.system_config.notification = {'notif_type': 'picture',
                                                   'content': self.system_config.potential_interested_frame,
                                                   'position': 'middle-right'}
            self.system_config.start_non_audio_feedback_display()
            return True
        current_frame = self.system_config.vision_detector.get_original_frame()

        if self.system_config.potential_interested_frame is not None:
            potential_frame_sim = compare_histograms(self.system_config.potential_interested_frame, current_frame)
            previous_frame_sim = compare_histograms(self.previous_vision_frame, current_frame)
            print(potential_frame_sim, previous_frame_sim)
            self.previous_vision_frame = current_frame

            # if potential_frame_sim < 0.6 and previous_frame_sim < 0.85:
            if potential_frame_sim < 0.75:
                # self.system_config.frame_shown_in_picture_window = self.system_config.potential_interested_frame
                with self.system_config.notification_lock:
                    self.system_config.notification = {'notif_type': 'picture',
                                                       'content': self.system_config.potential_interested_frame,
                                                       'position': 'middle-right'}
                self.system_config.start_non_audio_feedback_display()
                return True
        return False

    def detect_user_speak(self) -> bool:
        voice_transcribe = self.system_config.get_transcriber()
        if voice_transcribe.stop_event.is_set():
            voice_transcribe.start()
        if voice_transcribe.mode != "voice_transcription":
            voice_transcribe.stop_emotion_classification_and_start_transcription()
        score, category = self.system_config.get_bg_audio_analysis_result()
        if category is None:
            time.sleep(0.3)
            return False
        print(f"{category}: {score}")
        # if category is speech, then return True
        if category is not None and score is not None:
            if category == 'Speech' and score > 0.7:
                self.silence_start_time = None
                self.system_config.progress_bar_percentage = None
                return True
        time.sleep(0.3)
        return False

    def detect_speech_without_init_voice_transcribe(self) -> bool:
        score, category = self.system_config.get_bg_audio_analysis_result()
        if category is None:
            time.sleep(0.3)
            return False
        print(f"{category}: {score}")
        # if category is speech, then return True
        if category is not None and score is not None:
            if category == 'Speech' and score > 0.7:
                return True
        time.sleep(0.3)
        return False

    def detect_positive_tone(self):
        emotion_classifier = self.system_config.get_transcriber()
        if emotion_classifier is None:
            return False

        scores = emotion_classifier.scores

        if scores is None:
            return False

        if scores['joy'] + scores['surprise'] > 0.75 and scores != self.previous_sentiment_scores:
            self.previous_sentiment_scores = scores
            emotion_classifier.stop_emotion_classification_and_start_transcription()
            return True

    def detect_interested_audio(self):
        score, category = self.system_config.get_bg_audio_analysis_result()
        if category is not None and score is not None:
            if category in self.system_config.get_bg_audio_interesting_categories() and score > 0.8:
                last_time = self.system_config.previous_interesting_audio_time.get(category, 0)
                if time.time() - last_time > 60:
                    self.system_config.interesting_audio = category
                    self.system_config.previous_interesting_audio_time[category] = time.time()
                    return True

        return False

    def detect_interested_object(self) -> bool:
        potential_interested_object = self.system_config.vision_detector.get_potential_interested_object()
        if potential_interested_object is not None:
            last_time = self.system_config.previous_interesting_object_time.get(potential_interested_object, 0)
            if time.time() - last_time > 60:
                self.system_config.interesting_object = potential_interested_object
                self.system_config.previous_interesting_object_time[potential_interested_object] = time.time()
                return True

        return False

    def detect_user_ignore(self):
        if self.silence_start_time is None:
            self.silence_start_time = time.time()
            print("Silence start time: ", self.silence_start_time)
        else:
            time_diff = time.time() - self.silence_start_time
            print(f"Reply in {int(SILENCE_THRESHOLD - time_diff)}s or ignore it. Start time: {self.silence_start_time}")
            # self.system_config.notification = f"Reply in {int(SILENCE_THRESHOLD - time_diff)}s or ignore it."
            self.system_config.progress_bar_percentage = (SILENCE_THRESHOLD - time_diff) / SILENCE_THRESHOLD
            if time_diff > SILENCE_THRESHOLD:
                self.silence_start_time = None
                self.system_config.progress_bar_percentage = 0
                voice_transcribe = self.system_config.get_transcriber()
                if not voice_transcribe.stop_event.is_set():
                    voice_transcribe.stop_transcription_and_start_emotion_classification()
                return True
        # time.sleep(0.3)
        return False

    def detect_gpt_response(self):
        if self.system_config.text_feedback_to_show is not None \
                or self.system_config.audio_feedback_to_show is not None:
            return True
        return False

    def detect_user_explicit_input(self):
        if self.user_explicit_input is not None:
            return True

    def set_user_explicit_input(self, user_input):
        self.user_explicit_input = user_input
        if self.user_explicit_input == 'stop_recording':
            self.system_config.stop_recording_command = True
            self.user_explicit_input = None
        elif self.user_explicit_input == 'cancel_recording':
            self.system_config.stop_recording_command = True
            self.system_config.cancel_recording_command = True
            self.user_explicit_input = None
        elif self.user_explicit_input == 'hide_text_box':
            self.system_status.set_state("init")
        elif self.user_explicit_input == 'finish_photo_pending_status':
            self.user_confirm_move_to_another_place = True
        elif self.user_explicit_input == 'retake_photo':
            self.replace_new_photo()
        elif self.user_explicit_input == 'take_photo':
            with self.system_config.notification_lock:
                self.system_config.notification = {'notif_type': 'processing_icon',
                                                   'position': 'middle-right'}

    def simulate_func(self, func):
        if func == "gaze":
            self.simulated_fixation = True

    def add_photo_to_pending_task_list(self):
        with self.system_config.notification_lock:
            photo, path = PhotoCommand(self.system_config).execute()
            self.system_config.pending_task_list.append((photo, path))
            # # reduce question number when user take a photo to pending list
            # self.system_config.gpt_question_count += 1
            # self.system_config.notification = {'notif_type': 'picture_thumbnail',
            #                                    'content': photo,
            #                                    'position': 'middle-right', 'duration': 1.5}
            self.system_config.pending_photo_thumbnail = photo

    def replace_new_photo(self):
        self.silence_start_time = time.time()
        print("Silence start time: ", self.silence_start_time)
        remove_file_async(self.system_config.latest_photo_file_path)
        self.system_status.set_state('manual_photo_comments_pending')
        ActionParser.parse('manual_photo_comments_pending', self.system_config).execute()
        with self.system_config.notification_lock:
            self.system_config.notification = {'notif_type': 'picture',
                                               'content': self.system_config.potential_interested_frame,
                                               'position': 'middle-right'}

        self.system_config.start_non_audio_feedback_display()


def test():
    from pynput.keyboard import Key, Listener as KeyboardListener
    import os

    def on_press(key):
        try:
            if key == Key.up:
                backend_system.simulate_func('gaze')
            elif key == Key.down:
                backend_system.set_user_explicit_input('voice_comment')
            elif key == Key.left:
                backend_system.set_user_explicit_input('take_photo')
        except Exception as e:
            print(e)

    def start_mouse_key_listener():
        keyboard_listener = KeyboardListener(
            on_press=on_press)
        keyboard_listener.start()

    system_config = SystemConfig()

    system_config.set_vision_analysis()

    # set the folder path as project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    system_config.folder_path = os.path.join(project_root, "data", "recordings", "test_data")
    image_folder = os.path.join(system_config.folder_path, "auto_image")
    system_config.image_folder = image_folder

    voice_input_device_idx = "MacBook Pro Microphone"

    system_config.set_transcriber(LiveTranscriber(device_index=voice_input_device_idx))

    system_config.set_bg_audio_analysis(device=voice_input_device_idx)

    chat_history_file_name = os.path.join(system_config.folder_path, chat_file)
    slim_history_file_name = os.path.join(system_config.folder_path, slim_history_file)
    system_config.set_GPT(GPT(chat_history_file_name=chat_history_file_name,
                              slim_history_file_name=slim_history_file_name),
                          task_name="travel_blog")

    backend_system = BackendSystem(system_config)
    start_mouse_key_listener()
    backend_system.run()


if __name__ == '__main__':
    test()
