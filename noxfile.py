"""Nox sessions for cellpy.

Installs the project and its extras/dev group from ``pyproject.toml``
"""

import nox

PYTHON_VERSIONS = ["3.13", "3.14"]


def _install_project(session: nox.Session) -> None:
    """Editable install with optional extras + ``[dependency-groups].dev``."""
    session.install("-e", ".[all]", "--group", "dev")


@nox.session(python=PYTHON_VERSIONS)
def tests(session: nox.Session) -> None:
    """Run the test suite in a virtualenv."""
    _install_project(session)
    session.run("pytest", *session.posargs)


@nox.session(python=PYTHON_VERSIONS, venv_backend="conda")
def conda_tests(session: nox.Session) -> None:
    """Run the test suite in a conda-backed env (same pyproject deps)."""
    _install_project(session)
    session.run("pytest", *session.posargs)
