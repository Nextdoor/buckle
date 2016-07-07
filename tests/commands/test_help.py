import mock
import os
import stat
import subprocess

import pytest  # flake8: noqa

from nd_toolbelt.commands import help
from nd_toolbelt import autocomplete

STAT_OWNER_EXECUTABLE = stat.S_IEXEC


class TestNdHelpCommandClass:
    def test_with_no_args(self, capfd):
        with mock.patch.object(os, 'popen') as popen:
            popen.return_value.read.return_value = '80 80'

            help.main(['nd-help'])
            stdout, stderr = capfd.readouterr()
            assert 'usage: ' in stdout
            popen.assert_called_with('stty size', 'r')

    def test_with_command(self, monkeypatch, tmpdir):
        monkeypatch.setenv('PATH', tmpdir, prepend=':')
        test_cmd_path = str(tmpdir) + '/nd-my-command'

        with open(test_cmd_path, 'w+'):
            st = os.stat(test_cmd_path)
            os.chmod(test_cmd_path, st.st_mode | STAT_OWNER_EXECUTABLE)  # Make cmd executable

            with mock.patch.object(subprocess, 'check_output',
                                   return_value=test_cmd_path) as check_output:
                with mock.patch.object(os, 'execv') as execv:
                    help.main(['nd-help', 'my-command'])
                    execv.assert_called_with(test_cmd_path, ['nd-my-command', '--help'])
                    check_output.assert_called_with(['which', 'nd-my-command'])

    def test_with_namespace(self, monkeypatch, tmpdir, capfd):
        with mock.patch.object(os, 'popen') as popen:
            popen.return_value.read.return_value = '80 80'

            monkeypatch.setenv('PATH', tmpdir, prepend=':')
            test_cmd_path = str(tmpdir) + '/nd-my-namespace~my-command'

            with open(test_cmd_path, 'w+'):
                st = os.stat(test_cmd_path)
                os.chmod(test_cmd_path, st.st_mode | STAT_OWNER_EXECUTABLE)  # Make cmd executable

                with mock.patch.object(subprocess, 'check_output') as check_output:
                    with mock.patch.object(autocomplete, 'get_executables_starting_with',
                                           return_value=['nd-my-namespace~my-command']):
                        check_output.side_effect = [
                            subprocess.CalledProcessError(1, 'which'),
                            "usage: ...\n\ncustom help message\n\n".encode()]

                        help.main(['nd-help', 'my-namespace'])
                        stdout, stderr = capfd.readouterr()
                        assert 'my-namespace my-command' in stdout
                        assert 'custom help message' in stdout

                        popen.assert_called_with('stty size', 'r')
                        assert check_output.call_args_list == [
                            mock.call(['which', 'nd-my-namespace']),
                            mock.call('nd-my-namespace~my-command --help 2> /dev/null', shell=True)]

