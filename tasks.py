from invoke import task

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


@task
def clean(c, docs=False, bytecode=False, extra=''):
    """Clean up stuff from previous builds"""
    print(" Cleaning ".center(80, "="))
    patterns = ['dist', 'build', 'cellpy.egg-info']
    if docs:
        print(" - cleaning doc builds")
        patterns.append('docs/_build')
    if bytecode:
        print(" - cleaning bytecode (i.e. pyc-files)")
        patterns.append('**/*.pyc')
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
    """Get info about the cellpy (version at PyPI etc)"""
    import cellpy
    from pathlib import Path
    print()
    version_file_path = Path("cellpy") / "_version.py"
    dev_help_file_path = Path("dev_utils/helpers") / "dev_testutils.py"
    version_ns = {}
    with open(version_file_path) as f:
        exec(f.read(), {}, version_ns)

    print(" INFO ".center(80, "="))
    print(" version ".center(80, "-"))
    print(f"version (by import cellpy): cellpy {cellpy.__version__}")
    print(f"version (in _version.py):   cellpy {version_ns['__version__']}")
    print("version on PyPI:            ", end="")
    c.run("yolk -V cellpy")

    if full:
        print(" info from dev_testutils.py ".center(80, "-"))
        with open(dev_help_file_path) as f:
            while True:
                line = f.readline()
                parts = line.split()
                if parts:
                    if parts[0].isupper():
                        print(line.strip())

                if not line:
                    break
        print(" invoke tasks ".center(80, "-"))
        c.run("invoke -l")

    print(" the end ".center(80, "-"))


@task
def test(c):
    """Run tests with coverage"""
    c.run("pytest --cov=cellpy tests/")


@task
def build(c, docs=False, upload=True):
    """Create distribution (and optionally upload to PyPI)"""
    print(" Creating distribution ".center(80, "="))
    print("Running python setup.py sdist")
    c.run("python setup.py sdist")
    if docs:
        print(" Building docs ".center(80, "-"))
        c.run("sphinx-build docs docs/_build")
    if upload:
        print(" Uploading to PyPI ".center(80, "="))
        print(" Running 'twine upload dist/*'")
        c.run("twine upload dist/*")


@task
def conda_build(c):
    """Create conda distribution"""
    print(" Creating conda distribution ".center(80, "="))
    print("Running conda build")
    c.run("conda build recipe")
    print("\nTo upload: anaconda upload PATH")
    print("e.g.")
    print(r"anaconda upload C:\miniconda\envs\cellpy_dev\conda-bld\win-64\cellpy-0.3.0.post1-py37_0.tar.bz2")
    print("\nTo convert to different OS-es: conda convert --platform all PATH")
    print("e.g.")
    print("cd builds")
    print(r"conda convert --platform all "
          r"C:\miniconda\envs\cellpy_dev\conda-bld\win-64\cellpy-0.3.0.post1-py37_0.tar.bz2")


@task
def pypi(c):
    c.run("yolk -M cellpy")
