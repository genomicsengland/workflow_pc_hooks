from __future__ import annotations

import argparse


def detect_consecutive_blank_lines(
    contents: list, filename: str = '<unknown>'
) -> tuple[int, int]:
    """
    returns non-zero if the src contains consecutive blank lines
    """

    retv = 0
    n_consecutive_blank_lines = 0
    error_line_nums = []

    for i, l in enumerate(contents):

        if not l.strip():
            n_consecutive_blank_lines += 1

            if n_consecutive_blank_lines == 2:
                retv = 1
                error_line_nums.append(i)
                print(f'{filename}: consecutive blank line at line {i}')

        else:
            n_consecutive_blank_lines = 0

    return retv, error_line_nums


def remove_lines(contents: list, line_nums: list):
    """
    remove lines from file contents
    """

    for ele in sorted(line_nums, reverse=True):

        del contents[ele]

    return contents


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='*')
    args = parser.parse_args(argv)

    overall_retcode = 0
    for filename in args.filenames:
        with open(filename, 'rb') as inputfile:
            contents = inputfile.readlines()
        retcode, errors = detect_consecutive_blank_lines(contents, filename)
        overall_retcode |= retcode

    return overall_retcode
