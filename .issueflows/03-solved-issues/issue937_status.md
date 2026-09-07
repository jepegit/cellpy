# Issue #937 status

- [x] Done

## What's done

- Removed `matplotlib` and `ipykernel` from `[project.dependencies]`.
- Added extras `plotting-mpl` and `notebook`; both included in `all`.
- `matplotlib` stays in the `dev` group so `uv sync` / CI keep Agg tests.
- `require_matplotlib` raises `OptionalDependencyError` naming `cellpy[plotting-mpl]`.
- Guarded the four remaining module-scope matplotlib imports.
- Dependency-budget tests + docs (`agents.md`, installation extras table).

## Remaining work

- None.
