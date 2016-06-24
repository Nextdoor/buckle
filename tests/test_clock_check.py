import mock
import re
import socket
import struct
import time

import pytest  # flake8: noqa

from nd_toolbelt.commands import nd


def generate_ntp_time_string(offset=0):
    time_since_1900 = int(time.time()) + 2208988800
    return struct.pack('!12I', *(([0] * 10) + [time_since_1900 + offset] + [0]))


class TestNdCheckSystemClockClass(object):
    def test_that_nd_does_nothing_if_time_is_accurate_when_clock_check_is_required(self, capfd):
        fake_socket = mock.Mock()
        fake_socket.recvfrom = mock.Mock(return_value=(generate_ntp_time_string(), ''))
        with mock.patch.object(socket, 'socket', return_value=fake_socket):
            nd.check_system_clock(check_clock_freq=0)
            stdout, stderr = capfd.readouterr()
            assert stderr == 'Checking that the current machine time is accurate...\n'

    def test_check_system_clock_prints_an_warning_if_system_clock_is_too_far_behind(self, capfd):
        fake_socket = mock.Mock()
        fake_socket.recvfrom = mock.Mock(return_value=(generate_ntp_time_string(offset=120), ''))
        with mock.patch.object(socket, 'socket', return_value=fake_socket):
            nd.check_system_clock(check_clock_freq=0)
        stdout, stderr = capfd.readouterr()
        assert re.search(r'The system clock is behind by \d+', stderr)

    def test_check_system_clock_prints_an_warning_if_system_clock_is_too_far_ahead(self, capfd):
        fake_socket = mock.Mock()
        fake_socket.recvfrom = mock.Mock(return_value=(generate_ntp_time_string(offset=-120), ''))
        with mock.patch.object(socket, 'socket', return_value=fake_socket):
            nd.check_system_clock(check_clock_freq=0)
        stdout, stderr = capfd.readouterr()
        assert re.search(r'The system clock is behind by -\d+', stderr)

    def test_that_nd_continues_if_get_ntp_time_times_out(self, capfd):
        nd.check_system_clock(check_clock_freq=0, ntp_timeout=0.00000000000001)
        stdout, stderr = capfd.readouterr()
        assert 'timed out.' in stderr
