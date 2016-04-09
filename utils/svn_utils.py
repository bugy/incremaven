import utils.process_utils as process_utils


def changed_files(path):
    status_info = process_utils.invoke(["svn", "status", path])

    all_files = status_info.split("\n")
    return [line[line.index("/"):]
            for line in all_files
            if "/" in line]
