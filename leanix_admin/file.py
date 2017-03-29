import json

import os


def read_from_disk(name):
    file_name = './' + name + '.json'
    with open(file_name, 'r') as f:
        return json.load(f)


def write_to_disk(name, data):
    file_name = './' + name + '.json'
    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    with open(file_name, 'w') as f:
        json.dump(data, f, indent=4)
