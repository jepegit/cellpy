import os
import click
import pkg_resources

from cellpy.parameters import prmreader
from cellpy.exceptions import ConfigFileNotWritten
import cellpy._version

DEFAULT_FILENAME_START = "_cellpy_prms_"
DEFAULT_FILENAME_END = ".conf"
DEFAULT_FILENAME = DEFAULT_FILENAME_START + "default" + DEFAULT_FILENAME_END
VERSION = cellpy._version.__version__


def save_prm_file(prm_filename):
    """saves (writes) the prms to file"""
    prmreader._write_prm_file(prm_filename)
    print("saved_prm_file")
    print(prm_filename)


def get_package_dir(init_filename=None):
    """gets the folder where the cellpy package lives"""
    prm_dir = pkg_resources.resource_filename("cellpy", "parameters")
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


def create_custom_init_filename():
    """creates a custom prms filename"""
    return DEFAULT_FILENAME_START + os.environ.get(
        "USERNAME") + DEFAULT_FILENAME_END


@click.group()
def cli():
    pass


@click.command()
def setup():
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
        save_prm_file(dst_file)
    except ConfigFileNotWritten:
        click.echo("[cellpy] Something went wrong! Could not write the file")
        click.echo(
            "[cellpy] Trying to write a file"
            + f"called {DEFAULT_FILENAME} instead")

        try:
            userdir, dst_file = get_user_dir_and_dst(init_filename)
            save_prm_file(dst_file)

        except ConfigFileNotWritten:
            _txt = "[cellpy] No, that did not work either." \
                   + " Well, guess you have to talk to the developers."
            click.echo(_txt)

    click.echo("[cellpy] Directory path:\n")
    click.echo("[cellpy] %s" % os.path.dirname(dst_file))
    click.echo("[cellpy] File name: %s\n" % os.path.basename(init_filename))
    click.echo(
        "[cellpy] OK! Now you can edit it"
        + "(and save it with another name starting with")
    click.echo("[cellpy] _cellpy_prms and ending with .conf if you want)")
    click.echo("[cellpy]")


@click.command()
def configloc():
    click.echo("[cellpy] ->\n")
    config_file_name = prmreader._get_prm_file()
    click.echo("[cellpy] ->%s\n" % config_file_name)
    if not os.path.isfile(config_file_name):
        click.echo("[cellpy] File does not exist!")


@click.command()
def version():
    txt = "[cellpy] version: " + str(VERSION)
    click.echo(txt)


cli.add_command(setup)
cli.add_command(configloc)
cli.add_command(version)

if __name__ == "__main__":
    print("\n\n*******RUNNING MAIN**(test)******\n")
    file_name = create_custom_init_filename()
    print(file_name)
    user_directory, destination_file_name = get_user_dir_and_dst(file_name)
    print(user_directory)
    print(destination_file_name)
    print("trying to save it")
    save_prm_file(destination_file_name + "_dummy")
