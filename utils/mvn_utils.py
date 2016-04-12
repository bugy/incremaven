import model
import utils.process_utils as process_utils
import utils.xml_utils as xml_utils
import utils.file_utils as file_utils
import utils.string_utils as string_utils
import six
import os.path
import pathlib
import filecmp
import datetime

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

    return model.Project(artifact_id, group_id, version, str(pom_path))


def repo_artifact_path(project, repo_path):
    artifact_path = repo_folder_path(project, repo_path)

    return artifact_path.joinpath("{}-{}.jar".format(project.artifact_id, project.version))
    
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
    if (settings_path.exists()):
        values = xml_utils.read_values(str(settings_path), ["localRepository"])

        local_repository = values["localRepository"]
        if (local_repository is not None):
            local_repository = local_repository.replace("${user.home}", home)
            return local_repository

    return str(maven_path.joinpath("repository"))
    
def requires_jar(pom_path):
    project_path = pathlib.Path(pom_path).parent
    sources_path = project_path.joinpath("src")
    if (sources_path.exists()):
        for root, subdirs, files in os.walk(str(sources_path)):
            return files == []
    return False
    
def artifact_build_date(project, repo_path, only_pom):
    pom_path = repo_pom_path(project, repo_path)
    if (not pom_path.exists()):
        return None
    else:
        built_pom_content = file_utils.read_file(str(pom_path))
        current_pom_content = file_utils.read_file(str(project.get_build_file_path()))
        if (string_utils.differ(built_pom_content, current_pom_content, True)):
            return None
            
    if (only_pom):
        return datetime.datetime.today() 
    
    artifact_path = repo_artifact_path(project, repo_path)
    if (artifact_path.exists()):
        min_date = file_utils.modification_date(str(artifact_path))
    else:
        return None
            
    return min_date
