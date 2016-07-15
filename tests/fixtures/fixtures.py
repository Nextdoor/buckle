import fcntl
import io
import os
import stat
import traceback

import pytest  # flake8: noqa


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


class ChildError(Exception):
    pass


@pytest.fixture
def run_as_child():
    """ Returns a callable that runs a function as a child process and waits for it to complete """

    def runner(func):
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

    return runner
