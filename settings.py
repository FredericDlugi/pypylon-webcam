import json
import os

mod_time = 0
data = None
SETTINGS_FILE_NAME = "settings.json"


def update_settings():
    global data
    global mod_time
    cur_mod_time = os.path.getmtime(SETTINGS_FILE_NAME)

    if mod_time != cur_mod_time:
        settings_file = open(SETTINGS_FILE_NAME)
        data = json.load(settings_file)
        mod_time = cur_mod_time


def get_setting(name, default=None):
    update_settings()
    if name in data:
        return data[name]
    else:
        return default


def set_setting(name, value):
    update_settings()
    data[name] = value
    json.dump(data, SETTINGS_FILE_NAME, indent=4, sort_keys=True)


if __name__ == "__main__":
    print(get_setting("input_resolution"))
