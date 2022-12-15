from __future__ import annotations

import re


def isolate_process_scripts(contents: list[str]) -> list[str]:
    """
    isolates the process scripts from within the flow
    """

    regexs = [
        ('process', r'^\s*process \w+ {'),
        ('script', r'^\s*(script|shell|exec):'),
        ('start_block', r'^.*("""|\'\'\').*$'),
        ('end_block', r'^.*("""|\'\'\').*$'),
    ]

    # find the process blocks
    bits = []
    regex_index = 0
    current_search = regexs[regex_index]
    for i, l in enumerate(contents):
        if re.match(current_search[1], l):
            if current_search[0] == 'start_block':
                start_of_this_block = i
            elif current_search[0] == 'end_block':
                bits.append((start_of_this_block, i))
            regex_index += 1
            current_search = regexs[regex_index % len(regexs)]

    return bits


def get_ignore_flags_on_line(line: str) -> list[str]:
    """
    get the flags being pass as ignore arguments on a line
    """

    ignore_regex = r'#ignore: ([\w\- ]+)'

    res = re.search(ignore_regex, line)

    if res:

        return [x for x in re.split(' +', res.group(1).strip())]

    else:

        return []
