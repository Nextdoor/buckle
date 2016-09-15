import mock
import socket

import pytest

from buckle import ntp


class TestGetNtpTimeClass(object):
    def test_that_nd_continues_if_get_ntp_time_times_out(self, capfd):
        with pytest.raises(ntp.NtpTimeError):
            ntp.get_ntp_time(host='time.apple.com', timeout=0.00000000000001)
            stdout, stderr = capfd.readouterr()
            assert 'timed out.' in stderr

    def test_that_nd_continues_if_get_ntp_time_host_fails(self, capfd):
        with pytest.raises(ntp.NtpTimeError):
            ntp.get_ntp_time(host='somesitethatdefinitelywillneverexist', timeout=2)
            stdout, stderr = capfd.readouterr()
            assert '[Errno -2] Name or service not known' in stderr

    def test_that_nd_continues_if_ntp_time_returns_a_general_exception(self, capfd):
        fake_socket = mock.Mock()
        fake_socket.recvfrom = mock.Mock(side_effect=socket.error('my error'))

        with pytest.raises(ntp.NtpTimeError):
            with mock.patch.object(socket, 'socket', return_value=fake_socket):
                ntp.get_ntp_time(host='time.apple.com', timeout=2)
            stdout, stderr = capfd.readouterr()
            assert 'my error' in stderr
