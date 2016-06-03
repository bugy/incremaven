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
