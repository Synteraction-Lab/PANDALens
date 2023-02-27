import pyperclip
from pynput.keyboard import Controller, Key

from Utilities.utilities import get_system_name


def copy_content():
    keyboard = Controller()
    if get_system_name() == "Windows":
        keyboard.press(Key.ctrl)
        keyboard.press('c')
        keyboard.release('c')
        keyboard.release(Key.ctrl)

    elif get_system_name() == "Darwin":
        keyboard.press(Key.cmd)
        keyboard.press('c')
        keyboard.release('c')
        keyboard.release(Key.cmd)

    print(get_clipboard_content())


def get_clipboard_content():
    return pyperclip.paste()

if __name__ == '__main__':
    print(get_clipboard_content())