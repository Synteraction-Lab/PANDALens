import sys 
sys.path.append("./")
import tkinter
from tkinter import Toplevel, Label, Frame
import ttkbootstrap as ttk

from UI.widget_generator import get_bordered_frame, get_button
from Utilities.screen_capture import get_second_monitor_original_pos


class MessageBox:
    def __init__(self, parent=None, text=None, font=None, width=160, height=150, workflow=None):
        # style = ttk.Style("darkly")
        self.root = Toplevel(parent)
        self.root.overrideredirect(True)
        self.font = font
        self.width = width
        self.height = height
        self.text = text
        self.workflow = workflow
        self.pack_layout()
        self.root.attributes('-topmost', True)
        self.place_window_to_center()


    def pack_layout(self):
        self.main_frame = get_bordered_frame(self.root)
        self.frame = Frame(self.main_frame, width=self.width, height=self.height)
        self.message_txt = Label(self.frame, text=self.text)
        if self.font is not None:
            self.message_txt.configure(font=self.font)
        self.message_txt.pack(pady=10)
        self.frame.pack(expand=True, padx=10)
        self.main_frame.pack(expand=True)
        self.close_frame = Frame(self.frame)
        self.close_frame.pack(pady=10, side="bottom")
        self.close_btn = get_button(self.close_frame, text="OK", command=self.on_close_window, pattern=0)
        self.close_btn.pack()

    def on_close_window(self):
        if self.workflow is not None:
            self.workflow.lower()
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
    MessageBox(root, "tesX", font=(None, 12))
    root.mainloop()
