from __future__ import print_function

import subprocess


def find_commands_that_start_with(prefix, functions_only=False):
    """ Returns a sorted list of the commands with the given prefix on the path.

    Args:
        prefix: String to match the beginning of commands in path to.
        functions_only: Bool determining whether only functions are returned.

    Returns:
        A sorted list of commands that start with the given prefix.
    """

    if functions_only is False:
        opts = '-c'
    else:
        opts = 'abk -A function'

    try:
        results = subprocess.check_output('compgen {} "{}"'.format(opts, prefix),
                                          shell=True, executable='/bin/bash').decode('utf-8')
    except subprocess.CalledProcessError as e:
        return []
    else:
        return sorted(results.split())


def get_executables_starting_with(prefix=''):
    """ Returns a list of executables that start with the given nd namespace.

    Args:
        prefix: String prefix to match the beginning of executables in path to.

    Returns:
        A sorted list of all executables in the given nd namespace.
    """

    commands_list = find_commands_that_start_with(prefix)
    functions_list = find_commands_that_start_with(prefix, functions_only=True)

    namespace_executables = set(commands_list) - set(functions_list)
    return sorted(list(namespace_executables))
