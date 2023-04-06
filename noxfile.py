import nox


@nox.session(python=["3.9", "3.10", "3.11"])
def tests(session):
    """Run the test suite."""
    session.install("-r", "requirements_dev.txt")
    session.run("pytest")
