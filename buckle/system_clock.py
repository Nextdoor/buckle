import os
import subprocess
import tempfile
import time

from buckle import ntp


DEFAULT_NTP_HOST = 'time.apple.com'
CHECK_CLOCK_TIMEOUT = 2  # Only wait for ntp for 2 seconds
MAX_CLOCK_SKEW_TIME = 60  # Time in seconds to tolerate for system clock offset


def check_system_clock(message, check_clock_freq, ntp_host=DEFAULT_NTP_HOST,
                       ntp_timeout=CHECK_CLOCK_TIMEOUT):
    clock_checked_path = os.path.join(tempfile.gettempdir(), '.buckle_clock_last_checked')
    current_time = time.time()

    try:
        clock_checked_date = os.path.getmtime(clock_checked_path)
    except OSError:  # File doesn't exist
        check_clock = True
    else:
        check_clock = (current_time - clock_checked_date >= check_clock_freq or
                       check_clock_freq == 0)

    if check_clock:
        message.info('Checking that the current machine time is accurate...')

        # Time in seconds since 1970 epoch
        system_time = current_time

        try:
            network_time = ntp.get_ntp_time(host=ntp_host, timeout=ntp_timeout)
        except ntp.NtpTimeError as e:
            message.error('Error checking network time, exception: {}'.format(e))
            return

        time_difference = network_time - system_time

        if abs(time_difference) >= MAX_CLOCK_SKEW_TIME:
            message.warning(
                'The system clock is behind by {} seconds.'
                ' Please run "sudo ntpdate -u time.apple.com".'.format(int(time_difference)))
            try:
                os.remove(clock_checked_path)  # Ensure sure clock is checked on next run
            except OSError:
                pass
        else:
            subprocess.check_output(['touch', clock_checked_path])

