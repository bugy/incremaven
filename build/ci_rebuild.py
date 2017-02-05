from __future__ import print_function
import time
import sys
import os.path
import stat
import xml.etree.ElementTree as ElementTree
import re
import datetime
import os
import subprocess
import argparse
import copy
class Project(object):
    version = ""
    artifact_id = ""
    group = ""
    path = None
    def __init__(self, artifact_id, group, version, path):
        self.version = version
        self.artifact_id = artifact_id
        self.group = group
        self.path = path
    def __str__(self):
        return "{}:{}:{}".format(self.group, self.artifact_id, self.version)
    def get_path(self):
        return self.path
def invoke(command, work_dir="."):
    if isinstance(command, str):
        command = command.split()
    shell = (os.name == 'nt')  # on windows commands like mvn won't work without shell
    p = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         cwd=work_dir,
                         shell=shell)
    (output_bytes, error_bytes) = p.communicate()
    output = output_bytes.decode("utf-8")
    error = error_bytes.decode("utf-8")
    result_code = p.returncode
    if result_code != 0:
        message = "Execution failed with exit code " + str(result_code)
        print(message)
        print(output)
        if error:
            print(" --- ERRORS ---:")
            print(error)
        raise Exception(message)
    if error:
        print("WARN! Error output wasn't empty, although the command finished with code 0!")
    return output
def contains_whole_word(text, word):
    pattern = re.compile(r'\b({0})\b'.format(word), flags=re.IGNORECASE)
    search_result = pattern.search(text)
    return search_result is not None
def remove_empty_lines(text):
    lines = text.split("\n")
    filtered_lines = filter(lambda line:
                            line.strip() != '',
                            lines)
    return "\n".join(filtered_lines)
def differ(text1, text2, trim):
    if trim:
        text1 = trim_text(text1)
        text2 = trim_text(text2)
    return text1 != text2
def trim_text(text):
    lines = text.split("\n")
    trimmed_lines = [line.strip() for line in lines]
    trimmed_text = "\n".join(trimmed_lines)
    return remove_empty_lines(trimmed_text)
def find_in_file(xml_path, x_paths, ignore_namespaces=True):
    """
    :type xml_path: str
    :type x_paths: list
    :type ignore_namespaces: bool
    :rtype: dict
    """
    tree = ElementTree.parse(xml_path)
    return find_in_tree(tree, x_paths, ignore_namespaces)
def find_in_string(xml_string, x_paths, ignore_namespaces=True):
    tree = ElementTree.fromstring(xml_string)
    return find_in_tree(tree, x_paths, ignore_namespaces)
def find_in_tree(tree, x_paths, ignore_namespaces):
    elements_dict = gather_elements(tree, x_paths, ignore_namespaces)
    result = {}
    for x_path, elements in elements_dict.items():
        if (elements is not None) and elements:
            if len(elements) == 1:
                result[x_path] = read_element(elements[0])
            else:
                result[x_path] = [read_element(element) for element in elements]
        else:
            result[x_path] = None
    return result
def gather_elements(tree, x_paths, ignore_namespaces):
    root = tree.getroot()
    root_ns = namespace(root)
    ns = {}
    if root_ns and ignore_namespaces:
        ns["x"] = root_ns
    result = {}
    for x_path in x_paths:
        search_path = x_path
        if root_ns and ignore_namespaces:
            search_path = adapt_namespace(x_path, "x")
        elements = root.findall(search_path, ns)
        if (elements is not None) and elements:
            result[x_path] = elements
        else:
            result[x_path] = None
    return result
def read_element(element):
    sub_elements = list(element)
    if len(sub_elements) > 0:
        as_map = {}
        for sub_element in sub_elements:
            key = sub_element.tag
            key = key[key.rfind("}") + 1:]
            value = read_element(sub_element)
            if (key in as_map):
                if isinstance(as_map[key], list):
                    value_list = as_map[key]
                else:
                    value_list = [as_map[key]]
                    as_map[key] = value_list
                value_list.append(value)
            else:
                as_map[key] = value
        return as_map
    else:
        return element.text.strip()
def namespace(element):
    m = re.match('\{(.*)\}', element.tag)
    return m.group(1) if m else ''
def adapt_namespace(x_path, prefix):
    path_elements = x_path.split("/")
    path_elements = [(prefix + ":" + element)
                     for element in path_elements]
    return "/".join(path_elements)
def replace_in_tree(file_path, replace_dict, ignore_namespaces=True):
    tree = ElementTree.parse(file_path)
    elements_dict = gather_elements(tree, replace_dict.keys(), ignore_namespaces)
    for xpath, elements in elements_dict.items():
        if elements is None:
            continue
        value = replace_dict[xpath]
        if isinstance(elements, list):
            for element in elements:
                element.text = value
        else:
            elements.text = value
    tree.write(file_path)
def to_strings(value):
    if isinstance(value, list) or isinstance(value, set):
        return [str(x) for x in value]
    raise Exception("This collection type is not yet implemented")
def as_list(obj):
    result = []
    if isinstance(obj, list):
        result.extend(obj)
    elif not obj is None:
        result.append(obj)
    return result
def modification_date(file_path):
    time_string = time.ctime(os.path.getmtime(file_path))
    return datetime.datetime.strptime(time_string, "%a %b %d %H:%M:%S %Y")
def deletion_date(file_path):
    path = file_path
    while not os.path.exists(path):
        path = os.path.dirname(path)
        if is_root(path):
            raise Exception("Couldn't find parent folder for the deleted file " + file_path)
    return modification_date(path)
def is_root(path):
    return os.path.dirname(path) == path
def normalize_path(path_string):
    result = os.path.expanduser(path_string)
    if os.path.isabs(result):
        return result
    return os.path.abspath(result)
def read_file(filename):
    path = normalize_path(filename)
    file_content = ""
    with open(path, "r") as f:
        file_content += f.read()
    return file_content
def write_file(filename, content):
    path = normalize_path(filename)
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    with open(path, "w") as file:
        file.write(content)
def make_executable(filename):
    st = os.stat(filename)
    os.chmod(filename, st.st_mode | stat.S_IEXEC)
def exists(filename):
    path = normalize_path(filename)
    return os.path.exists(path)
def last_modification(folder_paths):
    result = None
    for root_folder_path in folder_paths:
        file_date = modification_date(root_folder_path)
        if (result is None) or (result < file_date):
            result = file_date
        for root, subdirs, files in os.walk(root_folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_date = modification_date(file_path)
                if (result is None) or (result < file_date):
                    result = file_date
            for folder in subdirs:
                folder_path = os.path.join(root, folder)
                folder_date = modification_date(folder_path)
                if (result is None) or (result < folder_date):
                    result = folder_date
    return result
class MavenProject(Project):
    pom_path = None
    packaging = None
    build_directory = None
    source_folders = None
    def __init__(self, artifact_id, group, version, pom_path):
        Project.__init__(self,
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
def create_project(pom_path):
    xml_values = find_in_file(pom_path,
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
    project_path = os.path.dirname(pom_path)
    for source_folder in source_folders:
        if (source_folder != "src") and (source_folder.startswith("src")):
            continue
        source_path = os.path.join(project_path, source_folder)
        if os.path.exists(source_path):
            result.append(source_path)
    return result
def repo_artifact_path(project, repo_path):
    artifact_path = repo_folder_path(project, repo_path)
    artifact_name = get_artifact_name(project)
    return os.path.join(artifact_path, artifact_name)
def get_artifact_name(project):
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
def rebuild(parent_project_path, projects, mvn_opts):
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
            print(to_strings(levels[i]))
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
            invoke(
                "mvn clean install -f {} {} -pl {}".format(root_path, mvn_opts, project_names_string),
                parent_project_path)
def rebuild_root(parent_project_path, mvn_opts):
    invoke(
        "mvn clean install " + mvn_opts,
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
        project_root_path = project.get_path()
        while not is_root(project_root_path):
            parent_path = os.path.dirname(project_root_path)
            parent_pom_path = os.path.join(parent_path, "pom.xml")
            if not os.path.exists(parent_pom_path):
                break
            sub_modules = read_sub_modules(parent_path)
            if not (os.path.basename(project_root_path) in sub_modules):
                break
            project_root_path = parent_path
        root_path_str = project_root_path
        project_roots[project] = root_path_str
    return project_roots
def get_direct_dependencies(project):
    """
    :type project: MavenProject
    """
    pom_path = project.get_pom_path()
    results = find_in_file(pom_path, ["dependencies/dependency"])
    dependencies = results["dependencies/dependency"]
    if isinstance(dependencies, list):
        return dependencies
    elif dependencies is None:
        return []
    else:
        return [dependencies]
def read_sub_modules(module_path):
    pom_path = os.path.join(module_path, 'pom.xml')
    modules_info = find_in_file(pom_path, ["modules/module", "profiles/profile"])
    sub_modules = as_list(modules_info["modules/module"])
    if modules_info["profiles/profile"]:
        profiles = as_list(modules_info["profiles/profile"])
        for profile in profiles:
            profile_modules_info = profile.get("modules")
            if (profile.get("activation")
                and profile.get("activation").get("activeByDefault") == "true"
                and profile_modules_info):
                profile_modules = as_list(profile_modules_info["module"])
                sub_modules.extend(profile_modules)
    return sub_modules
def repo_path():
    home = os.path.expanduser("~")
    maven_path = os.path.join(home, ".m2")
    settings_path = os.path.join(maven_path, "settings.xml")
    if os.path.exists(settings_path):
        values = find_in_file(settings_path, ["localRepository"])
        local_repository = values["localRepository"]
        if local_repository is not None:
            local_repository = local_repository.replace("${user.home}", home)
            return local_repository
    return os.path.join(maven_path, "repository")
def requires_archive(project):
    buildable_paths = get_buildable_paths(project)
    for buildable_path in buildable_paths:
        for root, subdirs, files in os.walk(buildable_path):
            if files:
                return True
    return False
def artifact_build_date(project, repo_path):
    dates = []
    pom_path = repo_pom_path(project, repo_path)
    if os.path.exists(pom_path):
        # we need to compare files, since maven just copies pom without changing modification date
        built_pom_content = read_file(pom_path)
        current_pom_content = read_file(project.get_pom_path())
        if differ(built_pom_content, current_pom_content, True):
            return None
        dates.append(datetime.datetime.today())
    else:
        return None
    if requires_archive(project):
        artifact_path = repo_artifact_path(project, repo_path)
        if os.path.exists(artifact_path):
            target = project.get_build_directory()
            project_path = os.path.dirname(project.get_pom_path())
            target_artifact_path = os.path.join(project_path, target, get_artifact_name(project))
            if not os.path.exists(target_artifact_path):
                return None
            target_date = modification_date(target_artifact_path)
            repo_date = modification_date(artifact_path)
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
def renew_metadata(projects, repo_path):
    if not projects:
        return
    now = datetime.datetime.now()
    current_time = datetime.datetime.strftime(now, "%Y%m%d%H%M%S")
    for project in projects:
        project_repo_path = repo_folder_path(project, repo_path)
        metadata_path = os.path.join(project_repo_path, "maven-metadata-local.xml")
        if os.path.exists(metadata_path):
            replace_in_tree(metadata_path, {
                "versioning/lastUpdated": current_time,
                "versioning/snapshotVersions/snapshotVersion/updated": current_time
            })
def get_local_changed_files(abs_path):
    status_info = invoke(["svn", "status", abs_path])
    all_lines = status_info.split("\n")
    return svn_status_to_files(all_lines)
def svn_status_to_files(all_lines, ignore_moved_source=True):
    result = []
    for line in all_lines:
        if ignore_moved_source and line.strip().startswith("> moved"):
            continue
        if os.name != 'nt':
            if not ('/' in line):
                continue
            file_path = line[line.index("/"):]
        else:
            if not ('\\' in line):
                continue
            file_path = line[line.index(':\\') - 1:]
        result.append(file_path)
    return result
def get_revision_changed_files(abs_path, from_revision, to_revision):
    changed_files = invoke(
        ['svn', 'diff', '--summarize', '-r' + from_revision + ':' + to_revision, abs_path])
    lines = changed_files.split('\n')
    return svn_status_to_files(lines, False)
def get_revision(project_path):
    svn_info = invoke(['svn', 'info', project_path])
    info_lines = svn_info.split('\n')
    revision_prefix = 'Revision: '
    for line in info_lines:
        if line.startswith(revision_prefix):
            return line[len(revision_prefix):]
    raise Exception("Couldn't get svn revision in " + project_path)
parser = argparse.ArgumentParser(description="Rebuild of complex (maven) projects.")
parser.add_argument("-r", "--rootPath", help="path to the root project", default=".")
parser.add_argument("-m", "--maven", help="maven parameters to pass to mvn command", default="")
args = vars(parser.parse_args())
if args["rootPath"]:
    ROOT_PROJECT_PATH = args["rootPath"]
else:
    ROOT_PROJECT_PATH = "."
MVN_OPTS = args["maven"]
ROOT_PROJECT_PATH = normalize_path(ROOT_PROJECT_PATH)
print("Root project path: " + ROOT_PROJECT_PATH)
print("Additional maven arguments: " + str(MVN_OPTS))
root_pom_path = os.path.join(ROOT_PROJECT_PATH, "pom.xml")
if not os.path.exists(root_pom_path):
    print("ERROR! No root pom.xml find in path", os.path.abspath(ROOT_PROJECT_PATH))
    sys.exit(1)
MAVEN_REPO_PATH = repo_path()
def incremental_rebuild(last_revision, current_revision):
    changed_files = get_revision_changed_files(ROOT_PROJECT_PATH, last_revision, current_revision)
    pom_paths = set([])
    for file_path in changed_files:
        file_path = normalize_path(file_path)
        if os.path.isdir(file_path):
            parent_path = file_path
        else:
            parent_path = os.path.dirname(file_path)
        while parent_path and not (is_root(parent_path)):
            pom_path = os.path.join(parent_path, "pom.xml")
            if os.path.exists(pom_path):
                pom_paths.add(pom_path)
                break
            if parent_path == ROOT_PROJECT_PATH:
                break
            parent_path = os.path.dirname(parent_path)
    projects = []
    for pom_path in pom_paths:
        project = create_project(pom_path)
        projects.append(project)
    print('Rebuilding revision changes (' + last_revision + ';' + current_revision + ']. Changed projects:')
    print('\n'.join(to_strings(projects)))
    rebuild(ROOT_PROJECT_PATH, projects, MVN_OPTS)
current_revision = get_revision(ROOT_PROJECT_PATH)
info_file_path = os.path.join(ROOT_PROJECT_PATH, "_ci_rebuild.info")
if os.path.exists(info_file_path):
    last_revision = read_file(info_file_path).strip()
    if last_revision != current_revision:
        incremental_rebuild(last_revision, current_revision)
    else:
        print("Svn revision is the same. Skipping rebuild")
else:
    print("No previous revision found, rebuilding the whole root project...")
    rebuild_root(ROOT_PROJECT_PATH, MVN_OPTS)
write_file(info_file_path, current_revision)