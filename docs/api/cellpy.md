# cellpy

The top-level entry points — what most scripts need. These are re-exported
lazily as `cellpy.get`, `cellpy.merge_cells`, and `cellpy.print_instruments`
(PEP 562); mkdocstrings documents the defining module because Griffe cannot
resolve `__getattr__` aliases.

::: cellpy.readers.cellreader.get

::: cellpy.readers.cellreader.merge_cells

::: cellpy.readers.cellreader.print_instruments

## Command-line API

Everything the `cellpy` command does is callable from Python, so scripts do not
have to shell out and parse output.

::: cellpy.cli_api
