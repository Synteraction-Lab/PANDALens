import glob
import json
import os
import sys
from os.path import isfile, join
from pathlib import Path
import platform
from screeninfo import get_monitors

ITEM = "item"
DETAILS = "details"

_isMacOS = sys.platform.startswith('darwin')
_isWindows = sys.platform.startswith('win')
_isLinux = sys.platform.startswith('linux')

def check_saving_path(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def get_system_name():
    return platform.uname().system


def remove_file(file_name):
    if os.path.exists(file_name):
        os.remove(file_name)


def read_file(file_name):
    if not os.path.exists(file_name):
        return ""
    try:
        file = open(file_name, "a")
        content = file.read()
        file.close()
        return content
    except Exception as e:
        print("Failed to read: ", e.__class__)


def append_data(file_name, new_data):
    # Create the file and directories if they don't exist
    if not os.path.exists(file_name):
        os.makedirs(os.path.dirname(file_name), exist_ok=True)
        with open(file_name, "w") as f:
            json.dump({"recordings": []}, f)

    # Load the existing data from the JSON file
    with open(file_name, "r") as f:
        data = json.load(f)

    # Append the new data to the existing data
    data["recordings"].append(new_data)

    # Write the updated data to the JSON file
    with open(file_name, "w") as f:
        json.dump(data, f, indent=4)


def is_file_exists(file_name):
    return os.path.exists(file_name)


def record_device_config(file_name, item, details):
    if not is_file_exists(file_name):
        append_data(file_name, f'{ITEM},{DETAILS}\n')

    append_data(file_name, f'{item},{details}\n')

def get_second_monitor_original_pos():
    if len(get_monitors()) == 1:
        selected_monitor_idx = 0
        return 0, 0, get_monitors()[selected_monitor_idx].width, get_monitors()[selected_monitor_idx].height
    else:
        selected_monitor_idx = 1
        if platform.uname().system == "Windows":
            y = get_monitors()[selected_monitor_idx].y
        else:
            y = -get_monitors()[selected_monitor_idx].y + get_monitors()[0].height - get_monitors()[1].height
        return get_monitors()[selected_monitor_idx].x, y, \
               get_monitors()[selected_monitor_idx].width, \
               get_monitors()[selected_monitor_idx].height


def get_possible_tasks():
    dir_name = "./data/task_description"
    return [f for f in os.listdir(dir_name) if isfile(join(dir_name, f))]


def get_creation_date(path):
    """
    Try to get the date that a file was created, falling back to when it was
    last modified if that isn't possible.
    """
    if _isWindows:
        return os.path.getctime(path)
    else:
        stat = os.stat(path)
        try:
            return stat.st_birthtime
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            return stat.st_mtime