# Issue #1054 plan

## Goal

Publish hand-maintained `llms.txt` and `llms-short.txt` at the docs site root, and point agents at them.

## Approach

- Add `docs/llms.txt` (llmstxt.org shape, `latest` chapter links) and `docs/llms-short.txt` (one-liner + 4–6 links).
- One findability line on `docs/getting_started/agents.md` and in root `AGENTS.md`.
- Do not add either file to `zensical.toml` `nav`.
- Confirm `zensical build` output; if `.txt` is not copied, add an explicit copy in `.readthedocs.yaml` `post_build` and the docs CI job.

## Files to touch

- `docs/llms.txt` (new)
- `docs/llms-short.txt` (new)
- `docs/getting_started/agents.md`
- `AGENTS.md`
- `.readthedocs.yaml` and/or `.github/workflows/docs.yml` only if the build does not copy the files

## Test strategy

- `uv run --group docs zensical build` (or `uvx --with mkdocstrings-python zensical build --clean`) and confirm `site/llms.txt` and `site/llms-short.txt`.

## Constraints

### Prior art

- None found (toolbox + grep + graph checked). Agent usage already lives in `agents.md` / `AGENTS.md`; these files are indexes, not a second copy.
