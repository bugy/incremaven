import argparse
import os.path
import sys

import utils.collections as collections
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
print("Root project path: " + ROOT_PROJECT_PATH)
print("Additional maven arguments: " + str(MVN_OPTS))

root_pom_path = os.path.join(ROOT_PROJECT_PATH, "pom.xml")
if not os.path.exists(root_pom_path):
    print("ERROR! No root pom.xml find in path", os.path.abspath(ROOT_PROJECT_PATH))
    sys.exit(1)

MAVEN_REPO_PATH = mvn_utils.repo_path()


def incremental_rebuild(last_revision, current_revision):
    changed_files = svn_utils.get_revision_changed_files(ROOT_PROJECT_PATH, last_revision, current_revision)

    pom_paths = set([])

    for file_path in changed_files:
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

    projects = []

    for pom_path in pom_paths:
        project = mvn_utils.create_project(pom_path)
        projects.append(project)

    print('Rebuilding revision changes (' + last_revision + ';' + current_revision + ']. Changed projects:')
    print('\n'.join(collections.to_strings(projects)))

    mvn_utils.rebuild(ROOT_PROJECT_PATH, projects, MVN_OPTS)


current_revision = svn_utils.get_revision(ROOT_PROJECT_PATH)

info_file_path = os.path.join(ROOT_PROJECT_PATH, "_ci_rebuild.info")
if os.path.exists(info_file_path):
    last_revision = file_utils.read_file(info_file_path).strip()

    if last_revision != current_revision:
        incremental_rebuild(last_revision, current_revision)
    else:
        print("Svn revision is the same. Skipping rebuild")
else:
    print("No previous revision found, rebuilding the whole root project...")
    mvn_utils.rebuild_root(ROOT_PROJECT_PATH, MVN_OPTS)

file_utils.write_file(info_file_path, current_revision)
