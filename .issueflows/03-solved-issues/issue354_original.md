# Issue #354: update build procedure

Source: https://github.com/jepegit/cellpy/issues/354

## Original issue text

Should use pyproject.toml and uv for building.

Tasks

- Replace requirements.txt, setup.py, etc. with complete `pyproject.toml`
- Use uv for management (e.g. `uv add` something)
- Set up a good way of testing building also on local computer (docker?)
