from __future__ import print_function

import copy
import datetime
import os.path
import shutil

import model
import utils.collections as collections
import utils.file_utils as file_utils
import utils.process_utils as process_utils
import utils.xml_utils as xml_utils


class MavenProject(model.Project):
    pom_path = None
    packaging = None
    build_directory = None
    source_folders = None
    artifact_name = None

    def __init__(self, artifact_id, group, version, pom_path):
        model.Project.__init__(self,
                               artifact_id,
                               group,
                               version,
                               os.path.dirname(pom_path))

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

    def set_artifact_name(self, artifact_name):
        self.artifact_name = artifact_name

    def get_artifact_name(self):
        return self.artifact_name


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
                                         "build/testResources/testResource/directory",
                                         "build/finalName"
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

    if xml_values["build/finalName"]:
        artifact_name = xml_values["build/finalName"]
        artifact_name += '.' + project.get_packaging()
    else:
        artifact_name = get_default_artifact_name(project)

    project.set_artifact_name(artifact_name)

    source_folders = collect_source_folders(pom_path, xml_values)
    project.set_source_folders(source_folders)

    return project


def collect_source_folders(pom_path, xml_values):
    source_folders = set()

    def add_source_folder(xpath, def_value):
        value = xml_values[xpath]
        if not value:
            value = def_value

        if isinstance(value, list):
            source_folders.update(value)
        elif value:
            source_folders.add(value)

    add_source_folder('build/sourceDirectory', os.path.join('src', 'main', 'java'))
    add_source_folder('build/testSourceDirectory', os.path.join('src', 'test', 'java'))
    add_source_folder('build/resources/resource/directory', os.path.join('src', 'main', 'resources'))
    add_source_folder('build/testResources/testResource/directory', os.path.join('src', 'test', 'resources'))

    result = [pom_path]
    project_path = os.path.dirname(pom_path)
    for folder in source_folders:
        if not os.path.isabs(folder):
            folder = os.path.join(project_path, folder)

        if os.path.exists(folder):
            result.append(folder)

    return result


def repo_artifact_path(project, repo_path):
    artifact_path = repo_folder_path(project, repo_path)

    artifact_name = get_default_artifact_name(project)

    return os.path.join(artifact_path, artifact_name)


def get_default_artifact_name(project):
    """

    :type project: MavenProject
    """
    package_type = project.get_packaging()

    artifact_name = "{}-{}.{}".format(project.artifact_id, project.version, package_type)

    return artifact_name


def repo_pom_path(project, repo_path):
    artifact_path = repo_folder_path(project, repo_path)

    return os.path.join(artifact_path, "{}-{}.pom".format(project.artifact_id, project.version))


def repo_folder_path(project, repo_path):
    folder_path = repo_path

    sub_folders = project.group.split(".")
    for sub_folder in sub_folders:
        folder_path = os.path.join(folder_path, sub_folder)

    folder_path = os.path.join(folder_path, project.artifact_id)
    folder_path = os.path.join(folder_path, project.version)

    return folder_path


def rebuild(parent_project_path, projects, mvn_opts, silent=True):
    if not projects:
        print("No projects to build, skipping")
        return None

    project_roots = analyze_project_roots(projects)

    levels = None

    if len(set(project_roots.values())) > 1:
        levels = split_by_dependencies(projects, project_roots)
        print("Complex structure detected. Rebuilding in several steps")

        for i in range(0, len(levels)):
            print("Step " + str(i) + ": ")
            print(collections.to_strings(levels[i]))
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

            command = "mvn clean install -f {} {} -pl {}".format(root_path, mvn_opts, project_names_string)
            if silent:
                process_utils.invoke(command, parent_project_path)
            else:
                process_utils.invoke_attached(command, parent_project_path)


def rebuild_root(parent_project_path, mvn_opts, silent=True):
    command = "mvn clean install " + mvn_opts

    if silent:
        process_utils.invoke(command, parent_project_path)
    else:
        process_utils.invoke_attached(command, parent_project_path)


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
        project_roots[project] = get_project_root_path(project.get_path())

    return project_roots


def get_project_root_path(project_path):
    project_root_path = project_path

    while not file_utils.is_root(project_root_path):
        parent_path = os.path.dirname(project_root_path)

        parent_pom_path = os.path.join(parent_path, "pom.xml")
        if not os.path.exists(parent_pom_path):
            break

        sub_modules = read_sub_modules(parent_path)
        if not (os.path.basename(project_root_path) in sub_modules):
            break

        project_root_path = parent_path

    return project_root_path


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
    pom_path = os.path.join(module_path, 'pom.xml')
    modules_info = xml_utils.find_in_file(pom_path, ["modules/module", "profiles/profile"])

    sub_modules = collections.as_list(modules_info["modules/module"])

    if modules_info["profiles/profile"]:
        profiles = collections.as_list(modules_info["profiles/profile"])

        for profile in profiles:
            profile_modules_info = profile.get("modules")

            if (profile.get("activation")
                and profile.get("activation").get("activeByDefault") == "true"
                and profile_modules_info):
                profile_modules = collections.as_list(profile_modules_info["module"])

                sub_modules.extend(profile_modules)

    return sub_modules


def repo_path():
    home = os.path.expanduser("~")
    maven_path = os.path.join(home, ".m2")

    settings_path = os.path.join(maven_path, "settings.xml")
    if os.path.exists(settings_path):
        values = xml_utils.find_in_file(settings_path, ["localRepository"])

        local_repository = values["localRepository"]
        if local_repository is not None:
            local_repository = local_repository.replace("${user.home}", home)
            return local_repository

    return os.path.join(maven_path, "repository")


def requires_archive(project):
    """

    :rtype: MavenProject
    """
    buildable_paths = get_buildable_paths(project)

    for buildable_path in buildable_paths:
        for root, subdirs, files in os.walk(buildable_path):
            if files:
                return True

    return False


def target_build_date(project):
    if not requires_archive(project):
        return datetime.datetime.today()

    target = get_full_build_directory(project)
    target_artifact_path = os.path.join(target, project.get_artifact_name())
    if not os.path.exists(target_artifact_path):
        return None

    return file_utils.modification_date(target_artifact_path)


def get_buildable_paths(project):
    """

    :type project: MavenProject
    """
    return project.get_source_folders()


def renew_metadata(projects, repo_path):
    if not projects:
        return

    now = datetime.datetime.now()
    current_time = datetime.datetime.strftime(now, "%Y%m%d%H%M%S")

    for project in projects:
        project_repo_path = repo_folder_path(project, repo_path)

        metadata_path = os.path.join(project_repo_path, "maven-metadata-local.xml")

        if os.path.exists(metadata_path):
            xml_utils.replace_in_tree(metadata_path, {
                "versioning/lastUpdated": current_time,
                "versioning/snapshotVersions/snapshotVersion/updated": current_time
            })
        else:
            local_metadata = '<metadata modelVersion="1.1.0">' + \
                             '  <groupId>' + project.group + '</groupId>' + \
                             '  <artifactId>' + project.artifact_id + '</artifactId>' + \
                             '  <version>' + project.version + '</version>' + \
                             '  <versioning>' + \
                             '    <snapshot>' + \
                             '      <localCopy>true</localCopy>' + \
                             '    </snapshot>' + \
                             '    <lastUpdated>' + current_time + '</lastUpdated>' + \
                             '    <snapshotVersions>' + \
                             '      <snapshotVersion>' + \
                             '        <extension>pom</extension>' + \
                             '        <value>' + project.version + '</value>' + \
                             '        <updated>' + current_time + '</updated>' + \
                             '      </snapshotVersion>'
            if requires_archive(project):
                local_metadata += '      <snapshotVersion>' + \
                                  '        <extension>' + project.get_packaging() + '</extension>' + \
                                  '        <value>' + project.version + '</value>' + \
                                  '        <updated>' + current_time + '</updated>' + \
                                  '      </snapshotVersion>'
            local_metadata += '    </snapshotVersions>' + \
                              '  </versioning>' + \
                              '</metadata>'
            file_utils.write_file(metadata_path, local_metadata)

def find_module(parent_path, module_name):
    if os.path.exists(os.path.join(parent_path, module_name)):
        return os.path.join(parent_path, module_name)

    for file in os.listdir(parent_path):
        file_path = os.path.join(parent_path, file)

        if not os.path.isdir(file_path):
            continue

        pom_path = os.path.join(file_path, 'pom.xml')
        if not os.path.exists(pom_path):
            continue

        xml_values = xml_utils.find_in_file(pom_path,
                                            ["artifactId"])
        artifact_id = xml_values["artifactId"]
        if artifact_id == module_name:
            return file_path

    return None


def gather_all_poms(root_path, root_only):
    if root_only:
        def gather_children(parent_project_path):
            paths = []

            modules = read_sub_modules(parent_project_path)
            for module in modules:
                module_path = find_module(parent_project_path, module)

                pom_path = os.path.join(module_path, 'pom.xml')
                paths.append(pom_path)
                paths.extend(gather_children(module_path))

            return paths

        result = [os.path.join(root_path, 'pom.xml')]
        result.extend(gather_children(root_path))
        return result

    else:
        result = []

        for root, subdirs, files in os.walk(root_path):
            for file in files:
                if file != 'pom.xml':
                    continue

                pom_path = os.path.join(root, file)
                result.append(pom_path)

        return result


def is_built(project):
    """

    :type project: MavenProject
    """

    if not requires_archive(project):
        return True

    build_directory = get_full_build_directory(project)

    built_artifact_path = os.path.join(build_directory, project.get_artifact_name())

    return os.path.exists(built_artifact_path)


def get_full_build_directory(project):
    build_directory = project.get_build_directory()

    if not os.path.isabs(build_directory):
        build_directory = os.path.join(project.get_path(), build_directory)

    return build_directory


def fast_install(project, repo_path):
    """

    :type project: MavenProject
    :type repo_path: str
    """

    repo_pom = repo_pom_path(project, repo_path)

    file_utils.prepare_folder(os.path.dirname(repo_pom))

    shutil.copyfile(project.get_pom_path(), repo_pom)

    if requires_archive(project):
        build_directory = get_full_build_directory(project)
        built_artifact_path = os.path.join(build_directory, project.get_artifact_name())
        repo_artifact = repo_artifact_path(project, repo_path)

        if (not os.path.exists(repo_artifact)) \
                or (not file_utils.equal(built_artifact_path, repo_artifact)):
            shutil.copyfile(built_artifact_path, repo_artifact)

    renew_metadata([project], repo_path)
