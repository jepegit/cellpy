import click
from click.testing import CliRunner

from cellpy import log
from cellpy import prms
import cellpy
from cellpy import cellpy_setup


def test_get_user_name():
    u = cellpy_setup.get_user_name()
    print(f"\ncurrent username: {u}")


def test_get_user_dir_and_dst():
    user_dir, dst_file = cellpy_setup.get_user_dir_and_dst("filename.conf")
    print(f"\nuserdir: {user_dir}")


def test_create_custom_init_filename():
    u = cellpy_setup.create_custom_init_filename()
    print(f"\ncustom config-file-name: {u}")


def test_get_package_prm_dir():
    u = cellpy_setup.get_package_prm_dir()
    print(f"\npackage directory: {u}")


def test_configloc():
    runner = CliRunner()
    result = runner.invoke(cellpy_setup.configloc)
    assert result.exit_code == 0


def test_version():
    runner = CliRunner()
    result = runner.invoke(cellpy_setup.version)
    assert result.exit_code == 0
    assert result.output.strip() == f"[cellpy] version: {cellpy.__version__}"


def test_cli_configloc():
    runner = CliRunner()
    result = runner.invoke(cellpy_setup.cli, ["configloc"])
    assert result.exit_code == 0
    assert ".conf" in result.output


def test_cli_setup():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cellpy_setup.cli, ["setup", "--dry-run"]
        )
        print(result.output)
        assert result.exit_code == 0

        result = runner.invoke(
            cellpy_setup.cli, ["setup", "--dry-run", "--bleeding-edge"]
        )
        print(result.output)
        assert result.exit_code == 0
