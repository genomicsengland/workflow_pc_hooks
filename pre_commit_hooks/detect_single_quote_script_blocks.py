from __future__ import annotations

import argparse
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


def detect_valid_script_block_type(start_line: str, end_line: str) -> int:
    """
    detect whether the script block is a single quote (invalid) or double quote (valid)
    block
    """

    valid = r'^.*""".*$'

    if re.match(valid, start_line) and re.match(valid, end_line):

        return 0

    else:

        return 1


def process_file_contents(contents: list, filename: str) -> int:
    """
    process a file and all it's script blocks
    """

    script_blocks = isolate_process_scripts(contents)

    print(f'{filename}: {len(script_blocks)} script blocks found')

    retv = 0

    for start, end in script_blocks:

        returncode = detect_valid_script_block_type(contents[start], contents[end])

        retv |= returncode

        if returncode == 1:

            print(f'single quote script block at lines {start + 1}:{end + 1}')

    return retv


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='*')
    args = parser.parse_args(argv)

    overall_retcode = 0
    for filename in args.filenames:
        with open(filename, 'r') as inputfile:
            contents = inputfile.readlines()
        retcode = process_file_contents(contents, filename)
        overall_retcode |= retcode

    return overall_retcode
