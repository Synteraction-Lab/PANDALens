import tkinter as tk
from customtkinter import CTkOptionMenu, CTkCheckBox, CTkButton, CTkSlider
import ttkbootstrap as ttk
from UI.entry_with_placeholder import EntryWithPlaceholder
import UI.UI_config
from PIL import Image, ImageTk

def get_circular_button(root, text=None, command=None):
    return CTkButton(root, text=text, fg_color=UI.UI_config.BUTTON_FG_COLOR,
                     hover_color=UI.UI_config.BUTTON_HOVER_COLOR, height=UI.UI_config.CIRCULAR_BUTTON_HEIGHT, width=UI.UI_config.CIRCULAR_BUTTON_WIDTH,
                     corner_radius=50, text_color=UI.UI_config.BUTTON_TEXT_COLOR,
                     command=command, font=(None, UI.UI_config.CIRCULAR_BUTTON_FONT_SIZE))


def get_button(root, text=None, command=None, fg_color=UI.UI_config.BUTTON_FG_COLOR, pattern=0):
    """
    :param root: master window
    :param text: text in the button
    :param command: button triggered function
    :param height: button height
    :param width: button width
    :param font_size: text font size
    :param fg_color: button foreground color
    :param pattern: button's size patter. From 0-3, the larger number, the larger button size
    :return: a button
    """
    if pattern == 3:
        height = UI.UI_config.BUTTON_SIZE_3_HEIGHT
        width = UI.UI_config.BUTTON_SIZE_3_WIDTH
        font_size = UI.UI_config.BUTTON_SIZE_3_FONT_SIZE
        corner_radius = UI.UI_config.BUTTON_SIZE_3_CORNER_RADIUS
    elif pattern == 1:
        height = UI.UI_config.BUTTON_SIZE_1_HEIGHT
        width = UI.UI_config.BUTTON_SIZE_1_WIDTH
        font_size = UI.UI_config.BUTTON_SIZE_1_FONT_SIZE
        corner_radius = UI.UI_config.BUTTON_SIZE_1_CORNER_RADIUS
    elif pattern == 0:
        height = UI.UI_config.BUTTON_SIZE_0_HEIGHT
        width = UI.UI_config.BUTTON_SIZE_0_WIDTH
        font_size = UI.UI_config.BUTTON_SIZE_0_FONT_SIZE
        corner_radius = UI.UI_config.BUTTON_SIZE_0_CORNER_RADIUS
    else:
        height = UI.UI_config.BUTTON_SIZE_0_HEIGHT
        width = UI.UI_config.BUTTON_SIZE_0_WIDTH
        font_size = UI.UI_config.BUTTON_SIZE_0_FONT_SIZE
        corner_radius = UI.UI_config.BUTTON_SIZE_0_CORNER_RADIUS

    return CTkButton(root, text=text, fg_color=fg_color,
                     hover_color=UI.UI_config.BUTTON_HOVER_COLOR, height=height, width=width, border_width=0,
                     border_color=UI.UI_config.BUTTON_BORDER_COLOR, corner_radius=corner_radius, text_color=UI.UI_config.BUTTON_TEXT_COLOR,
                     command=command, font=(None, font_size))


def get_checkbutton(root, text=None, variable=None, command=None, fg_color=UI.UI_config.CHECK_BUTTON_FG_COLOR,
                    hover_color=UI.UI_config.CHECK_BUTTON_HOVER_COLOR):
    return CTkCheckBox(root, text=text, variable=variable, fg_color=fg_color, hover_color=hover_color,
                       command=command, checkmark_color=UI.UI_config.CHECKMARK_COLOR, font=UI.UI_config.LABEL_0_FONT)


def get_dropdown_menu(root, command=None, variable=None, values=None, fg_color=UI.UI_config.DROPDOWN_MENU_FG_COLOR,
                      button_color=UI.UI_config.DROPDOWN_MENU_BUTTON_COLOR, button_hover_color=UI.UI_config.DROPDOWN_MENU_HOVER_COLOR,
                      font=UI.UI_config.LABEL_0_FONT, width=UI.UI_config.DROPDOWN_MENU_WIDTH):
    return CTkOptionMenu(root, width=width, values=values,
                         variable=variable, dropdown_fg_color=UI.UI_config.DROPDOWN_COLOR, font=font,
                         fg_color=fg_color, button_color=button_color, button_hover_color=button_hover_color,
                         dropdown_text_color=UI.UI_config.DROPDOWN_TEXT_COLOR, text_color=UI.UI_config.DROPDOWN_MENU_TEXT_COLOR, command=command)


def get_bordered_frame(root, border_color=UI.UI_config.BORDERED_FRAME_BORDER_COLOR):
    return tk.Frame(root, highlightthickness=UI.UI_config.BORDERED_FRAME_HIGHLIGHT_THICKNESS, highlightbackground=border_color,
                    highlightcolor=border_color)


def get_bordered_label_frame(root, text, border_color=UI.UI_config.BORDERED_FRAME_BORDER_COLOR):
    s = ttk.Style()
    # note must use relief='solid' to let borderwidth to show its actual width
    s.configure("Custom.TLabelframe", bordercolor=border_color, borderwidth=UI.UI_config.BORDERED_FRAME_HIGHLIGHT_THICKNESS,
                relief='solid')
    s.configure("Custom.TLabelframe.Label", font=UI.UI_config.LABEL_0_FONT)
    return ttk.LabelFrame(root, text=text, style="Custom.TLabelframe")


def get_entry_with_placeholder(master, placeholder, hightlightcolor=UI.UI_config.ENTRY_HIGHLIGHT_COLOR, width=None):
    return EntryWithPlaceholder(master=master, placeholder=placeholder, highlightcolor=hightlightcolor, font=UI.UI_config.MAIN_FONT,
                                width=width)


def get_text(root, font=UI.UI_config.LABEL_0_FONT):
    return tk.Text(root, font=font, wrap=tk.WORD)


def get_label(root, textvariable=None, text=None, pattern=0):
    if pattern == 1:
        font = UI.UI_config.LABEL_1_FONT
    elif pattern == 0:
        font = UI.UI_config.LABEL_0_FONT
    elif pattern == 2:
        font = UI.UI_config.LABEL_2_FONT
    elif pattern == 3:
        font = UI.UI_config.LABEL_BOLD_FONT
    elif pattern == 4:
        font = UI.UI_config.TABLE_NORMAL_FONT
    else:
        font = UI.UI_config.LABEL_0_FONT

    if textvariable is not None:
        return tk.Label(root, textvariable=textvariable, font=font)
    else:
        return tk.Label(root, text=text, font=font)


def get_messagebox(root, text, font=UI.UI_config.MESSAGEBOX_FONT, workflow=None):
    from UI.messagebox import MessageBox
    return MessageBox(root, text, font=font, workflow=workflow)


def get_slider(root, command, variable, orient):
    return CTkSlider(master=root, command=command, variable=variable, orientation=orient, from_=0, to=100,
                     button_color=UI.UI_config.MAIN_COLOR_LIGHT, height=UI.UI_config.ANALYZER_TIMELINE_THICKNESS)

def get_image(root, path, resize_width=24, resize_height=24):
    lbl = tk.Label(root)
    img = Image.open(path)
    img = img.resize((resize_width, resize_height))
    imgtk = ImageTk.PhotoImage(image=img)
    lbl.configure(image=imgtk)
    lbl.image = imgtk
    return lbl

