import re
import logging

import requests


NAMES_FILE_PATH = "unsee/names.py"


def retrieve():
    result = requests.get("https://unsee.cc/js/names.js")
    if not result.ok:
        print("Failed to retrieve names.js")
        return False

    return re.findall(r"[\"'](\w*)[\"']", result.text)


def generate_py_code(names):
    array_row_tmpl = '    "{}",\n'
    names_py_template = """
import random

NAMES = [
{}
]


def get_random():
    return random.choice(NAMES)

"""
    array_string = ""
    for name in names:
        array_string += array_row_tmpl.format(name)

    return names_py_template.format(array_string)


def save_file(filename, content):
    with open(filename, "w") as file:
        file.write(content)


if __name__ == "__main__":
    # noinspection PyBroadException
    try:
        names = retrieve()
        code = generate_py_code(names)
        save_file(NAMES_FILE_PATH, code)
    except:
        logging.error(f"Failed to generate {NAMES_FILE_PATH} file.")
        exit(1)
