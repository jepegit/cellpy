# Issue #990 — status

- [x] Done

## What's done

- Guarded the "project dir does not exist. Create?" prompt in `_new()`
  (`cellpy/cli_api.py`) with `no_input`, so `no_input=True` creates the
  directory without reading stdin. Interactive path unchanged (the prompt
  default was already `"yes"`).
- Added `test_create_project_with_no_input_creates_the_project_dir` to
  `tests/test_cli_api.py` (essential): the prompt helpers raise if called, and
  the test asserts the directory is created and `no_input=True` reaches
  cookiecutter. Registered in `04-designs-and-guides/test-registry.md`.
- Full suite: 1576 passed, 172 skipped, 13 xfailed.

## Remaining work

None.
