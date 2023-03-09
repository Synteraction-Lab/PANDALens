import json
import os

from Utilities.file import is_file_exists, ITEM, DETAILS


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


def record_device_config(file_name, item, details):
    if not is_file_exists(file_name):
        append_data(file_name, f'{ITEM},{DETAILS}\n')

    append_data(file_name, f'{item},{details}\n')
