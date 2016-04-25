import datetime
import os.path
import pathlib
import six

import model
import utils.file_utils as file_utils
import utils.process_utils as process_utils
import utils.string_utils as string_utils
import utils.xml_utils as xml_utils


def create_project(pom_path):
    xml_values = xml_utils.find_in_file(pom_path,
                                        ["artifactId",
                                         "version",
                                         "parent/version",
                                         "groupId",
                                         "parent/groupId"])

    artifact_id = xml_values["artifactId"]
    version = xml_values["version"]

    if not version:
        version = xml_values["parent/version"]

    group_id = xml_values["groupId"]
    if not group_id:
        group_id = xml_values["parent/groupId"]

    return model.Project(artifact_id, group_id, version, str(pom_path))


def get_package_type(pom_path):
    values = xml_utils.find_in_file(pom_path, ["packaging"])
    if values["packaging"]:
        return values["packaging"]

    return "jar"


def repo_artifact_path(project, repo_path):
    artifact_path = repo_folder_path(project, repo_path)

    artifact_name = get_artifact_name(project)

    return artifact_path.joinpath(artifact_name)


def get_artifact_name(project):
    package_type = get_package_type(project.get_build_file_path())

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

    project_names = [(":" + project.artifact_id) for project in projects]
    project_names_string = ",".join(project_names)

    process_utils.invoke("mvn clean install {} -pl {}".format(mvn_opts, project_names_string)
                         , parent_project_path)


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
        current_pom_content = file_utils.read_file(str(project.get_build_file_path()))
        if string_utils.differ(built_pom_content, current_pom_content, True):
            return None
        dates.append(datetime.datetime.today())
    else:
        return None

    if requires_archive(project):
        artifact_path = repo_artifact_path(project, repo_path)

        if artifact_path.exists():
            target_info = xml_utils.find_in_file(str(project.get_build_file_path()), ["build/directory"])
            target = target_info["build/directory"]
            if target is None:
                target = "target"

            project_path = pathlib.Path(project.get_build_file_path()).parent
            target_artifact_path = project_path.joinpath(target).joinpath(get_artifact_name(project))
            if (not target_artifact_path.exists()):
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
    pom_path = pathlib.Path(project.get_build_file_path())

    result = [pom_path]

    source_info = xml_utils.find_in_file(str(pom_path), ["build/sourceDirectory",
                                                         "build/testSourceDirectory",
                                                         "build/resources/resource/directory",
                                                         "build/testResources/testResource/directory"])

    source_folders = {"src"}
    for key, value in source_info.items():
        if value is not None:
            if isinstance(value, list):
                source_folders.update(value)
            elif value:
                source_folders.add(value)

    project_path = pom_path.parent
    for source_folder in source_folders:
        if (source_folder != "src") and (source_folder.startswith("src")):
            continue

        source_path = project_path.joinpath(source_folder)
        if source_path.exists():
            result.append(source_path)

    return result
