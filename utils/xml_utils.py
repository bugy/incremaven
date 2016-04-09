import xml.etree.ElementTree as ElementTree
import re


def read_values(xml_path, x_paths, ignore_namespaces=True):
    ns = {}

    tree = ElementTree.parse(xml_path)
    root = tree.getroot()
    root_ns = namespace(root)

    if root_ns and ignore_namespaces:
        ns["x"] = root_ns

    result = {}

    for x_path in x_paths:
        search_path = x_path

        if (root_ns and ignore_namespaces):
            search_path = adapt_namespace(x_path, "x")

        element = root.find(search_path, ns)
        if (element is not None):
            result[x_path] = element.text.strip()
        else:
            result[x_path] = None

    return result


def namespace(element):
    m = re.match('\{(.*)\}', element.tag)
    return m.group(1) if m else ''


def adapt_namespace(x_path, prefix):
    path_elements = x_path.split("/")
    path_elements = [(prefix + ":" + element)
                     for element in path_elements]

    return "/".join(path_elements)
