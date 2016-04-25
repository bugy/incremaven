import xml.etree.ElementTree as ElementTree
import re


def find_in_file(xml_path, x_paths, ignore_namespaces=True):
    tree = ElementTree.parse(xml_path)
    return find_in_tree(tree, x_paths, ignore_namespaces)


def find_in_string(xml_string, x_paths, ignore_namespaces=True):
    tree = ElementTree.fromstring(xml_string)
    return find_in_tree(tree, x_paths, ignore_namespaces)


def find_in_tree(tree, x_paths, ignore_namespaces):
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
            if len(elements) == 1:
                result[x_path] = elements[0].text.strip()
            else:
                result[x_path] = [element.text.strip() for element in elements]
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
