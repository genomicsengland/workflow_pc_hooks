from __future__ import annotations

import argparse
import re
import subprocess
import tempfile

from pre_commit_hooks import util

IGNORE_FLAG = 'check-process-script-syntax'


def extract_script(contents: list, start: int, end: int) -> str:
    """
    extract script block from the lines given
    """

    clean = contents[start : end + 1]
    clean[0] = re.sub('"""', '', clean[0])  # remove triple quotes
    clean[-1] = re.sub('"""', '', clean[-1])  # remove triple quotes
    clean = [x.lstrip() for x in clean]  # unindent
    clean = [x.replace('\\$', '$') for x in clean]  # unescape any escaped dollars

    return clean


def check_script_syntax(contents: list) -> int:
    """
    check syntax of a script using bash -n
    """

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:

        f.writelines(contents)

    result = subprocess.run(['bash', '-n', f.name], capture_output=True)

    return result


def beautify_bash_output(input: str) -> str:

    lines = input.split('\n')
    pretty = []
    for line in lines:

        pretty.append(re.sub(r'^[\w/]+: ', '', line))

    return pretty


def process_file_contents(contents: list, filename: str) -> int:
    """
    process a file and all it's script blocks
    """

    script_blocks = util.isolate_process_scripts(contents)

    print(f'{filename}: {len(script_blocks)} script blocks found')

    retv = 0

    for start, end in script_blocks:

        result = check_script_syntax(extract_script(contents, start, end))

        if result.returncode > 0 and IGNORE_FLAG not in util.get_ignore_flags_on_line(
            contents[start - 1]
        ):

            retv |= 1

            print(f'errors in block at line {start + 1}')

            msg = beautify_bash_output(result.stderr.decode())

            for line in msg:
                print(line)

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
