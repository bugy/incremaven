import os.path

import common
import utils.collections as collections
import utils.file_utils as file_utils
import utils.mvn_utils as mvn_utils
import utils.svn_utils as svn_utils

(ROOT_PROJECT_PATH, MVN_OPTS, ROOT_ONLY) = common.parse_options()
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

    projects = common.to_mvn_projects(pom_paths, ROOT_PROJECT_PATH, ROOT_ONLY)

    print('Rebuilding revision changes (' + last_revision + ';' + current_revision + ']. Changed projects:')
    print('\n'.join(collections.to_strings(projects)))

    mvn_utils.rebuild(ROOT_PROJECT_PATH, projects, MVN_OPTS, silent=False)


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
    mvn_utils.rebuild_root(ROOT_PROJECT_PATH, MVN_OPTS, silent=False)

file_utils.write_file(info_file_path, current_revision)
