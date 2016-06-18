import pytest

from nd_toolbelt.commands import nd


class TestNdCommandClass:
    def test_nd_update_and_no_update_cannot_be_set_together(self, capfd):
        with pytest.raises(SystemExit):
            nd.main(['nd', '--update', '--no-update', 'version'])
        stdout, stderr = capfd.readouterr()
        assert '--no-update: not allowed with argument --update' in stderr
