""" buckle help command

Prints help descriptions for commands.

"""

from __future__ import print_function

import argparse
import os
import re
import shlex
import subprocess
import sys

from buckle import autocomplete
from buckle import help_formatters
from buckle import message
from buckle import path as toolbelt_path


HELP_DESCRIPTION = """\
{toolbelt_upper} Toolbelt Help

Showing help for {tool_names}\
"""

TOOLBELT_DESCRIPTION = """\
For more details about the toolbelt, run '{toolbelt} readme'.

Run '{toolbelt} help <command|namespace>' for more information on a specific command or namespace.\
"""


def truncate(s, length=75):
    return s[:length - 3] + (s[length - 3:] and '...')


def print_help_for_all_commands(toolbelt_name, parser, args, path=()):
    prefix = toolbelt_name + '-' + '~'.join(path)

    sender = message.Sender(toolbelt_name)

    autocompleted_commands = [
        c for c in (autocomplete.get_executables_starting_with(prefix) +
                    autocomplete.get_executables_starting_with('buckle-'))
        if not re.search('.completion(..*)?$', c)]

    command_list = sorted(set(autocompleted_commands) - set(args.exclude))
    if not command_list:
        if not path:
            sys.exit(sender.format_error(
                'No {} commands found on path. Check your $PATH.'.format(toolbelt_name)))

    command_help_hash = {}
    for command in command_list:
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

        command_path = re.sub('^{}-'.format(toolbelt_name), '', command).split('~')

        command_help_hash[tuple(command_path)] = help_text or '<help not found>'

    print(HELP_DESCRIPTION.format(toolbelt_upper=toolbelt_name.upper(), tool_names=(
        ' '.join(path) if path else "all {} Toolbelt commands".format(toolbelt_name.upper()))))

    print('\nThe available commands are:')

    columns = os.getenv('COLUMNS')
    if not columns:
        rows, columns = os.popen('stty size', 'r').read().split()  # Get the console window size

    max_key_length = max([0] + [len(' '.join(path)) for path in command_help_hash.keys()])

    last_path = None

    for command_path, value in sorted(command_help_hash.items(),
                                      key=lambda item: (
                                              len(item[0]) > 1,  # commands without namespace first
                                              item[0])):
        name = ' '.join(command_path)

        # Insert a line if we're starting a new namespace
        if not last_path or command_path[:-1] != last_path[:-1]:
            print()

        # Right pads keys length and truncate text to fit in window
        print(truncate(('   {:<' + str(max_key_length) + '}   {}').format(name, value),
                       int(columns)))

        last_path = command_path

    print(TOOLBELT_DESCRIPTION.format(toolbelt=toolbelt_name))


def main(argv=sys.argv):
    toolbelt_name = os.getenv('BUCKLE_TOOLBELT_NAME', 'buckle')
    sender = message.Sender(toolbelt_name)
    parser = argparse.ArgumentParser(
        formatter_class=help_formatters.DedentDescriptionArgumentDefaultsHelpFormatter,
        description="{} Toolbelt Help".format(toolbelt_name.upper()))
    parser.add_argument('path', nargs='*', help='name of {} sub-command'.format(toolbelt_name))
    parser.add_argument('--exclude', '-X', action='append', default=[],
                        help='commands to exclude from help')

    args_with_opts = (shlex.split(os.getenv('BUCKLE_HELP_OPTS_' + toolbelt_name.upper(), '')) +
                      list(argv[1:]))
    args = parser.parse_args(args_with_opts)

    path = '{}-'.format(toolbelt_name) + '~'.join(args.path)  # Handle namespaces if they exist

    if path in args.exclude:
        sys.exit(sender.format_error("Command '{}' is excluded from help".format(path)))

    try:
        namespace, command, _ = toolbelt_path.split_path_and_command(toolbelt_name, args.path)
    except toolbelt_path.CommandOrNamespaceNotFound as e:
        sys.exit(sender.format_error(str(e)))

    if command:
        path = '{}-{}'.format(toolbelt_name, '~'.join(namespace + [command]))
        try:
            os.execvp(path, [path, '--help'])
        except OSError:
            sys.exit(sender.format_error("Command '{}' could not be run".format(path)))
    else:
        print_help_for_all_commands(toolbelt_name, parser, args, path=args.path)

if __name__ == "__main__":
    main(sys.argv)
