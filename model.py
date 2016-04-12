class Project(object):
    version = ""
    artifact_id = ""
    group = ""
    build_file_path = ""

    def __init__(self, artifact_id, group, version, build_file_path):
        self.version = version
        self.artifact_id = artifact_id
        self.group = group
        self.build_file_path = build_file_path

    def __str__(self):
        return "{}:{}:{}".format(self.group, self.artifact_id, self.version)
        
    def get_build_file_path(self):
        return self.build_file_path
