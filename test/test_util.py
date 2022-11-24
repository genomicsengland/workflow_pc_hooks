import unittest

from pre_commit_hooks import util

TEST_FILE = 'testing/resources/example_fail_single_quote_script_block.nf'
EXPECTED_SCRIPT_LINES = [
    (114, 124),
    (152, 169),
    (211, 236),
    (269, 306),
    (336, 355),
    (410, 441),
    (466, 484),
    (509, 514),
]


class TestDetectSingleQuoteScriptBlocks(unittest.TestCase):
    def test_isolate_process_scripts(self):

        with open(TEST_FILE) as f:
            contents = f.readlines()

        script_lines = util.isolate_process_scripts(contents)
        expected = [(start - 1, end - 1) for start, end in EXPECTED_SCRIPT_LINES]

        self.assertListEqual(script_lines, expected)
