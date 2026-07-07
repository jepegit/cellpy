<!-- BEGIN issue-flow (managed: do not edit this block) -->
# Issue-flow best practices


## Running python

**Respect the project's existing toolchain first.** If this project already
documents how to run Python and manage dependencies — in its `README`,
`AGENTS.md`, `CLAUDE.md`, `.cursor/rules`, `environment.yml`, `pyproject.toml`,
`Makefile`, CI config, etc. — **follow that**, even where it conflicts with the
defaults below. These rules describe issue-flow's *default* assumptions, not a
mandate to override a project that has already chosen differently.

The one tool-neutral principle: **don't call bare `python ...`** — invoke Python
through the project's environment (its runner, or an activated virtualenv/conda
env) so scripts and tests see the right interpreter and dependencies.

### If the project uses conda

When the project documents a conda environment, run **all** Python commands —
scripts **and `pytest`** — inside the **activated conda environment**. Do **not**
substitute `uv run`.

```bash
# Either activate the environment first…
conda activate <env-name>
python run_script.py
pytest

# …or run one-off commands inside it:
conda run -n <env-name> pytest
```

### If the project uses uv (issue-flow's default)

For projects scaffolded fresh (and this is the default when nothing else is
documented), use `uv`:

```bash
# ❌ BAD: bare interpreter
python run_script.py

# ✅ GOOD: through uv
uv run run_script.py
```

**Package management with `uv`**

- Install, synchronize, and lock dependencies with `uv`; don't reach for `pip`,
  `pip-tools`, or `poetry` in a uv-managed project.

```bash
# Add or upgrade dependencies
uv add <package>

# Remove dependencies
uv remove <package>

# Reinstall all dependencies from the lock file
uv sync

# Run a script with the right environment
uv run script.py
```

### Other toolchains (plain venv / pip / poetry)

If the project uses something else, use whatever it documents (e.g. activate its
`.venv` and use `pip`, or run `poetry run`). Match the project; don't force `uv`.


## Issue tracking structure

```bash
cellpy/
    .issueflows/
        00-tools/
        01-current-issues/
            issueXX_original.md
            issueXX_status.md
        02-partly-solved-issues/
        03-solved-issues/
        04-designs-and-guides/
    pyproject.toml
    readme.md
    ...
```


## Development information


### Working on issues

After each iteration, update the documents in `.issueflows/01-current-issues` (should contain one file labelled `_original` with the original issue description, a `_plan` file with the confirmed approach, and supplementary status files describing what has been done, current status, and remaining work).
Use an explicit status checkbox in the status file:
- `- [x] Done` when fully resolved
- `- [ ] Done` when not fully resolved

### Command lifecycle

If you have not chosen an issue yet, run **`/iflow-pick`** — the front door that helps you select the next issue (parked work first, else ranked open GitHub issues), creates the branch, and runs `/iflow-init` for you. It is off-path (never auto-dispatched).

If you just want the next right step, run **`/iflow`** — it detects state (by file presence under `.issueflows/01-current-issues/` and the status-file `- [x] Done` marker) and dispatches to `/iflow-init`, `/iflow-plan`, `/iflow-start`, or `/iflow-close`. It never auto-dispatches to `/iflow-pick`, `/iflow-pause`, `/iflow-cleanup`, or `/iflow-yolo` — those stay explicit.

The full slash-command lifecycle is:

1. **`/iflow-init`** — capture the GitHub issue as `issue<N>_original.md`.
2. **`/iflow-plan`** — design the approach in `issue<N>_plan.md` and get explicit confirmation before any code changes.
3. **`/iflow-start`** — implement the confirmed plan. Asks to run `/iflow-plan` first if the plan file is missing.
4. **`/iflow-pause`** *(optional)* — park work mid-stream: update status, move the issue group to `02-partly-solved-issues`, optional WIP commit.
5. **`/iflow-close`** — tests, optional `uv version --bump`, status update, commit, push, PR. Does not delete branches.
6. **`/iflow-cleanup`** — post-merge: switch to default, `git pull --ff-only`, `git fetch --prune`, `git branch -d` on merged local branches under a single consolidated confirm. Never `-D`.

`/iflow-yolo` chains `init → plan → start → close yolo` for small, low-risk issues with up-front safeguards (clean tree, passing tests, single consolidated confirm). Its close step is hands-off: changelog decided without a prompt, PR merged (`gh pr merge --squash`, `--auto` fallback), then default-branch switch + pull.


Issue labels can select the flow: when an issue picked via `/iflow-pick` carries the **`yolo`** label, it is routed through `/iflow-yolo` (one combined confirmation). Controlled by `label_flows` (default `true`) and `yolo_label` (default `"yolo"`) under `[issueflow]` in `.issueflows/config.toml`; re-run `issue-flow update` after changing them.



Lifecycle skills include a **`### MODEL & EXECUTION DIRECTIVE`** section that tells agents whether to prioritize **economy** (speed) or **reasoning** (depth) for that step. Toggle with `step_directives` under `[issueflow]`; override per step via `[issueflow.step_profiles]`; optional label hints during `/iflow-pick` via `model_label_flows`, `deep_model_label`, and `fast_model_label`. Re-run `issue-flow update` after changing any of these.


`/iflow-fix` opens an interactive iterative-fixes session: it creates one GitHub issue + long-lived branch, then loops over many small fixes (each gets a short plan and is implemented only on confirmation, recorded as a dated bullet in `issue<N>_status.md`), and ends with `/iflow-close`. It is off-path (never auto-dispatched); while a session is active, drive it with `/iflow-fix` + `/iflow-close`, not `/iflow`.

`/iflow-status` prints a **read-only** overview of where every issue stands — the local tracking state under `.issueflows/` (focus / parked / solved) plus open GitHub issues cross-referenced against it. It is off-path (never auto-dispatched) and changes nothing.

`/iflow-archive` condenses old solved issue groups under `.issueflows/03-solved-issues/` into a single dated `YYYY-MM-DD_archived_issues.md` summary file (recording the pre-archive git ref for recovery via `git show <ref>:<path>`), then deletes the original `issue<N>_*` files. It is off-path and destructive: nothing is deleted before one consolidated confirmation.

> On tools without project slash commands (e.g. Codex CLI), invoke the mirrored Agent Skills instead (for example `iflow-init` in place of `/iflow-init`).

### When finishing an issue

If the issue is fully resolved (no additional subtasks present), move the original, plan, and status markdown files to `.issueflows/03-solved-issues`. Else, move them to `.issueflows/02-partly-solved-issues`.

### Scripts that can help us when working on issues

`.issueflows/00-tools/` is the project's durable toolbox of reusable helper scripts, with a `README.md` index describing each one.

- **Check it first.** Before writing a new one-off helper for an issue, skim the `00-tools/README.md` index and the folder — a suitable tool may already exist.
- **Contribute back.** If you build something during an issue that could help on a future one, save it into `.issueflows/00-tools/` and add a one-line entry to the index (name, what it does, when to use it) so the next agent knows whether to reach for it.



### Optional response styles

A **caveman** Agent Skill is installed under `.cursor/skills/caveman/`. It
is a terse, "token-greedy" response style that keeps all technical substance
while dropping filler, articles, and pleasantries. It is **off by default** and
only kicks in when the user asks for it (e.g. "caveman", "token greedy", "be
terse"). Turn it off with **"stop caveman"** or **"normal mode"**. Code,
commits, PRs, security warnings, and destructive-action confirmations are always
written in normal prose, never caveman. (To make caveman on by default for this
project, set `caveman_default = true` under `[issueflow]` in
`.issueflows/config.toml` and re-run `issue-flow update`.)




### Planning aids

A **grill-me** Agent Skill is installed under `.cursor/skills/grill-me/`.
It runs a relentless planning interview that stress-tests a plan or design —
one question at a time, each with a recommended answer — until every branch of
the decision tree is resolved. It is **off by default** and only kicks in when
you ask for it (e.g. "grill me", "poke holes in this"). Turn it off with **"stop
grilling"** or **"normal mode"**. (To make grilling on by default during planning
for this project, set `grill_me_default = true` under `[issueflow]` in
`.issueflows/config.toml` and re-run `issue-flow update`.)



### Designs and guides

Long-lived design docs, design decisions, and project "good practices" live under `.issueflows/04-designs-and-guides/`. Unlike the issue folders, content here is **not** tied to a single issue and is **not** archived when an issue closes — it is the project's durable memory.

- **Project brief:** if `.issueflows/04-designs-and-guides/this-project.md` exists, read it early for project-specific context (what the repo is, stack/runtime, how to run/test, conventions, entry points, and known limitations).
- **Before planning or implementing**, skim `.issueflows/04-designs-and-guides/` for existing docs relevant to the current issue and follow them (cite them in the plan when they influence the approach).
- **When a non-trivial design decision is made** during `/iflow-plan` or `/iflow-start`, add or update a markdown file here. Keep entries terse: context, the decision, alternatives considered, and a link back to the issue.
- **Never overwritten by `issue-flow update`.** The folder is recreated if missing, but existing files are left alone.


### Multi-root workspaces

When an editor workspace contains **multiple sibling repositories**, each with its own `.issueflows/` scaffold:

- **Resolve the target repo first** — explicit `root:` / `repo:` hints, then `issue-flow agent resolve`, then branch/single-scaffold heuristics; **ask** when ambiguous. Never let `git` or `gh` infer the repo from cwd alone.
- **Scoped rules** — this repo's `issueflow-rules` apply under this project root only (path globs). Put **toolchain-specific** run/test commands in `.issueflows/04-designs-and-guides/this-project.md`, not in shared boilerplate that every repo merges.
- **Per-repo lifecycle** — `/iflow-cleanup`, branch hygiene, and focus issue folders are **per repository**; repeat commands in each repo when needed.
- **Design doc** — see `.issueflows/04-designs-and-guides/multi-repo-workspaces.md` when present (issue #67).


### Branch hygiene

- Do issue work on an **issue branch** named like `<N>-<short-slug>`, not on the default branch.
- Before starting or continuing work on an issue branch, run `git fetch --prune` and check where the branch sits relative to `origin/<default>` (ahead/behind). A branch that is "several commits ahead" after a merged PR usually means the PR was squash-merged and the local branch is stale.
- **Assume squash-merges on GitHub.** After a PR merges: run **`/iflow-cleanup`** — it switches to the default branch, runs `git pull --ff-only`, `git fetch --prune`, and deletes merged local branches with `git branch -d <branch>` under a single consolidated confirm (never `-D` automatically). `/iflow-close` no longer does this step itself.
- If an issue is already archived under `.issueflows/02-partly-solved-issues` or `.issueflows/03-solved-issues`, the matching local branch is stale; don't resume work on it silently — switch back to the default branch and, if the issue really needs re-opening, do it deliberately through `/iflow-init` (which will ask for a second confirmation).


### Folder hygiene for `.issueflows/01-current-issues`

- Only the **focus issue** (the one currently being worked on) should live in `.issueflows/01-current-issues`.
- `/iflow-init` and `/iflow-start` both sweep that folder automatically: every `issue<n>_*` group **other than the focus issue** is moved to `.issueflows/03-solved-issues` if a status file contains `- [x] Done`, otherwise to `.issueflows/02-partly-solved-issues`. Keep status files accurate so the sweep routes them correctly.


### Knowledge graph (optional, via [graphify](https://iflow-graphify.net))

If a `graphify-out/` folder exists in the project root, the project has the optional [graphify](https://iflow-graphify.net) integration enabled and a knowledge graph is available alongside the source.

- **Before grepping**, skim `graphify-out/GRAPH_REPORT.md`. It surfaces god-nodes (most-connected concepts), surprising cross-module connections, and suggested questions the graph can answer — often a faster way to locate the files an issue actually touches than full-text search.
- **`/iflow-graphify`** (slash command) or **`issue-flow graphify`** (CLI) rebuild the graph. With no extra args this runs `graphify update <project>` — AST-only, **no LLM API key needed**. For richer semantic relationships (cross-file links surfaced by an LLM pass), run `issue-flow graphify extract` after setting `GEMINI_API_KEY` / `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `MOONSHOT_API_KEY` (or pass `--backend ollama` for a local LLM). Other subcommands: `watch` (live), `cluster-only --no-viz` (re-cluster). Trailing flags pass through verbatim. Your agent's own LLM cannot be reused by subprocesses; graphify needs its own backend.
- `/iflow-graphify` is **off-path**: never auto-dispatched by `/iflow`, `/iflow-start`, or `/iflow-close`. It is the user's call. `/iflow-start` may *suggest* skimming `GRAPH_REPORT.md`; `/iflow-close` may *suggest* a rebuild after large structural changes — neither runs `graphify` automatically.
- If `graphify-out/` is not present, ignore graph-related guidance entirely. The integration is opt-in (install with `uv tool install graphifyy`, then `issue-flow update` to register the graphify skill).

<!-- END issue-flow (managed) -->
