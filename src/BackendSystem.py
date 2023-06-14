import os
import time

import cv2
import numpy as np

from src.Data.SystemConfig import SystemConfig
from src.Data.SystemStatus import SystemStatus
from src.Module.Audio.live_transcriber import LiveTranscriber
from src.Module.LLM.GPT import GPT
from src.Module.Vision.utilities import compare_histograms
from src.Storage.writer import log_manipulation
from src.Action import ActionParser

import warnings

from src.Utilities.constant import chat_file, slim_history_file

SILENCE_THRESHOLD = 10

warnings.filterwarnings("ignore", category=UserWarning)


class BackendSystem:
    def __init__(self, system_config, ui=None):
        self.previous_sentiment_scores = None
        self.user_explicit_input = None
        self.silence_start_time = None
        self.simulated_fixation = False
        self.zoom_in = None
        self.previous_vision_frame = None
        self.previous_norm_pos = None
        self.system_config = system_config
        self.system_status = SystemStatus()
        self.log_path = os.path.join(self.system_config.folder_path + "log.csv")
        self.current_state = None
        self.ui = ui

    def run(self):
        while True:
            # Get the current state
            current_state = self.system_status.get_current_state()
            if current_state != self.current_state:
                self.current_state = current_state
                print("Current state: " + current_state)

            if self.detect_user_explicit_input():
                if self.user_explicit_input == 'voice_comment':
                    self.system_status.set_state('comments_to_gpt')
                    action = self.system_status.get_current_state()
                    print("Action: " + action)
                    success = ActionParser.parse(action, self.system_config).execute()
                    if not success:
                        self.system_status.set_state("init")
                        self.system_config.notification = None
                        self.system_config.text_feedback_to_show = ""
                elif self.user_explicit_input == 'take_photo':
                    self.system_status.set_state('manual_photo_comments_pending')
                    action = self.system_status.get_current_state()
                    ActionParser.parse(action, self.system_config).execute()
                    self.system_config.frame_shown_in_picture_window = self.system_config.potential_interested_frame
                elif self.user_explicit_input == 'full_writing':
                    self.system_status.set_state('full_writing_pending')
                    action = self.system_status.get_current_state()
                    ActionParser.parse(action, self.system_config).execute()

                self.user_explicit_input = None
                continue

            if current_state == 'init':
                emotion_classifier = self.system_config.get_transcriber()
                if emotion_classifier is not None:
                    if emotion_classifier.stop_event.is_set():
                        emotion_classifier.start()
                if self.detect_gaze_and_zoom_in():
                    self.system_config.show_interest_icon = True
                    self.system_status.trigger('gaze')
                    action = self.system_status.get_current_state()
                    ActionParser.parse(action, self.system_config).execute()
                elif self.detect_positive_tone():
                    self.system_status.set_state('manual_photo_comments_pending')
                    action = self.system_status.get_current_state()
                    ActionParser.parse(action, self.system_config).execute()
                    self.system_config.frame_shown_in_picture_window = self.system_config.potential_interested_frame
                elif self.detect_interested_audio():
                    self.system_status.set_state('audio_comments_pending')
                    action = self.system_status.get_current_state()
                    ActionParser.parse(action, self.system_config).execute()
                elif self.detect_interested_object():
                    self.system_status.set_state('manual_photo_comments_pending')
                    action = self.system_status.get_current_state()
                    ActionParser.parse(action, self.system_config).execute()
                    self.system_config.frame_shown_in_picture_window = self.system_config.potential_interested_frame

            elif current_state == 'photo_pending':
                if self.detect_user_move_to_another_place():
                    self.system_status.trigger('move_to_another_place')
                    action = self.system_status.get_current_state()
                    ActionParser.parse(action, self.system_config).execute()
            elif current_state == 'photo_comments_pending' \
                    or current_state == 'manual_photo_comments_pending' \
                    or current_state == 'show_gpt_response' \
                    or current_state == 'audio_comments_pending':
                if self.system_config.audio_feedback_finished_playing \
                        and self.system_config.audio_feedback_to_show is None:
                    if self.detect_user_speak():
                        self.system_config.text_feedback_to_show = ""
                        self.system_status.trigger('speak')
                        action = self.system_status.get_current_state()
                        success = ActionParser.parse(action, self.system_config).execute()
                        if not success:
                            self.system_status.set_state("init")
                        self.system_config.notification = None

                    elif self.detect_user_ignore():
                        self.system_status.trigger('ignore')
                        self.system_config.notification = None
                        self.system_config.text_feedback_to_show = ""
            elif current_state == 'comments_on_photo' or current_state == 'comments_to_gpt' \
                    or current_state == 'full_writing_pending' or current_state == 'comments_on_audio':
                if self.detect_gpt_response():
                    self.system_config.notification = None
                    self.system_status.trigger('gpt_generate_response')
                    action = self.system_status.get_current_state()
                    ActionParser.parse(action, self.system_config).execute(self.ui)

    def take_user_explict_input(self, user_input):
        self.system_status.trigger(user_input)
        action = self.system_status.get_current_state()
        ActionParser.parse(action, self.system_config).execute()

    def detect_gaze_and_zoom_in(self):
        previous_frame_sim = 0
        last_interested_frame_sim = 0
        zoom_in = self.system_config.vision_detector.zoom_in
        closest_object = self.system_config.vision_detector.closest_object
        person_count = self.system_config.vision_detector.person_count
        fixation_detected = self.system_config.vision_detector.fixation_detected
        current_frame = self.system_config.vision_detector.original_frame
        norm_pos = self.system_config.vision_detector.norm_gaze_position

        if self.simulated_fixation:
            self.simulated_fixation = False
            fixation_detected = True
            norm_pos = (0.5, 0.5)

        if self.previous_norm_pos == norm_pos:
            return False

        self.previous_norm_pos = norm_pos


        if self.system_config.potential_interested_frame is not None:
            last_interested_frame_sim = compare_histograms(self.system_config.potential_interested_frame,
                                                           current_frame)
                # print(last_interested_frame_sim, previous_frame_sim)
            # print(frame_sim)

        not_similar_frame = last_interested_frame_sim < 0.6

        print(f"Zoom in: {zoom_in}, fixation: {fixation_detected}, "
              f"last_interested_frame_sim: {last_interested_frame_sim}, "
              f"not_similar_frame: {not_similar_frame}")

        if (zoom_in or fixation_detected) and not_similar_frame and norm_pos is not None:
            # print(f"Zoom in: {zoom_in}, fixation: {fixation_detected}, "
            #       f"frame_sim: {last_interested_frame_sim, previous_frame_sim}")

            # Conditions to determine the user's behavior
            if zoom_in and fixation_detected:
                self.system_config.user_behavior = f"Moving close to and looking at: {closest_object}"
            elif self.zoom_in:
                self.system_config.user_behavior = f"Moving close to: {closest_object}"
            elif fixation_detected:
                self.system_config.user_behavior = f"Looking at: {closest_object}"

            log_manipulation(self.log_path, self.system_config.user_behavior)
            self.previous_vision_frame = current_frame
            return True
        self.previous_vision_frame = current_frame
        return False

    def detect_user_move_to_another_place(self):
        current_frame = self.system_config.vision_detector.original_frame
        fixation_detected = self.system_config.vision_detector.fixation_detected
        # norm_pos = self.system_config.vision_detector.norm_gaze_position
        difference = cv2.subtract(current_frame, self.previous_vision_frame)
        result = not np.any(difference)
        if result:
            return False
        else:
            cv2.imwrite("diff.jpg", difference)
        # if self.previous_norm_pos == norm_pos:
        #     return False
        # self.previous_norm_pos = norm_pos
        # print(f"Fixation detected: {fixation_detected}, {self.system_config.potential_interested_frame is not None}")
        if self.system_config.potential_interested_frame is not None:
            potential_frame_sim = compare_histograms(self.system_config.potential_interested_frame, current_frame)
            previous_frame_sim = compare_histograms(self.previous_vision_frame, current_frame)
            print(potential_frame_sim, previous_frame_sim)
            self.previous_vision_frame = current_frame
            if potential_frame_sim < 0.6 and previous_frame_sim < 0.85:
                self.system_config.frame_shown_in_picture_window = self.system_config.potential_interested_frame
                return True
        return False

    def detect_user_speak(self):
        voice_transcribe = self.system_config.get_transcriber()
        if voice_transcribe.stop_event.is_set():
            voice_transcribe.start()
        else:
            voice_transcribe.stop_emotion_classification_and_start_transcription()
            # print("start to transcribe")
        score, category = self.system_config.get_bg_audio_analysis_result()
        if category is None:
            return False
        print(f"{category}: {score}")
        # if category is speech, then return True
        if category == 'Speech' and score > 0.7:
            self.silence_start_time = None
            return True
        time.sleep(0.2)
        return False

    def detect_positive_tone(self):
        emotion_classifier = self.system_config.get_transcriber()
        if emotion_classifier is None:
            return False

        scores = emotion_classifier.scores

        if scores is None:
            return False

        if scores['joy'] + scores['surprise'] > 0.7 and scores != self.previous_sentiment_scores:
            self.previous_sentiment_scores = scores
            print("Positive tone detected")
            emotion_classifier.stop()
            return True

    def detect_interested_audio(self):
        score, category = self.system_config.get_bg_audio_analysis_result()
        if category is not None:
            if category in self.system_config.get_bg_audio_interesting_categories() and score > 0.7:
                last_time = self.system_config.previous_interesting_audio_time.get(category, 0)
                if time.time() - last_time > 60:
                    self.system_config.interesting_audio = category
                    self.system_config.previous_interesting_audio_time[category] = time.time()
                    return True

        return False

    def detect_interested_object(self):
        if self.system_config.vision_detector.potential_interested_object is not None:
            potential_interested_object = self.system_config.vision_detector.potential_interested_object
            last_time = self.system_config.previous_interesting_object_time.get(potential_interested_object, 0)
            if time.time() - last_time > 60:
                self.system_config.interesting_object = potential_interested_object
                self.system_config.previous_interesting_object_time[potential_interested_object] = time.time()
                return True

        return False

    def detect_user_ignore(self):
        if self.silence_start_time is None:
            self.silence_start_time = time.time()
        else:
            time_diff = time.time() - self.silence_start_time
            print(f"Reply in {int(SILENCE_THRESHOLD - time_diff)}s or ignore it.")
            self.system_config.notification = f"Reply in {int(SILENCE_THRESHOLD - time_diff)}s or ignore it."
            if time_diff > SILENCE_THRESHOLD:
                self.silence_start_time = None
                voice_transcribe = self.system_config.get_transcriber()
                if not voice_transcribe.stop_event.is_set():
                    voice_transcribe.stop_transcription_and_start_emotion_classification()
                return True

        time.sleep(1)
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

    def simulate_func(self, func):
        if func == "gaze":
            self.simulated_fixation = True


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
