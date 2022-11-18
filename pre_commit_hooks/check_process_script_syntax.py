from __future__ import annotations

import argparse
import re
import subprocess
import tempfile


def isolate_process_scripts(contents: list[str]) -> list[str]:
    """
    isolates the process scripts from within the flow
    """

    regexs = [
        ('process', r'^\s*process \w+ {'),
        ('script', r'^\s*(script|shell|exec):'),
        ('start_block', r'^.*""".*$'),
        ('end_block', r'^.*""".*$'),
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


def extract_script(contents: list, start: int, end: int) -> str:
    """
    extract script block from the lines given
    """

    clean = contents[start : end + 1]
    clean[0] = re.sub('"""', '', clean[0])  # remove triple quotes
    clean[-1] = re.sub('"""', '', clean[-1])  # remove triple quotes
    clean = [x.lstrip() for x in clean]  # unindent

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

    script_blocks = isolate_process_scripts(contents)

    print(f'{filename}: {len(script_blocks)} script blocks found')

    retv = 0

    for start, end in script_blocks:

        result = check_script_syntax(extract_script(contents, start, end))

        if result.returncode > 0:

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
