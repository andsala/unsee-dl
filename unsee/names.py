import json
import re
import random

import requests


NAMES_FILENAME = 'names.json'


def retrieve():
    result = requests.get('https://unsee.cc/js/names.js')
    if not result.ok:
        print('Failed to retrieve names.js')
        return False

    names = re.findall(r"[\"'](\w*)[\"']", result.text)

    # TODO save names
    with open(NAMES_FILENAME, 'w') as file:
        json.dump({'names': names}, file)

    return True


def get():
    with open(NAMES_FILENAME, 'r') as file:
        names = json.load(file)

    return names['names']


def get_random():
    names = get()
    return random.choice(names)


if __name__ == '__main__':
    success = retrieve()
    if not success:
        exit(1)
