from PIL import Image
from customtkinter import CTkLabel, CTkImage, CTkFrame
import tkinter as tk
import os


class NotificationWidget:
    def __init__(self, parent, notif_type, *args, **kwargs):
        self.parent = parent
        self.notif_type = notif_type
        self.text = ""

        if "text" in kwargs:
            self.text = kwargs["text"]

        self.asset_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

        self.notification_box_img = CTkImage(Image.open(os.path.join(self.asset_path, "notification_box.png")),
                                             size=(375, 300))
        self.listening_icon = CTkImage(Image.open(os.path.join(self.asset_path, "listening_icon.png")),
                                       size=(250, 72))
        self.like_icon = CTkImage(Image.open(os.path.join(self.asset_path, "like_icon.png")),
                                  size=(30, 30))
        self.processing_icon = CTkImage(Image.open(os.path.join(self.asset_path, "processing_icon.png")),
                                        size=(250, 72))

        if self.notif_type == "text":
            self.notification_widget_text = CTkLabel(self.parent, text="self.text", font=('Roboto', 20),
                                                     text_color="white", wraplength=250, bg_color="#314A35")
            self.notification_widget_box = CTkLabel(self.parent, text="")
            self.notification_widget_box.configure(image=self.notification_box_img, compound="center")
            self.notification_widget_box.place(relwidth=1, relheight=1)
            self.notification_widget_text.place(relx=0.6, rely=0.55, anchor=tk.CENTER)
            self.notification_widget_text.lift()
        elif self.notif_type == "like_icon":
            self.icon = CTkLabel(self.parent, text="", image=self.like_icon)
            self.icon.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        elif self.notif_type == "listening_icon":
            self.icon = CTkLabel(self.parent, text="", image=self.listening_icon)
            self.icon.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        elif self.notif_type == "processing_icon":
            self.icon = CTkLabel(self.parent, text="", image=self.processing_icon)
            self.icon.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    def configure(self, **kwargs):
        if "text" in kwargs:
            self.text = kwargs["text"]
            self.notification_widget_text.configure(text=self.text)
        if "notif_type" in kwargs:
            self.notif_type = kwargs["notif_type"]

    def destroy(self):
        if self.notif_type == "text":
            self.notification_widget_text.destroy()
            self.notification_widget_box.destroy()
        elif self.notif_type == "like_icon":
            self.icon.destroy()
        elif self.notif_type == "listening_icon":
            self.icon.destroy()

    def get_desired_size(self):
        # Calculate the desired width and height based on the notif_type
        if self.notif_type == "text":
            width = self.notification_box_img.cget("size")[0]
            height = self.notification_box_img.cget("size")[1]
        elif self.notif_type == "like_icon":
            width = self.like_icon.cget("size")[0]
            height = self.like_icon.cget("size")[1]
        elif self.notif_type == "listening_icon":
            width = self.listening_icon.cget("size")[0]
            height = self.listening_icon.cget("size")[1]
        else:
            width = 0
            height = 0

        return width, height
