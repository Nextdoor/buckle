import mock
import os
import textwrap

import pytest  # flake8: noqa

from nd_toolbelt.commands import help


def make_help_command(message):
    """ Makes the contents of the test help commands """
    return "#!/bin/bash\ncat << 'EOF'\n{}\nEOF".format(textwrap.dedent(message))


class TestCommandHelp:
    def test_calls_commands_with_help_flag(self, capfd, executable_factory, run_as_child):
        """ Print help for all commands parses descriptions from generic commands' --help """

        executable_factory('nd-my-command', '#!/bin/echo')
        run_as_child(lambda: help.main(['nd-help', 'my-command']))
        stdout, stderr = capfd.readouterr()
        assert '--help' in stdout

    def test_with_missing_command(self, capfd):
        """ Running help for a missing command prints an error """

        with pytest.raises(SystemExit):
            help.main(['nd-help', 'my-missing-command'])
        stdout, stderr = capfd.readouterr()
        assert "executable nd-my-missing-command not found" in stderr

    def test_with_command_cannot_be_run(self, capfd, executable_factory):
        """ Handle the case where a command cannot be run """

        executable_factory('nd-my-command', '')
        with pytest.raises(SystemExit):
            help.main(['nd-help', 'my-command'])
        stdout, stderr = capfd.readouterr()
        assert 'executable nd-my-command could not be run' in stderr


class TestNamespaceHelp:
    @staticmethod
    @pytest.yield_fixture(autouse=True)
    def set_minimal_path(monkeypatch):
        monkeypatch.setenv('PATH', '/usr/bin:/bin')
        yield

    @staticmethod
    @pytest.yield_fixture
    def mock_terminal_size():
        with mock.patch.object(os, 'popen') as popen:
            popen.return_value.read.return_value = '80 80'
            yield
            popen.assert_called_with('stty size', 'r')

    def test_with_command_with_empty_help(self, capfd, executable_factory, mock_terminal_size):
        """ Handle the case where help returns empty string """

        executable_factory('nd-my-command', make_help_command(''))
        help.main(['nd-help'])
        stdout, stderr = capfd.readouterr()
        assert 'my-command   <help not found>' in stdout

    def test_with_no_args(self, capfd, executable_factory, mock_terminal_size):
        """ Running help without a command or namespace prints help of commands on path """

        executable_factory('nd-my-namespace~my-command', make_help_command('my help message'))
        help.main(['nd-help'])
        stdout, stderr = capfd.readouterr()
        assert 'usage: ' in stdout
        assert 'my-namespace my-command   my help message' in stdout

    def test_with_no_args_and_no_nd_commands(self, capfd, executable_factory):
        """ Running help without args prints the usage message if no nd commands are on path """

        with pytest.raises(SystemExit):
            help.main(['nd-help'])
        stdout, stderr = capfd.readouterr()
        assert 'No nd commands found on path. Check your $PATH.' in stderr

    def test_parses_argparse_generated_help(self, capfd, executable_factory, mock_terminal_size):
        """ Print help for all commands parses argparse's description from its generated help """

        executable_factory('nd-my-command', make_help_command("""\
            usage: ...

            my help message"""))
        help.main(['nd-help'])
        stdout, stderr = capfd.readouterr()
        assert 'my-command   my help message' in stdout

    def test_parses_nonargparse_generated_help(self, capfd, executable_factory, mock_terminal_size):
        """ Print help for all commands parses descriptions from generic commands' --help """

        executable_factory('nd-my-command', make_help_command('my help message'))
        help.main(['nd-help'])
        stdout, stderr = capfd.readouterr()
        assert 'my-command   my help message' in stdout

    def test_with_namespace(self, capfd, executable_factory, mock_terminal_size):
        """ Running help on a namespace shows help for each command in the namespace """

        executable_factory('nd-my-namespace~my-command', make_help_command('my help message'))
        help.main(['nd-help', 'my-namespace'])
        stdout, stderr = capfd.readouterr()
        assert 'my-namespace my-command   my help message' in stdout

    def test_with_failing_command(self, capfd, executable_factory, mock_terminal_size):
        """ Handle the case where a command returns non-zero exit status """

        executable_factory('nd-my-command', '#!/bin/bash\nexit 1')
        help.main(['nd-help'])
        stdout, stderr = capfd.readouterr()
        assert 'my-command   <help not found>' in stdout
