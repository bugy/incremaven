import argparse
import os.path
import six
import sys
from pathlib import Path

import utils.file_utils as file_utils
import utils.mvn_utils as mvn_utils
import utils.svn_utils as svn_utils
import utils.collections as collections

parser = argparse.ArgumentParser(description="Rebuild of complex (maven) projects.")
parser.add_argument("-r", "--rootPath", help="path to the root project", default=".")
parser.add_argument("-m", "--maven", help="maven parameters to pass to mvn command", default="")
args = vars(parser.parse_args())

if args["rootPath"]:
    ROOT_PROJECT_PATH = args["rootPath"]
else:
    ROOT_PROJECT_PATH = "."

MVN_OPTS = args["maven"]

ROOT_PROJECT_PATH = file_utils.normalize_path(ROOT_PROJECT_PATH)
six.print_("Root project path: " + ROOT_PROJECT_PATH)
six.print_("Additional maven arguments: " + str(MVN_OPTS))

rootPom = Path(ROOT_PROJECT_PATH).joinpath("pom.xml")
if not rootPom.exists():
    six.print_("ERROR! No root pom.xml find in path", os.path.abspath(ROOT_PROJECT_PATH))
    sys.exit(1)

MAVEN_REPO_PATH = mvn_utils.repo_path()


def is_important(file_path):
    return not file_path.endswith(".iml")


def get_unique_name(root_project_path):
    result = root_project_path.replace("/", "_")
    return result


changed_files = svn_utils.changed_files(ROOT_PROJECT_PATH)
important_files = filter(is_important, changed_files)

pom_paths = set([])

for file in important_files:
    file_path = Path(file)
    if file_path.is_dir():
        parent_path = file_path
    else:
        parent_path = file_path.parent

    while parent_path and not (file_utils.is_root(str(parent_path))):
        pom_path_str = Path(parent_path).joinpath("pom.xml")

        if pom_path_str.exists():
            pom_paths.add(pom_path_str)
            break

        if parent_path == ROOT_PROJECT_PATH:
            break

        parent_path = parent_path.parent

new_in_progress = collections.to_strings(pom_paths)

in_progress_file = "~/.rebuilder/" + get_unique_name(ROOT_PROJECT_PATH)
prev_in_progress = []
if file_utils.exists(in_progress_file):
    prev_in_progress = file_utils.read_file(in_progress_file).split("\n")
    prev_in_progress = filter(lambda line: line != "", prev_in_progress)

for pom_path_str in prev_in_progress:
    file_path = Path(pom_path_str)
    if file_path.exists():
        pom_paths.add(file_path)

pom_paths_str = collections.to_strings(pom_paths)
file_utils.write_file(in_progress_file, "\n".join(pom_paths_str))

projects = []

for file_path in pom_paths:
    project = mvn_utils.create_project(str(file_path))
    projects.append(project)

to_rebuild = []
to_renew_metadata = []

for project in projects:
    build_date = mvn_utils.artifact_build_date(project, MAVEN_REPO_PATH)

    project_src_paths = mvn_utils.get_buildable_paths(project)

    src_modification = file_utils.last_modification(collections.to_strings(project_src_paths))

    if (build_date is None) or (build_date < src_modification):
        six.print_(project, "needs rebuild. Last build update: " + str(build_date))
        to_rebuild.append(project)
    else:
        to_renew_metadata.append(project)

six.print_("Updating local build time for non-changed projects...")
mvn_utils.renew_metadata(to_renew_metadata, MAVEN_REPO_PATH)

six.print_("Rebuilding projects...")
mvn_utils.rebuild(ROOT_PROJECT_PATH, to_rebuild, MVN_OPTS)

file_utils.write_file(in_progress_file, "\n".join(new_in_progress))
