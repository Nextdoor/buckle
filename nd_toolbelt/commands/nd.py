""" nd command

Executes sub-commands in nd namespace.

"""

import argparse
import os
import re
import shlex
import subprocess
import sys
import time


def parse_args(argv, known_only=True):
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    update_group = parser.add_mutually_exclusive_group()
    update_group.add_argument('--update', action='store_true', dest='force_update',
                              help='Forces update of nd-toolbelt before the given command is run')
    update_group.add_argument('--no-update', action='store_true', dest='skip_update',
                              help='Prevents update of nd-toolbelt before the given command is run')
    parser.add_argument('--update-freq', type=int, default=3600,
                        help='Minimum number of seconds between updates.')
    parser.add_argument('command', help='The desired app to run via the nd_toolbelt app!')
    parser.add_argument('args', nargs=argparse.REMAINDER,
                        help='Arguments to pass to the desired app')

    args_with_opts = shlex.split(os.getenv('ND_TOOLBELT_OPTS', "")) + list(argv[1:])

    if known_only:
        return parser.parse_args(args_with_opts)
    else:
        return parser.parse_known_args(args_with_opts)[0]  # Return only known args from tuple


def maybe_reload_with_updates(argv):
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

        # Allow unknown arguments if they may be present in future versions of nd
        known_args = parse_args(argv, known_only=False)

        try:
            updated_creation_date = os.path.getmtime(updated_path)
        except OSError:  # File doesn't exist
            needs_update = True
        else:
            current_time = time.time()
            needs_update = (current_time - updated_creation_date) >= known_args.update_freq

        if needs_update and not known_args.skip_update or known_args.force_update:
            subprocess.check_output('touch {}'.format(updated_path), shell=True)

            branch = subprocess.check_output(
                'git rev-parse --abbrev-ref HEAD', shell=True).decode('utf-8')
            process = subprocess.Popen('git pull origin {}'.format(branch), shell=True,
                                       stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, close_fds=True)
            output = process.stdout.read().decode('utf-8')
            process.communicate()  # Collect the return code

            if 'Already up-to-date.' not in output and process.returncode == 0:
                # Install the new version
                subprocess.check_output('pip install -e .', shell=True)
                os.execvp('nd', argv)  # Hand off to new nd version
            elif process.returncode != 0:
                sys.stderr.write('Unable to update repository.\n')


def main(argv=sys.argv):
    maybe_reload_with_updates(argv)

    args = parse_args(argv)

    command = 'nd-' + args.command

    try:
        app_path = subprocess.check_output(['which', command]).strip()
    except subprocess.CalledProcessError:
        sys.exit('ERROR: executable "{}" not found'.format(command))

    os.execv(app_path, [command] + args.args)

if __name__ == "__main__":
    main(sys.argv)
