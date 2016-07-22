import os
import subprocess
import sys

import pytest  # flake8: noqa

sys.path.append(os.path.abspath('.'))
from fixtures import *


class TestRunAsChild:
    def test_child_prints_to_file_descriptors(self, capfd, run_as_child):
        run_as_child(os.execvp, 'echo', ['echo', 'my test output'])
        stdout, stderr = capfd.readouterr()
        assert stdout == 'my test output\n'

    def test_raises_exception_on_child_error(self, run_as_child):
        with pytest.raises(run_as_child.ChildError) as error:
            run_as_child(lambda: cant_find_this)
        assert 'is not defined' in str(error.value)
        assert 'cant_find_this' in str(error.value)

    def test_cannot_execv_as_test_runner(self, run_as_child):
        with pytest.raises(run_as_child.CannotExecAsTestRunner) as error:
            os.execv(['/bin/bash'])

    def test_cannot_execvp_as_test_runner(self, run_as_child):
        with pytest.raises(run_as_child.CannotExecAsTestRunner) as error:
            os.execvp(['bash'])


class TestExecutableFactory:
    def test_executable_contents(self, executable_factory):
        executable_factory('my-command', 'my content')
        contents = subprocess.check_output('cat $(which my-command)', shell=True).decode('utf-8')
        assert contents == 'my content'

    @staticmethod
    @pytest.fixture
    def original_path():
        return os.getenv('PATH')

    def test_appends_to_path(self, original_path, executable_factory):
        executable_factory('my-command', '')
        new_path = os.getenv('PATH')

        assert original_path != new_path
        assert original_path in new_path

    def test_returns_correct_path(self, executable_factory):
        path = executable_factory('my-command', 'my content')
        with open(path) as f:
            contents = f.read()
        assert contents == 'my content'

    def test_dedent(self, executable_factory):
        path = executable_factory('my-command', """\
            This command is not indented
            No way!""")
        with open(path) as f:
            contents = f.read()
        assert contents == 'This command is not indented\nNo way!'

    def test_no_dedent(self, executable_factory):
        path = executable_factory('my-command', """\
            This command is not indented
            No way!""", dedent=False)
        with open(path) as f:
            contents = f.read()
        assert contents == '            This command is not indented\n            No way!'
