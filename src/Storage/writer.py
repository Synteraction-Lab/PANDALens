import datetime
import json
import os

from src.Utilities.file import is_file_exists, ITEM, DETAILS, TIME


def append_json_data(file_name, new_data):
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


def append_csv_data(file_name, data, write_type="a"):
    os.makedirs(os.path.dirname(file_name), exist_ok=True)

    try:
        file = open(file_name, write_type)
        file.write(data)
        file.close()
    except Exception as e:
        print("Failed to write: ", e.__class__)


def record_device_config(file_name, item, details):
    if not is_file_exists(file_name):
        append_csv_data(file_name, f'{ITEM},{DETAILS}\n')

    append_csv_data(file_name, f'{item},{details}\n')


def log_manipulation(file_name, item):
    if not is_file_exists(file_name):
        append_csv_data(file_name, f'{ITEM},{TIME}\n')

    append_csv_data(file_name, f'{item},{datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")}\n')
    print(f'Logged: {item}')
