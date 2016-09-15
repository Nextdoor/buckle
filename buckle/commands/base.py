""" buckle command

Executes sub-commands in given namespace.

"""

from __future__ import print_function

import argparse
import os
import re
import shlex
import subprocess
import sys
import time

from buckle import system_clock
from buckle import message
from buckle import path as toolbelt_path


def flush_file_descriptors():
    sys.stdout.flush()
    sys.stderr.flush()


BUILTIN_TOOLBELT_NAME = 'buckle'

HELP_DESCRIPTION = """\
{toolbelt_name} Toolbelt centralizes {toolbelt_name} commands and tools.

Run '{toolbelt_name} help or '{toolbelt_name} readme' for more details about how to use and
extend the {toolbelt_name} Toolbelt.\
"""


class Command(object):
    def __init__(self, toolbelt_name):
        self._toolbelt_name = toolbelt_name
        self._message_sender = message.Sender(prefix=self._toolbelt_name + ':')

    @property
    def message(self):
        return self._message_sender

    @property
    def toolbelt_name(self):
        return self._toolbelt_name

    def parse_args(self, argv, known_only=True):
        """

        Args:
            argv: args excluding program name
            known_only: allow only arguments known to this version buckle

        Returns:
            Tuple:
                - toolbelt name
                - args

        """
        parser = argparse.ArgumentParser(
            prog=self.toolbelt_name,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description=HELP_DESCRIPTION.format(toolbelt_name=self.toolbelt_name.upper()))

        update_group = parser.add_mutually_exclusive_group()
        update_group.add_argument('--update', action='store_true', dest='force_update',
                                  help='Forces update of buckle before the given command is run')
        update_group.add_argument('--no-update', action='store_true', dest='skip_update',
                                  help='Prevents update of buckle before the given command is run')
        parser.add_argument('--update-freq', type=int, default=3600,
                            help='Minimum number of seconds between updates.')

        parser.add_argument('--no-clock-check', action='store_true', dest='skip_clock_check',
                            help='Do not check the system clock.')
        parser.add_argument('--check-clock-freq', type=int, default=600,
                            help='Minimum number of seconds between clock checks')

        parser.add_argument('--skip-dot-commands', action='store_true',
                            help='Do not run dot commands.')

        parser.add_argument('namespace', nargs='*', default=[],
                            help='The namespace path of the command to run.')
        parser.add_argument('command', nargs='?',
                            help='The command to run from the ND Toolbelt suite.')
        parser.add_argument('args', nargs=argparse.REMAINDER,
                            help='Arguments to pass to the command')

        args_with_opts = (shlex.split(os.getenv('BUCKLE_OPTS_' + self.toolbelt_name.upper(), '')) +
                          list(argv))

        if known_only:
            args = parser.parse_args(args_with_opts)
        else:
            args = parser.parse_known_args(args_with_opts)[0]

        all_args = args.namespace + list(filter(None, [args.command])) + args.args

        command = None
        toolbelt = self.toolbelt_name
        try:
            namespace, command, command_args = toolbelt_path.split_path_and_command(
                self.toolbelt_name, all_args)
        except toolbelt_path.CommandOrNamespaceNotFound as original_exception:
            try:
                # Now search builtin commands
                namespace, command, command_args = toolbelt_path.split_path_and_command(
                    BUILTIN_TOOLBELT_NAME, all_args)
                toolbelt = BUILTIN_TOOLBELT_NAME
            except toolbelt_path.CommandOrNamespaceNotFound:
                # Send help commands to help
                if original_exception.path[-1] == 'help':
                    namespace = list(original_exception.path[:-1])
                    # Let help to deal with the extra args
                    extra_args = all_args[len(original_exception.path):]
                    toolbelt = BUILTIN_TOOLBELT_NAME
                    namespace, command, command_args = ([], 'help', namespace + extra_args)
                else:
                    sys.exit(self.message.format_error(str(original_exception)))

        # Call help on the namespace if we have no command
        if not command:
            toolbelt = BUILTIN_TOOLBELT_NAME
            namespace, command, command_args = ([], 'help', namespace)

        args.namespace, args.command, args.args = (namespace, command, command_args)

        return toolbelt, args

    def maybe_reload_with_updates(self, argv):
        # Allow unknown arguments if they may be present in future versions of nd
        _, known_args = self.parse_args(argv, known_only=False)

        if known_args.skip_update:
            return

        buckle_root = os.getenv('BUCKLE_ROOT')

        # Get the repo location from pip if it isn't already defined
        if not buckle_root:
            output = subprocess.check_output(
                'pip show buckle --disable-pip-version-check', shell=True).decode('utf-8')
            matches = re.search("Location:\s+(/\S+)", output)
            if matches:
                buckle_root = matches.group(1)

        if buckle_root:
            updated_path = buckle_root + '/.updated'

            try:
                updated_creation_date = os.path.getmtime(updated_path)
            except OSError:  # File doesn't exist
                needs_update = True
            else:
                current_time = time.time()
                needs_update = (current_time - updated_creation_date) >= known_args.update_freq

            if needs_update or known_args.force_update:
                subprocess.check_output(['touch', updated_path])
                self.message.info('Checking for buckle updates...')

                # Disable password prompt
                env = os.environ.copy()
                env.update({'GIT_ASKPASS': '/bin/echo'})

                branch = subprocess.check_output(
                    'git rev-parse --abbrev-ref HEAD', cwd=buckle_root, shell=True).decode(
                    'utf-8')
                process = subprocess.Popen('git pull origin {}'.format(branch),
                                           cwd=buckle_root,
                                           shell=True, stdin=subprocess.PIPE,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.STDOUT, close_fds=True, env=env)
                output = process.stdout.read().decode('utf-8')
                process.communicate()  # Collect the return code

                if 'Already up-to-date.' not in output and process.returncode == 0:
                    self.message.info('Installing new buckle version...')
                    # Install the new version
                    subprocess.check_output('pip install -e .', cwd=buckle_root, shell=True)

                    flush_file_descriptors()
                    os.execvp(self.toolbelt_name, argv)  # Hand off to new version
                elif process.returncode != 0:
                    self.message.error('Unable to update repository.')

    def run_dot_commands(self, namespaces, command, args):
        for depth, namespace in enumerate([''] + namespaces):
            prefix = self.toolbelt_name + '-' + ''.join(ns + '~' for ns in namespaces[:depth])
            try:
                matches = subprocess.check_output('compgen -c "{}."'.format(prefix),
                                                  shell=True, executable='/bin/bash').decode(
                    'utf-8')
            except subprocess.CalledProcessError:
                continue  # No dot commands in current namespace

            for dot_command in sorted(set(matches.split())):  # Duplicates removed
                try:
                    subprocess.check_call([dot_command] + [' '.join(namespaces + [command])] + args)
                except subprocess.CalledProcessError:
                    sys.exit(self.message.format_error(
                        "Dot command '{}' failed.".format(dot_command)))

    def run(self, argv):
        toolbelt, args = self.parse_args(argv, known_only=False)
        self.maybe_reload_with_updates(argv)

        self.parse_args(argv, known_only=True)  # Ensure that arguments are all known at this point
        if not args.skip_clock_check:
            system_clock.check_system_clock(self.message, args.check_clock_freq)

        if not args.skip_dot_commands and not args.command.startswith('.'):
            self.run_dot_commands(args.namespace, args.command, args.args)

        flush_file_descriptors()
        path = toolbelt + '-{}'.format('~'.join(args.namespace + [args.command]))
        env = os.environ.copy()
        env['BUCKLE_TOOLBELT_NAME'] = self.toolbelt_name
        try:
            os.execvpe(path, [path] + args.args, env=env)  # Hand off to sub command
        except OSError:
            sys.exit(self.message.format_error("Command '{}' could not be run".format(path)))


def main(argv=sys.argv):
    toolbelt_name = os.getenv('BUCKLE_TOOLBELT_NAME', os.path.basename(argv[0]))
    Command(toolbelt_name).run(argv[1:])

if __name__ == "__main__":
    main(sys.argv)
