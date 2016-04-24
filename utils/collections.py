def to_strings(value):
    if (isinstance(value, list) or isinstance(value, set)):
        return [str(x) for x in value]

    raise Exception("This collection type is not yet implemented")
