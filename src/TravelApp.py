import os
import subprocess
import threading
import time
import tkinter as tk

import customtkinter
import cv2
import pandas
from PIL import Image, ImageTk, ImageDraw
from customtkinter import CTkProgressBar
from pynput import keyboard
from pynput.keyboard import Key, Listener as KeyboardListener
from pynput.mouse import Listener as MouseListener

from src.BackendSystem import BackendSystem
from src.Data.SystemConfig import SystemConfig
from src.Module.Audio.live_transcriber import LiveTranscriber, show_devices
from src.Module.LLM.GPT import GPT
from src.Storage.writer import log_manipulation
from src.UI.UI_config import MAIN_GREEN_COLOR
from src.UI.device_panel import DevicePanel
from src.UI.widget_generator import get_button
from src.Utilities.constant import audio_file, chat_file, slim_history_file, config_path, image_folder

INTEREST_ICON_SHOW_DURATION = 5

IMAGE_FRAME_SHOW_DURATION = 10


class App:
    def __init__(self, test_mode=False, ring_mouse_mode=False):
        self.progress_bar = None
        self.notification_widget = None
        self.frame_placed_time = None
        self.interest_icon_placed_time = None
        self.last_text_feedback_to_show = None
        self.last_notification = None
        self.picture_label = None
        self.shown_button = False
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

        chat_history_file_name = os.path.join(folder_path, chat_file)
        slim_history_file_name = os.path.join(folder_path, slim_history_file)
        self.system_config.set_GPT(GPT(chat_history_file_name=chat_history_file_name,
                                       slim_history_file_name=slim_history_file_name),
                                   task_name=task_name)

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
            current_system_state = self.backend_system.system_status.get_current_state()
            print(current_system_state)
            if key == keyboard.Key.right and current_system_state in ["comments_on_audio",
                                                                      "comments_on_photo",
                                                                      "comments_to_gpt"]:
                func = "Stop Recording"
            elif key == keyboard.Key.up and self.shown_button:
                func = "Summary"
            elif key == keyboard.Key.down and self.shown_button:
                func = "Photo"
            elif key == keyboard.Key.left and self.shown_button:
                func = "Select"
            elif key == keyboard.Key.right and self.shown_button:
                func = "Voice"
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
        elif func == "Discard":
            self.destroy_picture_window()
        elif func == "Stop Recording":
            self.backend_system.set_user_explicit_input('stop_recording')
        elif func == "Select":
            self.backend_system.set_user_explicit_input('select')

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
        self.text_widget = customtkinter.CTkTextbox(self.manipulation_frame, height=10, width=50, bg_color="#000000",
                                                    text_color=MAIN_GREEN_COLOR, font=('Arial', 36),
                                                    spacing1=10, spacing2=50, wrap="word")

        self.last_y = None

        # self.notification_widget = customtkinter.CTkLabel(self.root, text="", font=('Arial', 20), text_color=MAIN_GREEN_COLOR)

        self.button_up = get_button(self.manipulation_frame, text='Summary', fg_color='black', border_width=3,
                                    text_color=MAIN_GREEN_COLOR, font_size=10)
        self.button_down = get_button(self.manipulation_frame, text='Photo', fg_color='black', border_width=3,
                                      text_color=MAIN_GREEN_COLOR, font_size=14)
        # self.button_left = get_button(self.manipulation_frame, text='Hide')

        self.button_left = get_button(self.manipulation_frame, text='Select', fg_color='black', border_width=3,
                                    text_color=MAIN_GREEN_COLOR, font_size=14)

        self.button_right = get_button(self.manipulation_frame, text='Voice', fg_color='black', border_width=3,
                                       text_color=MAIN_GREEN_COLOR, font_size=14)

        self.asset_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "UI", "assets")

        # set a image as a button
        self.voice_icon_image = customtkinter.CTkImage(Image.open(os.path.join(self.asset_path, "voice_icon.png")),
                                                       size=(30, 30))
        self.button_right.configure(image=self.voice_icon_image, compound="top")

        self.summary_icon_image = customtkinter.CTkImage(Image.open(os.path.join(self.asset_path, "summary_icon.png")),
                                                         size=(30, 30))
        self.button_up.configure(image=self.summary_icon_image, compound="top")
        self.button_left.configure(image=self.summary_icon_image, compound="top")

        self.photo_icon_image = customtkinter.CTkImage(Image.open(os.path.join(self.asset_path, "photo_icon.png")),
                                                       size=(30, 30))
        self.button_down.configure(image=self.photo_icon_image, compound="top")

        self.notification_box = customtkinter.CTkImage(
            Image.open(os.path.join(self.asset_path, "notification_box.png")),
            size=(630, 90))
        # self.notification_widget.configure(image=self.notification_box, compound="center")

        self.buttons = {'up': self.button_up, 'down': self.button_down, 'left': self.button_left,
                        'right': self.button_right}
        self.buttons_places = {'up': {'relx': 0.5, 'rely': 0.1, 'anchor': 'center'},
                               'left': {'relx': 0.1, 'rely': 0.5, 'anchor': 'center'},
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
        # get ui update info from backend
        self.listen_notification_from_backend()
        self.listen_feedback_from_backend()
        self.listen_frame_from_backend()
        self.listen_show_interest_icon_from_backend()
        self.listen_timer_from_backend()

        # remove UI elements
        now = time.time()

        if self.interest_icon_placed_time is not None:
            if now - self.interest_icon_placed_time > INTEREST_ICON_SHOW_DURATION:
                self.remove_interest_icon()
                self.interest_icon_placed_time = None

        if self.frame_placed_time is not None:
            if now - self.frame_placed_time > IMAGE_FRAME_SHOW_DURATION:
                self.remove_frame()
                self.frame_placed_time = None

        # run this function again after 0.2 seconds
        self.root.after(300, self.update_ui_based_on_timer)

    def listen_timer_from_backend(self):
        progress_bar_percentage = self.system_config.progress_bar_percentage
        if progress_bar_percentage is not None:
            if progress_bar_percentage > 0:
                self.set_timer(progress_bar_percentage)
            else:
                self.remove_timer()

        if progress_bar_percentage is None and self.progress_bar is not None:
            self.remove_timer()

    def set_timer(self, progress_bar_percentage):
        if self.progress_bar is None:
            self.hide_show_buttons()
            self.progress_bar = CTkProgressBar(master=self.root,
                                               orientation='horizontal',
                                               mode='determinate',
                                               progress_color=MAIN_GREEN_COLOR, height=15)
            if self.notification_widget is not None:
                relx = float(self.notification_widget.place_info()['relx'])
                rely = float(self.notification_widget.place_info()['rely'])

                self.progress_bar.place(relx=relx, rely=rely + 0.1, relwidth=0.3, anchor=tk.CENTER)
            else:
                self.progress_bar.place(relx=0.8, rely=0.35, relwidth=0.3, anchor=tk.CENTER)
            self.root.update_idletasks()

        self.progress_bar.set(progress_bar_percentage)

    def remove_timer(self):
        if self.progress_bar is not None:
            self.progress_bar.destroy()
            self.progress_bar = None

    def listen_notification_from_backend(self):
        notification = self.system_config.notification
        if notification != self.last_notification:
            if self.last_notification is not None:
                if notification is None or notification["type"] != self.last_notification["type"]:
                    self.remove_notification()

            if notification is not None:
                if self.last_notification is None:
                    self.hide_button()
                if self.notification_widget is None:
                    self.show_notification_widget(notification)
                if notification["type"] == "text":
                    self.notification_widget.configure(text=notification["content"])

            self.last_notification = notification

    def show_notification_widget(self, notification):
        if notification["type"] == "text":
            self.notification_widget = customtkinter.CTkLabel(self.root, text="", font=('Roboto', 20), text_color="#59C9A0")
            self.notification_widget.configure(image=self.notification_box, compound="center")
        elif notification["type"] == "like_icon":
            self.like_icon = customtkinter.CTkImage(Image.open(os.path.join(self.asset_path, "like_icon.png")),
                                                    size=(30, 30))
            self.notification_widget = customtkinter.CTkLabel(self.root, text="", image=self.like_icon)
            print("like icon")

        if notification["position"] == "top-center":
            self.notification_widget.place(relx=0.5, rely=0.16, anchor='center')
        elif notification["position"] == "top_right":
            self.notification_widget.place(relx=0.8, rely=0.05, anchor='center')
            print("top_right")
        else:
            self.notification_widget.place(relx=0.5, rely=0.84, anchor='center')

    def remove_notification(self):
        self.notification_widget.destroy()
        self.notification_widget = None

    def listen_show_interest_icon_from_backend(self):
        if self.system_config.show_interest_icon:
            self.show_interest_icon()
            self.system_config.show_interest_icon = False

    def show_interest_icon(self):
        self.interest_icon = customtkinter.CTkImage(Image.open(os.path.join(self.asset_path, "light_icon.png")),
                                                    size=(20, 20))
        self.interest_icon_label = customtkinter.CTkLabel(self.root, text="", image=self.interest_icon)
        self.interest_icon_label.place(relx=0.85, rely=0.05, anchor='center')
        self.interest_icon_placed_time = time.time()

    def remove_interest_icon(self):
        self.interest_icon_label.destroy()

    def listen_feedback_from_backend(self):
        text_feedback_to_show = self.system_config.text_feedback_to_show
        audio_feedback_to_show = self.system_config.audio_feedback_to_show
        if text_feedback_to_show is not None and text_feedback_to_show != self.last_text_feedback_to_show:
            self.last_text_feedback_to_show = text_feedback_to_show
            self.render_text_response(text_feedback_to_show)
            # self.system_config.text_feedback_to_show = None
        if audio_feedback_to_show is not None:
            # print("audio text to show: ", self.system_config.text_feedback_to_show)
            self.render_audio_response(audio_feedback_to_show)
            self.system_config.audio_feedback_finished_playing = False
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
            # self.root.update()

    def show_button(self):
        for direction, button in self.buttons.items():
            button.place(**self.buttons_places[direction])  # Place the button

    def hide_show_content(self):
        self.hide_show_picture_window()
        if self.shown_button:
            self.hide_text()
            self.hide_button()
        else:
            self.show_text()
            self.show_button()
        self.root.update_idletasks()
        # self.root.update()
        self.shown_button = not self.shown_button

    def destroy_picture_window(self):
        # Check if the picture window is open and close it if necessary
        if self.picture_label:
            self.picture_label.destroy()
            # print("destroy picture window")
            self.picture_label = None
            self.system_config.picture_window_status = False
            # self.update_vision_analysis()
            return

    def hide_show_text(self):
        if not self.is_hidden_text:
            self.hide_text()
        elif self.is_hidden_text:
            self.show_text()

    def hide_text(self):
        if self.text_widget is not None:
            self.stored_text_widget_content = self.text_widget.get("1.0", tk.END)
            self.text_widget.place_forget()
            self.is_hidden_text = True

    def show_text(self):
        if self.stored_text_widget_content is not None:
            self.text_widget.place(relx=0.5, rely=0.5, anchor='center')
            self.text_widget.place_configure(relheight=0.55, relwidth=0.65)
            self.is_hidden_text = False

    def hide_show_picture_window(self):
        if self.picture_label and not self.picture_window_hidden:
            self.picture_label.place_forget()
            self.system_config.picture_window_status = False
            # self.update_vision_analysis()
            self.picture_window_hidden = True
        elif self.picture_label and self.picture_window_hidden:
            self.picture_label.place()
            self.system_config.picture_window_status = True
            # self.update_vision_analysis()
            self.picture_window_hidden = False

    def listen_frame_from_backend(self):
        frame = self.system_config.frame_shown_in_picture_window
        if frame is not None and self.picture_label is None:
            self.render_picture(frame)

    def render_picture(self, frame):
        if self.picture_label:
            self.destroy_picture_window()

        # convert the image from opencv to PIL format
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)

        # Resize the image to 1/4 of its original size
        img = img.resize((int(img.width / 4), int(img.height / 4)))

        # Create a round-rectangle mask for the image
        mask = Image.new("L", img.size, 0)
        draw = ImageDraw.Draw(mask)
        radius = min(img.width, img.height) // 10  # Adjust the radius as desired
        draw.rounded_rectangle((0, 0, img.width, img.height), radius, fill=200, width=3)

        # Apply the mask to the image
        img.putalpha(mask)

        img_tk = ImageTk.PhotoImage(img)

        # Create a label widget to display the image
        self.picture_label = tk.Label(self.root, bg="black")

        # Set the picture label to the top-right of the window
        self.picture_label.place(relx=0.8, rely=0.2, anchor=tk.CENTER)

        # Set the image on the label widget
        self.picture_label.configure(image=img_tk)
        self.picture_label.image = img_tk

        self.system_config.picture_window_status = True

        # Check Users' surrounding environment
        # print(f"Person count: {self.person_count}")
        if self.person_count > 3:
            self.notification_widget.configure(text="Too many people nearby. You may hide the pic and comment it later.")

        self.system_config.frame_shown_in_picture_window = None
        self.frame_placed_time = time.time()

    def remove_frame(self):
        self.destroy_picture_window()

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
