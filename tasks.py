from invoke import task

"""Tasks for cellpy development.

This is some text. Not sure where it is shown.
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
        c.run("rm -rf {}".format(pattern))


@task
def test(c):
    """Run tests with coverage"""
    c.run("pytest --cov=cellpy tests/")


@task
def build(c, docs=False, upload=False):
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
