from __future__ import print_function

import subprocess


def find_commands_that_start_with(prefix, functions_only=False):
    """ Returns a sorted list of the bash auto-completion for the given prefix.

    Args:
        prefix: Desired string to find the auto-completion of.
        functions_only: If true, the auto-completion will find only functions and not all commands

    Returns:
        A sorted list of auto-completion results.
    """
    if functions_only is False:
        opts = '-c'
    else:
        opts = 'abk -A function'

    try:
        results = subprocess.check_output('compgen {} "{}"'.format(opts, prefix),
                                          shell=True, executable='/bin/bash').decode('utf-8')
    except subprocess.CalledProcessError:
        return []
    else:
        return sorted(results.split())


def get_nd_namespace_autocompletion(namespace=''):
    prefix = 'nd-{}'.format(namespace)
    autocompleted_commands = find_commands_that_start_with(prefix)
    autocompleted_functions = find_commands_that_start_with(prefix, functions_only=True)

    namespace_autocomplete = set(autocompleted_commands) - set(autocompleted_functions)
    return sorted(list(namespace_autocomplete))
