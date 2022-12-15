import unittest

from pre_commit_hooks import check_process_script_syntax

TEST_FILES = [
    ('testing/resources/example.nf', True),
    ('testing/resources/example_fail_script_syntax_check.nf', False),
    ('testing/resources/example_fail_script_syntax_check_ignored.nf', True),
]


class TestCheckProcessScriptSyntax(unittest.TestCase):
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
