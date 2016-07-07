import mock
import os
import re
import socket
import stat
import struct
import time

import pytest  # flake8: noqa

from nd_toolbelt.commands import nd
from nd_toolbelt import autocomplete

STAT_OWNER_EXECUTABLE = stat.S_IEXEC


class TestNdCommandClass:
    def test_nd_update_and_no_update_cannot_be_set_together(self, capfd):
        with pytest.raises(SystemExit):
            nd.main(['nd', '--update', '--no-update', 'version'])
        stdout, stderr = capfd.readouterr()
        assert '--no-update: not allowed with argument --update' in stderr

    def test_with_no_args(self, capfd):
        with pytest.raises(SystemExit):
            nd.main(['nd', '--no-update', '--no-clock-check'])
        stdout, stderr = capfd.readouterr()
        assert 'usage: ' in stderr

    def test_with_command(self, monkeypatch, tmpdir):
        monkeypatch.setenv('PATH', tmpdir, prepend=':')
        test_cmd_path = str(tmpdir) + '/nd-my-command'

        with open(test_cmd_path, 'w+'):
            st = os.stat(test_cmd_path)
            os.chmod(test_cmd_path, st.st_mode | STAT_OWNER_EXECUTABLE)  # Make cmd executable

            with mock.patch.object(os, 'execvp') as execvp:
                with mock.patch.object(autocomplete, 'get_executables_starting_with',
                                       return_value=['nd-my-command']):
                    nd.main(['nd', '--no-update', '--no-clock-check', 'my-command'])
                    execvp.call_args = ['nd-my-command', ['nd-my-command']]

    def test_command_with_argument(self, monkeypatch, tmpdir):
        monkeypatch.setenv('PATH', tmpdir, prepend=':')
        test_cmd_path = str(tmpdir) + '/nd-my-command'

        with open(test_cmd_path, 'w+'):
            st = os.stat(test_cmd_path)
            os.chmod(test_cmd_path, st.st_mode | STAT_OWNER_EXECUTABLE)  # Make cmd executable

            with mock.patch.object(os, 'execvp') as execvp:
                with mock.patch.object(autocomplete, 'get_executables_starting_with',
                                       return_value=['nd-my-command']):
                    nd.main(['nd', '--no-update', '--no-clock-check', 'my-command', 'my-arg'])
                    execvp.call_args = ['nd-my-command', ['nd-my-command', 'my-arg']]

    def test_command_not_found(self, capfd):
        with pytest.raises(SystemExit):
            nd.main(['nd', 'my-command'])
        stdout, stderr = capfd.readouterr()
        assert 'executable "nd-my-command" not found' in stderr


def generate_ntp_time_string(offset=0):
    time_since_1900 = int(time.time()) + 2208988800
    return struct.pack('!12I', *(([0] * 10) + [time_since_1900 + offset] + [0]))


class TestNdCheckSystemClockClass(object):
    def test_nd_does_nothing_if_time_is_accurate_when_clock_check_is_required(self, capfd):
        fake_socket = mock.Mock()
        fake_socket.recvfrom = mock.Mock(return_value=(generate_ntp_time_string(), ''))
        with mock.patch.object(socket, 'socket', return_value=fake_socket):
            nd.check_system_clock(check_clock_freq=0)
            stdout, stderr = capfd.readouterr()
            assert 'WARNING:' not in stderr and 'ERROR:' not in stderr

    def test_warning_if_system_clock_is_too_far_behind(self, capfd):
        fake_socket = mock.Mock()
        fake_socket.recvfrom = mock.Mock(return_value=(generate_ntp_time_string(offset=120), ''))
        with mock.patch.object(socket, 'socket', return_value=fake_socket):
            nd.check_system_clock(check_clock_freq=0)
        stdout, stderr = capfd.readouterr()
        assert re.search(r'The system clock is behind by \d+', stderr)

    def test_warning_if_system_clock_is_too_far_ahead(self, capfd):
        fake_socket = mock.Mock()
        fake_socket.recvfrom = mock.Mock(return_value=(generate_ntp_time_string(offset=-120), ''))
        with mock.patch.object(socket, 'socket', return_value=fake_socket):
            nd.check_system_clock(check_clock_freq=0)
        stdout, stderr = capfd.readouterr()
        assert re.search(r'The system clock is behind by -\d+', stderr)

    def test_nd_continues_if_get_ntp_time_times_out(self, capfd):
        nd.check_system_clock(check_clock_freq=0, ntp_timeout=0.00000000000001)
        stdout, stderr = capfd.readouterr()
        assert 'timed out.' in stderr


class TestSeparateCommandAndArgumentsClass(object):
    def test_simple_command_name(self, monkeypatch, tmpdir):
        monkeypatch.setenv('PATH', tmpdir, prepend=':')
        test_cmd_path = str(tmpdir) + '/nd-my-command'

        with open(test_cmd_path, 'w+'):
            st = os.stat(test_cmd_path)
            os.chmod(test_cmd_path, st.st_mode | STAT_OWNER_EXECUTABLE)  # Make cmd executable
            args_list = ['my-command']

            cmd_list_result, args_list_result = nd.separate_command_and_arguments(args_list)
            assert cmd_list_result == 'nd-my-command'
            assert args_list_result == []

    def test_command_and_arguments_get_separated(self, monkeypatch, tmpdir):
        monkeypatch.setenv('PATH', tmpdir, prepend=':')
        test_cmd_path = str(tmpdir) + '/nd-my-namespace~my-subnamespace~my-test-command'

        with open(test_cmd_path, 'w+'):
            st = os.stat(test_cmd_path)
            os.chmod(test_cmd_path, st.st_mode | STAT_OWNER_EXECUTABLE)  # Make cmd executable
            args_list = ['my-namespace', 'my-subnamespace', 'my-test-command', 'arg1', 'arg2']

            cmd_list_result, args_list_result = nd.separate_command_and_arguments(args_list)
            assert cmd_list_result == 'nd-my-namespace~my-subnamespace~my-test-command'
            assert args_list_result == ['arg1', 'arg2']

    def test_no_arguments(self, monkeypatch, tmpdir):
        monkeypatch.setenv('PATH', tmpdir, prepend=':')
        test_cmd_path = str(tmpdir) + '/nd-my-namespace~my-subnamespace~my-test-command'

        with open(test_cmd_path, 'w+'):
            st = os.stat(test_cmd_path)
            os.chmod(test_cmd_path, st.st_mode | STAT_OWNER_EXECUTABLE)  # Make cmd executable
            args_list = ['my-namespace', 'my-subnamespace', 'my-test-command']

            cmd_list_result, args_list_result = nd.separate_command_and_arguments(args_list)
            assert cmd_list_result == 'nd-my-namespace~my-subnamespace~my-test-command'
            assert args_list_result == []

    def test_with_missing_command(self):
        with pytest.raises(nd.CommandNotFound) as e:
            nd.separate_command_and_arguments(['my-test-command'])
            assert str(e) == 'my-test-command'
