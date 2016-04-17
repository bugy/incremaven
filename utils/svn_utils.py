import utils.process_utils as process_utils

def changed_files(path):
    status_info = process_utils.invoke(["svn", "status", path])
    all_lines = status_info.split("\n")

    result = {}

    for line in all_lines:
        if (line.strip().startswith("> moved")):
            continue
        if (not ("/" in line)):
            continue

        file_path = line[line.index("/"):]
        result[file_path] = line.startswith("D");

    return result
