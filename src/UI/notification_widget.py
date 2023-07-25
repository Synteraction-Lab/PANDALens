import cv2
from PIL import Image, ImageTk
from customtkinter import CTkLabel, CTkImage, CTkTextbox
import tkinter as tk
import os

from src.UI.UI_config import MAIN_GREEN_COLOR


class NotificationWidget:
    def __init__(self, parent, notif_type, *args, **kwargs):
        self.parent = parent
        self.notif_type = notif_type
        self.text = ""
        self.icon = None

        if "text" in kwargs:
            self.text = kwargs["text"]

        self.asset_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

        if self.notif_type == "text":
            self.notification_robot_img = CTkImage(Image.open(os.path.join(self.asset_path, "robot_icon.png")),
                                                   size=(60, 60))
            self.notification_widget_text = CTkTextbox(self.parent, height=55, width=55,
                                                       text_color=MAIN_GREEN_COLOR, font=('Robot Bold', 20),
                                                       # bg_color='systemTransparent',
                                                       wrap="word", padx=5,
                                                       border_color="#42AF74", border_width=3)
            self.notification_robot_icon = CTkLabel(self.parent, text="")
            self.notification_robot_icon.configure(image=self.notification_robot_img, compound="center")
            self.notification_robot_icon.place(relx=0.5, rely=0.1, anchor=tk.CENTER)

            self.parent.update_idletasks()
        elif self.notif_type == "picture":
            self.listening_photo_comments_icon = CTkImage(
                Image.open(os.path.join(self.asset_path, "image_suggestion_box.png")),
                size=(230, 311))
            self.picture_notification_box = CTkLabel(self.parent, text="",
                                                     image=self.listening_photo_comments_icon)

            self.picture_notification_box.place(relwidth=1, relheight=1)

        elif self.notif_type == "listening_picture_comments":
            self.listening_photo_comments_icon = CTkImage(
                Image.open(os.path.join(self.asset_path, "listening_img_comments_box.png")),
                size=(230, 311))
            self.picture_notification_box = CTkLabel(self.parent, text="",
                                                     image=self.listening_photo_comments_icon)

            self.picture_notification_box.place(relwidth=1, relheight=1)
        elif self.notif_type == "listening_picture_comments":
            self.listening_photo_comments_icon = CTkImage(
                Image.open(os.path.join(self.asset_path, "listening_img_comments_box.png")),
                size=(375, 300))
            self.picture_notification_box = CTkLabel(self.parent, text="",
                                                     image=self.listening_photo_comments_icon)

            self.picture_notification_box.place(relwidth=1, relheight=1)

        elif self.notif_type == "like_icon":
            self.like_icon = CTkImage(Image.open(os.path.join(self.asset_path, "like_icon.png")),
                                      size=(60, 54))
            self.icon = CTkLabel(self.parent, text="", image=self.like_icon)
            self.icon.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        elif self.notif_type == "listening_icon":
            self.listening_icon = CTkImage(Image.open(os.path.join(self.asset_path, "listening_icon.png")),
                                           size=(60, 60))
            self.icon = CTkLabel(self.parent, text="", image=self.listening_icon)
            self.icon.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        elif self.notif_type == "cancel_recording_icon":
            self.cancel_listening_icon = CTkImage(
                Image.open(os.path.join(self.asset_path, "cancel_recording_icon.png")),
                size=(61, 61))
            self.icon = CTkLabel(self.parent, text="", image=self.cancel_listening_icon)
            self.icon.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        elif self.notif_type == "audio_icon":
            self.audio_icon = CTkImage(Image.open(os.path.join(self.asset_path, "audio_icon.png")),
                                       size=(60, 55))
            self.icon = CTkLabel(self.parent, text="", image=self.audio_icon)
            self.icon.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        elif self.notif_type == "processing_icon":
            self.processing_icon = CTkImage(Image.open(os.path.join(self.asset_path, "processing_icon.png")),
                                            size=(61, 71))
            self.icon = CTkLabel(self.parent, text="", image=self.processing_icon)
            self.icon.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        elif self.notif_type == "picture_thumbnail":
            self.pending_photo_icon = CTkImage(Image.open(os.path.join(self.asset_path, "pending_photo_icon.png")),
                                               size=(200, 247))
            self.icon = CTkLabel(self.parent, text="", image=self.pending_photo_icon)
            self.icon.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        elif self.notif_type == "mic_icon":
            self.mic_icon = CTkImage(Image.open(os.path.join(self.asset_path, "mic_icon.png")),
                                     size=(45, 60))
            self.icon = CTkLabel(self.parent, text="", image=self.mic_icon)
            self.icon.configure(bg_color="systemTransparent")
            self.icon.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            self.icon.lift()
        elif self.notif_type == "fpv_photo_icon":
            self.fpv_photo_icon = CTkImage(Image.open(os.path.join(self.asset_path, "fpv_photo_icon.png")),
                                           size=(60, 57))
            self.icon = CTkLabel(self.parent, text="", image=self.fpv_photo_icon)
            self.icon.configure(bg_color="systemTransparent")
            self.icon.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            self.icon.lift()

    def configure(self, **kwargs):
        if "text" in kwargs:
            self.text = kwargs["text"]
            self.notification_widget_text.insert(tk.END, self.text)
            self.notification_widget_text.place(relx=0.5, rely=0.6, relwidth=0.7, relheight=0.7, anchor=tk.CENTER)
            self.notification_widget_text.lift()
            self.parent.update_idletasks()
            self.notification_widget_text.update()
        if "notif_type" in kwargs:
            self.notif_type = kwargs["notif_type"]
        if "image" in kwargs:
            frame = kwargs["image"]
            # convert the image from opencv to PIL format
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)

            # Resize the image to 1/7 of its original size
            img = img.resize((int(img.width / 7), int(img.height / 7)))

            img_tk = ImageTk.PhotoImage(img)

            # Create a label widget to display the image
            self.picture_label = tk.Label(self.parent, bg="black")

            # Set the picture label to the top-right of the window
            if self.notif_type == "picture_thumbnail":
                self.picture_label.place(relx=0.5, rely=0.6, anchor=tk.CENTER, relwidth=0.45, relheight=0.25)
            else:
                self.picture_label.place(relx=0.5, rely=0.65, anchor=tk.CENTER, relwidth=0.6, relheight=0.34)

            # self.picture_label.pack()

            # Set the image on the label widget
            self.picture_label.configure(image=img_tk)
            self.picture_label.image = img_tk

    def destroy(self):
        if self.notif_type == "text":
            self.notification_widget_text.destroy()
            self.notification_robot_icon.destroy()
        elif self.icon is not None:
            if self.icon.winfo_exists():
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
