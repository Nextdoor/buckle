""" nd help command

Prints help descriptions for commands.

"""

from __future__ import print_function
from future.utils import iteritems

import argparse
import os
import re
import subprocess
import sys


def truncate(s, length=75):
    return s[:length - 3] + (s[length - 3:] and '...')


def print_help_for_all_commands(parser, args):
    nd_command_set = set(
        subprocess.check_output(
            'eval "$(nd init -)"; COMP_CWORD=1 _ndtoolbelt_autocomplete_hook; echo ${COMPREPLY[*]}',
            shell=True, executable='/bin/bash').decode('utf-8').split())
    nd_command_set -= set(args.exclude)

    command_help_hash = {}
    for command in nd_command_set:
        try:
            command_help_text = subprocess.check_output(
                'nd-{} --help 2> /dev/null'.format(command), shell=True).decode('utf-8')
        except subprocess.CalledProcessError:
            matches = None
        else:
            matches = re.search(r'\n\s*\n(.*?)\r?\n\s*\r?\n', command_help_text, flags=re.DOTALL)

        if matches:
            command_help_hash[command] = matches.group(1)
        else:
            command_help_hash[command] = "<help not found>"

    rows, columns = os.popen('stty size', 'r').read().split()  # Get the console window size
    max_key_length = max(len(key) for key in command_help_hash.keys())

    parser.print_usage()
    print('\nThe available commands are:')

    for key, value in sorted(iteritems(command_help_hash)):
        # Right pads keys length and truncate text to fit in window
        print(truncate(('   {:<' + str(max_key_length) + '}   {}').format(
            key, value.replace('\n', '')), int(columns)))

    print("\nSee 'nd help <command>' for more information on a specific command.")


def main(argv=sys.argv):
    parser = argparse.ArgumentParser(description='ND Toolbelt Help Tool',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('command', nargs='?', help='name of nd sub-command')
    parser.add_argument('--exclude', action='append', default=['memcache-top'],
                        help='nd commands to exclude from help')
    args = parser.parse_args(argv[1:])

    if args.command:
        command = 'nd-' + args.command

        try:
            app_path = subprocess.check_output(['which', command]).strip()
        except subprocess.CalledProcessError:
            sys.exit('ERROR: executable "%s" not found' % command)

        os.execv(app_path, [command, '--help'])
    else:
        print_help_for_all_commands(parser, args)

if __name__ == "__main__":
    main(sys.argv)
