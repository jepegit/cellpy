# Issue #1109 status

- [x] Done

## What's done

- `git mv cellpy src/cellpy`
- Hatch wheel `packages = ["src/cellpy"]`; coverage omit paths updated
- Source-walking tests and repo-root `__main__` walks use `src/cellpy`
- CI benchmark path filters, AGENTS lint paths, this-project + src-layout note
- `uv run pytest -m essential`: 959 passed
- `uv run pytest`: 1757 passed, 12 xfailed

## Remaining work

- None
