from pathlib import Path
import utils.file_utils as file_utils
import utils.svn_utils as svn_utils
import utils.mvn_utils as mvn_utils
import six
import getopt
import sys
import os.path

try:
    opts, args = getopt.getopt(sys.argv[1:], "r:")
except getopt.GetoptError:
    sys.exit(2)

ROOT_PROJECT_PATH = "."
for opt, arg in opts:
    if opt == '-r':
        ROOT_PROJECT_PATH = arg

ROOT_PROJECT_PATH = file_utils.normalize_path(ROOT_PROJECT_PATH)
six.print_("Root project path: " + ROOT_PROJECT_PATH)

rootPom = Path(ROOT_PROJECT_PATH).joinpath("pom.xml")
if (not rootPom.exists()):
    six.print_("ERROR! No root pom.xml find in path", os.path.abspath(ROOT_PROJECT_PATH))
    sys.exit(1)

MAVEN_REPO_PATH = mvn_utils.repo_path()

changed_files = svn_utils.changed_files(ROOT_PROJECT_PATH)
important_files = filter(lambda file: file.endswith(".java"),
                         changed_files)

pom_paths = set([])
last_updates = {}

for file in important_files:
    path = Path(file)
    parent_path = path.parent

    while (parent_path and (parent_path != ROOT_PROJECT_PATH)):
        pom_path = Path(parent_path).joinpath("pom.xml")

        if (pom_path.exists()):
            pom_paths.add(pom_path)

            jar_update = file_utils.modification_date(file)
            if ((pom_path not in [last_updates]) or (last_updates[pom_path] > jar_update)):
                last_updates[pom_path] = jar_update

            break

        parent_path = parent_path.parent

projects = []
last_projects_updates = {}

for path in pom_paths:
    project = mvn_utils.create_project(str(path))
    projects.append(project)

    last_projects_updates[project] = last_updates[path]

to_rebuild = []

for project in projects:
    artifact_path = mvn_utils.build_artifact_path(project, MAVEN_REPO_PATH)

    if (not artifact_path.exists()):
        six.print_(str(artifact_path), "not exists")
        to_rebuild.append(project)
    else:
        jar_update = file_utils.modification_date(str(artifact_path))
        if (jar_update < last_projects_updates[project]):
            six.print_(project, "needs rebuild")
            to_rebuild.append(project)

six.print_("Rebuilding projects...")
mvn_utils.rebuild(ROOT_PROJECT_PATH, to_rebuild)
