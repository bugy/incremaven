import datetime
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

    if os.path.isabs(result):
        return result

    return os.path.abspath(result)


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
