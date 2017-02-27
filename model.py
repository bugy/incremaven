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

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (self.path == other.path) and (self.artifact_id == other.artifact_id)

        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return not self.__eq__(other)

        return NotImplemented

    def __hash__(self):
        return (hash(self.path) * 13) + hash(self.artifact_id)
