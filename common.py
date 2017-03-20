import argparse
import os.path
import sys

import utils.file_utils as file_utils
import utils.git_utils as git_utils
import utils.mvn_utils as mvn_utils
import utils.svn_utils as svn_utils


def parse_options():
    parser = argparse.ArgumentParser(description="Rebuild of complex maven projects.")
    parser.add_argument("-r", "--root_path", help="path to the root project", default=".")
    parser.add_argument("-m", "--maven", help="maven parameters to pass to mvn command", default="")
    parser.add_argument("-o", "--root_only", help="skip projects, which are not submodules of root project hierarchy",
                        action='store_true')
    parser.add_argument("-t", "--track_unversioned", help="also consider local changes in unversioned files",
                        action='store_true')
    parser.add_argument("-c", "--vcs", help="version control system", choices=['svn', 'git'])
    args = vars(parser.parse_args())

    if args["root_path"]:
        root_project_path = args["root_path"]
    else:
        root_project_path = "."

    mvn_opts = args["maven"]

    root_only = args["root_only"]
    track_unversioned = args["track_unversioned"]

    root_project_path = file_utils.normalize_path(root_project_path)
    print("Root project path: " + root_project_path)
    print("Additional maven arguments: " + str(mvn_opts))

    root_pom_path = os.path.join(root_project_path, "pom.xml")
    if not os.path.exists(root_pom_path):
        print("ERROR! No root pom.xml find in path", os.path.abspath(root_project_path))
        sys.exit(1)

    if args['vcs']:
        if args['vcs'] == 'git':
            vcs_gateway = git_utils.GitGateway()
        else:
            vcs_gateway = svn_utils.SvnGateway()
    else:
        if svn_utils.is_svn_repo(root_project_path):
            vcs_gateway = svn_utils.SvnGateway()
        elif git_utils.is_git_repo(root_project_path):
            vcs_gateway = git_utils.GitGateway()
        else:
            print("Couldn't resolve VCS type, please specify it explicitly using -c argument")
            sys.exit(-1)

    return (root_project_path, mvn_opts, root_only, track_unversioned, vcs_gateway)


def to_mvn_projects(pom_paths, root_path, root_only):
    projects = []

    for pom_path in pom_paths:
        if root_only:
            project_path = os.path.dirname(pom_path)
            project_root_path = mvn_utils.get_project_root_path(project_path)
            if project_root_path != root_path:
                project_relative_path = os.path.relpath(project_path, root_path)
                print(project_relative_path + ' is not in root hierarchy. Skipping...')
                continue

        project = mvn_utils.create_project(pom_path)
        projects.append(project)

    return projects
