import datetime
import io
import os
import os.path
import stat
import time


def modification_date(file_path):
    time_string = time.ctime(os.path.getmtime(file_path))
    return datetime.datetime.strptime(time_string, "%a %b %d %H:%M:%S %Y")


def deletion_date(file_path):
    path = file_path

    while not os.path.exists(path):
        path = os.path.dirname(path)

        if is_root(path):
            raise Exception("Couldn't find parent folder for the deleted file " + file_path)

    return modification_date(path)


def is_root(path):
    return os.path.dirname(path) == path


def normalize_path(path_string):
    result = os.path.expanduser(path_string)

    if not os.path.isabs(result):
        result = os.path.abspath(result)

    return os.path.normpath(result)


def read_file(filename):
    path = normalize_path(filename)

    file_content = ""
    with open(path, "r") as f:
        file_content += f.read()

    return file_content


def write_file(filename, content):
    path = normalize_path(filename)

    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))

    with open(path, "w") as file:
        file.write(content)


def make_executable(filename):
    st = os.stat(filename)
    os.chmod(filename, st.st_mode | stat.S_IEXEC)


def exists(filename):
    path = normalize_path(filename)
    return os.path.exists(path)


def last_modification(folder_paths):
    result = None

    for root_folder_path in folder_paths:
        file_date = modification_date(root_folder_path)
        if (result is None) or (result < file_date):
            result = file_date

        for root, subdirs, files in os.walk(root_folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_date = modification_date(file_path)
                if (result is None) or (result < file_date):
                    result = file_date

            for folder in subdirs:
                folder_path = os.path.join(root, folder)
                folder_date = modification_date(folder_path)
                if (result is None) or (result < folder_date):
                    result = folder_date

    return result


def equal(path1, path2):
    if not os.path.exists(path1) or not os.path.exists(path2):
        return False

    if os.path.getsize(path1) != os.path.getsize(path2):
        return False

    buf1 = bytearray(4096)
    buf2 = bytearray(4096)
    try:
        file1 = io.open(path1, "rb", 0)
        file2 = io.open(path2, "rb", 0)
        while True:
            numread1 = file1.readinto(buf1)
            numread2 = file2.readinto(buf2)

            if numread1 != numread2:
                return False

            if not numread1:
                break

            if buf1 != buf2:
                return False

    finally:
        if file1:
            file1.close()
        if file2:
            file2.close()

    return True


def prepare_folder(folder_path):
    path = normalize_path(folder_path)

    if not os.path.exists(path):
        os.makedirs(path)
