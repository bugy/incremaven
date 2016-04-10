import os.path
import time
import datetime
import pathlib


def modification_date(file_path):
    timeString = time.ctime(os.path.getmtime(file_path))
    return datetime.datetime.strptime(timeString, "%a %b %d %H:%M:%S %Y")


def normalize_path(pathString):
    pathString = os.path.expanduser(pathString)

    if (os.path.isabs(pathString)):
        return pathString

    path = pathlib.Path(pathString)

    return str(path.resolve())


def read_file(filename):
    file_content = ""
    with open(filename, "r") as f:
        file_content += f.read()

    return file_content


def write_file(filename, content):
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))

    with open(filename, "w") as file:
        file.write(content)
