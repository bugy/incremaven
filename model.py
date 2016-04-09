class Project(object):
    version = ""
    artifact_id = ""
    group = ""

    def __init__(self, artifact_id, group, version):
        self.version = version
        self.artifact_id = artifact_id
        self.group = group

    def __str__(self):
        return "{}:{}:{}".format(self.group, self.artifact_id, self.version)
