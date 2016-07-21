""" nd command

Executes sub-commands in nd namespace.

"""

from __future__ import print_function

import argparse
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time

from nd_toolbelt import help_formatters
from nd_toolbelt import ntp
from nd_toolbelt import message
from nd_toolbelt import path as toolbelt_path


DEFAULT_NTP_HOST = 'time.apple.com'
CHECK_CLOCK_TIMEOUT = 2  # Only wait for ntp for 2 seconds
MAX_CLOCK_SKEW_TIME = 60  # Time in seconds to tolerate for system clock offset


def flush_file_descriptors():
    sys.stdout.flush()
    sys.stderr.flush()


def parse_args(argv, known_only=True):
    parser = argparse.ArgumentParser(
        formatter_class=help_formatters.DedentDescriptionArgumentDefaultsHelpFormatter,
        description="""\
        ND Toolbelt centralizes ND commands and tools.

        Run 'nd help or 'nd readme' for more details about how to use and extend the ND Toolbelt.\
        """)

    update_group = parser.add_mutually_exclusive_group()
    update_group.add_argument('--update', action='store_true', dest='force_update',
                              help='Forces update of nd-toolbelt before the given command is run')
    update_group.add_argument('--no-update', action='store_true', dest='skip_update',
                              help='Prevents update of nd-toolbelt before the given command is run')
    parser.add_argument('--update-freq', type=int, default=3600,
                        help='Minimum number of seconds between updates.')

    parser.add_argument('--no-clock-check', action='store_true', dest='skip_clock_check',
                        help='Do not check the system clock.')
    parser.add_argument('--check-clock-freq', type=int, default=600,
                        help='Minimum number of seconds between clock checks')

    parser.add_argument('namespace', nargs='*', default=[],
                        help='The namespace path of the command to run.')
    parser.add_argument('command', nargs='?',
                        help='The command to run from the ND Toolbelt suite.')
    parser.add_argument('args', nargs=argparse.REMAINDER,
                        help='Arguments to pass to the command')

    args_with_opts = shlex.split(os.getenv('ND_TOOLBELT_OPTS', '')) + list(argv[1:])

    if known_only:
        args = parser.parse_args(args_with_opts)
    else:
        args = parser.parse_known_args(args_with_opts)[0]

    all_args = args.namespace + list(filter(None, [args.command])) + args.args

    try:
        namespace, command, command_args = toolbelt_path.split_path_and_command(all_args)
    except toolbelt_path.CommandOrNamespaceNotFound as e:
        # Send help commands to nd-help
        if e.path[-1] == 'help':
            namespace = list(e.path[:-1])
            extra_args = all_args[len(e.path):]  # Let nd-help to deal with the extra args
            namespace, command, command_args = ([], 'help', namespace + extra_args)
        else:
            sys.exit(message.format_error(str(e)))
    else:
        # Call nd-help on the namespace if we have no command
        if not command:
            namespace, command, command_args = ([], 'help', namespace)

    args.namespace, args.command, args.args = (
        namespace, 'nd-{}'.format('~'.join(namespace + [command])), command_args)

    return args


def maybe_reload_with_updates(argv):
    # Allow unknown arguments if they may be present in future versions of nd
    known_args = parse_args(argv, known_only=False)

    if known_args.skip_update:
        return

    nd_toolbelt_root = os.getenv('ND_TOOLBELT_ROOT')

    # Get the repo location from pip if it isn't already defined
    if not nd_toolbelt_root:
        output = subprocess.check_output(
            'pip show nd-toolbelt --disable-pip-version-check', shell=True).decode('utf-8')
        matches = re.search("Location:\s+(/\S+)", output)
        if matches:
            nd_toolbelt_root = matches.group(1)

    if nd_toolbelt_root:
        updated_path = nd_toolbelt_root + '/.updated'

        try:
            updated_creation_date = os.path.getmtime(updated_path)
        except OSError:  # File doesn't exist
            needs_update = True
        else:
            current_time = time.time()
            needs_update = (current_time - updated_creation_date) >= known_args.update_freq

        if needs_update or known_args.force_update:
            subprocess.check_output(['touch', updated_path])
            message.info('Checking for toolbelt updates...')

            branch = subprocess.check_output(
                'git rev-parse --abbrev-ref HEAD', cwd=nd_toolbelt_root, shell=True).decode('utf-8')
            process = subprocess.Popen('git pull origin {}'.format(branch), cwd=nd_toolbelt_root,
                                       shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, close_fds=True)
            output = process.stdout.read().decode('utf-8')
            process.communicate()  # Collect the return code

            if 'Already up-to-date.' not in output and process.returncode == 0:
                message.info('Installing new toolbelt version...')
                # Install the new version
                subprocess.check_output('pip install -e .', cwd=nd_toolbelt_root, shell=True)

                flush_file_descriptors()
                os.execvp('nd', argv)  # Hand off to new nd version
            elif process.returncode != 0:
                message.error('Unable to update repository.')


def check_system_clock(check_clock_freq, ntp_host=DEFAULT_NTP_HOST,
                       ntp_timeout=CHECK_CLOCK_TIMEOUT):
    clock_checked_path = os.path.join(tempfile.gettempdir(), '.nd_toolbelt_clock_last_checked')
    current_time = time.time()

    try:
        clock_checked_date = os.path.getmtime(clock_checked_path)
    except OSError:  # File doesn't exist
        check_clock = True
    else:
        check_clock = current_time - clock_checked_date >= check_clock_freq or check_clock_freq == 0

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


def main(argv=sys.argv):
    args = parse_args(argv, known_only=False)
    maybe_reload_with_updates(argv)

    parse_args(argv, known_only=True)  # Ensure that arguments are all known at this point
    if not args.skip_clock_check:
        check_system_clock(args.check_clock_freq)

    flush_file_descriptors()
    try:
        os.execvp(args.command, [args.command] + args.args)  # Hand off to nd command
    except OSError:
        sys.exit(message.format_error("Command '{}' could not be run".format(args.command)))

if __name__ == "__main__":
    main(sys.argv)
