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

from nd_toolbelt import help_formatters
from nd_toolbelt import message
from nd_toolbelt import autocomplete


def truncate(s, length=75):
    return s[:length - 3] + (s[length - 3:] and '...')


def print_help_for_all_commands(parser, args, namespace=()):
    prefix = 'nd-' + '~'.join(namespace)
    autocompleted_commands = autocomplete.get_executables_starting_with(prefix)

    nd_command_list = sorted(set(autocompleted_commands) - set(args.exclude))
    if not nd_command_list:
        if namespace:
            sys.exit(message.error('executable {} not found'.format(prefix)))
        else:
            sys.exit(message.error('No nd commands found on path. Check your $PATH.'))

    command_help_hash = {}
    for command in nd_command_list:
        try:
            command_help_text = subprocess.check_output(
               '{} --help 2> /dev/null'.format(command), shell=True).decode('utf-8')
        except subprocess.CalledProcessError:
            help_text = None
        else:
            # Return first paragraph that is not empty or starts with usage
            help_text = next((
                paragraph.replace('\n', '')
                for paragraph in re.split('\n\s*\n', command_help_text)
                if paragraph.strip() and not paragraph.startswith('usage: ')), None)

        command = re.sub('^nd-', '', command).replace('~', ' ')

        command_help_hash[command] = help_text or '<help not found>'

    rows, columns = os.popen('stty size', 'r').read().split()  # Get the console window size
    max_key_length = max(len(key) for key in command_help_hash.keys())

    parser.print_usage()
    print('\nThe available commands are:')

    for key, value in sorted(iteritems(command_help_hash)):
        # Right pads keys length and truncate text to fit in window
        print(truncate(('   {:<' + str(max_key_length) + '}   {}').format(key, value),
                       int(columns)))

    print("\nSee 'nd help <command|namespace>' for more "
          "information on a specific command or namespace.")


def main(argv=sys.argv):
    parser = argparse.ArgumentParser(
        formatter_class=help_formatters.DedentDescriptionArgumentDefaultsHelpFormatter,
        description="""\
        ND Toolbelt Help

        Also run 'nd readme' for more details about the ND Toolbelt project.
        """)
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
        # Check if help is being called for a given namespace instead of a specific command
        print_help_for_all_commands(parser, args, namespace=args.command)
    else:
        try:
            os.execv(app_path, [command, '--help'])
        except:
            sys.exit(message.error('executable {} could not be run'.format(command)))

if __name__ == "__main__":
    main(sys.argv)
