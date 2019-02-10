import os
import getpass
import click
import pkg_resources

from cellpy.parameters import prmreader
from cellpy.exceptions import ConfigFileNotWritten
import cellpy._version

DEFAULT_FILENAME_START = "_cellpy_prms_"
DEFAULT_FILENAME_END = ".conf"
DEFAULT_FILENAME = DEFAULT_FILENAME_START + "default" + DEFAULT_FILENAME_END
VERSION = cellpy._version.__version__
REPO = "git-repo-name"


def save_prm_file(prm_filename):
    """saves (writes) the prms to file"""
    prmreader._write_prm_file(prm_filename)
    print("saved_prm_file")
    print(prm_filename)


def get_package_prm_dir():
    """gets the folder where the cellpy package lives"""
    prm_dir = pkg_resources.resource_filename("cellpy", "parameters")
    return prm_dir


def get_default_config_file_path(init_filename=None):
    """gets the path to the default config-file"""
    prm_dir = get_package_prm_dir()
    if not init_filename:
        init_filename = DEFAULT_FILENAME
    src = os.path.join(prm_dir, init_filename)
    return src


def get_user_dir_and_dst(init_filename):
    """gets the name of the user directory and full prm filepath"""
    user_dir = os.path.abspath(os.path.expanduser("~"))
    dst_dir = user_dir
    dst_file = os.path.join(dst_dir, init_filename)
    return user_dir, dst_file


def get_user_name():
    """get the user name of the current user (cross platform)"""
    return getpass.getuser()


def create_custom_init_filename():
    """creates a custom prms filename"""
    return DEFAULT_FILENAME_START + get_user_name() + DEFAULT_FILENAME_END


def check_if_needed_modules_exists():
    pass


def modify_config_file():
    pass


def create_cellpy_folders():
    pass


@click.group("cellpy")
def cli():
    pass


@click.command()
@click.option('--dry-run/--no-dry-run', default=False)
@click.option('--bleeding-edge/--no-bleeding-edge', default=False)
def setup(dry_run, bleeding_edge):
    if bleeding_edge:
        click.echo("[cellpy] Bleeding-edge mode!")
        click.echo("         Plan:")
        click.echo("           1) add option for creating folders")
        click.echo("           2) check if requirements are satisfied")
        click.echo("[cellpy] ... comming soon...")

    init_filename = create_custom_init_filename()
    userdir, dst_file = get_user_dir_and_dst(init_filename)
    click.echo("\n")
    click.echo("[cellpy] Writing configurations to user directory")
    click.echo("[cellpy] (%s)\n" % userdir)

    if os.path.isfile(dst_file):
        click.echo("[cellpy] File already exists!")
        click.echo(
            "[cellpy]  -> Trying to keep old configuration parameters...\n")
    try:
        if dry_run:
            print(f"dry-run: skipping actual saving of {dst_file}")
        else:
            save_prm_file(dst_file)

    except ConfigFileNotWritten:
        click.echo("[cellpy] Something went wrong! Could not write the file")
        click.echo(
            "[cellpy] Trying to write a file"
            + f"called {DEFAULT_FILENAME} instead")

        try:
            userdir, dst_file = get_user_dir_and_dst(init_filename)
            if dry_run:
                print(f"dry-run: skipping actual saving of {dst_file}")
            else:
                save_prm_file(dst_file)

        except ConfigFileNotWritten:
            _txt = "[cellpy] No, that did not work either." \
                   + " Well, guess you have to talk to the developers."
            click.echo(_txt)

    click.echo("[cellpy] Directory path:\n")
    click.echo("[cellpy] %s" % os.path.dirname(dst_file))
    click.echo("[cellpy] File name: %s\n" % os.path.basename(init_filename))
    click.echo(
        "[cellpy] OK! Now you can edit it."
        + f"For example by issuing \n[your-favourite-editor] {init_filename}")
    click.echo("[cellpy]")


@click.command()
@click.option(
    '--version', '-v', is_flag=True, help="Print version information."
)
@click.option(
    '--configloc', '-c', is_flag=True,
    help='Print full path to the config file.'
)
@click.option(
    '--params', '-p', is_flag=True, help='Dump all parameters to screen.'
)
def info(version, configloc, params):
    complete_info = True

    if version:
        complete_info = False
        _version()

    if configloc:
        complete_info = False
        _configloc()

    if params:
        complete_info = False
        _dump_params()

    if complete_info:
        _version()
        _configloc()


@click.command()
@click.option(
    '--tests', '-t', is_flag=True, help="Download test-files from repo."
)
@click.option(
    '--examples', '-e', is_flag=True, help="Download example-files from repo."
)
@click.option(
    '--clone', '-c', is_flag=True, help="Clone the full repo."
)
@click.option(
    '--directory', '-d', default=None, help="Save into custom directory DIR"
)
def pull(tests, examples, clone, directory):
    if directory is not None:
        click.echo(f"[cellpy] Custom directory: {directory}")
    if clone:
        _clone_repo(directory)
    else:
        if tests:
            _pull_tests(directory)
        if examples:
            _pull_examples(directory)


@click.command()
@click.option(
    '--journal', '-j', is_flag=True,
    help="Run a batch job defined in the given journal-file"
)
@click.option(
    '--debug', '-d', is_flag=True, help="Run in debug mode."
)
@click.option(
    '--silent', '-s', is_flag=True,
    help="Run in silent (i.e. no-plotting) mode."
)
@click.argument('file_name')
def run(journal, debug, silent, file_name):
    print("RUNNING".center(80, "*"))
    if not file_name:
        click.echo("[cellpy] No filename provided.")
        return
    txt = f"[cellpy] The plan is that this cmd will run a batch run\n"
    txt += f"[cellpy] journal: {journal}\n"

    if debug:
        txt += "[cellpy] debug mode on"

    if silent:
        txt += "[cellpy] silent mode on"

    txt += "[cellpy]\n"
    click.echo(txt)

    if journal:
        _run_journal(file_name, debug, silent)

    else:
        _run(file_name, debug, silent)


def _run_journal(file_name, debug, silent):
    print(f"running journal {file_name}")
    print(f" --debug [{debug}]")
    print(f" --silent [{silent}]")


def _run(file_name, debug, silent):
    print(f"running {file_name}")
    print(f" --debug [{debug}]")
    print(f" --silent [{silent}]")


def _clone_repo(directory):
    txt = "[cellpy] The plan is that this "
    txt += "[cellpy] cmd will pull (clone) the cellpy repo.\n"
    txt += "[cellpy] For now it only prins the link to the git-hub\n"
    txt += "[cellpy] repository:\n"
    txt += "[cellpy]\n"
    txt += "[cellpy] https://github.com/jepegit/cellpy.git\n"
    txt += "[cellpy]\n"
    click.echo(txt)


def _pull_tests(directory):
    txt = "[cellpy] The plan is that this cmd will run some tests.\n"
    txt += "[cellpy] For now it only prins the link to the git-hub\n"
    txt += "[cellpy] repository:\n"
    txt += "[cellpy]\n"
    txt += "[cellpy] https://github.com/jepegit/cellpy.git\n"
    txt += "[cellpy]\n"
    click.echo(txt)


def _pull_examples(directory):
    txt = "[cellpy] The plan is that this cmd will download examples.\n"
    txt += "[cellpy] For now it only prins the link to the git-hub\n"
    txt += "[cellpy] repository:\n"
    txt += "[cellpy]\n"
    txt += "[cellpy] https://github.com/jepegit/cellpy.git\n"
    txt += "[cellpy]\n"
    click.echo(txt)


def _version():
    txt = "[cellpy] version: " + str(VERSION)
    click.echo(txt)


def _configloc():
    config_file_name = prmreader._get_prm_file()
    click.echo("[cellpy] ->%s\n" % config_file_name)
    if not os.path.isfile(config_file_name):
        click.echo("[cellpy] File does not exist!")


def _dump_params():
    click.echo("[cellpy] Dumping parameters to screen:\n")
    prmreader.info()


cli.add_command(setup)
cli.add_command(info)
cli.add_command(pull)
cli.add_command(run)


if __name__ == "__main__":
    print("\n\n*******RUNNING MAIN**(test)******\n")
    file_name = create_custom_init_filename()
    print(file_name)
    user_directory, destination_file_name = get_user_dir_and_dst(file_name)
    print(user_directory)
    print(destination_file_name)
    print("trying to save it")
    save_prm_file(destination_file_name + "_dummy")
