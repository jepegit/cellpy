import logging

import pytest
from click.testing import CliRunner

import cellpy
from cellpy import cli, prmreader
from cellpy import prms, log

NUMBER_OF_DIRS = 11

log.setup_logging(default_level="DEBUG", testing=True)


def test_get_user_name():
    u = prmreader.get_user_name()
    print(f"\ncurrent username: {u}")


def test_get_user_dir_and_dst():
    user_dir, dst_file = prmreader.get_user_dir_and_dst("filename.conf")
    print(f"\nuserdir: {user_dir}")


def test_create_custom_init_filename():
    u = prmreader.create_custom_init_filename()
    print(f"\ncustom config-file-name: {u}")


def test_get_package_prm_dir():
    u = cli.get_package_prm_dir()
    print(f"\npackage directory: {u}")


def test_info_version():
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["info", "--version"])
    print(result.output)
    assert result.exit_code == 0
    assert f"[cellpy] version: {cellpy.__version__}" in result.output


def test_info_configloc():
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["info", "--configloc"])
    print()
    print(result.output)
    assert result.exit_code == 0
    assert "conf" in result.output


def test_info_no_option():
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["info"])
    print()
    print(result.output)
    assert result.exit_code == 0


def test_info_help():
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["info", "--help"])
    print()
    print(result.output)
    assert result.exit_code == 0
    assert "--help" in result.output


def test_info_params():
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["info", "--params"])
    print("\n", result.output)
    assert result.exit_code == 0
    assert "cellpydatadir" in result.output


def test_info_check():
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["info", "--check"])
    print("\n", result.output)
    assert result.exit_code == 0


@pytest.mark.slowtest
def test_pull_tests(tmp_path):
    runner = CliRunner()
    opts = list()
    opts.append("pull")
    opts.append("--tests")
    opts.append("--directory")
    opts.append(tmp_path)
    opts.append("--password")
    opts.append("env")
    result = runner.invoke(cli.cli, opts)
    print("\n", result.output)

    if result.exception:
        print(result.exception)
        assert result.exception.status == 403
    else:
        assert result.exit_code == 0


@pytest.mark.slowtest
def test_pull_examples(tmp_path):
    import github

    runner = CliRunner()
    opts = list()
    opts.append("pull")
    opts.append("--examples")
    opts.append("--directory")
    opts.append(tmp_path)
    opts.append("--password")
    opts.append("env")
    result = runner.invoke(cli.cli, ["pull", "--examples"])
    print("\n", result.output)

    if result.exception:
        print(result.exception)
        assert result.exception.status == 403
    else:
        assert result.exit_code == 0


@pytest.mark.slowtest
def test_pull_clone():
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["pull", "--clone"])
    print("\n", result.output)
    assert result.exit_code == 0


@pytest.mark.slowtest
def test_pull_custom_dir():
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["pull", "--clone", "--directory", "MyDir"])
    print("\n", result.output)
    assert result.exit_code == 0


@pytest.mark.slowtest
def test_pull_help():
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["pull", "--help"])
    print("\n", result.output)
    assert result.exit_code == 0


def test_run_help():
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["run", "--help"])
    print("\n", result.output)
    assert result.exit_code == 0


def test_run_empty():
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["run"])
    print("\n", result.output)
    assert result.exit_code != 0


def test_run():
    name = "20190210_cell001_cc_01.h5"
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["run", name])
    print("\n", result.output)
    assert result.exit_code == 0


def test_run_debug():
    name = "20190210_cell001_cc_01.h5"
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["run", "--debug", name])
    print("\n", result.output)
    assert result.exit_code == 0


def test_run_journal():
    name = "20190210_cell001_cc_01.h5"
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["run", "--journal", name])
    print("\n", result.output)
    assert result.exit_code == 0


def test_run_journal_silent():
    name = "20190210_cell001_cc_01.h5"
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["run", "--journal", "--silent", name])
    print("\n", result.output)
    assert result.exit_code == 0


def test_run_journal_debug():
    name = "20190210_cell001_cc_01.h5"
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["run", "--journal", "--debug", name])
    print("\n", result.output)
    assert result.exit_code == 0


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["--help"])
    print("\n", result.output)
    assert result.exit_code == 0


def test_cli_setup_help():
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["setup", "--help"])
    print("\n", result.output)
    assert result.exit_code == 0


def test_cli_setup():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli.cli, ["setup", "--dry-run"])
        print(result.output)
        assert result.exit_code == 0


def test_cli_setup_interactive():
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli.cli, ["setup", "-i", "--dry-run"], input=NUMBER_OF_DIRS * "\n"
        )
        print(result.output)
        assert result.exit_code == 0


def test_cli_setup_custom_dir():
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli.cli,
            ["setup", "-i", "--dry-run", "-d", "just_a_dir"],
            input=NUMBER_OF_DIRS * "\n",
        )
        print(result.output)
        assert result.exit_code == 0


def test_cli_new_list():
    logging.debug("\nSTARTING TEST")
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(cli.cli, ["new", "--list"])
    assert "https://github.com/jepegit/cellpy_cookie_standard.git" in result.output


# def test_cli_new(tmp_path):
#     logging.debug("\nSTARTING TEST")
#     runner = CliRunner()
#     notebookdir = tmp_path / "NOTEBOOKS"
#     notebookdir.mkdir(parents=True, exist_ok=True)
#     prms.Paths.notebookdir = notebookdir
#
#     interactive_prms = ["1", "another_project", "yes"]
#     with runner.isolated_filesystem():
#         result = runner.invoke(cli.cli, ["new"], "\n".join(interactive_prms))
#     assert "[another_project]:" in result.output
#     output_paths = str(list(notebookdir.glob("**/*.ipynb")))
#     assert "NOTEBOOKS/another_project" in output_paths
#     assert "_life.ipynb" in output_paths


# def test_cli_new_with_dir_as_input(tmp_path):
#     logging.debug("\nSTARTING TEST")
#     runner = CliRunner()
#     notebookdir = tmp_path / "CUSTOM_NOTEBOOK_DIR"
#     notebookdir.mkdir(parents=True, exist_ok=True)
#
#     interactive_prms = ["1", "another_project", "yes"]
#     with runner.isolated_filesystem():
#         result = runner.invoke(
#             cli.cli, ["new", "-d", str(notebookdir)], "\n".join(interactive_prms)
#         )
#     assert "[another_project]:" in result.output
#     output_paths = str(list(notebookdir.glob("**/*.ipynb")))
#     assert "CUSTOM_NOTEBOOK_DIR/another_project" in output_paths
#     assert "_life.ipynb" in output_paths


def test_cli_new_different_and_missing_default(tmp_path):
    logging.debug("\nSTARTING TEST")
    runner = CliRunner()
    prms.Batch.template = "missing_template"
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli.cli,
            ["new"],
        )
    assert "This template does not exist" in result.output
