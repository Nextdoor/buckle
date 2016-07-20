import fcntl
import functools
import io
import mock
import os
import stat
import traceback

import pytest  # flake8: noqa


@pytest.fixture()
def readout(capfd):
    """ Capture stdout """
    return lambda: capfd.readouterr()[0]


@pytest.fixture()
def readerr(capfd):
    """ Capture stderr """
    return lambda: capfd.readouterr()[1]


@pytest.fixture
def executable_factory(monkeypatch, tmpdir):
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


@pytest.yield_fixture(autouse=True)
def run_as_child():
    """ A fixture that yields a callable for running a function as a child process.

    Yields:
        callable - Calling callable(func, *args, **kwargs) runs the function in a child process
                   and waits for a to complete.  Raises callable.ChildError with details of any
                   exceptions that occur in the child process.
    """

    class ChildError(Exception):
        pass

    class CannotExecAsTestRunner(Exception):
        pass

    def prevent_execv_as_test_runner(func):
        test_runner_pid = os.getpid()
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            if os.getpid() == test_runner_pid:
                raise CannotExecAsTestRunner('Use run_as_child fixture if you need to call exec')
            return func(*args, **kwargs)
        return wrapped

    def child_runner(func, *args, **kwargs):
        error_pipe_in, error_pipe_out = os.pipe()
        fcntl.fcntl(error_pipe_in, fcntl.F_SETFL, os.O_NONBLOCK)  # prevents blocking

        child = os.fork()
        if child == 0:
            status = 0
            try:
                func(*args, **kwargs)
            except:
                with os.fdopen(error_pipe_out, 'w') as error_fd:
                    traceback.print_exc(None, error_fd)
                status = 1
            finally:
                # Use this instead of exit because it skips the py.test exit handlers
                os._exit(status)
        else:
            try:
                pid, status = os.waitpid(child, 0)
                if status != 0:
                    message = io.open(error_pipe_in).read()
                    raise ChildError("Traceback from child process:\n" + message)
            finally:
                os.close(error_pipe_out)

    with mock.patch.object(os, 'execv', prevent_execv_as_test_runner(os.execv)), \
         mock.patch.object(os, 'execvp', prevent_execv_as_test_runner(os.execvp)):
        child_runner.CannotExecAsTestRunner = CannotExecAsTestRunner
        child_runner.ChildError = ChildError
        yield child_runner
