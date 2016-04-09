import model
import utils.process_utils as process_utils
import utils.xml_utils as xml_utils
import six
import os.path
import pathlib


def create_project(pom_path):
    xml_values = xml_utils.read_values(pom_path,
                                       ["artifactId",
                                        "version",
                                        "parent/version",
                                        "groupId",
                                        "parent/groupId"])

    artifact_id = xml_values["artifactId"]
    version = xml_values["version"]

    if (not version):
        version = xml_values["parent/version"]

    group_id = xml_values["groupId"]
    if (not group_id):
        group_id = xml_values["parent/groupId"]

    return model.Project(artifact_id, group_id, version)


def build_artifact_path(project, maven_repo_path):
    artifact_path = pathlib.Path(maven_repo_path)

    sub_folders = project.group.split(".")
    for folder in sub_folders:
        artifact_path = artifact_path.joinpath(folder)

    artifact_path = artifact_path.joinpath(project.artifact_id)
    artifact_path = artifact_path.joinpath(project.version)

    return artifact_path.joinpath("{}-{}.jar".format(project.artifact_id, project.version))


def rebuild(parent_project_path, projects):
    if not projects:
        six.print_("No projects to build, skipping")
        return None

    project_names = [(":" + project.artifact_id) for project in projects]
    project_names_string = ",".join(project_names)

    process_utils.invoke("mvn clean install -X -fae -pl {}".format(project_names_string)
                         , parent_project_path)


def repo_path():
    home = os.path.expanduser("~")
    maven_path = pathlib.Path(home).joinpath(".m2")

    settings_path = maven_path.joinpath("settings.xml")
    if (settings_path.exists()):
        values = xml_utils.read_values(str(settings_path), ["localRepository"])

        local_repository = values["localRepository"]
        if (local_repository is not None):
            local_repository = local_repository.replace("${user.home}", home)
            return local_repository

    return str(maven_path.joinpath("repository"))
