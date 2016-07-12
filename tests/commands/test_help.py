import fcntl
import io
import mock
import os
import stat
import textwrap
import traceback

import pytest  # flake8: noqa

from nd_toolbelt.commands import help


class ChildError(Exception):
    pass


def make_help_command(message):
    """ Makes the contents of the test help commands """
    return textwrap.dedent("""\
        #!/bin/bash
        cat << 'EOF'
        {}
        EOF
        """.format(message))


def run_as_child(func):
    """ Run the code as a child process and wait for it to complete """

    error_pipe_in, error_pipe_out = os.pipe()
    fcntl.fcntl(error_pipe_in, fcntl.F_SETFL, os.O_NONBLOCK)  # prevents blocking

    child = os.fork()
    if child == 0:
        status = 0
        try:
            func()
        except:
            with os.fdopen(error_pipe_out, 'w') as error_fd:
                traceback.print_exc(None, error_fd)
            status = 1
        finally:
            os._exit(status)  # Use this instead of exit because it skips the py.test exit handlers
    else:
        try:
            pid, status = os.waitpid(child, 0)
            if status != 0:
                message = io.open(error_pipe_in).read()
                raise ChildError("Traceback from child process:\n" + message)
        finally:
            os.close(error_pipe_out)


def test_run_as_child():
    with pytest.raises(ChildError) as error:
        run_as_child(lambda: cant_find_this)
    assert 'is not defined' in str(error.value)
    assert 'cant_find_this' in str(error.value)


@pytest.fixture
def executable_factory(request, monkeypatch, tmpdir):
    """ Factory for creating executable files from contents """
    def factory(name, contents=''):
        monkeypatch.setenv('PATH', tmpdir, prepend=':')
        test_cmd_path = os.path.join(str(tmpdir), name)
        with open(test_cmd_path, 'w+') as f:
            f.write(contents)
        # Make file executable
        os.chmod(test_cmd_path, os.stat(test_cmd_path).st_mode | stat.S_IEXEC)
        return test_cmd_path
    return factory


@pytest.yield_fixture
def mock_terminal_size():
    with mock.patch.object(os, 'popen') as popen:
        popen.return_value.read.return_value = '80 80'
        yield
        popen.assert_called_with('stty size', 'r')


def test_with_no_args(capfd, mock_terminal_size):
    """ Running help without a command or namespace prints the usage message """

    help.main(['nd-help'])
    stdout, stderr = capfd.readouterr()
    assert 'usage: ' in stdout


def test_with_command(capfd, executable_factory):
    """ Running help for a command prints help for that command """

    executable_factory('nd-my-command', make_help_command('my help message'))
    run_as_child(lambda: help.main(['nd-help', 'my-command']))
    stdout, stderr = capfd.readouterr()
    assert 'my help message' in stdout


def test_with_missing_command(capfd):
    """ Running help for a missing command prints an error """
    with pytest.raises(SystemExit):
        help.main(['nd-help', 'my-missing-command'])
    stdout, stderr = capfd.readouterr()
    assert "executable nd-my-missing-command not found" in stderr


@pytest.mark.skipif(True, reason="this raises an exception")
def test_with_command_without_help(executable_factory, capfd):
    """ Handle the case where help is empty """

    executable_factory('nd-my-command', '#!/bin/bash')
    run_as_child(lambda: help.main(['nd-help', 'my-command']))
    stdout, stderr = capfd.readouterr()
    assert 'executable nd-my-command not found' in stdout


@pytest.mark.skipif(True, reason="need to improve behavior when command can't be run")
def test_with_command_cannot_be_run(executable_factory, capfd):
    """ Handle the case where a command cannot be run """

    executable_factory('nd-my-command')
    run_as_child(lambda: help.main(['nd-help', 'my-command']))
    stdout, stderr = capfd.readouterr()
    assert 'executable nd-my-command not found' in stderr


@pytest.mark.skipif(True, reason='need to update tool output')
def test_with_namespace(executable_factory, capfd, mock_terminal_size):
    """ Running help on a namespace shows help for each command in the namespace """

    executable_factory('nd-my-namespace~my-command', make_help_command('my help message'))
    help.main(['nd-help', 'my-namespace'])
    stdout, stderr = capfd.readouterr()
    assert 'my-namespace my-command' in stdout
    assert 'my help message' in stdout


def test_parses_argparse_generated_help(executable_factory, capfd, mock_terminal_size):
    """ Print help for all commands parses argparse's description string its generated --help """

    executable_factory('nd-my-command', make_help_command(
                        """usage: ...

                        my help message

                        """))
    help.main(['nd-help'])
    stdout, stderr = capfd.readouterr()
    assert 'my help message' in stdout


def test_parses_nonargparse_generated_help(executable_factory, capfd, mock_terminal_size):
    """ Print help for all commands parses descriptions from generic commands' --help """

    executable_factory('nd-my-command', make_help_command(
                        """my help message

                        """))
    help.main(['nd-help'])
    stdout, stderr = capfd.readouterr()
    assert 'my help message' in stdout
