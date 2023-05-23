import threading
import time
import tkinter as tk

from multiprocessing import Process

from PIL import Image, ImageTk

import pandas
from pynput import keyboard

from src.Command.Parser import parse
from src.Data.SystemConfig import SystemConfig
from src.Module.Audio.live_transcriber import LiveTranscriber, show_devices
from src.Module.LLM.GPT import GPT
from src.Module.Vision.utilities import compare_histograms

from src.UI.device_panel import DevicePanel
from src.UI.hierarchy_menu_config import HierarchyMenu
from src.UI.widget_generator import get_button
from src.Utilities.constant import VISUAL_OUTPUT, AUDIO_OUTPUT, audio_file, chat_file, slim_history_file, config_path, \
    image_folder

import os
from pynput.keyboard import Key, Listener as KeyboardListener
from pynput.mouse import Listener as MouseListener
import pyttsx3


def play_audio_response(response):
    response = response.replace("AI:", "")
    speech_engine = pyttsx3.init(debug=True)
    speech_engine.setProperty('rate', 120)
    speech_engine.say(response)
    speech_engine.runAndWait()


class App:
    def __init__(self, test_mode=False, ring_mouse_mode=False):
        self.stored_text_widget_content = None
        self.is_hidden_text = False
        self.previous_vision_frame = None
        self.picture_window = None
        self.output_mode = None
        self.ring_mouse_mode = ring_mouse_mode
        self.system_config = SystemConfig()
        self.system_config.set_test_mode(test_mode)
        self.root = tk.Tk()
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

        self.start_vision_analysis()

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
        self.system_config.set_bg_audio_analysis(device=audio_device_idx)
        self.start_bg_audio_analysis()
        self.system_config.set_image_folder(os.path.join(folder_path, image_folder))

        chat_history_file_name = os.path.join(folder_path, chat_file)
        slim_history_file_name = os.path.join(folder_path, slim_history_file)
        self.system_config.set_GPT(GPT(chat_history_file_name=chat_history_file_name,
                                       slim_history_file_name=slim_history_file_name),
                                   task_name=task_name)

        # Set up output modality
        self.output_mode = output_modality

        # Set up keyboard and mouse listener
        self.start_mouse_key_listener()

    def start_mouse_key_listener(self):
        # self.root.bind("<Button-1>", self.on_click)
        self.mouse_listener = MouseListener(on_click=self.on_click)
        self.keyboard_listener = KeyboardListener(
            on_press=self.on_press, on_release=self.on_release)
        self.mouse_listener.start()
        time.sleep(0.1)
        self.keyboard_listener.start()

    def on_press(self, key):
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
            # elif key.char == 'v':
            #     func = self.menu.trigger('show_voice_icon')
            # elif key.char == 'p':
            #     func = self.menu.trigger('show_photo_icon')
        except Exception as e:
            print(e)

        finally:
            self.parse_button_press(func)

    def parse_button_press(self, func):
        if func is None:
            return
        if func == "Hide" or func == "Show":
            self.hide_show_text(func)
        elif func == "Summary":
            self.on_summarize()
        elif func == "Voice" or func == "Stop":
            self.on_record()
        elif func == "Photo" or func == "Retake":
            self.on_photo()

    def on_release(self, key):
        # Resume Previous conversation
        try:
            if key == Key.esc:
                self.system_config.GPT.resume_stored_history()
        except Exception as e:
            print(e)

    def on_click(self, x, y, button, pressed):
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
                                   spacing1=10, spacing2=20, wrap="word", highlightbackground='black',
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
        self.audio_detector_notification.place(relx=0, rely=0.1, anchor='w')

        self.vision_detector_notification = tk.Label(self.root,
                                                     text="",
                                                     fg='green', bg='black', font=('Arial', 20))
        self.vision_detector_notification.place(relx=1, rely=0.1, anchor='center')

        self.scrollbar = tk.Scrollbar(self.text_frame, command=self.text_widget.yview, bg='black', troughcolor='black',
                                      activebackground='black', highlightbackground='black', highlightcolor='black',
                                      elementborderwidth=0, width=0)
        self.scrollbar.place(relx=1.0, relheight=1.0, anchor='ne', width=20)
        self.scrollbar.place_forget()

        self.button_up = get_button(self.manipulation_frame, text='', fg_color="green")
        self.button_down = get_button(self.manipulation_frame, text='', fg_color="green")
        self.button_left = get_button(self.manipulation_frame, text='', fg_color="green")
        self.button_right = get_button(self.manipulation_frame, text='', fg_color="green")

        self.buttons = {'up': self.button_up, 'down': self.button_down, 'left': self.button_left,
                        'right': self.button_right}
        self.buttons_places = {'up': {'relx': 0.5, 'rely': 0.05, 'anchor': 'center'},
                               'left': {'relx': 0.05, 'rely': 0.5, 'anchor': 'center'},
                               'down': {'relx': 0.5, 'rely': 0.95, 'anchor': 'center'},
                               'right': {'relx': 0.95, 'rely': 0.5, 'anchor': 'center'}}

        self.menu = HierarchyMenu(self.root, self.buttons, self.buttons_places)
        self.menu.on_enter_state()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.attributes("-fullscreen", True)
        # self.root.attributes("-alpha", 0.95)

    def on_close(self):
        self.root.destroy()
        self.keyboard_listener.stop()
        self.mouse_listener.stop()

    def on_summarize(self):
        self.determinate_voice_feedback_process()
        self.notification.config(text="Summarizing...")
        if not self.system_config.is_recording:
            t = threading.Thread(target=self.thread_summarize, daemon=True)
            t.start()

    def determinate_voice_feedback_process(self):
        voice_feedback_process = self.system_config.voice_feedback_process
        if voice_feedback_process is not None:
            voice_feedback_process.terminate()

    def thread_summarize(self):
        summarizingCommand = parse("summary", self.system_config)
        response = summarizingCommand.execute()
        self.render_response(response, self.output_mode)
        self.notification.config(text="")

    def hide_show_text(self, mode):
        # Check if the picture window is open and close it if necessary
        if self.picture_window:
            self.picture_window.destroy()
            self.picture_window = None
            self.system_config.picture_window_status = False
            self.update_vision_analysis()
            return

        if mode == "Hide":
            # self.stored_text_widget_content = self.text_widget.get("1.0", tk.END)
            self.text_widget.delete(1.0, tk.END)
            # self.left_button.configure(text="Show")
            self.determinate_voice_feedback_process()
            self.scrollbar.place()
        elif self.stored_text_widget_content is not None:
            self.text_widget.delete(1.0, tk.END)
            self.text_widget.insert(tk.END, self.stored_text_widget_content)
            # self.left_button.configure(text="Hide")
            self.scrollbar.place_forget()

        self.is_hidden_text = not self.is_hidden_text

    def thread_new_recording_command(self, command_type):
        self.notification.config(text="Analyzing...")

        if self.picture_window:
            self.picture_window.destroy()
            self.picture_window = None

        newRecordingCommand = parse("new", self.system_config)
        response = newRecordingCommand.execute()

        # Render response
        self.render_response(response, self.output_mode)
        self.notification.config(text="")

        # Enable new recording
        self.system_config.is_recording = False
        self.update_vision_analysis()

    def on_photo(self):
        photoCommand = parse("photo", self.system_config)
        frame = photoCommand.execute()
        if frame is not None:
            self.render_picture(frame)

    def render_picture(self, frame):
        if self.picture_window:
            self.picture_window.destroy()
            self.system_config.picture_window_status = False

        # Convert frame to tkinter image
        img = Image.fromarray(frame)

        # Resize the image to 1/4 of its original size
        img = img.resize((int(img.width / 2), int(img.height / 2)))

        img_tk = ImageTk.PhotoImage(img)

        # Create a new window to display the image
        self.picture_window = tk.Toplevel(self.root)
        # self.picture_window.title("Picture")
        self.picture_window.wm_attributes("-topmost", True)
        # Over direct the window to remove the border
        self.picture_window.overrideredirect(True)
        # make the pic window transparent by change its alpha value
        self.picture_window.wm_attributes("-alpha", 0.8)
        self.picture_window.lift()
        self.picture_window.geometry(
            f"{img.width}x{img.height}+{int((self.root.winfo_screenwidth() - img.width) / 2)}+{int((self.root.winfo_screenheight() - img.height) / 2)}")

        # Create a label widget to display the image
        label = tk.Label(self.picture_window, image=img_tk)
        label.image = img_tk
        label.pack()
        self.system_config.picture_window_status = True

    def on_record(self):
        self.determinate_voice_feedback_process()
        if not self.system_config.is_recording:
            with self.audio_lock:
                self.system_config.interesting_audio_for_recording = self.system_config.interesting_audio
            print(self.system_config.interesting_audio_for_recording)
            self.notification.config(text="Reminder: Press \"Right\" button again to stop recording!")
            # self.record_button.configure(text="Stop")
            self.start_recording()
            self.system_config.is_recording = True
        else:
            self.stop_recording()

            command_type = ""

            t = threading.Thread(target=self.thread_new_recording_command, args=(command_type,), daemon=True)
            t.start()
            # self.record_button.configure(text="Record")

    def start_recording(self):
        voice_transcriber = self.system_config.get_transcriber()
        if voice_transcriber is not None:
            voice_transcriber.start()
            self.update_transcription()

    def stop_recording(self):
        voice_transcriber = self.system_config.get_transcriber()
        if voice_transcriber is not None:
            self.system_config.set_final_transcription(voice_transcriber.stop())

    def update_transcription(self):
        voice_transcriber = self.system_config.get_transcriber()
        if self.system_config.get_previous_transcription() != voice_transcriber.full_text:
            self.render_response(voice_transcriber.full_text, VISUAL_OUTPUT)
            self.system_config.set_previous_transcription(voice_transcriber.full_text)
        if not voice_transcriber.stop_event.is_set():
            self.root.after(100, self.update_transcription)

    def start_bg_audio_analysis(self):
        self.update_bg_audio_analysis()

    def start_vision_analysis(self):
        self.update_vision_analysis()

    def update_bg_audio_analysis(self):
        score, category = self.system_config.get_bg_audio_analysis_result()
        if category is not None:
            if category in self.system_config.get_bg_audio_interesting_categories() \
                    and score > 0.5 \
                    and category != self.system_config.previous_interesting_audio:
                self.audio_detector_notification.config(text=f"Detected your surrounding audio: {category}. "
                                                             f"Any comments?")
                self.menu.trigger('show_voice_icon')
                with self.audio_lock:
                    self.system_config.interesting_audio = category
                self.system_config.previous_interesting_audio = category
                self.root.after(8000, self.clear_audio_notification)
            else:
                self.clear_audio_notification()
        else:
            self.clear_audio_notification()

    def clear_audio_notification(self):
        with self.audio_lock:
            if self.system_config.interesting_audio is not None:
                self.system_config.interesting_audio = None
                self.audio_detector_notification.config(text="")
                self.menu.trigger('ignore_voice_icon')
        self.root.after(500, self.update_bg_audio_analysis)

    def update_vision_analysis(self):
        if self.picture_window:
            return
        frame_sim = 0
        self.zoom_in = self.system_config.vision_detector.zoom_in
        self.closest_object = self.system_config.vision_detector.closest_object
        self.person_count = self.system_config.vision_detector.person_count
        self.fixation_detected = self.system_config.vision_detector.fixation_detected
        current_frame = self.system_config.vision_detector.original_frame
        norm_pos = self.system_config.vision_detector.norm_gaze_position

        if norm_pos is not None:
            norm_pos_x, norm_pos_y = norm_pos
            # print(self.zoom_in, self.closest_object, self.person_count, self.fixation_detected, norm_pos_x, norm_pos_y)

        if self.previous_vision_frame is not None:
            frame_sim = compare_histograms(self.previous_vision_frame, current_frame)
            print(frame_sim)

        if (self.zoom_in or self.fixation_detected) and frame_sim < 0.6 and norm_pos is not None:
            self.vision_detector_notification.place(relx=norm_pos_x, rely=norm_pos_y, anchor=tk.CENTER)
            self.vision_detector_notification.config(text=f"Do you want to take a picture?")
            self.menu.trigger('show_photo_icon')
            self.root.after(8000, self.clear_vision_notification)
            self.previous_vision_frame = current_frame
        else:
            self.clear_vision_notification()

    def clear_vision_notification(self):
        if self.vision_detector_notification.cget("text") != "":
            self.vision_detector_notification.config(text="")
            self.menu.trigger('ignore_photo_icon')
        self.root.after(500, self.update_vision_analysis)

    def render_response(self, response, output_mode):
        self.text_widget.delete(1.0, tk.END)
        response = response.strip()
        self.text_widget.insert(tk.END, response)
        self.stored_text_widget_content = response
        self.scrollbar.place()
        self.menu.trigger('get_response')
        if output_mode == AUDIO_OUTPUT:
            voice_feedback_process = Process(target=play_audio_response, args=(response,))
            self.system_config.set_voice_feedback_process(voice_feedback_process)
            voice_feedback_process.start()


if __name__ == '__main__':
    App()
