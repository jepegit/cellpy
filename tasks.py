import io
import os
import re
import sys
from contextlib import contextmanager
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

import dotenv
from dotenv import load_dotenv

import requests
from invoke import task

load_dotenv()

"""Tasks for cellpy development.

You need to have invoke installed in your
python environment for this to work.

Examples:

    # build and upload to pypi:
    > invoke build --upload

    # build only the docs
    > invoke build --docs

    # clean up
    > invoke clean

    # clean up and build
    > invoke clean build

"""


def sphinx_serve():
    host = "0.0.0.0"
    port = 8081
    try:
        httpd = HTTPServer((host, port), SimpleHTTPRequestHandler)
        httpd.serve_forever()
    except KeyboardInterrupt:
        print(" Keyboard interrupt received, exiting.")

    return 0


def get_platform():
    """get the platform you are running on"""
    platforms = {
        "linux1": "Linux",
        "linux2": "Linux",
        "darwin": "OS X",
        "win32": "Windows",
        "win64": "Windows",
    }
    if sys.platform not in platforms:
        return sys.platform

    return platforms[sys.platform]


@contextmanager
def capture():
    """context manager to capture output from a running subproject"""
    o_stream = io.StringIO()
    yield o_stream
    print(o_stream.getvalue())
    o_stream.close()


def get_pypi_info(package="cellpy"):
    """get version number and sha256 for a pypi package

    Args:
        package (str): name of package

    Returns:
        [version, sha256]
    """
    from pprint import pprint

    url = f"https://pypi.org/pypi/{package}/json"
    response = requests.get(url)
    if not response:
        print(f"url {url} not responding")
        return None, None

    response = response.json()
    version = response["info"]["version"]
    release = response["releases"][version][-1]
    sha256 = release["digests"]["sha256"]
    all_releases = list(response["releases"].keys())
    version_last_published = all_releases[-1]
    return version, sha256, version_last_published


def update_meta_yaml_line(line, update_dict):
    if line.find("set name") >= 0:
        v = update_dict["name"]
        line = f'{{% set name = "{v}" %}}\n'

    if line.find("set version") >= 0:
        v = update_dict["version"]
        line = f'{{% set version = "{v}" %}}\n'

    if line.find("set sha256") >= 0:
        v = update_dict["sha"]
        line = f'{{% set sha256 = "{v}" %}}\n'
    return line


def update_meta_yaml(meta_filename, update_dict):
    lines = []
    with open(meta_filename, "r") as ifile:
        while 1:
            line = ifile.readline()
            if not line:
                break

            if line.find("{%") >= 0:
                line = update_meta_yaml_line(line, update_dict)
            lines.append(line)
    with open(meta_filename, "w") as ofile:
        for line in lines:
            ofile.write(line)


@task
def pypi(c, package="cellpy"):
    """Query pypi"""
    version, sha, last = get_pypi_info(package=package)
    if version:
        print(f"version: {version}")
        print(f"sha256: {sha}")
        print(f"last-ver: {last}")


@task
def commit(c, push=True, comment="automatic commit"):
    """Simply commit and push"""
    cos = get_platform()
    print(" Running commit task ".center(80, "="))
    print(f"Running on platform: {cos}")
    print(" status ".center(80, "-"))

    with capture() as o:
        c.run("git status", out_stream=o)
        status_lines = o.getvalue()

    # it seems it is also possible to do
    # out = c.run(command)
    # status_lines = out.stdout

    new_files_regex = re.compile(r"modified:[\s]+([\S]+)")
    new_files = new_files_regex.search(status_lines)
    if new_files:
        print(new_files.groups())
        print(" staging ".center(80, "-"))
        c.run("git add .")
        print(" committing ".center(80, "-"))
        c.run(f'git commit . -m "{comment}"')
        if push:
            print(" pushing ".center(80, "-"))
            c.run("git push")
    print(" finished ".center(80, "-"))


@task
def clean(c, docs=False, bytecode=False, extra=""):
    """Clean up stuff from previous builds"""
    print(" Cleaning ".center(80, "="))
    patterns = ["dist", "build", "cellpy.egg-info"]
    if docs:
        print(" - cleaning doc builds")
        patterns.append("docs/_build")
    if bytecode:
        print(" - cleaning bytecode (i.e. pyc-files)")
        patterns.append("**/*.pyc")
    if extra:
        print(f" - cleaning {extra}")
        patterns.append(extra)
    for pattern in patterns:
        print(".", end="")
        try:
            cmd = delete_stuff(pattern)
            c.run(cmd)
        except Exception:
            print(f"(could not remove {pattern}", end="")
    print()
    print(f"Cleaned {patterns}")


def delete_stuff(pattern):
    platforms = {
        "linux1": "Linux",
        "linux2": "Linux",
        "darwin": "OS X",
        "win32": "Windows",
        "win64": "Windows",
    }
    platform = get_platform()
    if platform == "Windows":
        cmd = f'rd /s /q "{pattern}"'
    else:
        cmd = "rm -rf {}".format(pattern)
    return cmd


@task
def info(c, full=False):
    """Get info about your cellpy"""
    from pathlib import Path

    import cellpy

    print()
    version_file_path = Path("cellpy") / "_version.py"
    version_ns = {}
    with open(version_file_path) as f:
        exec(f.read(), {}, version_ns)

    version_stable, sha, version_last = get_pypi_info(package="cellpy")
    version_in_code = version_ns["__version__"]
    version_by_import = cellpy.__version__

    print(" INFO ".center(80, "="))
    print(" version ".center(80, "-"))
    print(f"version (by import cellpy): cellpy {version_by_import}")
    print(f"version (in _version.py):   cellpy {version_in_code}")
    if version_in_code != version_by_import:
        print("WARNING: version mismatch")

    if version_stable:
        print(f"version on PyPI:            cellpy {version_stable}")
    if version_last:
        print(f"last on PyPI:               cellpy {version_last}")
        if version_in_code == version_last:
            print("You need to bump version number before you can publish!")
            print("Use bump task to do this:")
            print("> inv bump")
    print(80 * "-")


@task
def sha(c, version=None):
    import cellpy

    if version is None:
        version = f"{cellpy.__version__}"
    full_version = f"cellpy/{version}"
    pypi_version, sha_hash, last = get_pypi_info(package=full_version)
    print(f"ver: {pypi_version}")
    print(f"sha: {sha_hash}")
    print(f"last-ver: {last}")


@task
def jupyterlab(c):
    print("installing jupyter lab-extensions")
    extensions = [
        "@jupyter-widgets/jupyterlab-manager@2.0",
        "@pyviz/jupyterlab_pyviz",
        "@jupyter-widgets/jupyterlab-toc",
    ]
    for extension in extensions:
        print(f"installing {extension}")
        c.run(f"jupyter labextension install {extension}")
    print("OK")


@task
def man(c):
    print("-----")
    print("CONDA")
    print("-----")
    print("\ncreate new environment from environment.yml file:")
    print("> conda env create -f environment.yml")
    print("\nremove environment:")
    print("> conda env remove --name myenv")
    print("\nadd conda env to jupyter:")
    print(
        "(assuming you are already in the conda env you would like to add to jupyter)"
    )
    print("> python -m ipykernel install --user --name=firstEnv")

    print("----------")
    print("JUPYTERLAB")
    print("----------")
    print("> jupyter labextension install @jupyter-widgets/jupyterlab-manager@2.0")
    print("> jupyter labextension install @pyviz/jupyterlab_pyviz")
    print("> jupyter labextension build")
    print("> jupyter labextension list")

    print(
        """
    ----------------------------
    Some pycharm tips and tricks
    ----------------------------
    Multiple Selections

        Set multiple cursors in the editor area: Alt + Mouse Click (Option + Mouse Click for Mac OS X).
        Select/unselect the next occurrence: Alt + J / Shift + Alt + J (Ctrl + G / Shift + Ctrl +G for Mac OS X)
        Select all occurrences: Shift + Ctrl + Alt + J (Ctrl + Cmd + G for Mac OS X)
        Clone caret above/below (the shortcuts are not mapped yet)
        Remove all selections: Esc
        You can redefine these shortcuts in Settings -> Keymap -> Editor Actions if necessary.

    """
    )

    print(
        """
    ---------------------------
    Conda forge tips and tricks
    ---------------------------
    This is a short description in how to update the conda-forge recipe:
    - (If not done): make a fork of https://github.com/conda-forge/cellpy-feedstock
    - (if not done): clone the repo (jepegit/cellpy-feedstock)
         >>> git clone https://github.com/jepegit/cellpy-feedstok.git
         >>> git remote add upstream https://github.com/conda-forge/cellpy-feedstock
    - Get recent changes
         git fetch upstream
         git rebase upstream/master
    - Make a new branch in your local clone
         git checkout -b update_x_x_x
    - Edit
        hash and version and build number
        (hash: pypi - release history - Download files)
        (version: use normalized format e.g. 0.5.2a3 not 0.5.2.a3!)
        (build number: should be 0 for new versions)
    - Add and commit (e.g. updated feedstock to version 1.0.1)
    - Push
        >>> git push origin <branch-name>
    - re-render if needed (different requirements, platforms, issues)
        >>> conda install -c conda-forge conda-smithy
        >>> conda smithy rerender -c auto
    - Create a pull request via the web interface by navigating to
      https://github.com/jepegit/cellpy-feedstok.git with your web browser
      and clicking the button create pull request.
    - Wait for the automatic checks have complete (takes several minutes)
    - Merge pull request (big green button)
    - Drink a cup of coffee or walk the dog

    - check if the new version is there:
      >>> conda search -f cellpy
    - now you can delete the branch (if you want)

    """
    )


@task
def test(c):
    """Run tests with coverage"""
    c.run("pytest --cov=cellpy tests/")


def _get_bump_tag(bump):
    bump_tags = {
        "nano": "tag-num",
        "micro": "patch",
        "minor": "minor",
        "major": "major",
        "alpha": "tag alpha",
        "beta": "tag beta",
        "rc": "tag rc",
        "post": "tag post",
        "final": "tag final",
    }
    default_bumper = "tag-num"

    if (
        bump in ["false", "keep", "skip", "no", "no-chance", "nope", "n"]
        or bump is False
    ):
        return False
    if bump is None or bump is True:
        return default_bumper

    if bump.startswith("v."):
        bumper = f"set-version {bump[2:]}"
    elif bump not in ["p", "patch", "m", "minor", "major", "t", "tag"]:
        bumper = bump_tags.get(bump, default_bumper)
    else:
        bumper = bump
    return bumper


def create_commit_message_from_output(output, regexp):
    # MIGHT-DO: consider changing from try-except to if statement
    # since re.search returns None if nothing is found.
    try:
        txt = regexp.search(output).group(1)
    except Exception as e:
        print(e)
        print("could not read bumping")
        return
    return txt


@task
def requirements(c, check=True):
    if check:
        # Should check that all the different requirement files (including
        # conda environment files) are in synch.
        print("check requirements - not implemented yet")


@task
def bump(c, bumper=None):
    """Bump version.

    Args:
        bumper (str): nano, micro, minor, major, alpha, beta, rc, post, final, keep

    The following bumpers are allowed:
        nano: tag-num, increment from e.g. 0.4.2b2 to 0.4.2b3
        final: tag final, increment from e.g. 0.4.2b2 to 0.4.2
        micro: patch, increment from e.g. 0.4.2b3 to 0.4.3b or 0.4.2 to 0.4.3
        minor: minor, increment from e.g. 0.4.2b3 to 0.5.0b or 0.4.2 to 0.5.0
        major: major, increment from e.g. 0.4.2b3 to 1.0.0b or 0.4.2 to 1.0.0
        alpha: tag alpha
        beta: tag beta
        rc: tag rc
        post: tag post
        keep: don't change it

    Typically, you would use 'nano' until you are satisfied with your packaage, and then
    use a 'final'. And then start again with new features by first using an 'alpha' then
    start all over with 'nano'.


    """
    bumper = _get_bump_tag(bumper)
    if not bumper:
        regex_current = re.compile("Current Version: (.*)")
        print("only checking current version (no bumping)")
        out = c.run(f"bumpver show")
        version = create_commit_message_from_output(out.stdout, regex_current)
        print(f"Current version: {version}")
        return

    regex_old = re.compile("- Old Version: (.*)")
    regex_new = re.compile("- New Version: (.*)")
    print(f" running bumpver ({bumper} --dry) ".center(80, "-"))
    out = c.run(f"bumpver update --{bumper} --dry")
    old_version = create_commit_message_from_output(out.stderr, regex_old)
    new_version = create_commit_message_from_output(out.stderr, regex_new)
    commit_message = f"bump version {old_version} -> {new_version}"
    print(f"{commit_message}")
    is_ok = input("> continue? [y]/n: ") or "y"

    if not is_ok.lower() in ["y", "yes", "ok", "sure"]:
        print("Aborting!")
        return

    c.run(f"bumpver update --{bumper}")
    print("DONE")


@task
def build(
    c, _clean=True, dist=True, docs=False, upload=True, _serve=False, browser=False
):
    """Create distribution (and optionally upload to PyPI)"""

    if _clean:
        clean(c)

    if dist:
        print(" Creating distribution ".center(80, "="))
        print("Running python setup.py sdist")
        c.run("python -m build")
    if docs:
        print(" Building docs ".center(80, "-"))
        c.run("sphinx-build docs docs/_build")
    if upload:
        dotenv.load_dotenv()
        print(" Uploading to PyPI ".center(80, "="))
        print(" Running 'twine upload dist/*'")
        print(" Using token from environment (PYPI_TOKEN).")
        try:
            password = os.environ["PYPI_TOKEN"]
            c.run(f"python -m twine upload dist/* -u __token__ -p {password}")
        except Exception:
            print("Could not extract token from environment")
            print("For it to work you need to export PYPI_TOKEN")
            print("   e.g.  export PYPI_TOKEN=<token>")
            print("or add it to your .env file.")
            print("Running upload (insert username and password when prompted)")
            c.run("python -m twine upload dist/*")

    else:
        print(" To upload to pypi: 'python -m twine upload dist/*'")
    if _serve:
        import pathlib

        builds_path = pathlib.Path("docs") / "_build"
        print(" Serving docs")
        os.chdir(builds_path)
        _location = r"localhost:8081"
        if browser:
            print(f" - opening browser in http://{_location}")
            c.run(f"python -m webbrowser -t http://{_location}")
        else:
            print(
                f" - hint! you can open your browser by typing:\n       python -m webbrowser -t http://{_location}"
            )
        sphinx_serve()


@task
def docs(c, _clean=False, _serve=True, browser=True):
    """Build and view docs"""

    if _clean:
        clean(c)
    print(" Building docs ".center(80, "-"))
    c.run("sphinx-build docs docs/_build")

    if _serve:
        import pathlib

        builds_path = pathlib.Path("docs") / "_build"
        print(" Serving docs")
        os.chdir(builds_path)
        _location = r"localhost:8081"
        if browser:
            print(f" - opening browser in http://{_location}")
            c.run(f"python -m webbrowser -t http://{_location}")
        else:
            print(
                f" - hint! you can open your browser by typing:\n       python -m webbrowser -t http://{_location}"
            )
        sphinx_serve()


@task
def serve(c):
    _location = r"localhost:8081"
    c.run(f"python -m webbrowser -t http://{_location}")


if __name__ == "__main__":
    delete_stuff(pattern="NOTHING")
