# This script assembles all the scripts (build.py and its local imports)
# to a single file build/rebuild.py

import pathlib

import utils.file_utils as file_utils
import utils.string_utils as string_utils


def get_import_lines(file_content):
    file_lines = file_content.split("\n")
    return filter(lambda line: string_utils.contains_whole_word(line, "import"),
                  file_lines)


def read_new_content(existing_content, imported_files):
    import_lines = get_import_lines(existing_content)
    additional_content = ""
    updated_existing_content = existing_content

    for import_line in import_lines:
        if not import_line.startswith("import"):
            # from imports are not supported
            continue

        words = import_line.split(" ")
        import_name = words[1]
        import_path = import_name.replace(".", "/") + ".py"
        path = pathlib.Path(import_path)
        if not path.exists():
            continue

        alias = import_name
        if (len(words) == 4) and words[2] and (words[2] == "as"):
            alias = words[3]

        updated_existing_content = updated_existing_content.replace(import_line, "")
        updated_existing_content = updated_existing_content.replace(alias + ".", "")

        if not (import_name in imported_files):
            imported_files.append(import_name)
            additional_content += file_utils.read_file(import_path) + "\n"

    return updated_existing_content, additional_content


def optimize_imports(assembled_content):
    result = assembled_content

    import_lines = set(get_import_lines(assembled_content))
    for import_line in import_lines:
        result = result.replace(import_line + "\n", "")

    result = "\n".join(import_lines) + "\n" + result
    return result


build_file_content = file_utils.read_file("build.py")
imported_files = ["build"]

assembled_content = ""

next_content = build_file_content
while next_content:
    (processed_content, next_content) = read_new_content(next_content, imported_files)
    assembled_content = processed_content + "\n" + assembled_content

assembled_content = optimize_imports(assembled_content)
assembled_content = string_utils.remove_empty_lines(assembled_content)

file_utils.write_file("build/rebuild.py", assembled_content)
file_utils.make_executable("build/rebuild.py")
