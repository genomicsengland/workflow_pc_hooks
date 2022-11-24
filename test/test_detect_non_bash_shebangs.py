import unittest

from pre_commit_hooks import detect_non_bash_shebangs

TEST_FILES = [
    ('testing/resources/example.nf', True),
    ('testing/resources/example_fail_non_bash_shebang.nf', False),
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

    def test_from_file(self):

        for path, pass_test in TEST_FILES:

            with open(path) as f:

                contents = f.readlines()

                retcode = detect_non_bash_shebangs.process_file_contents(contents, path)

                self.assertEqual(pass_test, retcode == 0)
