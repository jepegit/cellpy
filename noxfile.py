import nox

from yaml import safe_load
from pathlib import Path

CONDA_ENV = "github_actions_environment.yml"
PYTHON_VERSIONS = ["3.10", "3.11"]


@nox.session(python=PYTHON_VERSIONS)
def tests(session):
    """Run the test suite."""
    session.install("-r", "requirements_dev.txt")
    session.run("pytest")


@nox.session(python=PYTHON_VERSIONS, venv_backend="conda")
def conda_tests(session):
    """Run the test suite."""
    environment = safe_load(Path(CONDA_ENV).read_text())
    conda = environment.get("dependencies")
    requirements = conda.pop(-1).get("pip")

    for package in conda:
        session.conda_install(package)
    for requirement in requirements:
        session.install(requirement)
        session.run("pytest")
