import tempfile
import unittest

from pre_commit_hooks.detect_consecutive_blank_lines import (
    detect_consecutive_blank_lines,
    main,
)

TESTS = (
    ([''], 0, []),
    (['a', 'b'], 0, []),
    (['a', '', 'b', ''], 0, []),
    (['a', '', '', 'b'], 1, [2]),
    (['a', '', '', 'b', '', ''], 1, [2, 5]),
)


def write_str_to_file(contents: list) -> str:
    """
    write list of strings to tempfile
    """

    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:

        f.writelines('\n'.join(contents))

    return f.name


class TestDetectConsecutiveBlankLines(unittest.TestCase):
    def test_func(self):

        for contents, exp_retcode, exp_linenums in TESTS:

            self.assertEqual(
                detect_consecutive_blank_lines(contents), (exp_retcode, exp_linenums)
            )

    def test_from_file(self):

        for contents, exp_retcode, _ in TESTS:

            f = write_str_to_file(contents)

            retcode = main([f])

            self.assertEqual(retcode, exp_retcode)
