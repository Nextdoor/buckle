import mock
import stat
import subprocess

import pytest  # flake8: noqa

from buckle import autocomplete

from fixtures import executable_factory

STAT_OWNER_EXECUTABLE = stat.S_IEXEC


class TestGetExecutablesStartingWith(object):
    @staticmethod
    @pytest.fixture(autouse=True)
    def set_minimal_path(monkeypatch):
        monkeypatch.setenv('PATH', None)

    def test_returns_sorted_list(self, executable_factory):
        executable_factory('nd-c')
        executable_factory('nd-a')
        executable_factory('nd-b')
        result = autocomplete.get_executables_starting_with('nd-')
        assert result == ['nd-a', 'nd-b', 'nd-c']

    def test_functions_excluded(self):
        ordered_return_list = ['nd-init nd-help nd-function'.encode(), 'nd-function'.encode()]
        with mock.patch.object(subprocess, 'check_output', side_effect=ordered_return_list):
            result = autocomplete.get_executables_starting_with()
            assert result == ['nd-help', 'nd-init']

    def test_returns_empty_list_if_no_results(self):
        ordered_return_list = ['nd-delete-me'.encode(), 'nd-delete-me'.encode()]
        with mock.patch.object(subprocess, 'check_output', side_effect=ordered_return_list):
            result = autocomplete.get_executables_starting_with()
            assert not result

    def test_finds_commands_in_path(self, executable_factory):
        executable_factory('nd-my-test-command')
        result = autocomplete.get_executables_starting_with(prefix='nd-my-test-command')
        assert result == ['nd-my-test-command']
