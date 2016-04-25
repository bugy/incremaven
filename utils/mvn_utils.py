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

    package_type = get_package_type(project.get_build_file_path())

    return artifact_path.joinpath("{}-{}.{}".format(project.artifact_id, project.version, package_type))


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


def requires_archive(pom_path):
    project_path = pathlib.Path(pom_path).parent
    sources_path = project_path.joinpath("src")
    if sources_path.exists():
        for root, subdirs, files in os.walk(str(sources_path)):
            return files == []
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

    if requires_archive(project.build_file_path):
        artifact_path = repo_artifact_path(project, repo_path)
        if artifact_path.exists():
            dates.append(file_utils.modification_date(str(artifact_path)))
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
