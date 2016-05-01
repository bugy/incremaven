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
