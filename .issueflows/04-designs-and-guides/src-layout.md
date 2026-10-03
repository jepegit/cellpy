# Src layout

**Issue:** [#1109](https://github.com/jepegit/cellpy/issues/1109)

The installable package lives at `src/cellpy/`. Tests stay at repo-root
`tests/`. Hatch matches cellpy-core:

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/cellpy"]
```

Import path and CLI stay `cellpy`. Editable installs (`uv sync`) put the
package on `sys.path`; tests must not add repo-root `cellpy/` to the path.

Non-Python files that ship in the wheel stay next to the modules
(`logging.json`, `parameters/.cellpy_prms_default.conf`,
`readers/instruments/SQL Table IDs.txt`).

Helpers that walk up from a source file to the **repo root** need three
parents from `src/cellpy/<subdir>/file.py` (`parents[3]`), not two.

Docs: mkdocstrings/Griffe inventories from `src/` (`zensical.toml`
`[project.plugins.mkdocstrings.handlers.python] paths = ["src"]`), same as
cellpy-core. The Docs workflow does not install cellpy.
