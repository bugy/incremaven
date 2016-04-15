import datetime
import os
import os.path
import pathlib
import stat
import time


def modification_date(file_path):
    timeString = time.ctime(os.path.getmtime(file_path))
    return datetime.datetime.strptime(timeString, "%a %b %d %H:%M:%S %Y")


def deletion_date(file_path):
    path = pathlib.Path(file_path)

    while (not path.exists()):
        path = pathlib.Path(path.parent)

        if (is_root(str(path))):
            raise Exception("Couldn't find parent folder for the deleted file " + file_path)

    return modification_date(str(path))


def is_root(path):
    return os.path.dirname(path) == path


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


def make_executable(filename):
    st = os.stat(filename)
    os.chmod(filename, st.st_mode | stat.S_IEXEC)
