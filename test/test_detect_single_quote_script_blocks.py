import unittest

from pre_commit_hooks import detect_single_quote_script_blocks

TEST_FILES = [
    ('testing/resources/example.nf', True),
    ('testing/resources/example_fail_single_quote_script_block.nf', False),
]
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

        with open(TEST_FILES[0][0]) as f:
            contents = f.readlines()

        script_lines = detect_single_quote_script_blocks.isolate_process_scripts(
            contents
        )
        expected = [(start - 1, end - 1) for start, end in EXPECTED_SCRIPT_LINES]

        self.assertListEqual(script_lines, expected)

    def test_detect_valid_script_block_type(self):

        scenarios = [
            (['script: """', 'end here """'], True),
            (['"""', '"""'], True),
            (['""" start something', ' end of script """'], True),
            ([' script: """ start something', ' end of script """ carrying on'], True),
            (["script: '''", "end here '''"], False),
            (["'''", "'''"], False),
            (["''' start something", " end of script '''"], False),
            ([" script: ''' start something", " end of script ''' carrying on"], False),
        ]

        for lines, pass_test in scenarios:

            print(lines)

            result = detect_single_quote_script_blocks.detect_valid_script_block_type(
                lines[0], lines[1]
            )

            print(result)

            self.assertEqual(pass_test, result == 0)

    def test_from_file(self):

        for path, pass_test in TEST_FILES:

            with open(path) as f:

                contents = f.readlines()

                retcode = detect_single_quote_script_blocks.process_file_contents(
                    contents, path
                )

                self.assertEqual(pass_test, retcode == 0)
