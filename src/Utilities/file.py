import os
import sys
from os.path import isfile, join
from pathlib import Path
import platform
from screeninfo import get_monitors

from src.Utilities.constant import task_description_path

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


def is_file_exists(file_name):
    return os.path.exists(file_name)


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
    dir_name = task_description_path
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
