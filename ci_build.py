#!/usr/bin/env python

import os.path

import sys

import common
import utils.collections as collections
import utils.file_utils as file_utils
import utils.mvn_utils as mvn_utils

(ROOT_PROJECT_PATH, MAVEN_REPO_PATH, MVN_OPTS, ROOT_ONLY, track_unversioned, vcs_gateway) = common.parse_options()


def incremental_rebuild(last_revision, current_revision):
    changed_files = vcs_gateway.get_revision_changed_files(ROOT_PROJECT_PATH, last_revision, current_revision)

    changed_project_poms = set([])

    for file_path in changed_files:
        file_path = file_utils.normalize_path(file_path)

        if os.path.isdir(file_path):
            parent_path = file_path
        else:
            parent_path = os.path.dirname(file_path)

        while parent_path and not (file_utils.is_root(parent_path)):
            pom_path = os.path.join(parent_path, "pom.xml")

            if os.path.exists(pom_path):
                changed_project_poms.add(pom_path)
                break

            if parent_path == ROOT_PROJECT_PATH:
                break

            parent_path = os.path.dirname(parent_path)

    changed_projects = common.to_mvn_projects(changed_project_poms, ROOT_PROJECT_PATH, ROOT_ONLY)

    print('Rebuilding revision changes (' + last_revision + ';' + current_revision + ']. Changed projects:')
    print('\n'.join(collections.to_strings(changed_projects)))

    all_poms = mvn_utils.gather_all_poms(ROOT_PROJECT_PATH, ROOT_ONLY)
    unchanged_project_poms = []
    for pom_path in all_poms:
        if pom_path in changed_project_poms:
            continue

        unchanged_project_poms.append(pom_path)

    for pom_path in unchanged_project_poms:
        unchanged_project = mvn_utils.create_project(pom_path)

        if not mvn_utils.is_built(unchanged_project):
            print('project ' + str(unchanged_project) + ' was cleaned, sending to rebuild')
            changed_projects.append(unchanged_project)
            continue

        mvn_utils.fast_install(unchanged_project, MAVEN_REPO_PATH)

    mvn_utils.rebuild(ROOT_PROJECT_PATH, changed_projects, MVN_OPTS, silent=False)


current_revision = vcs_gateway.get_revision(ROOT_PROJECT_PATH)

info_file_path = os.path.join(ROOT_PROJECT_PATH, "_ci_rebuild.info")
if os.path.exists(info_file_path):
    last_revision = file_utils.read_file(info_file_path).strip()

    if last_revision != current_revision:
        try:
            incremental_rebuild(last_revision, current_revision)
        except mvn_utils.IncorrectConfigException as e:
            print('ERROR! {}'.format(e))
            sys.exit(-1)
    else:
        print("Svn revision is the same. Skipping rebuild")
else:
    print("No previous revision found, rebuilding the whole root project...")
    mvn_utils.rebuild_root(ROOT_PROJECT_PATH, MVN_OPTS, silent=False)

file_utils.write_file(info_file_path, current_revision)
