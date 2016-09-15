from buckle import autocomplete


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


def split_path_and_command(toolbelt_name, args, namespace_separator='~'):
    """ Parses a list of arguments and separates a command from its arguments and namespace.

    Args:
        toolbelt_name: name of the toolbelt
        args: a list of arguments to be parsed.

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

        prefix = toolbelt_name + '-' + namespace_separator.join(path + [arg])

        # Find executables where the prefix is the whole command or the prefix is a complete
        # namespace
        possible_executables = [
            p for p in autocomplete.get_executables_starting_with(prefix)
            if p == prefix or p.startswith(prefix + namespace_separator)]

        if possible_executables == [prefix]:
            return path, arg, rest
        elif possible_executables and not rest:
            return path + [arg], None, []  # Namespace only
        elif not possible_executables:
            if rest:
                raise CommandOrNamespaceNotFound(path + [arg])
            else:
                raise CommandNotFound(path + [arg])

    return [], None, []  # Handle being called with no arguments
