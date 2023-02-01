import os


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


def append_data(file_name, data):
    os.makedirs(os.path.dirname(file_name), exist_ok=True)

    try:
        file = open(file_name, "a")
        file.write(data)
        file.close()
    except Exception as e:
        print("Failed to write: ", e.__class__)
