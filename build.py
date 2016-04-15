import argparse
import os.path
import six
import sys
from pathlib import Path

import utils.file_utils as file_utils
import utils.mvn_utils as mvn_utils
import utils.svn_utils as svn_utils

parser = argparse.ArgumentParser(description="Smart build of complex (maven) projects.")
parser.add_argument("-r", "--rootPath", help="path to the root project", default=".")
parser.add_argument("-m", "--maven", help="maven parameters to pass to mvn command", default="")
args = vars(parser.parse_args())

if (args["rootPath"]):
    ROOT_PROJECT_PATH = args["rootPath"]

MVN_OPTS = args["maven"]

ROOT_PROJECT_PATH = file_utils.normalize_path(ROOT_PROJECT_PATH)
six.print_("Root project path: " + ROOT_PROJECT_PATH)
six.print_("Additional maven arguments: " + str(MVN_OPTS))

rootPom = Path(ROOT_PROJECT_PATH).joinpath("pom.xml")
if (not rootPom.exists()):
    six.print_("ERROR! No root pom.xml find in path", os.path.abspath(ROOT_PROJECT_PATH))
    sys.exit(1)

MAVEN_REPO_PATH = mvn_utils.repo_path()


def is_important(file_path):
    return (file_path.endswith(".java") or file_path.endswith("pom.xml"))


changed_files = svn_utils.changed_files(ROOT_PROJECT_PATH)
important_files = filter(is_important, changed_files)

pom_paths = set([])
last_updates = {}
no_jar_required_poms = []

for file in important_files:
    path = Path(file)
    parent_path = path.parent

    while (parent_path and (parent_path != ROOT_PROJECT_PATH)):
        pom_path = Path(parent_path).joinpath("pom.xml")

        if (pom_path.exists()):
            pom_paths.add(pom_path)

            if (file.endswith("pom.xml") and (pom_path not in last_updates)):
                if (not mvn_utils.requires_jar(str(pom_path))):
                    no_jar_required_poms.append(pom_path)

            file_update = None
            if (not changed_files[file]):
                file_update = file_utils.modification_date(file)
            else:
                file_update = file_utils.deletion_date(file)

            six.print_("{} | modified: {}".format(file, file_update))

            if ((pom_path not in last_updates) or (last_updates[pom_path] < file_update)):
                last_updates[pom_path] = file_update

            break

        parent_path = parent_path.parent

projects = []
last_projects_updates = {}
only_pom_projects = []

for path in pom_paths:
    project = mvn_utils.create_project(str(path))
    projects.append(project)

    last_projects_updates[project] = last_updates[path]

    if (path in no_jar_required_poms):
        only_pom_projects.append(project)

to_rebuild = []

for project in projects:
    only_pom = (project in only_pom_projects)
    build_date = mvn_utils.artifact_build_date(project, MAVEN_REPO_PATH, only_pom)

    if ((build_date is None) or (build_date < last_projects_updates[project])):
        six.print_(project, "needs rebuild. Last update: " + str(build_date))
        to_rebuild.append(project)

six.print_("Rebuilding projects...")
mvn_utils.rebuild(ROOT_PROJECT_PATH, to_rebuild, MVN_OPTS)
