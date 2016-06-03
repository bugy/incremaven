import re
import xml.etree.ElementTree as ElementTree


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
                result[x_path] = read_element(elements[0])
            else:
                result[x_path] = [read_element(element) for element in elements]
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
