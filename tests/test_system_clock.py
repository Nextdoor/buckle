import mock
import re
import socket
import struct
import time

import pytest

from buckle import message
from buckle import system_clock

from fixtures import readerr, readout  # noqa


class TestCheckSystemClock:
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

    def setup(self):
        self.message = message.Sender('test')

    def test_nothing_happens_if_time_is_accurate(self, readerr, ntp_response_factory):
        """ Running nd with accurate system time does not print to readerr """

        ntp_response_factory(0)
        with readerr() as err:
            system_clock.check_system_clock(self.message, check_clock_freq=0)
        assert 'WARNING:' not in err and 'ERROR:' not in err

    def test_warning_if_system_clock_is_too_far_behind(self, readerr, ntp_response_factory):
        """ Running nd with system time too far behind the threshold prints to readerr """

        ntp_response_factory(120)
        with readerr() as err:
            system_clock.check_system_clock(self.message, check_clock_freq=0)
        assert re.search(r'The system clock is behind by \d+', str(err))

    def test_warning_if_system_clock_is_too_far_ahead(self, readerr, ntp_response_factory):
        """ Running buckle with system time too far ahead the threshold prints to readerr """

        ntp_response_factory(-120)
        with readerr() as err:
            system_clock.check_system_clock(self.message, check_clock_freq=0)
        assert re.search(r'The system clock is behind by -\d+', str(err))

    def test_nd_continues_if_get_ntp_time_times_out(self, readerr):
        """ Handle ntp request for current time timing out """

        with mock.patch.object(socket, 'socket') as mock_socket:
            mock_socket.return_value.recvfrom.side_effect = socket.timeout()
            with readerr() as err:
                system_clock.check_system_clock(self.message, check_clock_freq=0)
            assert 'timed out.' in err

    def test_nd_continues_if_get_ntp_time_raises_socket_error(self, readerr):
        """ Handle ntp request for socket raising an error """

        with mock.patch.object(socket, 'socket') as mock_socket:
            mock_socket.return_value.sendto.side_effect = socket.error()
            with readerr() as err:
                system_clock.check_system_clock(self.message, check_clock_freq=0)
            assert 'Error checking network time, exception: ' in err
