import mock
import re
import socket
import struct
import time

import pytest  # flake8: noqa

from fixtures import executable_factory, run_as_child, readerr, readout

from nd_toolbelt.commands import nd


class TestNdCommand:
    def test_nd_update_and_no_update_cannot_be_set_together(self, readerr):
        """ Handle the case where --update and --no-update are both called as options """

        with pytest.raises(SystemExit):
            nd.main(['nd', '--update', '--no-update', 'version'])
        assert '--no-update: not allowed with argument --update' in readerr()

    def test_with_no_args(self, readout, executable_factory, run_as_child):
        """ Handle nd being passed no command or namespace """

        executable_factory('nd-help', '#!/bin/bash\necho -n help "<$@>"')
        run_as_child(nd.main, ['nd'])
        assert 'help <>' in readout()

    def test_with_command(self, readout, executable_factory, run_as_child):
        """ Handle executing nd command in path """

        executable_factory('nd-my-command', '#!/bin/bash\necho my command output')
        run_as_child(nd.main, ['nd', 'my-command'])
        assert readout() == 'my command output\n'

    def test_command_with_argument(self, readout, executable_factory, run_as_child):
        """ Handle executing nd command in path with arguments passed from nd """

        executable_factory('nd-my-command', '#!/bin/echo')
        run_as_child(nd.main, ['nd', 'my-command', '--my-option', 'my-argument'])
        assert '--my-option my-argument' in readout()

    def test_with_namespace(self, readout, executable_factory, run_as_child):
        """ Handle executing nd command in path """

        executable_factory('nd-help', '#!/bin/bash\necho -n $@')
        executable_factory('nd-my-namespace~my-command')

        run_as_child(nd.main, ['nd', 'my-namespace'])
        assert readout() == 'my-namespace'

    def test_help_for_command(self, readout, executable_factory, run_as_child):
        """ Handle executing nd-help for command in path """

        executable_factory('nd-help', '#!/bin/bash\necho -n $@')
        run_as_child(nd.main, ['nd', 'help', 'my-command'])
        assert readout() == 'my-command'

    def test_command_or_namespace_not_found(self):
        """ Handle being given a command or namespace not in path """

        with pytest.raises(SystemExit) as exc_info:
            nd.main(['nd', 'missing'])
        assert "Command 'missing' not found." in str(exc_info.value)

    def test_command_or_namespace_help_not_found(self, executable_factory):
        """ Handle being given a command or namespace for help not in path """

        executable_factory('nd-help', '#!/bin/bash\necho -n $@')
        executable_factory('nd-my-namespace~my-command')

        with pytest.raises(SystemExit) as exc_info:
            nd.main(['nd', 'my-namespace', 'missing', 'help'])
        assert "Command or namespace 'missing' not found in 'my-namespace'" in str(exc_info.value)

    def test_with_command_that_cannot_be_run(self, executable_factory, run_as_child):
        """ Handle the case where a command cannot be run """

        executable_factory('nd-my-command')
        with pytest.raises(run_as_child.ChildError) as exc_info:
            run_as_child(nd.main, ['nd', 'my-command'])
        assert 'SystemExit' in str(exc_info.value)
        assert "Command 'nd-my-command' could not be run" in str(exc_info.value)


class TestParseArgs:
    @staticmethod
    def split(*args):
        args = nd.parse_args(('nd',) + args)
        return args.namespace, args.command, args.args

    def test_commands(self, executable_factory):
        """ Handle being given a command or namespaces for help """

        executable_factory('nd-my-command')
        executable_factory('nd-my-namespace~my-command')

        assert ([], 'nd-my-command', []) == self.split('my-command')
        assert (['my-namespace'], 'nd-my-namespace~my-command', []) == \
               self.split('my-namespace', 'my-command')
        assert (['my-namespace'], 'nd-my-namespace~my-command', ['arg']) == \
               self.split('my-namespace', 'my-command', 'arg')

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

        assert ([], 'nd-help', []) == self.split()
        assert ([], 'nd-help', ['my-command']) == self.split('help', 'my-command')
        assert ([], 'nd-help', ['missing']) == self.split('help', 'missing')
        assert ([], 'nd-help', ['my-namespace']) == self.split('help', 'my-namespace')
        assert ([], 'nd-help', ['my-namespace', 'missing']) == \
               self.split('help', 'my-namespace', 'missing')
        assert ([], 'nd-help', ['my-namespace', 'missing']) == \
               self.split('my-namespace', 'help', 'missing')
        assert (['my-other-namespace'], 'nd-my-other-namespace~help', []) == \
               self.split('my-other-namespace', 'help')
        assert (['my-other-namespace'], 'nd-my-other-namespace~help', ['arg']) == \
               self.split('my-other-namespace', 'help', 'arg')

        with pytest.raises(SystemExit) as exc_info:
            self.split('my-namespace', 'missing', 'help')
        assert "Command or namespace 'missing' not found in 'my-namespace" in str(exc_info.value)


class TestNdCheckSystemClock(object):
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
        nd.check_system_clock(check_clock_freq=0)
        err = readerr()
        assert 'WARNING:' not in err and 'ERROR:' not in err

    def test_warning_if_system_clock_is_too_far_behind(self, readerr, ntp_response_factory):
        """ Running nd with system time too far behind the threshold prints to readerr """

        ntp_response_factory(120)
        nd.check_system_clock(check_clock_freq=0)
        assert re.search(r'The system clock is behind by \d+', readerr())

    def test_warning_if_system_clock_is_too_far_ahead(self, readerr, ntp_response_factory):
        """ Running nd with system time too far ahead the threshold prints to readerr """

        ntp_response_factory(-120)
        nd.check_system_clock(check_clock_freq=0)
        assert re.search(r'The system clock is behind by -\d+', readerr())

    def test_nd_continues_if_get_ntp_time_times_out(self, readerr):
        """ Handle ntp request for current time timing out """

        with mock.patch.object(socket, 'socket') as mock_socket:
            mock_socket.return_value.recvfrom.side_effect = socket.timeout()
            nd.check_system_clock(check_clock_freq=0)
            assert 'timed out.' in readerr()

    def test_nd_continues_if_get_ntp_time_raises_socket_error(self, readerr):
        """ Handle ntp request for socket raising an error """

        with mock.patch.object(socket, 'socket') as mock_socket:
            mock_socket.return_value.sendto.side_effect = socket.error()
            nd.check_system_clock(check_clock_freq=0)
            assert 'Error checking network time, exception: ' in readerr()
