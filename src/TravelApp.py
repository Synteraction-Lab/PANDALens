import os
import subprocess
import threading
import time
import tkinter as tk

import customtkinter
import numpy as np
import pandas
from PIL import Image
from customtkinter import CTkLabel
from pynput import keyboard
from pynput.keyboard import Key, Listener as KeyboardListener

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
import numpy as np

PERSON_COUNT_THRESHOLD_FOR_AUDIO_ON = 5

SHOW_GAZE_MOVEMENT = False


class App:
    def __init__(self, test_mode=False, ring_mouse_mode=False):
        self.enable_to_retake_photo = False
        self.notification_to_be_removed_with_delay = None
        self.last_click_time = None
        self.warning_notification = None
        self.auto_scroll_id = None
        self.temporal_audio_response = None
        self.audio_process = None
        self.notification_window = None
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
        self.is_muted = False

        show_devices()

        # Open Setup panel
        DevicePanel(self.root, parent_object_save_command=self.update_config)

        # Pack and run the main UI
        self.pack_layout()

        self.root.bind('<Button-1>', self.on_click)

        # Remote reset system by admin
        self.root.bind('<Next>', self.experimenter_click)

        self.root.mainloop()

    def update_config(self):
        if not os.path.isfile(config_path):
            pid_num = os.path.join("p1", "01")
            task_name = "travel_blog"
            audio_device_idx = 0
            naive = "UbiWriter"
            gaze_record = False
        else:
            try:
                df = pandas.read_csv(config_path)
                pid_num = df[df['item'] == 'pid']['details'].item()
                task_name = df[df['item'] == 'task']['details'].item()
                audio_device_idx = df[df['item'] == 'audio_device']['details'].item()
                naive = df[df['item'] == 'naive']['details'].item()
                gaze_record = df[df['item'] == 'gaze_recording']['details'].item() == "True"
            except Exception as e:
                print("Config file has an error!", e)
                pid_num = os.path.join("p1", "01")
                task_name = "travel_blog"
                audio_device_idx = 0
                naive = "UbiWriter"
                gaze_record = False

        # Set up path
        folder_path = os.path.join(os.path.join("data", "recordings"), pid_num)
        self.system_config.set_folder_path(folder_path)
        self.system_config.set_audio_file_name(os.path.join(folder_path, audio_file))
        self.system_config.set_transcriber(LiveTranscriber(device_index=audio_device_idx))

        self.system_config.set_naive(naive)

        self.system_config.set_vision_analysis(record=gaze_record)
        self.system_config.set_bg_audio_analysis(device=audio_device_idx)
        self.system_config.set_image_folder(os.path.join(folder_path, image_folder))
        self.log_path = os.path.join(folder_path, "log.csv")
        self.system_config.set_log_path(self.log_path)

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
            print("Current system state: ", current_system_state)
            if key == keyboard.Key.right and current_system_state in ["comments_on_audio",
                                                                      "comments_on_photo",
                                                                      "comments_to_gpt"]:
                func = "Stop Recording"
            elif key == keyboard.Key.up and self.mute_button.winfo_ismapped():
                func = "Mute/Unmute"
            elif key == keyboard.Key.down and self.text_visibility_button.winfo_ismapped():
                func = "Hide/Show Text"
            elif key == keyboard.Key.up and self.shown_button and current_system_state == "init":
                func = "Select"
            elif key == keyboard.Key.down and self.enable_to_retake_photo:
                func = "Retake"
                self.enable_to_retake_photo = False
            elif key == keyboard.Key.down and (self.shown_button or (
                        self.notification_widget is None and current_system_state not in ['comments_on_photo',
                                                                                          'comments_to_gpt',
                                                                                          'full_writing_pending',
                                                                                          'comments_on_audio',
                                                                                          'select_moments'])):
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
            self.hide_show_buttons()
            self.hide_text()
            self.mute_audio()
        elif func == "Show Photo Button":
            self.switch_photo_button()
        elif func == "Voice" or func == "Stop":
            self.backend_system.set_user_explicit_input('voice_comment')
            self.mute_audio()
            # self.hide_text()
            self.hide_button()
        elif func == "Cancel Recording":
            self.backend_system.set_user_explicit_input('cancel_recording')
        elif func == "Photo":
            # if self.notification_widget is not None:
            if self.backend_system.system_status.get_current_state() in ['comments_on_photo', 'comments_to_gpt',
                                                                         'full_writing_pending',
                                                                         'comments_on_audio', 'select_moments']:
                self.backend_system.add_photo_to_pending_task_list()
                self.hide_button()
                return
            self.backend_system.set_user_explicit_input('take_photo')
            self.hide_text()
        elif func == "Retake":
            self.backend_system.set_user_explicit_input('retake_photo')
        elif func == "Summary":
            self.backend_system.set_user_explicit_input('full_writing')
        # elif func == "Discard":
        #     self.destroy_picture_window()
        elif func == "Stop Recording":
            self.backend_system.set_user_explicit_input('stop_recording')
        elif func == "Select":
            self.backend_system.set_user_explicit_input('select')
            self.hide_text()
        elif func == "Terminate Waiting for User Response":
            self.backend_system.set_user_explicit_input('terminate_waiting_for_user_response')
            self.hide_text()
            self.hide_button()
        elif func == "Store":
            self.create_output_file()
        elif func == "Mute/Unmute":
            if self.is_muted:
                self.system_config.audio_feedback_finished_playing = False
                self.play_audio_response(self.temporal_audio_response)
                self.temporal_audio_response = None
            else:
                self.mute_audio()
            self.switch_mute_button()
        elif func == "Hide/Show Text":
            self.switch_text_visibility_button()
        elif func == "Hide Text Box":
            self.backend_system.set_user_explicit_input('hide_text_box')
        elif func == "Finish Photo Pending Status":
            self.backend_system.set_user_explicit_input('finish_photo_pending_status')

    def on_release(self, key):
        if not self.config_updated:
            return
        # Resume Previous conversation
        try:
            if key == Key.esc:
                self.system_config.GPT.resume_stored_history()
        except Exception as e:
            print(e)

    def experimenter_click(self, event):
        log_manipulation(self.log_path, "Experimenter Clicked")
        self.on_click()

    def on_click(self, *args, **kwargs):
        if not self.config_updated:
            return
        if self.ring_mouse_mode:
            # prevent double click
            if self.last_click_time is not None and time.time() - self.last_click_time < 0.2:
                self.show_warning_notification("Please don't click frequently.")
                return
            self.last_click_time = time.time()
            func = None
            print("Mouse clicked")
            current_system_state = self.backend_system.system_status.get_current_state()
            if current_system_state == "photo_pending":
                func = "Finish Photo Pending Status"
            if current_system_state in ['photo_comments_pending', 'manual_photo_comments_pending',
                                        'audio_comments_pending'] \
                    or (current_system_state == 'show_gpt_response' and
                        self.system_config.gpt_response_type == "authoring"):
                func = "Terminate Waiting for User Response"
                if not self.system_config.detect_audio_feedback_finished():
                    self.mute_audio()
            elif self.notification_widget is None and current_system_state not in ['comments_on_photo',
                                                                                   'comments_to_gpt',
                                                                                   'full_writing_pending',
                                                                                   'comments_on_audio',
                                                                                   'select_moments']:
                func = "Hide"
            elif current_system_state in ['comments_on_photo', 'comments_to_gpt', 'full_writing_pending',
                                          'comments_on_audio', 'select_moments'] and self.last_notification is None:
                func = "Show Photo Button"
            elif current_system_state in ['comments_on_photo', 'comments_to_gpt', 'full_writing_pending',
                                          'comments_on_audio', 'select_moments'] and self.last_notification["notif_type"] == "processing_icon":
                func = "Show Photo Button"
            elif current_system_state in ["comments_on_audio", "comments_on_photo", "comments_to_gpt"]:
                func = "Cancel Recording"
            elif self.last_text_feedback_to_show:
                func = "Show Voice Button"
            elif self.text_widget.winfo_ismapped():
                func = "Hide Text Box"
            # else:
            #     self.show_warning_notification("Please click the button later.")
            self.parse_button_press(func)

    def show_warning_notification(self, message):
        if self.warning_notification is None:
            self.warning_notification = CTkLabel(self.root, text=message, fg_color="#42AF74",
                                                 font=("Robot", 20))
        else:
            self.warning_notification.configure(text=message)
        self.warning_notification.place(relx=0.9, rely=0.1, anchor='center')

        # remove warning notification after 1 seconds
        self.root.after(1000, self.remove_warning_notification)

    def remove_warning_notification(self):
        if self.warning_notification is not None:
            self.warning_notification.place_forget()
            self.root.update_idletasks()

    def pack_layout(self):
        # set the dimensions of the window to match the screen
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.init_screen_size = f"{screen_width}x{screen_height}+0+0"
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")

        self.root.configure(bg='black')
        self.is_hidden_text = True
        self.manipulation_frame = tk.Frame(self.root, bg='black')
        self.manipulation_frame.place(relx=0.5, rely=0.5, anchor='center')
        self.manipulation_frame.place_configure(relwidth=1.0, relheight=1.0)

        # make the text border black
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

        self.mute_button = get_button(self.manipulation_frame, text="Mute", fg_color='black', border_width=3,
                                      text_color=MAIN_GREEN_COLOR, font_size=14)

        self.text_visibility_button = get_button(self.manipulation_frame, text="Hide\nText", fg_color='black',
                                                 border_width=3,
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

        if SHOW_GAZE_MOVEMENT:
            self.canvas = tk.Canvas(self.root, width=10, height=10, bg='black', bd=0, highlightthickness=0)
            self.circle = self.canvas.create_oval(0, 0, 10, 10, fill='yellow')
            self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.attributes("-fullscreen", True)
        self.update_ui_based_on_timer()

    def on_close(self):
        self.root.destroy()
        self.keyboard_listener.stop()

    def determinate_voice_feedback_process(self):
        voice_feedback_process = self.system_config.voice_feedback_process
        if voice_feedback_process is not None:
            voice_feedback_process.terminate()

    def update_ui_based_on_timer(self):
        # get UI update info from backend
        self.listen_notification_from_backend()
        self.listen_gpt_feedback_from_backend()
        self.listen_progress_bar_from_backend()
        # if SHOW_GAZE_MOVEMENT:
        #     self.listen_gaze_pos_from_backend()
        self.root.after(100, self.update_ui_based_on_timer)

    def listen_gaze_pos_from_backend(self):
        gaze_pos = self.system_config.gaze_pos
        if gaze_pos is None:
            return
        if gaze_pos is not None:
            # Update canvas position
            if 0 < gaze_pos[0] < 1 and 0 < gaze_pos[1] < 1:
                self.canvas.place(relx=gaze_pos[0], rely=gaze_pos[1], anchor=tk.CENTER)

    def listen_progress_bar_from_backend(self):
        progress_bar_percentage = self.system_config.progress_bar_percentage
        if progress_bar_percentage is not None:
            if progress_bar_percentage > 0:
                # set the transparency of the notification widget
                if self.notification_window is not None:
                    self.notification_window.attributes("-alpha", progress_bar_percentage)
            else:
                self.hide_button()
                self.remove_notification()
                self.system_config.progress_bar_percentage = None

    def are_equal(self, n1, n2):
        # If both are None
        if n1 is None and n2 is None:
            return True
        # If only one is None
        if n1 is None or n2 is None:
            return False
        # Now we know they're both not None, so we can safely access their keys
        # If the keys do not match
        if set(n1.keys()) != set(n2.keys()):
            return False
        # Compare values for each key
        for key in n1:
            v1 = n1[key]
            v2 = n2[key]
            # If they're both arrays
            if isinstance(v1, np.ndarray) and isinstance(v2, np.ndarray):
                # If their shapes are not equal or any pair of elements are not equal
                if v1.shape != v2.shape or not np.all(v1 == v2):
                    return False
            # If they're not both arrays but they're not equal
            elif v1 != v2:
                return False
        # If no mismatches were found, they're equal
        return True

    def listen_notification_from_backend(self):
        with self.system_config.notification_lock:
            notification = self.system_config.notification
            # Update the notification if not the same as the previous one
        if not self.are_equal(notification, self.last_notification):
            if self.last_notification is not None:
                # Remove previous notification if it's not the same as the current one or the current one is set to None
                if notification is None:
                    self.remove_notification()
                elif notification["notif_type"] != self.last_notification["notif_type"]:
                    self.remove_notification()
                    if notification["notif_type"] == "listening_icon" and \
                            self.last_notification["notif_type"] == "picture":
                        notification = self.system_config.notification = {
                            "notif_type": "listening_picture_comments",
                            "content": self.last_notification["content"],
                            "position": self.last_notification["position"]
                        }

            if notification is not None:
                self.enable_to_retake_photo = False
                self.hide_button()
                if self.notification_widget is None:
                    self.show_notification_widget(notification)

                if notification["notif_type"] == "text":
                    # print("Notification: ", notification["content"])
                    self.notification_widget.configure(text=notification["content"])
                elif (notification["notif_type"] == "picture"
                      or notification["notif_type"] == "listening_picture_comments"
                      or notification["notif_type"] == "picture_thumbnail") \
                        and notification["content"] is not None:
                    self.notification_widget.configure(image=notification["content"])
                    # enable to retake photo when showing the picture to users
                    if notification["notif_type"] == "picture":
                        self.switch_photo_button()
                        self.enable_to_retake_photo = True
                elif notification["notif_type"] == "audio_icon":
                    self.notification_widget.configure(label=notification["label"])
                elif notification["notif_type"] == "like_object_icon":
                    self.notification_widget.configure(label=notification["label"])

            self.last_notification = notification

    def show_notification_widget(self, notification):
        # Due to the limitation of tkinter, we can only set the transparency of the whole window, thus,
        # we create a new window to show the notification widget
        if self.notification_window:
            self.notification_window.destroy()

        self.system_config.progress_bar_percentage = 1

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
        elif notification["position"] == "top-right":
            relx, rely = 0.8, 0.1
        elif notification["position"] == "middle-right":
            relx, rely = 0.8, 0.5
        elif notification["position"] == "in-box-bottom-right":
            relx, rely = 0.8, 0.72
        else:
            relx, rely = 0.5, 0.85

        # Pack the notification widget based on the notif_type of the notification
        self.notification_widget = NotificationWidget(self.notification_window, notification["notif_type"])
        if "duration" in notification.keys():
            self.notification_to_be_removed_with_delay = notification
            self.root.after(int(notification["duration"] * 1000), self.remove_notification_with_delay)

        # Set the size and location of the notification window
        widget_width = 350
        widget_height = 350

        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()

        pos_x = int(root_width * relx - widget_width / 2)
        pos_y = int(root_height * rely - widget_height / 2)

        # Set the size and location of the notification window
        self.notification_window.geometry(f"{widget_width}x{widget_height}+{pos_x}+{pos_y}")

    def remove_notification(self):
        if self.notification_widget is not None:
            if self.system_config.notification != self.last_notification:
                self.notification_widget.destroy()
                self.notification_widget = None
        if self.notification_window is not None:
            if self.system_config.notification != self.last_notification:
                self.notification_window.destroy()
                self.notification_window = None

        self.hide_mute_button()
        self.hide_text_visibility_button()

    def remove_notification_with_delay(self):
        if self.notification_to_be_removed_with_delay == self.system_config.notification:
            self.system_config.notification = None
            self.remove_notification()
            self.notification_to_be_removed_with_delay = None

    def listen_gpt_feedback_from_backend(self):
        text_feedback_to_show = self.system_config.text_feedback_to_show
        audio_feedback_to_show = self.system_config.audio_feedback_to_show
        if text_feedback_to_show is not None and text_feedback_to_show != self.last_text_feedback_to_show:
            self.last_text_feedback_to_show = text_feedback_to_show
            self.render_text_response(text_feedback_to_show)
        if audio_feedback_to_show is not None:
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

    def hide_button(self):
        print("hide button")
        for direction, button in self.buttons.items():
            button.place_forget()
        self.root.update_idletasks()
        self.hide_mute_button()
        self.hide_text_visibility_button()
        self.shown_button = False

    def show_button(self):
        for direction, button in self.buttons.items():
            button.place(**self.buttons_places[direction])  # Place the button
        self.shown_button = True

    def switch_photo_button(self):
        if self.shown_button:
            self.hide_button()
        else:
            self.buttons["down"].place(**self.buttons_places["down"])
            self.shown_button = True

    def show_voice_button(self):
        self.buttons["right"].place(**self.buttons_places["right"])
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
            self.is_hidden_text = False
            self.show_text_visibility_button()
            self.show_voice_button()
            self.root.update_idletasks()
            self.system_config.text_feedback_to_show = None
            self.text_widget.update()

            # Cancel the old auto scroll if it exists
            if self.auto_scroll_id is not None:
                self.root.after_cancel(self.auto_scroll_id)

            # Schedule a new auto scroll and store its ID
            self.auto_scroll_id = self.root.after(6000, self.auto_scroll_text)

    def auto_scroll_text(self):
        if self.text_widget is not None:
            if self.text_widget.winfo_ismapped():
                self.text_widget.yview_scroll(1, "units")

                # Cancel the old auto scroll if it exists
                if self.auto_scroll_id is not None:
                    self.root.after_cancel(self.auto_scroll_id)

                # Schedule a new auto scroll and store its ID
                self.auto_scroll_id = self.root.after(3500, self.auto_scroll_text)

    def render_audio_response(self, audio_response):
        # Switch the audio feedback on if many people are shown in the FPV
        if self.system_config.vision_detector.get_person_count() > PERSON_COUNT_THRESHOLD_FOR_AUDIO_ON:
            self.is_muted = True

        self.show_mute_button()
        if self.is_muted:
            self.temporal_audio_response = audio_response
            self.system_config.audio_feedback_finished_playing = True
        else:
            self.play_audio_response(audio_response)

    def play_audio_response(self, response):
        if response is None:
            return
        self.audio_process = subprocess.Popen(['say', '-v', 'Daniel', '-r', '180', response])
        self.check_subprocess()

    def check_subprocess(self):
        if self.audio_process.poll() is None:  # Subprocess is still running
            self.root.after(3500, self.check_subprocess)
            self.root.update_idletasks()
        else:
            # Perform actions when subprocess finishes
            self.system_config.audio_feedback_to_show = None
            self.system_config.audio_feedback_finished_playing = True
            if self.system_config.gpt_response_type == "authoring":
                self.hide_mute_button()
                self.hide_text_visibility_button()
                print("Audio feedback finished playing")

    def create_output_file(self):
        dialog = customtkinter.CTkInputDialog(text="Enter the title:", title="UbiWriter")
        title = dialog.get_input()
        generate_output_file(chat_history_path=self.chat_history_file_name,
                             image_path=self.system_config.image_folder,
                             title=title)

    def show_mute_button(self):
        if self.mute_button is not None:
            if self.is_muted:
                self.mute_button.configure(text="Unmute")
            else:
                self.mute_button.configure(text="Mute")
            self.mute_button.place(relx=0.5, rely=0.1, anchor='center')
            self.root.update_idletasks()

    def switch_mute_button(self):
        if self.mute_button is not None:
            if self.is_muted:
                self.mute_button.configure(text="Mute")
                self.is_muted = False
            else:
                self.mute_button.configure(text="Unmute")
                self.is_muted = True

    def hide_mute_button(self):
        if self.mute_button is not None:
            self.mute_button.place_forget()
            self.root.update_idletasks()

    def show_text_visibility_button(self):
        if self.text_visibility_button is not None:
            self.text_visibility_button.place(relx=0.5, rely=0.9, anchor='center')
            self.root.update_idletasks()

    def switch_text_visibility_button(self):
        if not self.is_hidden_text:
            self.text_visibility_button.configure(text="Show\nText")
            self.hide_text()
        elif self.is_hidden_text:
            self.text_visibility_button.configure(text="Hide\nText")
            self.show_text()

    def hide_text_visibility_button(self):
        if self.text_visibility_button is not None:
            self.text_visibility_button.place_forget()
            self.root.update_idletasks()

    def mute_audio(self):
        if self.audio_process is not None:
            self.audio_process.terminate()

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
