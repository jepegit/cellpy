# Plan: Issue #695 — check docs for mistakes

## Goal

Run an interactive `/iflow-fix` pass over the cellpy documentation: find and
fix spelling, broken/outdated facts, and small logic/clarity mistakes. Land
everything in one PR via `/iflow-close`.

## Constraints

- **Session type:** iterative `/iflow-fix` — one small fix per confirm; no bulk
  rewrite of tutorials into native 2.x idioms (that is a separate issue).
- **Source of truth for examples:** notebooks under `docs/examples/` are rendered
  to `.md` via `dev/render_example_notebooks.py` (see
  [dev_docs.md](../../docs/contributing/developers_guide/dev_docs.md)). Prefer
  fixing the notebook when the mistake lives in notebook prose; re-render or
  keep `.md` in sync per that guide.
- **Keep tone:** warm, direct prose already used on the landing pages; no joke
  “planted bugs” style.
- **Do not invent product claims** (e.g. “fully stable”) — only correct what is
  wrong or clearly outdated.
- **No new deps / no docs linter package** unless a one-off script in
  `.issueflows/00-tools/` proves useful later.
- **British English** in existing taglines (`analysing`) is fine unless a true
  typo.

### Prior art

- Toolbox (`00-tools/`): no docs/spelling/link checkers — nothing to reuse.
- Graph: skip (docs polish, not code architecture).
- Docs toolchain: `uv run --group docs python dev/render_example_notebooks.py`
  for example pages; mkdocstrings owns `docs/api/` (avoid hand-editing generated
  API pages except for clear directive/index mistakes).
- Recent related commit on `master`: note wording on `docs/index.md` /
  `docs/examples/index.md` (`better wording`) — already done, out of this branch.

## Approach

1. **Sweep order** (user-facing first):
   1. Landing + getting started (`docs/index.md`, `docs/getting_started/`)
   2. Examples indexes + notebook prose (`docs/examples/`)
   3. Fundamentals (`docs/fundamentals/`)
   4. Guides / other / reference (`docs/guides/`, `docs/other/`, `docs/reference/`)
   5. Contributing / developer guides (lower priority; only clear mistakes)
   6. Skip or deprioritize agent-workflow mirrors (`docs/issue-workflow.md`,
      `docs/cursor-issue-workflow.md`) unless you want them in scope
2. **Per fix:** restate → short plan → confirm → edit → append dated bullet to
   `issue695_status.md` → next.
3. **Seed backlog** (already spotted; order flexible):
   - `docs/examples/05_GITT.md` — stray trailing `"` on intro line
   - `docs/examples/06_loading_different_formats.md` — `possibilites`,
     `seperator`, missing “to” in “possibility select”
   - `docs/examples/templates/tutorial_templates.md` — `succesfully`
4. **Escalate** anything that needs a product/API decision or large rewrite into
   its own issue (do not stretch this session).
5. **Close** with `/iflow-close` (not `/iflow-build`).

## Files to touch

| Path | What changes |
| --- | --- |
| `docs/**/*.md` (and matching `.ipynb` when needed) | Spot fixes only |
| `.issueflows/01-current-issues/issue695_status.md` | Iterative fixes log |
| Possibly `dev/render_example_notebooks.py` output only | Re-render after notebook edits |

Exact file list grows with confirmed fixes; no Python package code expected.

## Test strategy

- Docs-only: no pytest required for prose fixes.
- After notebook edits: re-render with
  `uv run --group docs python dev/render_example_notebooks.py` (scoped if the
  script allows) and spot-check the affected `.md`.
- Optional smoke: build docs if you want before close (not required for every
  micro-fix).

## Open questions

Resolved on Accept (2026-07-26), using recommended defaults:

1. **Notebook sync** — Edit `.ipynb`, then re-render to `.md`.
2. **Scope** — User-facing + examples + fundamentals first; issue-workflow /
   deep dev guides only if an obvious mistake turns up.
3. **Vague hedges** — Soften or trim “will be improved soon”-style claims when
   found.
