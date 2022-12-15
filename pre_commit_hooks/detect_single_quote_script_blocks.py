from __future__ import annotations

import argparse
import re

from pre_commit_hooks import util

IGNORE_FLAG = 'detect-single-quote-script-blocks'


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

    script_blocks = util.isolate_process_scripts(contents)

    print(f'{filename}: {len(script_blocks)} script blocks found')

    retv = 0

    for start, end in script_blocks:

        returncode = detect_valid_script_block_type(contents[start], contents[end])

        if returncode == 1 and IGNORE_FLAG not in util.get_ignore_flags_on_line(
            contents[start - 1]
        ):

            retv |= returncode

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
