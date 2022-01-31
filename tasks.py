import sys
import io
import re
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from contextlib import contextmanager

from invoke import task
import requests


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
    url = f"https://pypi.org/pypi/{package}/json"
    response = requests.get(url)
    if not response:
        print(f"url {url} not responding")
        return None, None

    response = response.json()
    version = response["info"]["version"]
    release = response["releases"][version][-1]
    sha256 = release["digests"]["sha256"]
    return version, sha256


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
    version, sha = get_pypi_info(package=package)
    if version:
        print(f"version: {version}")
        print(f"sha256: {sha}")


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
        c.run("rm -rf {}".format(pattern))
    print()
    print(f"Cleaned {patterns}")


@task
def info(c, full=False):
    """Get info about your cellpy"""
    import cellpy
    from pathlib import Path

    print()
    version_file_path = Path("cellpy") / "_version.py"
    version_ns = {}
    with open(version_file_path) as f:
        exec(f.read(), {}, version_ns)

    version, sha = get_pypi_info(package="cellpy")
    print(" INFO ".center(80, "="))
    print(" version ".center(80, "-"))
    print(f"version (by import cellpy): cellpy {cellpy.__version__}")
    print(f"version (in _version.py):   cellpy {version_ns['__version__']}")
    if version:
        print(f"version on PyPI:            cellpy {version}")


@task
def sha(c, version=None):
    import cellpy

    if version is None:
        version = f"{cellpy.__version__}"
    full_version = f"cellpy/{version}"
    pypi_version, sha_hash = get_pypi_info(package=full_version)
    print(f"ver: {pypi_version}")
    print(f"sha: {sha_hash}")


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


@task
def build(c, dist=True, docs=False, upload=True, serve=False, browser=False):
    """Create distribution (and optionally upload to PyPI)"""
    print(" Creating distribution ".center(80, "="))
    print("Running python setup.py sdist")
    if dist:
        c.run("python setup.py sdist")
    if docs:
        print(" Building docs ".center(80, "-"))
        c.run("sphinx-build docs docs/_build")
    if upload:
        print(" Uploading to PyPI ".center(80, "="))
        print(" Running 'twine upload dist/*'")
        print(" Trying with using username and password from keyring.")
        c.run("twine upload dist/*")
    else:
        print(" To upload to pypi: 'twine upload dist/*'")
    if serve:
        import pathlib

        builds_path = pathlib.Path("docs") / "_build"
        print(" Serving docs")
        os.chdir(builds_path)
        _location = r"localhost:8081"
        if browser:
            print(f" - opening browser in http://{_location}")
            c.run(f"python -m webbrowser -t http://{_location}")
        else:
            print(f" - hint! you can open your browser by typing:\n       python -m webbrowser -t http://{_location}")
        sphinx_serve()


@task
def serve(c):
    _location = r"localhost:8081"
    c.run(f"python -m webbrowser -t http://{_location}")


@task
def conda_build(c, upload=False):
    """Create conda distribution"""
    recipe_path = Path("./recipe/meta.yaml")

    print(" Creating conda distribution ".center(80, "="))
    if not recipe_path.is_file():
        print(f"conda recipe not found ({str(recipe_path.resolve())})")
        return

    version, sha = get_pypi_info(package="cellpy")
    update_dict = {"name": "cellpy", "version": version, "sha": sha}

    print("Updating meta.yml")
    update_meta_yaml(recipe_path, update_dict)

    print("Running conda build")
    print(update_dict)
    with capture() as o:
        c.run("conda build recipe", out_stream=o)
        status_lines = o.getvalue()

    new_files_regex = re.compile(r"TEST END: (.+)")
    new_files = new_files_regex.search(status_lines)
    path = new_files.group(1)
    if upload:
        upload_cmd = f"anaconda upload {path}"
        c.run(upload_cmd)
    else:
        print(f"\nTo upload: anaconda upload {path}")

    print("\nTo convert to different OS-es: conda convert --platform all PATH")
    print("e.g.")
    print("cd builds")
    print(
        r"conda convert --platform all "
        r"C:\miniconda\envs\cellpy_dev\conda-bld\win-"
        r"64\cellpy-0.3.0.post1-py37_0.tar.bz2"
    )


@task
def help(c):
    """Print some help"""
    print(" available invoke tasks ".center(80, "-"))
    c.run("invoke -l")
    print()
    print(" info from dev_testutils.py ".center(80, "-"))
    dev_help_file_path = Path("dev_utils/helpers") / "dev_testutils.py"
    with open(dev_help_file_path) as f:
        while True:
            line = f.readline()
            parts = line.split()
            if parts:
                if parts[0].isupper():
                    print(line.strip())

            if not line:
                break
    print(" bye ".center(80, "-"))
