# Create package for PyPI

## Build package

```bash
$ python -m build
```

## Upload package

The `cellpy` package on PyPI requires 2-factor identification. For this to work, you need to create a token.
See below for instructions on how to do this.

```bash
$ python -m twine upload dist/* -u __token__ -p pypi-<token>"
```

:::{Note}
The following instructions are copied from the PyPI website (<https://pypi.org/help/#apitoken>).
Please see the PyPI website for the latest instructions.

Get the API token:
: - Verify your email address (check your account settings).
  - In your account settings, go to the API tokens section and select "Add API token"

To use an API token:
: - Set your username to "\_\_token\_\_"
  - Set your password to the token value, including the pypi- prefix
:::
