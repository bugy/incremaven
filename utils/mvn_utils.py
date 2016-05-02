import copy
import datetime
import os.path
import pathlib

import six

import model
import utils.collections as collections
import utils.file_utils as file_utils
import utils.process_utils as process_utils
import utils.string_utils as string_utils
import utils.xml_utils as xml_utils


class MavenProject(model.Project):
    pom_path = None
    packaging = None
    build_directory = None
    source_folders = None

    def __init__(self, artifact_id, group, version, pom_path):
        model.Project.__init__(self,
                               artifact_id,
                               group,
                               version,
                               str(pathlib.Path(pom_path).parent))

        self.pom_path = pom_path

    def get_pom_path(self):
        return self.pom_path

    def set_packaging(self, value):
        self.packaging = value

    def get_packaging(self):
        return self.packaging

    def get_build_directory(self):
        return self.build_directory

    def set_build_directory(self, value):
        self.build_directory = value

    def get_source_folders(self):
        return self.source_folders

    def set_source_folders(self, value):
        self.source_folders = value


def create_project(pom_path):
    xml_values = xml_utils.find_in_file(pom_path,
                                        ["artifactId",
                                         "version",
                                         "parent/version",
                                         "groupId",
                                         "parent/groupId",
                                         "packaging",
                                         "build/directory",
                                         "build/sourceDirectory",
                                         "build/testSourceDirectory",
                                         "build/resources/resource/directory",
                                         "build/testResources/testResource/directory"
                                         ])

    artifact_id = xml_values["artifactId"]
    version = xml_values["version"]

    if not version:
        version = xml_values["parent/version"]

    group_id = xml_values["groupId"]
    if not group_id:
        group_id = xml_values["parent/groupId"]

    project = MavenProject(artifact_id, group_id, version, pom_path)

    if xml_values["packaging"]:
        project.set_packaging(xml_values["packaging"])
    else:
        project.set_packaging("jar")

    if xml_values["build/directory"]:
        project.set_build_directory(xml_values["build/directory"])
    else:
        project.set_build_directory("target")

    source_folders = collect_source_folders(pom_path,
                                            xml_values["build/sourceDirectory"],
                                            xml_values["build/testSourceDirectory"],
                                            xml_values["build/resources/resource/directory"],
                                            xml_values["build/testResources/testResource/directory"])
    project.set_source_folders(source_folders)

    return project


def collect_source_folders(pom_path, *source_paths):
    result = [pom_path]

    source_folders = {"src"}
    for value in source_paths:
        if value is not None:
            if isinstance(value, list):
                source_folders.update(value)
            elif value:
                source_folders.add(value)

    project_path = pathlib.Path(pom_path).parent
    for source_folder in source_folders:
        if (source_folder != "src") and (source_folder.startswith("src")):
            continue

        source_path = project_path.joinpath(source_folder)
        if source_path.exists():
            result.append(source_path)

    return result


def repo_artifact_path(project, repo_path):
    artifact_path = repo_folder_path(project, repo_path)

    artifact_name = get_artifact_name(project)

    return artifact_path.joinpath(artifact_name)


def get_artifact_name(project):
    """

    :type project: MavenProject
    """
    package_type = project.get_packaging()

    artifact_name = "{}-{}.{}".format(project.artifact_id, project.version, package_type)

    return artifact_name


def repo_pom_path(project, repo_path):
    artifact_path = repo_folder_path(project, repo_path)

    return artifact_path.joinpath("{}-{}.pom".format(project.artifact_id, project.version))


def repo_folder_path(project, repo_path):
    folder_path = pathlib.Path(repo_path)

    sub_folders = project.group.split(".")
    for folder in sub_folders:
        folder_path = folder_path.joinpath(folder)

    folder_path = folder_path.joinpath(project.artifact_id)
    folder_path = folder_path.joinpath(project.version)

    return folder_path


def rebuild(parent_project_path, projects, mvn_opts):
    if not projects:
        six.print_("No projects to build, skipping")
        return None

    project_roots = analyze_project_roots(projects)

    levels = None

    if len(set(project_roots.values())) > 1:
        levels = split_by_dependencies(projects, project_roots)
        six.print_("Complex structure detected. Rebuilding in several steps")

        for i in range(0, len(levels)):
            six.print_("Step " + str(i) + ": ")
            six.print_(collections.to_strings(levels[i]))
    else:
        levels = [project_roots.keys()]

    for level in levels:
        grouped_by_root = {}
        for project in level:
            root = project_roots[project]
            if not (root in grouped_by_root):
                grouped_by_root[root] = []
            grouped_by_root[root].append(project)

        for root_path, child_projects in grouped_by_root.items():
            project_names = [(":" + project.artifact_id) for project in child_projects]
            project_names_string = ",".join(project_names)

            process_utils.invoke(
                "mvn clean install -f {} {} -pl {}".format(root_path, mvn_opts, project_names_string),
                parent_project_path)


def split_by_dependencies(projects, project_roots):
    short_names = {}
    for project in projects:
        short_names[project.group + ":" + project.artifact_id] = project

    project_dependencies = {}
    for project in projects:
        dependencies = get_direct_dependencies(project)

        project_dependencies[project] = []

        for dependency in dependencies:
            short_name = dependency["groupId"] + ":" + dependency["artifactId"]
            if short_name in short_names:
                project_dependencies[project].append(short_names[short_name])
    remaining_projects = copy.copy(projects)

    levels = []
    while remaining_projects:
        current_level = []

        remaining_copy = copy.copy(remaining_projects)
        for project in remaining_copy:
            dependencies = project_dependencies[project]
            if dependencies:
                continue

            current_level.append(project)
            remaining_projects.remove(project)

        if not current_level:
            raise Exception(
                "Couldn't build dependency sequence. Most probably cyclic dependency found in: " + str(
                    remaining_projects))

        next_level_projects = set()

        while True:
            level_changed = False

            remaining_copy = copy.copy(remaining_projects)
            for project in remaining_copy:
                dependencies = project_dependencies[project]

                project_root = project_roots[project]

                dependencies_copy = copy.copy(dependencies)
                for dependency in dependencies_copy:
                    if dependency in current_level:
                        dependencies.remove(dependency)

                    if (not (project in next_level_projects)) and (project_root != project_roots[dependency]):
                        next_level_projects.add(project)

                if not dependencies and not (project in next_level_projects):
                    level_changed = True

                    current_level.append(project)
                    remaining_projects.remove(project)

            if not level_changed:
                break

        levels.append(current_level)

    return levels


def analyze_project_roots(projects):
    project_roots = {}
    for project in projects:
        project_root_path = pathlib.Path(project.get_path())

        while not file_utils.is_root(str(project_root_path)):
            parent = project_root_path.parent

            if not parent.joinpath("pom.xml").exists():
                break

            sub_modules = read_sub_modules(str(parent))
            if not (project_root_path.name in sub_modules):
                break

            project_root_path = parent

        root_path_str = str(project_root_path)
        project_roots[project] = root_path_str
    return project_roots


def get_direct_dependencies(project):
    """

    :type project: MavenProject
    """
    pom_path = project.get_pom_path()
    results = xml_utils.find_in_file(pom_path, ["dependencies/dependency"])
    dependencies = results["dependencies/dependency"]

    if isinstance(dependencies, list):
        return dependencies
    elif dependencies is None:
        return []
    else:
        return [dependencies]


def read_sub_modules(module_path):
    modules_info = xml_utils.find_in_file(module_path + "/pom.xml", ["modules/module"])

    sub_modules = []
    if isinstance(modules_info["modules/module"], list):
        sub_modules.extend(modules_info["modules/module"])
    elif modules_info["modules/module"]:
        sub_modules.append(modules_info["modules/module"])

    return sub_modules


def repo_path():
    home = os.path.expanduser("~")
    maven_path = pathlib.Path(home).joinpath(".m2")

    settings_path = maven_path.joinpath("settings.xml")
    if settings_path.exists():
        values = xml_utils.find_in_file(str(settings_path), ["localRepository"])

        local_repository = values["localRepository"]
        if local_repository is not None:
            local_repository = local_repository.replace("${user.home}", home)
            return local_repository

    return str(maven_path.joinpath("repository"))


def requires_archive(project):
    buildable_paths = get_buildable_paths(project)

    for buildable_path in buildable_paths:
        for root, subdirs, files in os.walk(str(buildable_path)):
            if files:
                return True

    return False


def artifact_build_date(project, repo_path):
    dates = []

    pom_path = repo_pom_path(project, repo_path)
    if pom_path.exists():
        # we need to compare files, since maven just copies pom without changing modification date
        built_pom_content = file_utils.read_file(str(pom_path))
        current_pom_content = file_utils.read_file(str(project.get_pom_path()))
        if string_utils.differ(built_pom_content, current_pom_content, True):
            return None
        dates.append(datetime.datetime.today())
    else:
        return None

    if requires_archive(project):
        artifact_path = repo_artifact_path(project, repo_path)

        if artifact_path.exists():
            target = project.get_build_directory()

            project_path = pathlib.Path(project.get_pom_path()).parent
            target_artifact_path = project_path.joinpath(target).joinpath(get_artifact_name(project))
            if not target_artifact_path.exists():
                return None

            target_date = file_utils.modification_date(str(target_artifact_path))
            repo_date = file_utils.modification_date(str(artifact_path))

            install_time_diff = repo_date - target_date
            if (install_time_diff.seconds > 5) or (install_time_diff.seconds < 0):
                return None

            dates.append(repo_date)
        else:
            return None

    return min(dates)


def get_buildable_paths(project):
    """

    :type project: MavenProject
    """
    return project.get_source_folders()
