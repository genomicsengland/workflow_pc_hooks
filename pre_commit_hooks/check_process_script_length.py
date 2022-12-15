from __future__ import annotations

import argparse

from pre_commit_hooks import util

IGNORE_FLAG = 'check-process-script-length'


def process_file_contents(contents: list, filename: str, max_block_length: int) -> int:
    """
    process a single file and count number of lines in its
    script blocks
    """

    script_blocks = util.isolate_process_scripts(contents)

    retv = 0

    for start, end in script_blocks:

        # start and end are the triple quotes so script length is one less
        # than the difference between these two
        block_length = end - start - 1

        if (
            block_length > max_block_length
            and IGNORE_FLAG not in util.get_ignore_flags_on_line(contents[start - 1])
        ):

            retv |= 1
            print(f'{filename}: script block at {start} is {block_length} lines long')

    return retv


def main(argv: list[str] | None = None) -> int:

    parser = argparse.ArgumentParser()
    parser.add_argument('--max_block_length', type=int)
    parser.add_argument('filenames', nargs='*')
    args = parser.parse_args(argv)

    overall_retcode = 0
    for filename in args.filenames:
        with open(filename, 'r') as inputfile:
            contents = inputfile.readlines()
        retcode = process_file_contents(contents, filename, args.max_block_length)
        overall_retcode |= retcode

    return overall_retcode
