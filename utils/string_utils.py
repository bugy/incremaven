import re

import sys


def contains_whole_word(text, word):
    pattern = re.compile(r'\b({0})\b'.format(word), flags=re.IGNORECASE)
    search_result = pattern.search(text)
    return search_result is not None


def remove_empty_lines(text):
    lines = text.split("\n")
    filtered_lines = filter(lambda line:
                            line.strip() != '',
                            lines)
    return "\n".join(filtered_lines)


def differ(text1, text2, trim):
    if trim:
        text1 = trim_text(text1)
        text2 = trim_text(text2)

    return text1 != text2


def trim_text(text):
    lines = text.split("\n")
    trimmed_lines = [line.strip() for line in lines]
    trimmed_text = "\n".join(trimmed_lines)

    return remove_empty_lines(trimmed_text)


def utf_to_stdout(utf_string):
    if (sys.stdout.encoding is not None) and (sys.stdout.encoding != 'utf-8'):
        return utf_string.encode('utf').decode(sys.stdout.encoding, 'replace')

    return utf_string
