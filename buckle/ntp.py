import socket
import struct


class NtpTimeError(Exception):
    pass


# From http://blog.mattcrampton.com/post/88291892461/query-an-ntp-server-from-python
def get_ntp_time(host, timeout):
    """ Returns a long of the time from the given ntp host server.
    If the server does not exist or times out, returns None.

    Args:
        host: ntp host url to query.
        timeout: Length of time to wait for ntp host.

    Returns:
        ntp host server's time as a string.
    """

    # reference time (in seconds since 1900-01-01 00:00:00)
    TIME1970 = 2208988800  # 1970-01-01 00:00:00

    # connect to server
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.settimeout(timeout)

    try:
        s = '\x1b' + 47 * '\0'
        client.sendto(s.encode(), (host, 123))
        msg, _ = client.recvfrom(1024)
    except socket.timeout:
        raise NtpTimeError('Request to ntp host "{}" timed out.'.format(host))
    except socket.error as e:
        raise NtpTimeError("General exception: {}".format(str(e)))

    t = struct.unpack('!12I', msg)[10]
    return t - TIME1970
