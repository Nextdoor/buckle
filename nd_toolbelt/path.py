from nd_toolbelt import autocomplete


class CommandOrNamespaceNotFound(Exception):
    prefix = 'Command or namespace'

    def __init__(self, path):
        self.path = tuple(path)

    def __str__(self):
        error_message = "{} '{}' not found".format(self.prefix, self.path[-1])

        namespace = self.path[:-1]
        if namespace:
            error_message += " in '{}'".format(' '.join(namespace))

        return error_message + '.'


class CommandNotFound(CommandOrNamespaceNotFound):
    prefix = 'Command'


def split_path_and_command(args, parse_help=False):
    """ Parses a list of arguments and separates a command from its arguments and namespace.

    Args:
        args: a list of arguments to be parsed.
        parse_help: a bool determining whether to convert path to a help command

    Returns:
        Tuple:
            - Namespaces: A list of strings of the path through the namespaces
            - Command: A string of the command name if it exists(?)
            - Args: A list of strings containing the arguments to pass into the command

    Raises:
        CommandNotFound
        CommandOrNamespaceNotFound
    """

    # Try increasingly long command names until command can't be found
    for cmd_end, arg in enumerate(args):
        path = list(args[:cmd_end])
        rest = list(args[cmd_end+1:])
        prefix = 'nd-' + '~'.join(path + [arg])
        possible_executables = autocomplete.get_executables_starting_with(prefix)

        if possible_executables == [prefix]:
            return path, arg, rest
        elif parse_help and arg == 'help':
            return [], 'help', path + rest
        elif parse_help and possible_executables and not rest:
            return [], 'help', path + [arg]  # 'nd help' on a namespace
        elif possible_executables and not rest:
            return path + [arg], None, []  # Namespace only
        elif not possible_executables:
            if rest:
                raise CommandOrNamespaceNotFound(path + [arg])
            else:
                raise CommandNotFound(path + [arg])

    return [], 'help' if parse_help else None, []  # Handle being called with no arguments
