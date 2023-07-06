import cv2
from PIL import Image, ImageTk
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

        if self.notif_type == "text":
            self.notification_box_img = CTkImage(Image.open(os.path.join(self.asset_path, "notification_box.png")),
                                                 size=(375, 300))
            self.notification_widget_text = CTkLabel(self.parent, text="", font=('Roboto', 16),
                                                     text_color="white", wraplength=250, bg_color="#314A35")
            self.notification_widget_box = CTkLabel(self.parent, text="")
            self.notification_widget_box.configure(image=self.notification_box_img, compound="center")
            self.notification_widget_box.place(relwidth=1, relheight=1)
            self.notification_widget_text.place(relx=0.62, rely=0.55, anchor=tk.CENTER)
            self.notification_widget_text.lift()
        elif self.notif_type == "picture":
            self.listening_photo_comments_icon = CTkImage(
                Image.open(os.path.join(self.asset_path, "image_suggestion_box.png")),
                size=(375, 300))
            self.picture_notification_box = CTkLabel(self.parent, text="",
                                                     image=self.listening_photo_comments_icon)

            self.picture_notification_box.place(relwidth=1, relheight=1)

        elif self.notif_type == "like_icon":
            self.like_icon = CTkImage(Image.open(os.path.join(self.asset_path, "like_icon.png")),
                                      size=(30, 30))
            self.icon = CTkLabel(self.parent, text="", image=self.like_icon)
            self.icon.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        elif self.notif_type == "listening_icon":
            self.listening_icon = CTkImage(Image.open(os.path.join(self.asset_path, "listening_icon.png")),
                                           size=(250, 72))
            self.icon = CTkLabel(self.parent, text="", image=self.listening_icon)
            self.icon.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        elif self.notif_type == "audio_icon":
            self.audio_icon = CTkImage(Image.open(os.path.join(self.asset_path, "audio_icon.png")),
                                       size=(29, 26))
            self.icon = CTkLabel(self.parent, text="", image=self.audio_icon)
            self.icon.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        elif self.notif_type == "processing_icon":
            self.processing_icon = CTkImage(Image.open(os.path.join(self.asset_path, "processing_icon.png")),
                                            size=(250, 72))
            self.icon = CTkLabel(self.parent, text="", image=self.processing_icon)
            self.icon.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        elif self.notif_type == "mic_icon":
            self.mic_icon = CTkImage(Image.open(os.path.join(self.asset_path, "mic_icon.png")),
                                     size=(30, 40))
            self.icon = CTkLabel(self.parent, text="", image=self.mic_icon)
            self.icon.configure(bg_color="systemTransparent")
            self.icon.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            self.icon.lift()
            print("mic icon created")

    def configure(self, **kwargs):
        if "text" in kwargs:
            self.text = kwargs["text"]
            self.notification_widget_text.configure(text=self.text)
        if "notif_type" in kwargs:
            self.notif_type = kwargs["notif_type"]
        if "image" in kwargs:
            frame = kwargs["image"]
            # convert the image from opencv to PIL format
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)

            # Resize the image to 1/6 of its original size
            img = img.resize((int(img.width / 6), int(img.height / 6)))

            img_tk = ImageTk.PhotoImage(img)

            # Create a label widget to display the image
            self.picture_label = tk.Label(self.parent, bg="black")

            # Set the picture label to the top-right of the window
            self.picture_label.place(relx=0.62, rely=0.6, anchor=tk.CENTER, relwidth=0.5, relheight=0.45)
            # self.picture_label.pack()

            # Set the image on the label widget
            self.picture_label.configure(image=img_tk)
            self.picture_label.image = img_tk

    def destroy(self):
        if self.notif_type == "text":
            self.notification_widget_text.destroy()
            self.notification_widget_box.destroy()
        elif self.icon.winfo_exists():
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
