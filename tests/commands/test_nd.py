import mock
import re
import socket
import struct
import time

import pytest  # flake8: noqa

from fixtures import executable_factory, run_as_child, readerr, readout

from nd_toolbelt.commands import nd


@pytest.fixture(autouse=True)
def clear_toolbelt_options(monkeypatch):
    monkeypatch.delenv('ND_TOOLBELT_OPTS', raising=False)


@pytest.fixture()
def disable_update(monkeypatch):
    monkeypatch.setenv('ND_TOOLBELT_OPTS', '--no-update', prepend=' ')


@pytest.fixture()
def disable_clock_check(monkeypatch):
    monkeypatch.setenv('ND_TOOLBELT_OPTS', '--no-clock-check', prepend=' ')


@pytest.fixture()
def disable_dot_commands(monkeypatch):
    monkeypatch.setenv('ND_TOOLBELT_OPTS', '--skip-dot-commands', prepend=' ')


class TestNdCommand:
    @pytest.fixture(autouse=True)
    def setup(self, executable_factory, readout, run_as_child,
              disable_update, disable_clock_check, disable_dot_commands):
        self.executable_factory = executable_factory
        self.readout = readout
        self.run_as_child = run_as_child

    def test_runs_command_and_passes_arguments(self):
        """ Handle executing nd command in path with arguments passed from nd """

        self.executable_factory('nd-my-command', '#!/bin/echo')
        with self.readout() as output:
            self.run_as_child(nd.main, ['nd', 'my-command', '--my-option', 'my-argument'])
        assert '--my-option my-argument' in output

    def test_runs_command(self):
        """ Handle executing nd command in path """

        self.executable_factory('nd-my-command', '#!/bin/bash\necho my command output')
        with self.readout() as output:
            self.run_as_child(nd.main, ['nd', 'my-command'])
        assert output == 'my command output\n'

    def test_calls_help_if_given_no_commands_or_arguments(self):
        """ Handle nd being passed no command or namespace """

        self.executable_factory('nd-help', '#!/bin/bash\necho -n help "<$@>"')
        with self.readout() as output:
            self.run_as_child(nd.main, ['nd'])
        assert 'help <>' in output

    def test_calls_help_if_namespace_given_without_command(self):
        """ Handle executing nd namespace in path """

        self.executable_factory('nd-help', '#!/bin/bash\necho -n $@')
        self.executable_factory('nd-my-namespace~my-command')

        with self.readout() as output:
            self.run_as_child(nd.main, ['nd', 'my-namespace'])
        assert output == 'my-namespace'

    def test_calls_help_for_command_when_help_is_first_argument(self):
        """ Handle executing nd-help for command in path """

        self.executable_factory('nd-help', '#!/bin/bash\necho -n $@')
        with self.readout() as output:
            self.run_as_child(nd.main, ['nd', 'help', 'my-command'])
        assert output == 'my-command'

    def test_command_or_namespace_not_found(self):
        """ Handle being given a command or namespace not in path """

        with pytest.raises(SystemExit) as exc_info:
            nd.main(['nd', 'missing'])
        assert "Command 'missing' not found." in str(exc_info.value)

    def test_command_or_namespace_help_not_found(self):
        """ Handle being given a command or namespace for help not in path """

        self.executable_factory('nd-help', '#!/bin/bash\necho -n $@')
        self.executable_factory('nd-my-namespace~my-command')

        with pytest.raises(SystemExit) as exc_info:
            nd.main(['nd', 'my-namespace', 'missing', 'help'])
        assert "Command or namespace 'missing' not found in 'my-namespace'" in str(exc_info.value)

    def test_with_command_that_cannot_be_run(self):
        """ Handle the case where a command cannot be run """

        self.executable_factory('nd-my-command')
        with pytest.raises(self.run_as_child.ChildError) as exc_info:
            self.run_as_child(nd.main, ['nd', 'my-command'])
        assert 'SystemExit' in str(exc_info.value)
        assert "Command 'nd-my-command' could not be run" in str(exc_info.value)


class TestDotCommand:
    @pytest.fixture(autouse=True)
    def setup(self, disable_clock_check, disable_update, executable_factory, readout, run_as_child):
        self.executable_factory = executable_factory
        self.readout = readout
        self.run_as_child = run_as_child

    def test_dot_commands_run_automatically_before_command(self):
        """ All dot commands for the given namespace should run before the given command """

        self.executable_factory('nd-.my-check', '#!/bin/bash\necho my dot command output')
        self.executable_factory('nd-my-command', '#!/bin/bash\necho my command output')
        with self.readout() as output:
            self.run_as_child(nd.main, ['nd', 'my-command'])
        assert output == 'my dot command output\nmy command output\n'

    def test_dot_commands_are_passed_command_name_and_arguments(self):
        """ All dot commands get passed the target namespace + command and its arguments """

        self.executable_factory('nd-my-namespace~.my-check', '#!/bin/bash\necho $@')
        self.executable_factory('nd-my-namespace~my-command', '#!/bin/bash\necho my command output')
        with self.readout() as output:
            self.run_as_child(nd.main, ['nd', 'my-namespace', 'my-command', 'arg1', 'arg2'])
        assert output == 'my-namespace my-command arg1 arg2\nmy command output\n'

    def test_dot_commands_run_as_command_does_not_run_dot_commands_prior_to_running(self):
        """ When calling a dot command directly, do not call dot commands prior to executing """

        self.executable_factory('nd-.my-first-check', '#!/bin/bash\necho my first check')
        self.executable_factory('nd-.my-second-check', '#!/bin/bash\necho my second check')
        with self.readout() as output:
            self.run_as_child(nd.main, ['nd', '.my-first-check'])
        assert output == 'my first check\n'


class TestNdOptions:
    def test_nd_update_and_no_update_cannot_be_set_together(self, disable_clock_check,
                                                            disable_dot_commands, readerr):
        """ Handle the case where --update and --no-update are both called as options """

        with readerr() as errout, pytest.raises(SystemExit):
            nd.main(['nd', '--update', '--no-update', 'version'])
        assert '--no-update: not allowed with argument --update' in errout

    def test_dot_commands_disabled_option(self, disable_clock_check, disable_update,
                                       executable_factory, readout, run_as_child):
        """ Ignore dot commands before the given command if option is set in toolbelt """

        executable_factory('nd-.my-check', '#!/bin/bash\necho my dot command output')
        executable_factory('nd-my-command', '#!/bin/bash\necho my command output')
        with readout() as output:
            run_as_child(nd.main, ['nd', '--skip-dot-commands', 'my-command'])
        assert output == 'my command output\n'


class TestParseArgs:
    @staticmethod
    def split(*args):
        args = nd.parse_args(('nd',) + args)
        return args.namespace, args.command, args.args

    def test_commands(self, executable_factory):
        """ Handle being given a command with or without namespaces """

        executable_factory('nd-my-command')
        executable_factory('nd-my-namespace~my-command')

        assert ([], 'my-command', []) == self.split('my-command')
        assert (['my-namespace'], 'my-command', []) == self.split('my-namespace', 'my-command')
        assert (['my-namespace'], 'my-command', ['arg']) == \
               self.split('my-namespace', 'my-command', 'arg')

    def test_missing_commands(self, executable_factory):
        """ Handle being given a missing command with or without namespaces """
        executable_factory('nd-my-namespace~my-command')

        with pytest.raises(SystemExit) as exc_info:
            self.split('missing')
        assert "Command 'missing' not found" in str(exc_info.value)

        with pytest.raises(SystemExit) as exc_info:
            self.split('my-namespace', 'missing')
        assert "Command 'missing' not found in 'my-namespace" in str(exc_info.value)

    def test_help(self, executable_factory):
        """ Handle being given a command or namespaces for help """

        executable_factory('nd-help')
        executable_factory('nd-my-command')
        executable_factory('nd-my-namespace~my-command')
        executable_factory('nd-my-other-namespace~help')

        assert ([], 'help', []) == self.split()
        assert ([], 'help', ['my-command']) == self.split('help', 'my-command')
        assert ([], 'help', ['missing']) == self.split('help', 'missing')
        assert ([], 'help', ['my-namespace']) == self.split('help', 'my-namespace')
        assert ([], 'help', ['my-namespace', 'missing']) == \
               self.split('help', 'my-namespace', 'missing')
        assert ([], 'help', ['my-namespace', 'missing']) == \
               self.split('my-namespace', 'help', 'missing')
        assert (['my-other-namespace'], 'help', []) == \
               self.split('my-other-namespace', 'help')
        assert (['my-other-namespace'], 'help', ['arg']) == \
               self.split('my-other-namespace', 'help', 'arg')

        with pytest.raises(SystemExit) as exc_info:
            self.split('my-namespace', 'missing', 'help')
        assert "Command or namespace 'missing' not found in 'my-namespace" in str(exc_info.value)


class TestNdCheckSystemClock:
    @staticmethod
    @pytest.yield_fixture
    def ntp_response_factory():
        with mock.patch.object(socket, 'socket') as mock_socket:
            def factory(offset):
                time_since_1900 = int(time.time()) + 2208988800
                encoded_time = struct.pack('!12I', *(([0] * 10) + [time_since_1900 + offset] + [0]))

                mock_socket.return_value.recvfrom.return_value = (encoded_time, None)

            yield factory

            mock_socket.assert_called_with(socket.AF_INET, socket.SOCK_DGRAM)

    def test_nothing_happens_if_time_is_accurate(self, readerr, ntp_response_factory):
        """ Running nd with accurate system time does not print to readerr """

        ntp_response_factory(0)
        with readerr() as err:
            nd.check_system_clock(check_clock_freq=0)
        assert 'WARNING:' not in err and 'ERROR:' not in err

    def test_warning_if_system_clock_is_too_far_behind(self, readerr, ntp_response_factory):
        """ Running nd with system time too far behind the threshold prints to readerr """

        ntp_response_factory(120)
        with readerr() as err:
            nd.check_system_clock(check_clock_freq=0)
        assert re.search(r'The system clock is behind by \d+', str(err))

    def test_warning_if_system_clock_is_too_far_ahead(self, readerr, ntp_response_factory):
        """ Running nd with system time too far ahead the threshold prints to readerr """

        ntp_response_factory(-120)
        with readerr() as err:
            nd.check_system_clock(check_clock_freq=0)
        assert re.search(r'The system clock is behind by -\d+', str(err))

    def test_nd_continues_if_get_ntp_time_times_out(self, readerr):
        """ Handle ntp request for current time timing out """

        with mock.patch.object(socket, 'socket') as mock_socket:
            mock_socket.return_value.recvfrom.side_effect = socket.timeout()
            with readerr() as err:
                nd.check_system_clock(check_clock_freq=0)
            assert 'timed out.' in err

    def test_nd_continues_if_get_ntp_time_raises_socket_error(self, readerr):
        """ Handle ntp request for socket raising an error """

        with mock.patch.object(socket, 'socket') as mock_socket:
            mock_socket.return_value.sendto.side_effect = socket.error()
            with readerr() as err:
                nd.check_system_clock(check_clock_freq=0)
            assert 'Error checking network time, exception: ' in err


class TestRunDotCommands:
    @staticmethod
    @pytest.fixture(autouse=True)
    def set_minimal_path(monkeypatch):
        monkeypatch.setenv('PATH', '/usr/bin:/bin')

    def test_runs_with_passed_command_and_args(self, executable_factory, readout):
        """ Dot Commands are called with the called command and its args """
        executable_factory('nd-my-namespace~.my-check', """\
            #!/bin/bash
            echo $1
            echo $2
            echo $3""")
        with readout() as output:
            nd.run_dot_commands(['my-namespace'], 'my-command', ['arg1', 'arg2'])
        assert output == 'my-namespace my-command\narg1\narg2\n'

    def test_dot_commands_run_only_once(self, executable_factory, monkeypatch, readout):
        """ Handle the dot command appearing multiple times on path by running it only once """

        tmp_path = executable_factory('nd-.my-check', '#!/bin/bash\necho my dot command output')
        monkeypatch.setenv('PATH', tmp_path, prepend=':')
        with readout() as output:
            nd.run_dot_commands([], '', [])
        assert output == 'my dot command output\n'

    def test_dot_command_fails_triggers_system_exit(self, executable_factory):
        """ Handle dot command failing with exit code not zero by exiting system """

        executable_factory('nd-.my-check', '#!/bin/bash\nexit 1')
        with pytest.raises(SystemExit) as exc_info:
            nd.run_dot_commands([], '', [])
        assert "Dot command 'nd-.my-check' failed." in str(exc_info.value)

    def test_with_no_dot_commands(self):
        """ Handle no dot command being in namespace """

        assert nd.run_dot_commands([], '', []) is None

    def test_dot_commands_run_alphabetically(self, executable_factory, readout):
        """ All dot commands for the given namespace should run in alphabetical order """

        executable_factory('nd-.my-checkC', '#!/bin/bash\necho dot command C output')
        executable_factory('nd-.my-checkA', '#!/bin/bash\necho dot command A output')
        executable_factory('nd-.my-checkB', '#!/bin/bash\necho dot command B output')
        with readout() as output:
            nd.run_dot_commands([], '', [])
        assert output == 'dot command A output\ndot command B output\ndot command C output\n'

    def test_child_dot_commands_do_not_run(self, executable_factory, readout):
        """ Dot commands in child namespaces do not get called """

        executable_factory('nd-.my-check', '#!/bin/bash\necho parent dot command output')
        executable_factory('nd-my-namespace~.my-check',
                           '#!/bin/bash\necho child dot command output')
        with readout() as output:
            nd.run_dot_commands([], '', [])
        assert output == 'parent dot command output\n'

    def test_dot_commands_run_in_order_of_namespace(self, executable_factory, readout):
        """ Dot commands in parent namespaces run before its children """

        executable_factory('nd-.my-check', '#!/bin/bash\necho parent dot command output')
        executable_factory('nd-my-namespace~.my-check',
                           '#!/bin/bash\necho child dot command output')
        executable_factory('nd-my-namespace~subnamespace~.my-check',
                           '#!/bin/bash\necho grandchild dot command output')
        with readout() as output:
            nd.run_dot_commands(['my-namespace', 'subnamespace'], '', [])
        assert output == ('parent dot command output\nchild dot command output\n'
                          'grandchild dot command output\n')
