import mock
import re
import socket
import struct
import time

import pytest  # flake8: noqa

from fixtures import executable_factory, run_as_child

from nd_toolbelt.commands import nd


class TestNdCommand:
    def test_nd_update_and_no_update_cannot_be_set_together(self, capfd):
        """ Handle the case where --update and --no-update are both called as options """

        with pytest.raises(SystemExit):
            nd.main(['nd', '--update', '--no-update', 'version'])
        stdout, stderr = capfd.readouterr()
        assert '--no-update: not allowed with argument --update' in stderr

    def test_with_no_args(self, capfd):
        """ Handle nd being passed no command or namespace """
        with pytest.raises(SystemExit):
            nd.main(['nd', '--no-update', '--no-clock-check'])
        stdout, stderr = capfd.readouterr()
        assert 'error: ' in stderr

    def test_with_command(self, capfd, executable_factory, run_as_child):
        """ Handle executing nd command on path """

        executable_factory('nd-my-command', '#!/bin/bash\necho my command output')
        run_as_child(lambda: nd.main(['nd-help', 'my-command']))
        stdout, stderr = capfd.readouterr()
        assert stdout == 'my command output\n'

    def test_command_with_argument(self, capfd, executable_factory, run_as_child):

        """ Handle executing nd command on path with arguments passed from nd """
        executable_factory('nd-my-command', '#!/bin/echo')
        run_as_child(lambda: nd.main(['nd-help', 'my-command', '--my-option', 'my-argument']))
        stdout, stderr = capfd.readouterr()
        assert '--my-option my-argument' in stdout

    def test_command_not_found(self, capfd):

        """ Handle being given command not found on path """
        with pytest.raises(SystemExit):
            nd.main(['nd', 'my-command'])
        stdout, stderr = capfd.readouterr()
        assert 'executable "nd-my-command" not found' in stderr


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

    def test_nothing_happens_if_time_is_accurate(self, capfd, ntp_response_factory):
        """ Running nd with accurate system time does not print to stderr """

        ntp_response_factory(0)
        nd.check_system_clock(check_clock_freq=0)
        stdout, stderr = capfd.readouterr()
        assert 'WARNING:' not in stderr and 'ERROR:' not in stderr

    def test_warning_if_system_clock_is_too_far_behind(self, capfd, ntp_response_factory):
        """ Running nd with system time too far behind the threshold prints to stderr """

        ntp_response_factory(120)
        nd.check_system_clock(check_clock_freq=0)
        stdout, stderr = capfd.readouterr()
        assert re.search(r'The system clock is behind by \d+', stderr)

    def test_warning_if_system_clock_is_too_far_ahead(self, capfd, ntp_response_factory):
        """ Running nd with system time too far ahead the threshold prints to stderr """

        ntp_response_factory(-120)
        nd.check_system_clock(check_clock_freq=0)
        stdout, stderr = capfd.readouterr()
        assert re.search(r'The system clock is behind by -\d+', stderr)

    def test_nd_continues_if_get_ntp_time_times_out(self, capfd):
        """ Handle ntp request for current time timing out """

        with mock.patch.object(socket, 'socket') as mock_socket:
            mock_socket.return_value.recvfrom.side_effect = socket.timeout()
            nd.check_system_clock(check_clock_freq=0)
            stdout, stderr = capfd.readouterr()
            assert 'timed out.' in stderr

    def test_nd_continues_if_get_ntp_time_raises_socket_error(self, capfd):
        """ Handle ntp request for socket raising an error """

        with mock.patch.object(socket, 'socket') as mock_socket:
            mock_socket.return_value.sendto.side_effect = socket.error()
            nd.check_system_clock(check_clock_freq=0)
            stdout, stderr = capfd.readouterr()
            assert 'Error checking network time, exception: ' in stderr


class TestSplitCommandAndArguments(object):
    """ Handles lists of arguments and uses bash autocomplete return the command and args """

    def test_simple_command_name(self, executable_factory):
        """ Handle splitting a command on the path by itself without namespaces or arguments """

        executable_factory('nd-my-command', '')
        cmd_list_result, args_list_result = nd.split_command_and_arguments(['my-command'])
        assert cmd_list_result == 'nd-my-command'
        assert args_list_result == []

    def test_command_and_arguments_get_split(self, executable_factory):
        """ Handle splitting a command on the path with namespaces and arguments"""

        executable_factory('nd-my-namespace~my-subnamespace~my-command', '')

        args_list = ['my-namespace', 'my-subnamespace', 'my-command', 'arg1', 'arg2']
        cmd_list_result, args_list_result = nd.split_command_and_arguments(args_list)

        assert cmd_list_result == 'nd-my-namespace~my-subnamespace~my-command'
        assert args_list_result == ['arg1', 'arg2']

    def test_no_arguments(self, executable_factory):
        """ Handle splitting only a command's namespace without arguments  """

        executable_factory('nd-my-namespace~my-subnamespace~my-command', '')

        args_list = ['my-namespace', 'my-subnamespace', 'my-command']
        cmd_list_result, args_list_result = nd.split_command_and_arguments(args_list)

        assert cmd_list_result == 'nd-my-namespace~my-subnamespace~my-command'
        assert args_list_result == []

    def test_with_missing_command(self):
        """ Handle the list of arguments not containing a command that is in the path """

        with pytest.raises(nd.CommandNotFound) as e:
            nd.split_command_and_arguments(['my-command'])
            assert str(e) == 'my-command'
