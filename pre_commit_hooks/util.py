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
