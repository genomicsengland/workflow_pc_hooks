import tempfile
import unittest

from pre_commit_hooks import util
from pre_commit_hooks.remove_consecutive_blank_lines import (
    detect_consecutive_blank_lines,
    main,
)

TESTS = (
    ([''], 0, [], ['']),
    (['a', 'b'], 0, [], ['a', 'b']),
    (['a', '', 'b', ''], 0, [], ['a', '', 'b', '']),
    (['a', '', '', 'b'], 1, [2], ['a', '', 'b']),
    (['a', '', '', '', 'b'], 1, [2, 3], ['a', '', 'b']),
    (
        ['a', '', '', 'b', '', ''],
        1,
        [2, 5],
        [
            'a',
            '',
            'b',
            '',
        ],
    ),
)


def write_list_to_tempfile(contents):

    f = tempfile.NamedTemporaryFile(mode='w+', delete=False)

    util.write_list_to_file(contents, f.name)

    return f.name


class TestDetectConsecutiveBlankLines(unittest.TestCase):
    def test_func(self):

        for contents, exp_retcode, exp_linenums, _ in TESTS:

            self.assertEqual(
                detect_consecutive_blank_lines(contents), (exp_retcode, exp_linenums)
            )

    def test_from_file(self):

        for contents, exp_retcode, _, _ in TESTS:

            f = write_list_to_tempfile(contents)

            retcode = main([f])

            self.assertEqual(retcode, exp_retcode)

    def test_deletion(self):

        for contents, _, _, exp_output in TESTS:

            f = write_list_to_tempfile(contents)

            _ = main([f])

            new_contents = util.read_file_to_list(f)

            self.assertListEqual(new_contents, exp_output)
