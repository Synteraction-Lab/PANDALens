import os
import tkinter as tk

import customtkinter
import pandas

from src.Module.Audio.live_transcriber import get_recording_devices
from src.Storage.writer import record_device_config
from src.UI.widget_generator import get_button, get_dropdown_menu, get_entry_with_placeholder, get_label, \
    get_checkbutton
from src.Utilities.constant import CONFIG_FILE_NAME, VISUAL_OUTPUT, AUDIO_OUTPUT
from src.Utilities.file import get_second_monitor_original_pos, \
    get_possible_tasks


def save_device_config(path, item, data):
    print("Saving to: " + path)
    record_device_config(path, item, data)


class DevicePanel:
    def __init__(self, root=None, parent_object_save_command=None):
        self.audio_device_list = []
        self.parent_object_save_command = parent_object_save_command

        self.path = os.path.join("data", CONFIG_FILE_NAME)
        self.load_config()
        self.load_recording_device_index()

        self.root = tk.Toplevel(root)
        # self.place_window_to_center()
        # self.root.overrideredirect(True)
        self.root.wm_transient(root)

        self.pack_layout()
        self.root.wm_attributes("-topmost", True)
        # self.place_window_to_center()

    def place_window_to_center(self):
        self.root.update_idletasks()
        self.root.geometry(
            '+{}+{}'.format(get_second_monitor_original_pos()[0] +
                            (get_second_monitor_original_pos()[2] - self.root.winfo_width()) // 2,
                            get_second_monitor_original_pos()[1] +
                            (get_second_monitor_original_pos()[3] - self.root.winfo_height()) // 2))

    def load_recording_device_index(self):
        input_devices = get_recording_devices()
        for device in input_devices:
            self.audio_device_list.append(device["name"])

    def set_default_device_config(self, path):
        self.pid_num = os.path.join("p1", "01")
        self.task_name = "travel_blog"
        self.output_modality = AUDIO_OUTPUT
        self.audio_device_idx = 0
        self.naive = "UbiWriter"
        self.gaze_recording = False
        save_device_config(path, "pid", self.pid_num)
        save_device_config(path, "task", self.task_name)
        save_device_config(path, "output", self.output_modality)
        save_device_config(path, "audio_device", self.audio_device_idx)
        save_device_config(path, "naive", self.naive)
        save_device_config(path, "gaze_recording", self.gaze_recording)

    def load_config(self):
        if not os.path.isfile(self.path):
            self.set_default_device_config(self.path)
        try:
            self.df = pandas.read_csv(self.path)
            self.pid_num = self.df[self.df['item'] == 'pid']['details'].item()
            self.task_name = self.df[self.df['item'] == 'task']['details'].item()
            self.output_modality = self.df[self.df['item'] == 'output']['details'].item()
            self.audio_device_idx = self.df[self.df['item'] == 'audio_device']['details'].item()
            self.naive = self.df[self.df['item'] == 'naive']['details'].item()
            self.gaze_recording = self.df[self.df['item'] == 'gaze_recording']['details'].item()
        except:
            print("Config file has an error! device_panel.py")
            # delete previous file
            os.remove(self.path)
            self.set_default_device_config(self.path)
            self.df = pandas.read_csv(self.path)
            self.pid_num = self.df[self.df['item'] == 'pid']['details'].item()
            self.task_name = self.df[self.df['item'] == 'task']['details'].item()
            self.output_modality = self.df[self.df['item'] == 'output']['details'].item()
            self.audio_device_idx = self.df[self.df['item'] == 'audio_device']['details'].item()
            self.naive = self.df[self.df['item'] == 'naive']['details'].item()
            self.gaze_recording = self.df[self.df['item'] == 'gaze_recording']['details'].item()

    def update_pid(self):
        self.pid_num = self.pid_txt.get_text()
        self.df.loc[self.df['item'] == "pid", ['details']] = self.pid_num

    def update_task(self):
        self.task_name = self.task_var.get()
        self.df.loc[self.df['item'] == "task", ['details']] = self.task_name

    def update_naive(self):
        self.naive = self.naive_var.get()
        self.df.loc[self.df['item'] == "naive", ['details']] = self.naive

    def update_gaze_recording(self):
        self.gaze_recording = self.gaze_recording_var.get()
        self.df.loc[self.df['item'] == "gaze_recording", ['details']] = self.gaze_recording

    def update_output(self):
        self.output_modality = self.output_var.get()
        self.df.loc[self.df['item'] == "output", ['details']] = self.output_modality

    def update_screen_recording_source(self):
        self.audio_device_idx = self.audio_device.get()
        self.df.loc[self.df['item'] == "audio_device", ['details']] = self.audio_device_idx

    def on_close_window(self):
        self.update_pid()
        self.update_task()
        self.update_output()
        self.update_screen_recording_source()
        self.update_naive()
        self.update_gaze_recording()
        self.df.to_csv(self.path, index=False)
        if self.parent_object_save_command is not None:
            self.parent_object_save_command()
        self.root.destroy()

    def pack_layout(self):
        self.frame = tk.Frame(self.root)
        self.frame.pack()

        self.pid_frame = tk.Frame(self.frame)
        self.pid_frame.pack(pady=10, anchor="w")

        self.task_frame = tk.Frame(self.frame)
        self.task_frame.pack(pady=10, anchor="w")

        self.output_frame = tk.Frame(self.frame)
        self.output_frame.pack(pady=10, anchor="w")

        self.recording_device_frame = tk.Frame(self.frame)
        self.recording_device_frame.pack(pady=10, anchor="w")

        self.gaze_recording_frame = tk.Frame(self.frame)
        self.gaze_recording_frame.pack(pady=10, anchor="w")

        self.pid_label = get_label(self.pid_frame, text="PID", pattern=0)
        self.pid_label.pack(side="left", padx=5)
        self.pid_txt = get_entry_with_placeholder(master=self.pid_frame, placeholder=self.pid_num)
        self.pid_txt.pack(side="left", padx=5)

        self.task_label = get_label(self.task_frame, text="Task", pattern=0)
        self.task_label.pack(side="left", padx=5)

        self.task_var = tk.StringVar()
        self.task_var.set(self.task_name)

        self.task_list = get_possible_tasks()
        self.task_options = get_dropdown_menu(self.task_frame, values=self.task_list,
                                              variable=self.task_var)

        self.task_options.pack(side="left", padx=5)

        self.output_label = get_label(self.task_frame, text="Output", pattern=0)
        self.output_label.pack(side="left", padx=5)

        self.output_var = tk.StringVar()
        self.output_var.set(self.output_modality)

        self.output_list = [VISUAL_OUTPUT, AUDIO_OUTPUT]
        self.output_options = get_dropdown_menu(self.task_frame, values=self.output_list,
                                                variable=self.output_var)

        self.output_options.pack(side="left", padx=5)

        # ubiwriter vs naive llm
        self.naive_label = get_label(self.task_frame, text="System Type", pattern=0)
        self.naive_label.pack(side="left", padx=5)

        self.naive_var = tk.StringVar()
        self.naive_var.set(self.naive)

        self.naive_list = ["UbiWriter", "Naive LLM"]
        self.naive_options = get_dropdown_menu(self.task_frame, values=self.naive_list,
                                               variable=self.naive_var)

        self.naive_options.pack(side="left", padx=5)

        # audio device
        self.audio_device = tk.StringVar()
        self.audio_device.set(self.audio_device_idx)

        self.audio_label = get_label(self.recording_device_frame, text="Recording Audio Source:")
        self.audio_label.grid(column=0, row=2, columnspan=1, padx=10, pady=10, sticky="w")
        self.audio_options = get_dropdown_menu(self.recording_device_frame, values=self.audio_device_list,
                                               variable=self.audio_device)

        self.audio_options.grid(column=1, row=2, columnspan=1, padx=10, pady=10, sticky="w")

        self.gaze_recording_var = customtkinter.BooleanVar()
        self.gaze_recording_var.set(self.gaze_recording)
        self.gaze_recording_checkbox = get_checkbutton(self.gaze_recording_frame, text="Gaze Recording",
                                                                 # command=self.update_gaze_recording,
                                                                 variable=self.gaze_recording_var)
        self.gaze_recording_checkbox.pack(side="left", padx=5)

        self.close_frame = tk.Frame(self.frame)
        self.close_frame.pack(pady=10)
        self.close_btn = get_button(self.close_frame, text="Save", command=self.on_close_window)
        self.close_btn.pack()


if __name__ == '__main__':
    root = tk.Tk()
    DevicePanel(root)
    root.mainloop()
