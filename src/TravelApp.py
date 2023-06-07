import os
import subprocess
import threading
import time
import tkinter as tk
from multiprocessing import Process

import cv2
import pandas
import pyttsx3
from PIL import Image, ImageTk
from pynput import keyboard
from pynput.keyboard import Key, Listener as KeyboardListener
from pynput.mouse import Listener as MouseListener

from src.BackendSystem import BackendSystem
from src.Data.SystemConfig import SystemConfig
from src.Module.Audio.emotion_classifer import EmotionClassifier
from src.Module.Audio.live_transcriber import LiveTranscriber, show_devices
from src.Module.LLM.GPT import GPT
from src.Storage.writer import log_manipulation
from src.UI.device_panel import DevicePanel
from src.UI.hierarchy_menu_config import HierarchyMenu
from src.UI.widget_generator import get_button
from src.Utilities.constant import VISUAL_OUTPUT, AUDIO_OUTPUT, audio_file, chat_file, slim_history_file, config_path, \
    image_folder

SILENCE_TIME_THRESHOLD_FOR_STOP_RECORDING = 8


class App:
    def __init__(self, test_mode=False, ring_mouse_mode=False):
        self.backend_system = None
        self.log_path = None
        self.person_count = 0
        self.picture_window_hidden = False
        self.stored_text_widget_content = None
        self.is_hidden_text = False
        self.previous_vision_frame = None
        self.picture_window = None
        self.output_mode = None
        self.config_updated = False
        self.ring_mouse_mode = ring_mouse_mode
        self.system_config = SystemConfig()
        self.system_config.set_test_mode(test_mode)

        self.enable_interest_detection_notification = True

        self.root = tk.Tk()
        # Set up keyboard and mouse listener
        self.start_mouse_key_listener()
        self.audio_lock = threading.Lock()
        self.root.title("UbiWriter")
        # self.root.wm_attributes("-topmost", True)
        self.init_screen_size = "800x600"

        show_devices()

        # Open Setup panel
        DevicePanel(self.root, parent_object_save_command=self.update_config)

        self.system_config.set_vision_analysis()

        # Pack and run the main UI
        self.pack_layout()

        self.root.mainloop()

    def update_config(self):
        if not os.path.isfile(config_path):
            pid_num = os.path.join("p1", "01")
            task_name = "travel_blog"
            output_modality = AUDIO_OUTPUT
            audio_device_idx = 0
        else:
            try:
                df = pandas.read_csv(config_path)
                pid_num = df[df['item'] == 'pid']['details'].item()
                task_name = df[df['item'] == 'task']['details'].item()
                output_modality = df[df['item'] == 'output']['details'].item()
                audio_device_idx = df[df['item'] == 'audio_device']['details'].item()
            except Exception as e:
                pid_num = os.path.join("p1", "01")
                task_name = "travel_blog"
                output_modality = AUDIO_OUTPUT
                audio_device_idx = 0
                print("Config file has an error!")

        # Set up path
        folder_path = os.path.join(os.path.join("data", "recordings"), pid_num)
        self.system_config.set_folder_path(folder_path)
        self.system_config.set_audio_file_name(os.path.join(folder_path, audio_file))
        self.system_config.set_transcriber(LiveTranscriber(device_index=audio_device_idx))
        self.system_config.set_emotion_classifier(EmotionClassifier(device_index=audio_device_idx))
        self.system_config.set_bg_audio_analysis(device=audio_device_idx)
        self.system_config.set_image_folder(os.path.join(folder_path, image_folder))
        self.log_path = os.path.join(folder_path, "log.csv")

        chat_history_file_name = os.path.join(folder_path, chat_file)
        slim_history_file_name = os.path.join(folder_path, slim_history_file)
        self.system_config.set_GPT(GPT(chat_history_file_name=chat_history_file_name,
                                       slim_history_file_name=slim_history_file_name),
                                   task_name=task_name)

        # Set up output modality
        self.output_mode = output_modality
        self.config_updated = True

        self.backend_system = BackendSystem(self.system_config, self)
        threading.Thread(target=self.backend_system.run).start()

    def start_mouse_key_listener(self):
        self.mouse_listener = MouseListener(on_click=self.on_click)
        self.keyboard_listener = KeyboardListener(
            on_press=self.on_press, on_release=self.on_release)
        self.mouse_listener.start()
        time.sleep(0.1)
        self.keyboard_listener.start()

    def on_press(self, key):
        if not self.config_updated:
            return
        func = None
        try:
            if key == keyboard.Key.up:
                func = self.menu.trigger('up')
            elif key == keyboard.Key.down:
                func = self.menu.trigger('down')
            elif key == keyboard.Key.left:
                func = self.menu.trigger('left')
            elif key == keyboard.Key.right:
                func = self.menu.trigger('right')
        except Exception as e:
            print(e)

        finally:
            self.parse_button_press(func)

    def parse_button_press(self, func):
        if func is None:
            return
        log_manipulation(self.log_path, func)
        # if func == "Hide" or func == "Show":
        #     self.hide_show_content(func)
        if func == "Voice" or func == "Stop":
            self.backend_system.set_user_explicit_input('voice_comment')
        elif func == "Photo" or func == "Retake":
            self.backend_system.set_user_explicit_input('take_photo')
        elif func == "Summary":
            self.backend_system.set_user_explicit_input('full_writing')
        elif func == "Discard":
            self.destroy_picture_window()

    def on_release(self, key):
        if not self.config_updated:
            return
        # Resume Previous conversation
        try:
            if key == Key.esc:
                self.system_config.GPT.resume_stored_history()
        except Exception as e:
            print(e)

    def on_click(self, x, y, button, pressed):
        if not self.config_updated:
            return
        if self.ring_mouse_mode:
            if pressed:
                func = self.menu.trigger('left')
                self.parse_button_press(func)

    def pack_layout(self):
        # set the dimensions of the window to match the screen
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.init_screen_size = f"{screen_width}x{screen_height}+0+0"
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")

        self.root.configure(bg='black')
        self.is_hidden_text = False
        self.manipulation_frame = tk.Frame(self.root, bg='black')
        self.manipulation_frame.place(relx=0.5, rely=0.5, anchor='center')
        self.manipulation_frame.place_configure(relwidth=1.0, relheight=1.0)

        self.text_frame = tk.Frame(self.manipulation_frame, bg='black', background="black", bd=0)
        self.text_frame.place(relx=0.5, rely=0.5, anchor='center')
        self.text_frame.place_configure(relx=0.5, rely=0.5, relwidth=0.8, relheight=0.8)

        # maek the text border black
        self.text_widget = tk.Text(self.text_frame, height=10, width=50, fg='green', bg='black', font=('Arial', 40),
                                   spacing1=10, spacing2=50, wrap="word", highlightbackground='black',
                                   highlightcolor='black')
        self.text_widget.place(relwidth=1.0, relheight=1.0)

        self.last_y = None

        self.notification = tk.Label(self.root,
                                     text="",
                                     fg='green', bg='black', font=('Arial', 20))
        self.notification.place(relx=0.5, rely=0.1, anchor='center')

        self.audio_detector_notification = tk.Label(self.root,
                                                    text="",
                                                    fg='green', bg='black', font=('Arial', 20))
        self.audio_detector_notification.place(relx=0.05, rely=0.1, anchor='w')

        self.emotion_detector_notification = tk.Label(self.root,
                                                      text="",
                                                      fg='green', bg='black', font=('Arial', 20))
        self.emotion_detector_notification.place(relx=0.65, rely=0.1, anchor='w')

        self.vision_detector_notification = tk.Label(self.root,
                                                     text="",
                                                     fg='green', bg='black', font=('Arial', 20))
        self.vision_detector_notification.place(relx=1, rely=0.1, anchor='center')

        self.scrollbar = tk.Scrollbar(self.text_frame, command=self.text_widget.yview, bg='black', troughcolor='black',
                                      activebackground='black', highlightbackground='black', highlightcolor='black',
                                      elementborderwidth=0, width=0)
        self.scrollbar.place(relx=1.2, relheight=1.0, anchor='ne', width=20)
        # self.scrollbar.place_forget()

        self.button_up = get_button(self.manipulation_frame, text='', fg_color="green")
        self.button_down = get_button(self.manipulation_frame, text='', fg_color="green")
        self.button_left = get_button(self.manipulation_frame, text='', fg_color="green")
        self.button_right = get_button(self.manipulation_frame, text='', fg_color="green")

        self.buttons = {'up': self.button_up, 'down': self.button_down, 'left': self.button_left,
                        'right': self.button_right}
        self.buttons_places = {'up': {'relx': 0.5, 'rely': 0.05, 'anchor': 'center'},
                               'left': {'relx': -0.05, 'rely': 0.5, 'anchor': 'center'},
                               'down': {'relx': 0.5, 'rely': 0.95, 'anchor': 'center'},
                               'right': {'relx': 0.95, 'rely': 0.5, 'anchor': 'center'}}

        self.menu = HierarchyMenu(self.root, self.buttons, self.buttons_places)
        self.menu.on_enter_state()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.attributes("-fullscreen", True)
        self.listen_notification_from_backend()
        self.listen_feedback_from_backend()
        self.listen_frame_from_backend()
        # self.root.attributes("-alpha", 0.95)

    def on_close(self):
        self.root.destroy()
        self.keyboard_listener.stop()
        self.mouse_listener.stop()

    def determinate_voice_feedback_process(self):
        voice_feedback_process = self.system_config.voice_feedback_process
        if voice_feedback_process is not None:
            voice_feedback_process.terminate()

    def listen_notification_from_backend(self):
        notification = self.system_config.notification
        if notification is not None:
            self.notification.config(text=notification)
            self.root.update_idletasks()
            self.notification.update()
        else:
            self.notification.config(text="")
            self.root.update_idletasks()
            self.notification.update()
            # self.system_config.notification = None
        self.root.after(200, self.listen_notification_from_backend)

    def listen_feedback_from_backend(self):
        text_feedback_to_show = self.system_config.text_feedback_to_show
        audio_feedback_to_show = self.system_config.audio_feedback_to_show
        if text_feedback_to_show is not None:
            self.render_text_response(text_feedback_to_show)
            # self.system_config.text_feedback_to_show = None
        if audio_feedback_to_show is not None:
            # print("audio text to show: ", self.system_config.text_feedback_to_show)
            self.render_audio_response(audio_feedback_to_show)
            self.system_config.audio_feedback_finished_playing = False
            self.system_config.audio_feedback_to_show = None
            print("start to play the feedback...")

        self.root.after(200, self.listen_feedback_from_backend)

    def hide_show_content(self, mode):
        self.hide_show_picture_window()
        self.hide_show_text(mode)

    def destroy_picture_window(self):
        # Check if the picture window is open and close it if necessary
        if self.picture_window:
            self.picture_window.destroy()
            self.picture_window = None
            self.system_config.picture_window_status = False
            # self.update_vision_analysis()
            return

    def hide_show_text(self, mode):
        if mode == "Hide":
            # self.stored_text_widget_content = self.text_widget.get("1.0", tk.END)
            self.text_widget.delete(1.0, tk.END)
            self.determinate_voice_feedback_process()
            # self.scrollbar.place()
        elif self.stored_text_widget_content is not None:
            self.text_widget.delete(1.0, tk.END)
            self.text_widget.insert(tk.END, self.stored_text_widget_content)
            # self.scrollbar.place_forget()

        self.is_hidden_text = not self.is_hidden_text

    def hide_show_picture_window(self):
        if self.picture_window and not self.picture_window_hidden:
            self.picture_window.withdraw()
            self.system_config.picture_window_status = False
            # self.update_vision_analysis()
            self.picture_window_hidden = True
        elif self.picture_window and self.picture_window_hidden:
            self.picture_window.update_idletasks()
            self.picture_window.deiconify()
            self.system_config.picture_window_status = True
            # self.update_vision_analysis()
            self.picture_window_hidden = False

    def listen_frame_from_backend(self):
        frame = self.system_config.frame_shown_in_picture_window
        if frame is not None:
            self.render_picture(frame)
        else:
            self.root.after(200, self.listen_frame_from_backend)

    def render_picture(self, frame):
        if self.picture_window:
            self.picture_window.destroy()
            self.system_config.picture_window_status = False

        # convert the image from opencv to PIL format
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)

        # Resize the image to 1/4 of its original size
        img = img.resize((int(img.width / 2), int(img.height / 2)))

        img_tk = ImageTk.PhotoImage(img)

        # Create a new window to display the image
        self.picture_window = tk.Toplevel(self.root)
        self.picture_window.wm_attributes("-topmost", True)

        # Over direct the window to remove the border
        # self.picture_window.overrideredirect(True)

        # make the pic window transparent by change its alpha value
        self.picture_window.wm_attributes("-alpha", 0.7)
        self.picture_window.lift()
        self.picture_window.geometry(
            f"{img.width}x{img.height}+{int((self.root.winfo_screenwidth() - img.width) / 2)}+{int((self.root.winfo_screenheight() - img.height) / 2)}")

        # Create a label widget to display the image
        label = tk.Label(self.picture_window, image=img_tk)
        label.image = img_tk
        label.pack()
        self.system_config.picture_window_status = True

        # Check Users' surrounding environment
        print(f"Person count: {self.person_count}")
        if self.person_count > 3:
            self.notification.config(text="Too many people nearby. You may hide the pic and comment it later.")

        self.system_config.frame_shown_in_picture_window = None

        self.root.after(10000, self.clear_frame)

    def clear_frame(self):
        self.destroy_picture_window()
        self.root.after(200, self.listen_frame_from_backend)

    def render_text_response(self, text_response):
        self.text_widget.delete(1.0, tk.END)
        text_response = text_response.strip()
        self.text_widget.insert(tk.END, text_response)
        self.stored_text_widget_content = text_response
        # self.scrollbar.place()
        self.root.update_idletasks()
        self.text_widget.update()

    def render_audio_response(self, audio_response):
        # self.determinate_voice_feedback_process()
        voice_feedback_process = threading.Thread(target=self.play_audio_response, args=(audio_response,))
        # self.system_config.set_voice_feedback_process(voice_feedback_process)
        voice_feedback_process.start()

    def play_audio_response(self, response):
        process = subprocess.Popen(['say', '-v', 'Daniel', '-r', '180', response])
        self.check_subprocess(process)

    def check_subprocess(self, process):
        if process.poll() is None:  # Subprocess is still running
            self.root.after(500, lambda: self.check_subprocess(process))
        else:  # Subprocess has finished
            # Perform actions when subprocess finishes
            self.system_config.audio_feedback_to_show = None
            self.system_config.audio_feedback_finished_playing = True
            print("Audio feedback finished playing")

    # def on_record(self):
    #     self.determinate_voice_feedback_process()
    #     if not self.system_config.is_recording:
    #         with self.audio_lock:
    #             self.system_config.interesting_audio_for_recording = self.system_config.interesting_audio
    #         self.system_config.user_behavior_when_recording = self.system_config.user_behavior
    #         self.notification.config(text="Reminder: Press \"Right\" button again to stop recording!")
    #         # self.record_button.configure(text="Stop")
    #         self.stop_emotion_analysis()
    #         self.start_recording()
    #         self.system_config.is_recording = True
    #     else:
    #         self.stop_recording()
    #
    #         command_type = ""
    #
    #         t = threading.Thread(target=self.thread_new_recording_command, args=(command_type,), daemon=True)
    #         t.start()
    #         self.start_emotion_analysis()
    #         # self.record_button.configure(text="Record")
    #
    # def start_recording(self):
    #     voice_transcriber = self.system_config.get_transcriber()
    #     if voice_transcriber is not None:
    #         voice_transcriber.start()
    #         self.update_transcription()
    #
    # def stop_recording(self):
    #     voice_transcriber = self.system_config.get_transcriber()
    #     if voice_transcriber is not None:
    #         self.system_config.set_final_transcription(voice_transcriber.stop())

    # def update_transcription(self):
    #     voice_transcriber = self.system_config.get_transcriber()
    #     if self.system_config.get_previous_transcription() != voice_transcriber.full_text:
    #         self.render_response(text_response=voice_transcriber.full_text, output_mode=VISUAL_OUTPUT)
    #         self.system_config.set_previous_transcription(voice_transcriber.full_text)
    #     # print(voice_transcriber.silence_duration)
    #     # Help user automatically stop recording if there is no sound for a while
    #     if voice_transcriber.silence_duration > SILENCE_TIME_THRESHOLD_FOR_STOP_RECORDING \
    #             and voice_transcriber.on_processing_count <= 0 and self.system_config.is_recording:
    #         voice_transcriber.silence_duration = 0
    #         func = self.menu.trigger('right')
    #         self.parse_button_press(func)
    #     if not voice_transcriber.stop_event.is_set():
    #         self.root.after(100, self.update_transcription)
    #
    # def start_bg_audio_analysis(self):
    #     self.update_bg_audio_analysis()
    #
    # def start_vision_analysis(self):
    #     self.update_vision_analysis()
    #
    # def start_emotion_analysis(self):
    #     emotion_classifier = self.system_config.emotion_classifier
    #     if emotion_classifier is not None:
    #         emotion_classifier.start()
    #         self.update_emotion_analysis()
    #
    # def stop_emotion_analysis(self):
    #     emotion_classifier = self.system_config.emotion_classifier
    #     if emotion_classifier is not None:
    #         emotion_classifier.stop()
    #
    # def update_emotion_analysis(self):
    #     emotion_classifier = self.system_config.emotion_classifier
    #     # if not enable notification or text_widget is not empty, skip this update
    #     if not self.enable_interest_detection_notification or self.text_widget.get("1.0", "end-1c") != "":
    #         self.root.after(500, self.update_emotion_analysis)
    #         return
    #
    #     emotion_scores = emotion_classifier.scores
    #     if emotion_scores != self.system_config.previous_emotion_scores:
    #         print(f"Emotion scores: {emotion_scores}")
    #         positive_score = emotion_scores['joy'] + emotion_scores['surprise']
    #         if positive_score > 0.5:
    #             self.emotion_detector_notification.config(text=f"Detected your positive tone.\n"
    #                                                            f"Want to record this moment?")
    #             log_manipulation(self.log_path, "positive tone detected")
    #             self.root.after(10000, self.clear_emotion_notification)
    #         self.system_config.previous_emotion_scores = emotion_scores
    #
    #     if not emotion_classifier.stop_event.is_set():
    #         self.root.after(500, self.update_emotion_analysis)
    #
    #
    # def update_bg_audio_analysis(self):
    #     score, category = self.system_config.get_bg_audio_analysis_result()
    #     if category is not None:
    #         if category in self.system_config.get_bg_audio_interesting_categories() and score > 0.5:
    #             last_time = self.system_config.previous_interesting_audio_time.get(category, 0)
    #             if time.time() - last_time > 60:
    #                 self.audio_detector_notification.config(text=f"Detected your surrounding audio: {category}. "
    #                                                              f"Any comments?")
    #                 log_manipulation(self.log_path, "audio notification")
    #                 self.menu.trigger('show_voice_icon')
    #                 with self.audio_lock:
    #                     self.system_config.interesting_audio = category
    #                 self.system_config.previous_interesting_audio_time[category] = time.time()
    #                 self.root.after(10000, self.clear_audio_notification)
    #             else:
    #                 self.clear_audio_notification()
    #         else:
    #             self.clear_audio_notification()
    #     else:
    #         self.clear_audio_notification()


if __name__ == '__main__':
    App()
