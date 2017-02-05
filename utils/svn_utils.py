import os

import utils.process_utils as process_utils


def get_local_changed_files(abs_path):
    status_info = process_utils.invoke(["svn", "status", abs_path])
    all_lines = status_info.split("\n")

    return svn_status_to_files(all_lines)


def svn_status_to_files(all_lines, ignore_moved_source=True):
    result = []

    for line in all_lines:
        if ignore_moved_source and line.strip().startswith("> moved"):
            continue

        if os.name != 'nt':
            if not ('/' in line):
                continue
            file_path = line[line.index("/"):]

        else:
            if not ('\\' in line):
                continue
            file_path = line[line.index(':\\') - 1:]

        result.append(file_path)

    return result


def get_revision_changed_files(abs_path, from_revision, to_revision):
    changed_files = process_utils.invoke(
        ['svn', 'diff', '--summarize', '-r' + from_revision + ':' + to_revision, abs_path])
    lines = changed_files.split('\n')

    return svn_status_to_files(lines, False)


def get_revision(project_path):
    svn_info = process_utils.invoke(['svn', 'info', project_path])
    info_lines = svn_info.split('\n')

    revision_prefix = 'Revision: '

    for line in info_lines:
        if line.startswith(revision_prefix):
            return line[len(revision_prefix):]

    raise Exception("Couldn't get svn revision in " + project_path)
