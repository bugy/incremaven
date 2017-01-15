import argparse
import os.path
import six
import sys

import utils.file_utils as file_utils
import utils.mvn_utils as mvn_utils
import utils.svn_utils as svn_utils

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

root_pom_path = os.path.join(ROOT_PROJECT_PATH, "pom.xml")
if not os.path.exists(root_pom_path):
    six.print_("ERROR! No root pom.xml find in path", os.path.abspath(ROOT_PROJECT_PATH))
    sys.exit(1)

MAVEN_REPO_PATH = mvn_utils.repo_path()


def is_important(file_path):
    return not file_path.endswith(".iml")


def get_unique_name(root_project_path):
    if os.name == 'nt':
        result = root_project_path.replace('\\', "_")
    else:
        result = root_project_path.replace('/', "_")

    result = result.replace(":", "_")
    return result


changed_files = svn_utils.changed_files(ROOT_PROJECT_PATH)
important_files = filter(is_important, changed_files)

pom_paths = set([])

for file_path in important_files:
    file_path = file_utils.normalize_path(file_path)

    if os.path.isdir(file_path):
        parent_path = file_path
    else:
        parent_path = os.path.dirname(file_path)

    while parent_path and not (file_utils.is_root(parent_path)):
        pom_path = os.path.join(parent_path, "pom.xml")

        if os.path.exists(pom_path):
            pom_paths.add(pom_path)
            break

        if parent_path == ROOT_PROJECT_PATH:
            break

        parent_path = os.path.dirname(parent_path)

new_in_progress = set(pom_paths)

home_folder = os.path.expanduser('~')
unique_name = get_unique_name(ROOT_PROJECT_PATH)
in_progress_file = os.path.join(home_folder, '.rebuilder', unique_name)

prev_in_progress = []
if os.path.exists(in_progress_file):
    prev_in_progress = file_utils.read_file(in_progress_file).split("\n")
    prev_in_progress = filter(lambda line: line != "", prev_in_progress)

for pom_path in prev_in_progress:
    if os.path.exists(pom_path):
        pom_paths.add(pom_path)

file_utils.write_file(in_progress_file, "\n".join(pom_paths))

projects = []

for pom_path in pom_paths:
    project = mvn_utils.create_project(pom_path)
    projects.append(project)

to_rebuild = []
to_renew_metadata = []

for project in projects:
    build_date = mvn_utils.artifact_build_date(project, MAVEN_REPO_PATH)

    project_src_paths = mvn_utils.get_buildable_paths(project)

    src_modification = file_utils.last_modification(project_src_paths)

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
