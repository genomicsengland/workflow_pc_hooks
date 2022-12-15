import unittest

from pre_commit_hooks import detect_non_bash_shebangs

TEST_FILES = [
    ('testing/resources/example.nf', True),
    ('testing/resources/example_fail_non_bash_shebang.nf', False),
    ('testing/resources/example_fail_non_bash_shebang_ignored.nf', True),
]


class TestDetectNonBashShebangs(unittest.TestCase):
    def test_detect_non_bash_shebangs(self):

        scenarios = [
            (['"""', '#!/bin/bash', '"""'], ['bash']),
            (['"""', '#!/bin/python', '"""'], ['python']),
            (['"""', '#!/bin/python', '#!/bin/bash' '"""'], ['python', 'bash']),
            (
                ['"""', ' start of script #!/bin/python', '#!/bin/bash' '"""'],
                ['python', 'bash'],
            ),
            (['"""', 'some script' '"""'], []),
            (['"""', '#!some comment' '"""'], []),
        ]

        for lines, shebangs in scenarios:

            result = detect_non_bash_shebangs.extract_shebangs(lines)

            self.assertEqual(result, shebangs)

    def test_ignoring_of_lines(self):
        scenarios = [
            (
                # no script
                ['hello', 'world'],
                True,
            ),
            (
                # valid script but no contents
                ['process something {', 'script:', '"""', '"""'],
                True,
            ),
            (
                # valid script with bash shebang
                ['process something {', 'script:', '"""', '#!/bin/bash', '"""'],
                True,
            ),
            (
                # valid script with python shebang
                ['process something {', 'script:', '"""', '#!/bin/python', '"""'],
                False,
            ),
            (
                # valid script with python shebang, but ignored
                [
                    'process something {',
                    'script:',
                    '""" #ignore: detect-non-bash-shebangs',
                    '#!/bin/python',
                    '"""',
                ],
                True,
            ),
            (
                # valid script with python shebang, but wrong ignored flag
                [
                    'process something {',
                    'script:',
                    '""" #ignore: some-other-thing',
                    '#!/bin/python',
                    '"""',
                ],
                False,
            ),
        ]

        for contents, pass_test in scenarios:

            retcode = detect_non_bash_shebangs.process_file_contents(contents, 'test')

            self.assertEqual(pass_test, retcode == 0)

    def test_from_file(self):

        for path, pass_test in TEST_FILES:

            with open(path) as f:

                contents = f.readlines()

                retcode = detect_non_bash_shebangs.process_file_contents(contents, path)

                self.assertEqual(pass_test, retcode == 0)
