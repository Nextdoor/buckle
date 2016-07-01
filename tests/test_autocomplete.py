import mock
import os
import tempfile
import stat
import subprocess

import pytest  # flake8: noqa

from nd_toolbelt import autocomplete

STAT_OWNER_EXECUTABLE = stat.S_IEXEC


class TestGetNdNamespaceAutocompletion(object):
    def test_get_nd_namespace_autocompletion_returns_sorted_list(self):
        ordered_return_list = ['nd-init nd-version nd-help'.encode(), ''.encode()]
        with mock.patch.object(subprocess, 'check_output', side_effect=ordered_return_list):
            result = autocomplete.get_nd_namespace_autocompletion(namespace='')
            assert result == ['nd-help', 'nd-init', 'nd-version']

    def test_get_nd_namespace_autocompletion_ignores_functions(self):
        ordered_return_list = ['nd-init nd-help nd-function'.encode(), 'nd-function'.encode()]
        with mock.patch.object(subprocess, 'check_output', side_effect=ordered_return_list):
            result = autocomplete.get_nd_namespace_autocompletion(namespace='')
            assert result == ['nd-help', 'nd-init']

    def test_get_nd_namespace_autocompletion_returns_empty_list_if_no_results(self):
        ordered_return_list = ['nd-delete-me'.encode(), 'nd-delete-me'.encode()]
        with mock.patch.object(subprocess, 'check_output', side_effect=ordered_return_list):
            result = autocomplete.get_nd_namespace_autocompletion(namespace='')
            assert not result

    def test_get_nd_namespace_autocompletion_finds_commands_in_path(self, monkeypatch):
        monkeypatch.setenv('PATH', tempfile.gettempdir(), prepend=':')
        test_cmd_path = tempfile.gettempdir() + '/nd-my-test-command'

        with open(test_cmd_path, 'w+'):
            st = os.stat(test_cmd_path)
            os.chmod(test_cmd_path, st.st_mode | STAT_OWNER_EXECUTABLE)  # Make cmd executable

            result = autocomplete.get_nd_namespace_autocompletion(namespace='my-test')
            assert result == ['nd-my-test-command']
