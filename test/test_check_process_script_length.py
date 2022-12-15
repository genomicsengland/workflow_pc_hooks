import unittest

from pre_commit_hooks import check_process_script_length

TEST_FILES = [
    ('testing/resources/example.nf', True),
    ('testing/resources/example_fail_script_length.nf', False),
    ('testing/resources/example_fail_script_length_ignored.nf', True),
]


class TestCheckProcessScriptLength(unittest.TestCase):
    def test_check_script_length(self):

        scenarios = [
            (
                # valid script but no contents
                ['process something {', 'script:', '"""', '"""'],
                True,
            ),
            (
                # valid script of exactly 20 length
                ['process something {', 'script:', '"""', *['soemthing'] * 20, '"""'],
                True,
            ),
            (
                # no script here
                [
                    *['soemthing'] * 21,
                ],
                True,
            ),
            (
                # script over max script length
                ['process something {', 'script:', '"""', *['soemthing'] * 21, '"""'],
                False,
            ),
            (
                # script over max script length but ignored
                [
                    'process something {',
                    'script:',
                    '//ignore: check-process-script-length',
                    '"""',
                    *['soemthing'] * 21,
                    '"""',
                ],
                True,
            ),
            (
                # script over max script length, wrong ignore flag
                [
                    'process something {',
                    'script:',
                    '//ignore: ignore-something-else',
                    '"""',
                    *['soemthing'] * 21,
                    '"""',
                ],
                False,
            ),
        ]

        for contents, pass_test in scenarios:

            result = check_process_script_length.process_file_contents(
                contents, 'a', 20
            )

            self.assertEqual(pass_test, result == 0)

    def test_from_file(self):

        for path, pass_test in TEST_FILES:

            with open(path) as f:

                contents = f.readlines()

                retcode = check_process_script_length.process_file_contents(
                    contents, path, 50
                )

                self.assertEqual(pass_test, retcode == 0)
