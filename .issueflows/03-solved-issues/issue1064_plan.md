# Issue #1064 — plan

## Goal

Add a catalog of ~10 copy-paste prompts a human can give their LLM agent, each
ending in a `latest` Read the Docs URL. Track those hard links with an
`<!-- agent-doc: … -->` comment and a docs-CI check so a moved page fails the
build instead of rotting in a snippet.

## Constraints

- Docs-only on `master` ([docs-on-master.md](../04-designs-and-guides/docs-on-master.md)).
  Snippets always use `https://cellpy.readthedocs.io/en/latest/…` (not
  `stable`).
- Task-first, scientist with limited Python. One quoted paragraph per prompt;
  no unexplained idioms.
- Root `AGENTS.md` stays short: one pointer, no paste catalog
  ([this-project.md](../04-designs-and-guides/this-project.md) agent-docs
  convention).
- Do not generate the markdown from a sidecar YAML. Hand-written page +
  comments + checker is enough for ten snippets.
- Do not invent a link-shortener or comment syntax beyond `<!-- agent-doc: <src.md> -->`.
- Do not scan `_old_docs/`.

### Prior art

- Toolbox: no docs/link helper (`scan_member_usage.py` / header scanners only).
- Graph: `graphify-out/` absent — skipped.
- Existing paste prompt: [docs/getting_started/mcp.md](../../docs/getting_started/mcp.md)
  “Ask your agent to do it” already uses the issue’s example URL.
- Hard `latest` URLs already live in `docs/llms.txt`, `docs/llms-short.txt`,
  `docs/getting_started/agents.md`, root `AGENTS.md`.
- Docs CI: [.github/workflows/docs.yml](../../.github/workflows/docs.yml)
  builds with `uvx --with mkdocstrings-python zensical build --clean`, then
  `test -f site/llms.txt` and greps the issue count. Same place to assert
  RTD paths exist under `site/`.
- Task index to mine prompts from: [docs/how_do_i.md](../../docs/how_do_i.md).
- Convention: new page + `zensical.toml` nav + findability links (same
  pattern as #1051 / #1054).

## Approach

### 1. Catalog page

Add `docs/getting_started/agent_prompts.md`. Each entry:

```markdown
### How to install cellpy MCP

<!-- agent-doc: getting_started/mcp.md -->
> Install the cellpy MCP server, register it with Cursor, and run
> `cellpy mcp check --client cursor` to prove it works. Follow
> https://cellpy.readthedocs.io/en/latest/getting_started/mcp/.
```

The HTML comment is the source-of-truth path (repo-relative under `docs/`).
The URL path must be that file without `.md`, with a trailing slash. One
comment + one `latest` URL per snippet.

Keep the MCP prompt on `mcp.md` as well (it is the install checklist’s
entry). Same comment + same wording so the checker covers both.

### 2. The ten snippets

| Title | Points at |
| --- | --- |
| How to install cellpy MCP | `getting_started/mcp.md` |
| How to install cellpy and prove it works | `getting_started/installation.md` + checkup via `getting_started/checkup.md` (one URL: installation; checkup named in the prose) |
| How to load a cycler file | `getting_started/basic_usage.md` |
| How to try cellpy without a data file | `getting_started/first_hour.md` |
| How to run a batch from the Excel database | `guides/batch_database.md` |
| How to plot one cell | `guides/plotting.md` |
| How to compute ICA / DVA | `guides/ica.md` |
| How to fix capacities or units that look wrong | `troubleshooting.md` |
| How to use schema names instead of hardcoded headers | `getting_started/agents.md` |
| How to fetch the agent docs map | `getting_started/agents.md` (llms.txt / llms-short.txt) |

Wording is imperative, names a checkable outcome, and ends with Follow
`<latest-url>`. Prefer one URL per snippet; a second page can be named in
words without a second hard link.

### 3. Findability

- Nav: after “Connect an agent IDE (MCP)” in `zensical.toml`.
- Link from `agents.md`, `mcp.md` (catalog vs checklist), `how_do_i.md`
  (new “paste a prompt to my agent” under Get started), `docs/llms.txt`
  (+ short if it still fits), one line in root `AGENTS.md`.

### 4. Hard-link tracker

New helper `.issueflows/00-tools/check_rtd_latest_links.py`:

1. Walk `docs/**/*.md`, `docs/llms.txt`, `docs/llms-short.txt`, `AGENTS.md`.
   Skip `_old_docs/`.
2. Collect `https://cellpy.readthedocs.io/en/latest/<path>`.
3. After a zensical build, each URL must exist as `site/<path>` or
   `site/<path>/index.html` (or the raw file for `.txt`).
4. Collect `<!-- agent-doc: <src.md> -->`. The file `docs/<src.md>` must
   exist. The next `latest` URL in that block must match
   `…/en/latest/<src without .md>/`.
5. Exit 1 with the missing paths listed.

Wire it into `docs.yml` after the site-root llms checks, via
`uv run` / `python` on the helper (no extra deps). Add
`.issueflows/00-tools/check_rtd_latest_links.py` to the workflow `paths:`
filter so a checker-only change still runs Docs CI. Index the helper in
`00-tools/README.md`.

Existing `latest` URLs in `llms.txt` / `agents.md` become covered for free
(step 3). Only snippet blocks need the comment (step 4).

### 5. HISTORY

One Unreleased bullet. Docs-only; no `pyproject.toml` version edit.

## Files to touch

- `docs/getting_started/agent_prompts.md` — new catalog
- `zensical.toml` — nav entry
- `docs/getting_started/agents.md`, `docs/getting_started/mcp.md`,
  `docs/how_do_i.md`, `docs/llms.txt`, `docs/llms-short.txt`, `AGENTS.md` —
  findability; MCP prompt gets the `agent-doc` comment
- `.issueflows/00-tools/check_rtd_latest_links.py` + `00-tools/README.md`
- `.github/workflows/docs.yml` — run the checker; watch its path
- `HISTORY.md` — Unreleased bullet

## Test strategy

- `uv run --group docs zensical build` — “No issues found”
- `uv run .issueflows/00-tools/check_rtd_latest_links.py` (or the invocation
  docs.yml uses) against that `site/`
- No new pytest. Essential suite unchanged.
- Docs workflow is the merge signal for this PR.

## Open questions

None that block coding. Snippet titles above can shift slightly in build if
a page name is clearer; the set stays ~10 and each has one tracked URL.
