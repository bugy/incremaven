import re


def contains_whole_word(text, word):
    compile = re.compile(r'\b({0})\b'.format(word), flags=re.IGNORECASE)
    search_result = compile.search(text)
    return search_result is not None


def remove_empty_lines(text):
    lines = text.split("\n")
    filtered_lines = filter(lambda line:
                            line.strip() != '',
                            lines)
    return "\n".join(filtered_lines)
