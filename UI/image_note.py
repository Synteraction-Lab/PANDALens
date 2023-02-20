import csv
import os
import tkinter
from tkinter import Toplevel, Label, Frame

import pandas as pd
import ttkbootstrap as ttk
from PIL import ImageTk, Image

from UI.widget_generator import get_bordered_frame, get_button, get_text
from Utilities.screen_capture import get_second_monitor_original_pos


class ImageNoteWindow:
    def __init__(self, parent=None, pid=None, timestamp=None, image=None, font=None, width=160, height=150):
        # style = ttk.Style("darkly")
        self.parent = parent
        self.root = Toplevel()
        self.root.wait_visibility()
        self.root.overrideredirect(True)
        self.font = font
        self.pid = pid
        self.folder_path = os.path.join("data", pid)
        self.width = width
        self.height = height
        self.timestamp = timestamp
        self.image = image
        self.load_data_file()
        self.pack_layout()
        self.root.attributes('-topmost', True)
        self.place_window_to_center()

    def load_data_file(self):
        self.file_path = os.path.join(self.folder_path, 'task_info.csv')
        self.df = pd.read_csv(self.file_path)

    def get_text_from_file(self):
        time_stamp = self.timestamp.replace("_", ":")
        text = self.df.loc[self.df['time'] == time_stamp, 'note'].iloc[0]
        return text if pd.notna(text) else ""

    def add_new_notes(self):
        time_stamp = self.timestamp.replace("_", ":")
        notes = self.notes_txt.get("1.0", "end-1c")
        self.load_data_file()
        self.df.loc[self.df['time'] == time_stamp, ['note']] = notes
        self.df.to_csv(self.file_path, index=False)
        self.notes_txt.delete("1.0", "end-1c")

    def pack_layout(self):
        self.main_frame = get_bordered_frame(self.root)
        self.frame = Frame(self.main_frame, width=self.width, height=self.height)
        self.image_label = Label(self.frame)
        self.image_label.configure(image=self.image)
        self.image_label.pack()
        self.notes_row = tkinter.LabelFrame(self.frame, text="Note:")
        self.notes_txt = get_text(self.notes_row)
        self.notes_txt.insert(1.0, self.get_text_from_file())
        self.notes_txt.configure(state="normal", height=10, borderwidth=0, highlightthickness=0)
        self.notes_txt.pack()
        self.notes_row.pack()
        self.frame.pack(expand=True, padx=10)
        self.main_frame.pack(expand=True)
        self.close_frame = Frame(self.frame)
        self.close_frame.pack(pady=10, side="bottom")
        self.close_btn = get_button(self.close_frame, text="OK", command=self.on_close_window, pattern=0)
        self.close_btn.pack()

    def on_close_window(self):
        self.parent.on_close_image_note_window()
        self.add_new_notes()
        self.root.destroy()

    def place_window_to_center(self):
        self.root.update_idletasks()
        self.root.geometry(
            '+{}+{}'.format(get_second_monitor_original_pos()[0] +
                            (get_second_monitor_original_pos()[2] - self.root.winfo_width()) // 2,
                            get_second_monitor_original_pos()[1] +
                            (get_second_monitor_original_pos()[3] - self.root.winfo_height()) // 2))


if __name__ == '__main__':
    root = tkinter.Tk()
    img = Image.open("../data/huhu/00_00_12.png")
    img = img.resize((100, int(100 * img.height / img.width)))
    imgtk = ImageTk.PhotoImage(image=img)
    ImageNoteWindow(root, pid="huhu", image=imgtk, timestamp="00_00_12")
    root.mainloop()
