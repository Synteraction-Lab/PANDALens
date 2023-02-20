import sys
sys.path.append("./")
import tkinter
from tkinter import Toplevel, Label, Frame
import ttkbootstrap as ttk

from UI.messagebox import MessageBox 
from UI.widget_generator import get_bordered_frame, get_button, get_label


class ConfirmBox(MessageBox):
    def __init__(self, parent=None, text=None, font=None, width=300, height=200, on_click_yes_func=None):
        super().__init__(parent, text, font, width, height)
        self.on_click_yes_option_func = on_click_yes_func

    def pack_layout(self):
        self.main_frame = get_bordered_frame(self.root)
        self.frame = Frame(self.main_frame, width=self.width, height=self.height)
        self.message_txt = Label(self.frame, text=self.text)
        if self.font is not None:
            self.message_txt.configure(font=self.font)
        self.message_txt.pack(pady=10)
        self.frame.pack(expand=True, padx=10)
        self.main_frame.pack(expand=True)
        self.options_frame = Frame(self.frame)
        self.options_frame.pack(pady=10, side="bottom")
        self.yes_btn = get_button(self.options_frame, text="YES", command=self.on_click_yes, pattern=0)
        self.yes_btn.pack(side="left")
        self.no_btn = get_label(self.options_frame, text="NO")
        self.no_btn.bind("<Button-1>", lambda e: self.on_close_window())
        self.no_btn.pack(side="right", padx=5)


    def on_click_yes(self):
        if self.on_click_yes_option_func == None:
            return 
        self.on_click_yes_option_func()
        self.on_close_window()


def on_click_yes_option():
    print("clicked yes")

if __name__ == '__main__':
    root = tkinter.Tk()
    ConfirmBox(root, "Are you sure you want to STOP the pilot now?", font=(None, 12), on_click_yes_func=on_click_yes_option)
    root.mainloop()