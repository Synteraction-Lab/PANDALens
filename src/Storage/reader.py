import os

from src.Utilities.constant import task_description_path


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


def load_task_description(task_type):
    with open(os.path.join(task_description_path, task_type)) as f:
        task_description = f.read()
        return task_description
