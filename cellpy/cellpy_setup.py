import os
import shutil
import click
import pkg_resources

DEFAULT_FILENAME_START = "_cellpy_prms_"
DEFAULT_FILENAME_END = ".ini"
DEFAULT_FILENAME = DEFAULT_FILENAME_START + "default" + DEFAULT_FILENAME_END

ORIGINAL_FILENAME = "_cellpyx_prms_default.ini"

DEFAULT_PRMS = """
[Paths]
outdatadir: ..\outdata
rawdatadir: ..\indata
cellpydatadir: ..\indata
db_path: ..\databases
filelogdir: ..\databases

[FileNames]
db_filename: cellpy_db.xlsx
dbc_filename: cellpy_dbc.xlsx
"""


def get_package_dir(init_filename=None):
    prm_dir = pkg_resources.resource_filename("cellpy","parameters")
    if not init_filename:
        init_filename = ORIGINAL_FILENAME
    src = os.path.join(prm_dir, init_filename)
    return src


def get_user_dir_and_dst(file_name):
    user_dir = os.path.expanduser("~")
    dst_dir = user_dir  # might include .cellpy directory here in the future (must then modify prmreader)
    dst_file = os.path.join(dst_dir,file_name)
    return user_dir, dst_file


def create_custom_init_filename():
    return DEFAULT_FILENAME_START + os.environ.get("USERNAME") + DEFAULT_FILENAME_END


# TODO (jepe): func for getting ini location

# TODO (jepe): func for make csv dump of .xxx file (filetype as option or interpreted from extension)

# TODO (jepe): func for giving stats of a file



@click.group()
def cli():
    pass


@click.command()
def setup():
    src = get_package_dir()
    if not os.path.isfile(src):
        click.echo("\n[cellpy] Could not find (and copy) default prm-file.")
        click.echo("[cellpy] You should make your own prm-file")
        click.echo("[cellpy] with a name starting with _cellpy_prms_xxx.ini,")
        click.echo("[cellpy] where xxx could be any name.")
        click.echo("[cellpy] The prm-file should be saved either in your user directory,")
        click.echo("[cellpy] or in the folder where you will run the cellpy scripts from.")
        click.echo("[cellpy] Content of prm-file:\n")
        click.echo(DEFAULT_PRMS)
    else:
        init_filename = create_custom_init_filename()
        userdir, dst_file = get_user_dir_and_dst(init_filename)
        click.echo("\n[cellpy] Copying %s to user directory" % DEFAULT_FILENAME)
        click.echo("[cellpy] (%s)\n" % userdir)
        if os.path.isfile(dst_file):
            click.echo("[cellpy] File already exists!")
            click.echo("[cellpy]  -> Overwriting...\n")
        shutil.copyfile(src, dst_file)
        click.echo("[cellpy] Directory path:\n")
        click.echo("[cellpy] %s" % os.path.dirname(dst_file))
        click.echo("[cellpy] File name: %s\n" % os.path.basename(init_filename))
        click.echo("[cellpy] OK! Now you can edit it (and save it with another name starting with")
        click.echo("[cellpy] _cellpy_prms and ending with .ini if you want)")
        click.echo("[cellpy]")


cli.add_command(setup)
