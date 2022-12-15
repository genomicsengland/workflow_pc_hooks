from __future__ import annotations

import argparse
import re

from pre_commit_hooks import util

ACCEPTABLE_SHEBANGS = ['bash']
IGNORE_FLAG = 'detect-non-bash-shebangs'


def extract_shebangs(contents: list) -> list:
    """
    extract shebangs from the script
    """

    # matches #! followed by one or more /<word>
    shebang_regex = r'^.*(#!)(/\w+){1,}.*$'

    matches = [res.groups()[1] for x in contents if (res := re.match(shebang_regex, x))]

    return [re.sub(r'^/', '', x) for x in matches]


def process_file_contents(contents: list, filename: str) -> int:
    """
    process a file and all it's script blocks
    """

    script_blocks = util.isolate_process_scripts(contents)

    print(f'{filename}: {len(script_blocks)} script blocks found')

    retv = 0

    for start, end in script_blocks:

        shebangs = extract_shebangs(contents[start : end + 1])

        unacceptable_shebangs = set(shebangs) - set(ACCEPTABLE_SHEBANGS)

        if unacceptable_shebangs and IGNORE_FLAG not in util.get_ignore_flags_on_line(
            contents[start]
        ):

            retv = 1

            for shebang in unacceptable_shebangs:

                print(f'{shebang} shebang in block at line {start + 1}')

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
