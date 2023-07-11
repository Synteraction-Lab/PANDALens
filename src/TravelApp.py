import os
import subprocess
import threading
import time
import tkinter as tk

import customtkinter
import pandas
from PIL import Image
from customtkinter import CTkFrame
from pynput import keyboard
from pynput.keyboard import Key, Listener as KeyboardListener
from pynput.mouse import Listener as MouseListener

from src.BackendSystem import BackendSystem
from src.Data.SystemConfig import SystemConfig
from src.Module.Audio.live_transcriber import LiveTranscriber, show_devices
from src.Module.LLM.GPT import GPT
from src.Storage.writer import log_manipulation, generate_output_file
from src.UI.UI_config import MAIN_GREEN_COLOR
from src.UI.device_panel import DevicePanel
from src.UI.notification_widget import NotificationWidget
from src.UI.widget_generator import get_button
from src.Utilities.constant import audio_file, chat_file, slim_history_file, config_path, image_folder

INTEREST_ICON_SHOW_DURATION = 5

IMAGE_FRAME_SHOW_DURATION = 10


class App:
    def __init__(self, test_mode=False, ring_mouse_mode=False):
        self.notification_window = None
        self.progress_bar = None
        self.notification_widget = None
        self.frame_placed_time = None
        self.interest_icon_placed_time = None
        self.last_text_feedback_to_show = None
        self.last_notification = None
        self.picture_label = None
        self.shown_button = False
        self.shown_content = False
        self.backend_system = None
        self.log_path = None
        self.person_count = 0
        self.picture_window_hidden = False
        self.stored_text_widget_content = None
        self.is_hidden_text = False
        self.previous_vision_frame = None
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

        self.root.bind('<Button-1>', self.on_click)

        self.root.mainloop()

    def update_config(self):
        if not os.path.isfile(config_path):
            pid_num = os.path.join("p1", "01")
            task_name = "travel_blog"
            audio_device_idx = 0
        else:
            try:
                df = pandas.read_csv(config_path)
                pid_num = df[df['item'] == 'pid']['details'].item()
                task_name = df[df['item'] == 'task']['details'].item()
                audio_device_idx = df[df['item'] == 'audio_device']['details'].item()
            except Exception as e:
                pid_num = os.path.join("p1", "01")
                task_name = "travel_blog"
                audio_device_idx = 0
                print("Config file has an error!")

        # Set up path
        folder_path = os.path.join(os.path.join("data", "recordings"), pid_num)
        self.system_config.set_folder_path(folder_path)
        self.system_config.set_audio_file_name(os.path.join(folder_path, audio_file))
        self.system_config.set_transcriber(LiveTranscriber(device_index=audio_device_idx))
        # self.system_config.set_emotion_classifier(EmotionClassifier(device_index=audio_device_idx))
        self.system_config.set_bg_audio_analysis(device=audio_device_idx)
        self.system_config.set_image_folder(os.path.join(folder_path, image_folder))
        self.log_path = os.path.join(folder_path, "log.csv")

        self.chat_history_file_name = os.path.join(folder_path, chat_file)
        slim_history_file_name = os.path.join(folder_path, slim_history_file)
        self.system_config.set_GPT(GPT(chat_history_file_name=self.chat_history_file_name,
                                       slim_history_file_name=slim_history_file_name),
                                   task_name=task_name)

        self.config_updated = True

        self.backend_system = BackendSystem(self.system_config)
        threading.Thread(target=self.backend_system.run).start()

    def start_mouse_key_listener(self):
        # self.mouse_listener = MouseListener(on_click=self.on_click)
        self.keyboard_listener = KeyboardListener(
            on_press=self.on_press, on_release=self.on_release)
        # self.mouse_listener.start()
        time.sleep(0.1)
        self.keyboard_listener.start()

    def on_press(self, key):
        if not self.config_updated:
            return
        func = None
        try:
            current_system_state = self.backend_system.system_status.get_current_state()
            print(current_system_state)
            if key == keyboard.Key.right and current_system_state in ["comments_on_audio",
                                                                      "comments_on_photo",
                                                                      "comments_to_gpt"]:
                func = "Stop Recording"
            elif key == keyboard.Key.up and self.shown_button:
                func = "Select"
            elif key == keyboard.Key.down and self.shown_button:
                func = "Photo"
            elif key == keyboard.Key.right and self.shown_button:
                func = "Voice"
            elif key == keyboard.Key.cmd_r:
                func = "Store"

        except Exception as e:
            print(e)

        finally:
            self.parse_button_press(func)

    def parse_button_press(self, func):
        if func is None:
            return
        log_manipulation(self.log_path, func)
        if func == "Hide" or func == "Show":
            self.hide_show_content()
        if func == "Voice" or func == "Stop":
            self.backend_system.set_user_explicit_input('voice_comment')
        elif func == "Photo" or func == "Retake":
            self.backend_system.set_user_explicit_input('take_photo')
        elif func == "Summary":
            self.backend_system.set_user_explicit_input('full_writing')
        # elif func == "Discard":
        #     self.destroy_picture_window()
        elif func == "Stop Recording":
            self.backend_system.set_user_explicit_input('stop_recording')
        elif func == "Select":
            self.backend_system.set_user_explicit_input('select')
        elif func == "Terminate Waiting for User Response":
            self.backend_system.set_user_explicit_input('terminate_waiting_for_user_response')
            self.hide_text()
            self.hide_button()
        elif func == "Store":
            self.create_output_file()

    def on_release(self, key):
        if not self.config_updated:
            return
        # Resume Previous conversation
        try:
            if key == Key.esc:
                self.system_config.GPT.resume_stored_history()
        except Exception as e:
            print(e)

    def on_click(self, *args, **kwargs):
        if not self.config_updated:
            return
        if self.ring_mouse_mode:
            # if pressed:
            current_system_state = self.backend_system.system_status.get_current_state()
            is_audio_finished = self.system_config.detect_audio_feedback_finished()
            if current_system_state in ['photo_comments_pending', 'manual_photo_comments_pending',
                                        'show_gpt_response', 'audio_comments_pending'] and is_audio_finished:
                func = "Terminate Waiting for User Response"
            else:
                func = "Hide"
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

        # maek the text border black
        self.text_widget = customtkinter.CTkTextbox(self.manipulation_frame, height=10, width=50,
                                                    text_color=MAIN_GREEN_COLOR, font=('Arial', 36),
                                                    bg_color='systemTransparent',
                                                    spacing1=10, spacing2=50, wrap="word",
                                                    border_color="#42AF74", border_width=2)

        self.last_y = None

        self.button_up = get_button(self.manipulation_frame, text='Generate\nWriting', fg_color='black', border_width=3,
                                    text_color=MAIN_GREEN_COLOR, font_size=14)
        self.button_down = get_button(self.manipulation_frame, text='Photo', fg_color='black', border_width=3,
                                      text_color=MAIN_GREEN_COLOR, font_size=14)

        self.button_right = get_button(self.manipulation_frame, text='Voice', fg_color='black', border_width=3,
                                       text_color=MAIN_GREEN_COLOR, font_size=14)

        self.asset_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "UI", "assets")

        self.voice_icon_image = customtkinter.CTkImage(Image.open(os.path.join(self.asset_path, "voice_icon.png")),
                                                       size=(30, 30))
        self.button_right.configure(image=self.voice_icon_image, compound="top")

        self.summary_icon_image = customtkinter.CTkImage(Image.open(os.path.join(self.asset_path, "summary_icon.png")),
                                                         size=(30, 30))
        self.button_up.configure(image=self.summary_icon_image, compound="top")

        self.photo_icon_image = customtkinter.CTkImage(Image.open(os.path.join(self.asset_path, "photo_icon.png")),
                                                       size=(30, 30))
        self.button_down.configure(image=self.photo_icon_image, compound="top")

        self.buttons = {'up': self.button_up, 'down': self.button_down, 'right': self.button_right}
        self.buttons_places = {'up': {'relx': 0.5, 'rely': 0.1, 'anchor': 'center'},
                               'down': {'relx': 0.5, 'rely': 0.9, 'anchor': 'center'},
                               'right': {'relx': 0.9, 'rely': 0.5, 'anchor': 'center'}}

        self.shown_button = False

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.attributes("-fullscreen", True)
        self.update_ui_based_on_timer()

    def on_close(self):
        self.root.destroy()
        self.keyboard_listener.stop()
        self.mouse_listener.stop()

    def determinate_voice_feedback_process(self):
        voice_feedback_process = self.system_config.voice_feedback_process
        if voice_feedback_process is not None:
            voice_feedback_process.terminate()

    def update_ui_based_on_timer(self):
        # get UI update info from backend
        self.listen_notification_from_backend()
        self.listen_gpt_feedback_from_backend()
        # self.listen_show_interest_icon_from_backend()
        self.listen_progress_bar_from_backend()

        # remove UI elements
        now = time.time()

        # if self.interest_icon_placed_time is not None:
        #     if now - self.interest_icon_placed_time > INTEREST_ICON_SHOW_DURATION:
        #         self.remove_interest_icon()
        #         self.interest_icon_placed_time = None

        # run this function again after 0.3 seconds
        self.root.after(300, self.update_ui_based_on_timer)

    def listen_progress_bar_from_backend(self):
        progress_bar_percentage = self.system_config.progress_bar_percentage
        if progress_bar_percentage is not None:
            if progress_bar_percentage > 0:
                # set the transparency of the notification widget
                if self.notification_window is not None:
                    self.notification_window.attributes("-alpha", progress_bar_percentage)
            else:
                self.remove_notification()

    def listen_notification_from_backend(self):
        notification = self.system_config.notification
        # Update the notification if not the same as the previous one
        if notification != self.last_notification:
            if self.last_notification is not None:
                # Remove previous notification if it's not the same as the current one or the current one is set to None
                if notification is None or notification["notif_type"] != self.last_notification["notif_type"]:
                    self.remove_notification()

            if notification is not None:
                print("Notification Type: ", notification["notif_type"], self.notification_widget)
                if self.last_notification is None:
                    self.hide_button()
                if self.notification_widget is None:
                    self.show_notification_widget(notification)

                if notification["notif_type"] == "text":
                    # print("Notification: ", notification["content"])
                    self.notification_widget.configure(text=notification["content"])
                elif notification["notif_type"] == "picture":
                    self.notification_widget.configure(image=notification["content"])

            self.last_notification = notification

    def show_notification_widget(self, notification):
        # Due to the limitation of tkinter, we can only set the transparency of the whole window, thus,
        # we create a new window to show the notification widget
        if self.notification_window:
            self.notification_window.destroy()

        self.notification_window = tk.Toplevel(self.root)
        self.notification_window.overrideredirect(True)
        self.notification_window.overrideredirect(False)
        self.notification_window.attributes("-topmost", True)
        # self.notification_window.configure(background="black")

        self.notification_window.wm_attributes("-transparent", True)
        # Set the root window background color to a transparent color
        self.notification_window.config(bg='systemTransparent')

        # Set location for the notification window
        if notification["position"] == "top-center":
            relx, rely = 0.5, 0.1
        elif notification["position"] == "top_right":
            relx, rely = 0.8, 0.1
        elif notification["position"] == "middle-right":
            relx, rely = 0.8, 0.5
        elif notification["position"] == "in-box-bottom-right":
            relx, rely = 0.8, 0.72
        else:
            relx, rely = 0.5, 0.85

        # Pack the notification widget based on the notif_type of the notification
        self.notification_widget = NotificationWidget(self.notification_window, notification["notif_type"])

        # Set the size and location of the notification window
        widget_width = 400
        widget_height = 300

        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()

        pos_x = int(root_width * relx - widget_width / 2)
        pos_y = int(root_height * rely - widget_height / 2)

        # Set the size and location of the notification window
        self.notification_window.geometry(f"{widget_width}x{widget_height}+{pos_x}+{pos_y}")

    def remove_notification(self):
        if self.notification_widget is not None:
            self.notification_widget.destroy()
            self.notification_widget = None
        if self.notification_window is not None:
            self.notification_window.destroy()
            self.notification_window = None

    # def listen_show_interest_icon_from_backend(self):
    #     if self.system_config.show_interest_icon:
    #         self.show_interest_icon()
    #         self.system_config.show_interest_icon = False

    # def show_interest_icon(self):
    #     self.interest_icon = customtkinter.CTkImage(Image.open(os.path.join(self.asset_path, "light_icon.png")),
    #                                                 size=(20, 20))
    #     self.interest_icon_label = customtkinter.CTkLabel(self.root, text="", image=self.interest_icon)
    #     self.interest_icon_label.place(relx=0.85, rely=0.05, anchor='center')
    #     self.interest_icon_placed_time = time.time()

    # def remove_interest_icon(self):
    #     self.interest_icon_label.destroy()

    def listen_gpt_feedback_from_backend(self):
        text_feedback_to_show = self.system_config.text_feedback_to_show
        audio_feedback_to_show = self.system_config.audio_feedback_to_show
        if text_feedback_to_show is not None and text_feedback_to_show != self.last_text_feedback_to_show:
            self.last_text_feedback_to_show = text_feedback_to_show
            self.render_text_response(text_feedback_to_show)
            # self.system_config.text_feedback_to_show = None
        if audio_feedback_to_show is not None:
            # print("audio text to show: ", self.system_config.text_feedback_to_show)
            self.system_config.audio_feedback_finished_playing = False
            self.render_audio_response(audio_feedback_to_show)
            self.system_config.audio_feedback_to_show = None

    def hide_show_buttons(self):
        if self.shown_button:
            self.hide_button()
        else:
            self.show_button()

        self.manipulation_frame.update_idletasks()
        self.manipulation_frame.update()
        self.root.update_idletasks()
        # self.root.update()

    def hide_button(self):
        for direction, button in self.buttons.items():
            button.place_forget()
            self.root.update_idletasks()
        self.shown_button = False
        # self.root.update()

    def show_button(self):
        for direction, button in self.buttons.items():
            button.place(**self.buttons_places[direction])  # Place the button
        self.shown_button = True

    def hide_show_content(self):
        if self.shown_button:
            self.hide_text()
            self.hide_button()
        else:
            self.show_text()
            self.show_button()
        self.root.update_idletasks()

    def hide_show_text(self):
        if not self.is_hidden_text:
            self.hide_text()
        elif self.is_hidden_text:
            self.show_text()

    def hide_text(self):
        if self.text_widget is not None:
            self.stored_text_widget_content = self.text_widget.get("1.0", tk.END)
            if self.stored_text_widget_content.strip() == "":
                self.stored_text_widget_content = None
            self.text_widget.place_forget()
            self.is_hidden_text = True

    def show_text(self):
        if self.stored_text_widget_content is not None:
            print(self.stored_text_widget_content)
            self.text_widget.place(relx=0.5, rely=0.5, anchor='center')
            self.text_widget.place_configure(relheight=0.55, relwidth=0.65)
            self.is_hidden_text = False

    def render_text_response(self, text_response):
        if text_response == "":
            self.hide_text()
            return
        else:
            self.text_widget.delete(1.0, tk.END)
            self.text_widget.insert(tk.END, text_response)
            self.text_widget.place(relx=0.5, rely=0.5, anchor='center')
            self.text_widget.place_configure(relheight=0.55, relwidth=0.65)
            self.stored_text_widget_content = text_response
            self.root.update_idletasks()
            self.text_widget.update()

    def render_audio_response(self, audio_response):
        self.play_audio_response(audio_response)

    def play_audio_response(self, response):
        process = subprocess.Popen(['say', '-v', 'Daniel', '-r', '180', response])
        self.check_subprocess(process)

    def check_subprocess(self, process):
        if process.poll() is None:  # Subprocess is still running
            self.root.after(400, lambda: self.check_subprocess(process))
        else:
            # Perform actions when subprocess finishes
            self.system_config.audio_feedback_to_show = None
            self.system_config.audio_feedback_finished_playing = True
            print("Audio feedback finished playing")

    def create_output_file(self):
        dialog = customtkinter.CTkInputDialog(text="Enter the title:", title="UbiWriter")
        title=dialog.get_input()
        generate_output_file(chat_history_path=self.chat_history_file_name,
                             image_path=self.system_config.image_folder,
                             title=title)

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


if __name__ == '__main__':
    App()
