import unittest

from pre_commit_hooks import check_process_script_syntax

TEST_FILES = [
    ('testing/resources/example.nf', True),
    ('testing/resources/example_fail_script_syntax_check.nf', False),
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


class TestCheckProcessScriptSyntax(unittest.TestCase):
    def test_isolate_process_scripts(self):

        with open(TEST_FILES[0][0]) as f:
            contents = f.readlines()

        script_lines = check_process_script_syntax.isolate_process_scripts(contents)
        expected = [(start - 1, end - 1) for start, end in EXPECTED_SCRIPT_LINES]

        self.assertListEqual(script_lines, expected)

    def test_check_script_syntax(self):

        scenarios = [
            (['echo "Hello World!"'], True),
            (['echo "Hello World!'], False),
        ]

        for contents, pass_test in scenarios:

            result = check_process_script_syntax.check_script_syntax(contents)

            self.assertEqual(pass_test, result.returncode == 0)

    def test_from_file(self):

        for path, pass_test in TEST_FILES:

            with open(path) as f:

                contents = f.readlines()

                retcode = check_process_script_syntax.process_file_contents(
                    contents, path
                )

                self.assertEqual(pass_test, retcode == 0)
