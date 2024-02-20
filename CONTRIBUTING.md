# Contributing

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

You can contribute in many ways:

## Types of Contributions

### Report Bugs

Report bugs in the [cellpy repository at GitHub](https://github.com/jepegit/cellpy/issues).

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

### Fix Bugs

Look through the GitHub issues for bugs. Anything tagged with "bug"
and "help wanted" is open to whoever wants to implement it.

### Implement Features

Look through the GitHub issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it.

### Write Documentation

cellpy could always use more documentation, whether as part of the
official cellpy docs, in docstrings, or even on the web in blog posts,
articles, and such.

### Submit Feedback

The best way to send feedback is to file an issue in the
[cellpy repository at GitHub](https://github.com/jepegit/cellpy/issues).

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

## Get Started

Ready to contribute? Here's how to set up ``cellpy`` for local development.

1. Fork the ``cellpy`` repo on GitHub.
2. Clone your fork locally:

    ```shell
    git clone git@github.com:your_name_here/cellpy.git
    ```

3. Create a local python virtual environment and activate it using python's venv utility:

    ```shell
    python -m venv .venv
    source .venv/bin/activate  # or .venv\Scripts\activate on Windows
    ```

   Or use ``conda`` environments. See the conda documentation for more information.
   A suitable environment yaml configuration file
   can be found in the root of the repository (``dev_environment.yml``; to create the environment,
   run ``conda env create -f dev_environment.yml``).

4. Install your local copy into your virtualenv:

    ```shell
    python -m pip install . -e
    ```

5. Create a branch for local development:

    ```shell
    git checkout -b name-of-your-bugfix-or-feature
    ```

   Now you can make your changes locally.

6. When you're done making changes, check that your changes pass the tests:

    ```shell
    pytest
    ```

   If there are any libraries missing (it could happen) just pip install them into your virtual environment (or
   conda install them into your conda environment).

7. Commit your changes and push your branch to GitHub:

    ```shell
    git add .
    git commit -m "Your detailed description of your changes."
    git push origin name-of-your-bugfix-or-feature
    ```

8. Submit a pull request through the GitHub website (or your IDE if that option exists).

## Pull Request Guidelines

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. The pull request should not include any gluten.

## Tips

To self-hypnotize yourself to sleep well at night::

```shell
  echo "You feel sleepy"
  echo "You are a great person"
```

