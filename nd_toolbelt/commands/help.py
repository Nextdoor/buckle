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

from nd_toolbelt import message
from nd_toolbelt import autocomplete


class NoCommandsInNamespace(Exception):
    pass


def truncate(s, length=75):
    return s[:length - 3] + (s[length - 3:] and '...')


def print_help_for_all_commands(parser, args, namespace=()):
    prefix = 'nd-' + '~'.join(namespace)
    autocompleted_commands = autocomplete.get_executables_starting_with(prefix)

    nd_command_list = sorted(set(autocompleted_commands) - set(args.exclude))
    if not nd_command_list:
        raise NoCommandsInNamespace()

    command_help_hash = {}
    for command in nd_command_list:
        try:
            command_help_text = subprocess.check_output(
               '{} --help 2> /dev/null'.format(command), shell=True).decode('utf-8')
        except subprocess.CalledProcessError:
            matches = None
        else:
            # Parse the command's help for the general description
            matches = re.search(r'(?:usage:.*?\n\s*\n)?(.*?)\r?\n\s*\r?\n', command_help_text,
                                flags=re.DOTALL)

        command = re.sub('^nd-', '', command).replace('~', ' ')
        if matches:
            command_help_hash[command] = matches.group(1)
        else:
            command_help_hash[command] = '<help not found>'

    rows, columns = os.popen('stty size', 'r').read().split()  # Get the console window size
    max_key_length = max(len(key) for key in command_help_hash.keys())

    parser.print_usage()
    print('\nThe available commands are:')

    for key, value in sorted(iteritems(command_help_hash)):
        # Right pads keys length and truncate text to fit in window
        print(truncate(('   {:<' + str(max_key_length) + '}   {}').format(
            key, value.replace('\n', '')), int(columns)))

    print("\nSee 'nd help <command|namespace>' for more "
          "information on a specific command or namespace.")


def main(argv=sys.argv):
    parser = argparse.ArgumentParser(description='ND Toolbelt Help Tool',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('command', nargs='*', help='name of nd sub-command')
    parser.add_argument('--exclude', action='append', default=['nd-memcache-top'],
                        help='nd commands to exclude from help')
    args = parser.parse_args(argv[1:])

    command = 'nd-' + '~'.join(args.command)  # Handle namespaces if they exist

    if command in args.exclude:
        sys.exit(message.error('executable {} excluded from nd help'.format(command)))

    try:
        app_path = subprocess.check_output(['which', command]).strip()
    except subprocess.CalledProcessError:
        try:
            # Check if help is being called for a given namespace instead of a specific command
            print_help_for_all_commands(parser, args, namespace=args.command)
        except NoCommandsInNamespace:
            sys.exit(message.error('executable {} not found'.format(command)))
    else:
        os.execv(app_path, [command, '--help'])

if __name__ == "__main__":
    main(sys.argv)
