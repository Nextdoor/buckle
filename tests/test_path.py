import pytest  # flake8: noqa

from fixtures import executable_factory, run_as_child

from nd_toolbelt import path


def split(*args, **kwargs):
    return path.split_path_and_command(args, **kwargs)


class TestSplitPathAndCommand(object):
    """ Handles lists of arguments and uses bash autocomplete return the command and args """

    def test_simple_command_name(self, executable_factory):
        """ Handle splitting a command on the path by itself without namespaces or arguments """

        executable_factory('nd-my-command', '')
        assert ([], 'my-command', []) == split('my-command')

    def test_namespace_and_command_and_arguments_get_split(self, executable_factory):
        """ Handle splitting a command on the path with namespaces and arguments"""

        executable_factory('nd-my-namespace~my-subnamespace~my-command', '')

        assert (['my-namespace', 'my-subnamespace'], 'my-command', []) == \
               split('my-namespace', 'my-subnamespace', 'my-command')
        assert (['my-namespace', 'my-subnamespace'], 'my-command', ['arg1', 'arg2']) == \
               split('my-namespace', 'my-subnamespace', 'my-command', 'arg1', 'arg2')

    def test_raises_missing_command_or_namespace(self, executable_factory):
        """ Handle the list of arguments not containing a command that is in the path """

        executable_factory('nd-my-namespace~my-command')

        with pytest.raises(path.CommandNotFound) as e:
            split('my-command')
        assert e.value.path == ('my-command',)

        with pytest.raises(path.CommandOrNamespaceNotFound) as e:
            split('missing', 'some-arg')
        assert e.value.path == ('missing',)

        with pytest.raises(path.CommandNotFound) as e:
            split('my-namespace', 'missing')
        assert e.value.path == ('my-namespace', 'missing')

        with pytest.raises(path.CommandOrNamespaceNotFound) as e:
            split('my-namespace', 'missing', 'some-arg')
        assert e.value.path == ('my-namespace', 'missing')

        with pytest.raises(path.CommandOrNamespaceNotFound) as e:
            split('missing-namespace', 'missing-command')
        assert e.value.path == ('missing-namespace',)

    def test_with_help(self, executable_factory):
        """ Handle being given a command or namespaces for help """

        executable_factory('nd-help')
        executable_factory('nd-my-namespace~my-command')

        assert ([], 'help', ['missing']) == split('help', 'missing', parse_help=True)
        assert ([], 'help', ['my-namespace', 'missing']) == \
               split('help', 'my-namespace', 'missing', parse_help=True)
        assert ([], 'help', ['my-namespace', 'missing']) == \
               split('my-namespace', 'help', 'missing', parse_help=True)

        with pytest.raises(path.CommandOrNamespaceNotFound) as e:
            split('my-namespace', 'missing', 'help', parse_help=True)
        assert e.value.path == ('my-namespace', 'missing')
