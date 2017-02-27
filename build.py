from __future__ import print_function

import os.path

import utils.file_utils as file_utils
import utils.mvn_utils as mvn_utils
import utils.svn_utils as svn_utils
import common

(ROOT_PROJECT_PATH, MVN_OPTS, ROOT_ONLY) = common.parse_options()
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


changed_files = svn_utils.get_local_changed_files(ROOT_PROJECT_PATH)
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

projects = common.to_mvn_projects(pom_paths, ROOT_PROJECT_PATH, ROOT_ONLY)

to_rebuild = []
to_install = []

for project in projects:
    build_date = mvn_utils.target_build_date(project)
    if build_date is None:
        print(str(project) + ' needs rebuild. Artifact is missing in target')
        to_rebuild.append(project)
        continue

    project_src_paths = mvn_utils.get_buildable_paths(project)
    src_modification = file_utils.last_modification(project_src_paths)

    if build_date < src_modification:
        print(str(project) + ' needs rebuild. Last build update: ' + str(build_date))
        to_rebuild.append(project)
    else:
        to_install.append(project)

print('Installing non-changed artifacts to local repository...')
for project in to_install:
    mvn_utils.fast_install(project, MAVEN_REPO_PATH)

print('Rebuilding projects...')
mvn_utils.rebuild(ROOT_PROJECT_PATH, to_rebuild, MVN_OPTS)

file_utils.write_file(in_progress_file, '\n'.join(new_in_progress))
