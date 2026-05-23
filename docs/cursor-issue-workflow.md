# Cursor issue workflow (slash commands)

This repo uses nine Cursor **slash commands** under `.cursor/commands/` that line up with how we track GitHub issues in `.issueflows/01-current-issues/`.

**Quick start: just run `/iflow`.** It inspects the state of the focus issue and dispatches to the right linear-flow command (`/issue-init`, `/issue-plan`, `/issue-start`, or `/issue-close`) — so you don't have to remember which step is next.

| Command | File | Role |
|--------|------|------|
| `/iflow` | `iflow.md` | **Smart dispatcher.** Detect current state and run `/issue-init`, `/issue-plan`, `/issue-start`, or `/issue-close` automatically. Never auto-dispatches to pause / cleanup / yolo / build. |
| `/issue-init` | `issue-init.md` | Pull an issue from GitHub into the repo as a local markdown file and tidy older current issues. |
| `/issue-plan` | `issue-plan.md` | Write a structured `issue<N>_plan.md` and get explicit user confirmation before any code is touched. |
| `/issue-start` | `issue-start.md` | Implement the confirmed plan (no planning step of its own any more). |
| `/issue-pause` | `issue-pause.md` | Park work safely: update status, move the issue group to `02-partly-solved-issues/`, optional WIP commit and branch switch. |
| `/issue-close` | `issue-close.md` | Finish: tests, optional semver bump (`uv version --bump …`), `HISTORY.md` update, issue-folder housekeeping, commit, push, PR. |
| `/issue-cleanup` | `issue-cleanup.md` | Post-merge hygiene: switch to default, `git pull --ff-only`, `git fetch --prune`, delete merged local branches (single consolidated confirm). |
| `/issue-yolo` | `issue-yolo.md` | All-in-one for small, low-risk issues: chains `init → plan → start → close` with up-front safeguards and a single confirmation. |
| `/build` | `build.md` | **Off-path.** Rebuild the [graphify](https://graphify.net) knowledge graph (`graphify-out/graph.html`, `GRAPH_REPORT.md`, `graph.json`). Wraps `issue-flow build` / `graphify`. Optional: only meaningful when `graphifyy` is installed. |

---

## Agent Skills (optional)

`issue-flow init` / `issue-flow update` also install **Cursor Agent Skills** under `.cursor/skills/` — longer, on-demand playbooks that mirror the slash commands (plus a small helper for version bumps):

| Skill folder | Invoke (examples) | Role |
|--------------|-------------------|------|
| `issueflow-iflow` | `/issueflow-iflow` or attach `@issueflow-iflow` | Smart dispatcher — same state machine as `/iflow`. |
| `issueflow-issue-init` | `/issueflow-issue-init` or attach `@issueflow-issue-init` | Same flow as `/issue-init`. |
| `issueflow-issue-plan` | `/issueflow-issue-plan` | Same flow as `/issue-plan` (write & confirm plan). |
| `issueflow-issue-start` | `/issueflow-issue-start` | Read the plan, implement from `.issueflows/01-current-issues/`. |
| `issueflow-issue-pause` | `/issueflow-issue-pause` | Update status, move issue group to `02-partly-solved-issues/`, optional WIP commit + branch switch. |
| `issueflow-issue-close` | `/issueflow-issue-close` | Tests, optional bump, status checkboxes, move issue docs, commit, push, PR. |
| `issueflow-issue-cleanup` | `/issueflow-issue-cleanup` | Post-merge cleanup (single consolidated confirm, never `-D`). |
| `issueflow-issue-yolo` | `/issueflow-issue-yolo` | Chain `init → plan → start → close` with safeguards. |
| `issueflow-version-bump` | `@issueflow-version-bump` (often used from `/issue-close`) | Bump `[project]` version in `pyproject.toml` via `uv version --bump patch|minor|major`. |
| `issueflow-history-update` | `@issueflow-history-update` (used from `/issue-close`) | Append an entry to `## [Unreleased]` in `HISTORY.md`, or promote it to a new `## [x.y.z] - YYYY-MM-DD` release section when a version bump happened. |
| `issueflow-build` | `/issueflow-build` | Same flow as `/build`: rebuild the graphify knowledge graph for the project. Off-path; never auto-dispatched. |

Each skill sets `disable-model-invocation: true` so it is included when you **explicitly** invoke it, not on every chat. See [Agent Skills](https://cursor.com/docs/context/skills) in the Cursor docs.

---

## Branch and folder hygiene

Two recurring pain points the commands actively help with:

- **Stale local branches that look "several commits ahead of main" after a squash-merged PR.** `/issue-cleanup` detects merge status via `gh pr view`, and once the PR is merged it offers (with one consolidated confirm) to switch back to the default branch, `git pull --ff-only`, `git fetch --prune`, and run `git branch -d` on every local branch whose commits are already in the default branch (including squash-merged ones). Destructive flags like `-D` are never used automatically. `/issue-close` no longer performs this step itself.
- **Left-overs in `.issueflows/01-current-issues/`.** Both `/issue-init` (when a new issue is captured) and `/issue-start` (before implementation begins) sweep that folder: every `issue<n>_*` group **other than the focus issue** is moved automatically to `.issueflows/03-solved-issues/` if a status file contains `- [x] Done`, otherwise to `.issueflows/02-partly-solved-issues/`.

All the commands that touch git also run a short **branch-status preflight**: `git fetch --prune`, current branch, ahead/behind vs the default branch, and a warning when the current branch's leading digits refer to an issue already archived in `02-`/`03-`.

---

## 0. `/iflow` — smart dispatcher (quick start)

**When:** Any time you want the next right step without remembering which specific command applies.

**What you pass:** Nothing, or the same arguments the target command would take (e.g. `/iflow 42` on a fresh branch, `/iflow bump minor` when the issue is done). `/iflow` forwards the trailing text verbatim.

**How it decides:**

| State of the focus issue | Dispatches to |
|--------------------------|---------------|
| No `issue<N>_original.md` (or no focus issue yet) | `/issue-init` |
| `original` exists, no `issue<N>_plan.md` | `/issue-plan` |
| Plan exists, status file missing or `- [ ] Done` | `/issue-start` |
| Status file contains `- [x] Done` | `/issue-close` |

**Focus-issue resolution:** prefer the leading digits of the current branch when it matches `^<N>-.+`; else the single group in `.issueflows/01-current-issues/`; else ask.

**Not auto-dispatched:** `/issue-pause`, `/issue-cleanup`, and `/issue-yolo`. `/iflow` will mention them in its output when relevant (e.g. "after the PR merges, run `/issue-cleanup`") but never picks them for you.

**Result:** One of the four linear commands runs, with its own normal checkpoints intact.

---

## 1. `/issue-init` — capture the issue locally

**When:** You have a GitHub issue you want to work on (or archive older "current" issues before starting a new one).

**What you pass:** Either an issue number (e.g. `42`), a full GitHub issue URL, or nothing after `/issue-init`—in that case, on a branch named like `42-short-description`, the assistant may ask to use `#42` from the branch (and refuses to guess on `main`/`master`). The assistant resolves `owner/repo` from `git remote origin` when you only pass a number.

**What happens:**

- The assistant uses **GitHub CLI** (`gh`) to fetch title, body, URL, and number. You need `gh` authenticated (`gh auth login` if needed).
- It creates **`.issueflows/01-current-issues/issue<number>_original.md`** with the title, source URL, and the **exact** issue body from GitHub.
- **Archive:** Other files already in `.issueflows/01-current-issues/` (grouped by issue number, e.g. `issue121_*`) may be **moved** to `.issueflows/02-partly-solved-issues/` or `.issueflows/03-solved-issues/`, based on whether a status file for that issue contains a checked **Done** line (`- [x] Done`). The new issue's files are never moved as part of this step.
- If the target `issue<number>_original.md` already exists, the assistant should not overwrite it without asking.

**Result:** One canonical "original issue" file under `.issueflows/01-current-issues/` plus optional archive moves.

---

## 2. `/issue-plan` — design the approach

**When:** The issue is captured (`*_original.md` exists) and you want a confirmed plan **before** any code changes.

**What you pass:** Optional free-form hints (constraints, design preferences).

**What the assistant does:**

1. Finds the focus issue in `.issueflows/01-current-issues/`.
2. Runs the branch-status preflight (non-destructive).
3. Reads the original issue and any prior status.
4. Writes **`issue<N>_plan.md`** with sections: **Goal**, **Constraints**, **Approach**, **Files to touch**, **Test strategy**, **Open questions**.
5. Runs a scope check — if the change is broad, proposes splitting into smaller issues or phases.
6. **Stops and asks for explicit confirmation**: accept, revise, or abort. `/issue-plan` never implements code itself.

**Result:** A confirmed `issue<N>_plan.md` ready for `/issue-start` to execute.

---

## 3. `/issue-start` — implement the plan

**When:** The issue has a confirmed `issue<N>_plan.md` (from `/issue-plan`) and you are ready to code.

**What you pass:** Optional implementation hints.

**What the assistant does:**

1. Confirms **which** issue file applies if several exist or things are ambiguous.
2. **Branch status preflight** — `git fetch --prune`, report current branch and ahead/behind vs the default branch, warn if the current branch looks stale or if you are still on the default branch.
3. **Sweeps stale current issues** — moves every `issue<n>_*` group **other than the focus issue** to `.issueflows/03-solved-issues/` (done) or `.issueflows/02-partly-solved-issues/` (not done).
4. **Plan precondition** — reads `issue<N>_plan.md`. If missing, asks the user to choose: run `/issue-plan` now, proceed without a plan (note in status file), or abort. Does **not** hard-stop.
5. **Implements** the plan. Updates the status markdown as work progresses.

**Result:** Implementation aligned with the confirmed plan and project rules (tests with `uv run`, dependency management with `uv`, etc.).

---

## 4. `/issue-pause` — park work safely

**When:** You need to stop partway through an issue (context switch, blocked on input) without closing it.

**What you pass:** Optional short note that becomes the **Remaining work** text.

**What the assistant does:**

1. Updates `issue<N>_status.md` with **Done so far**, **Remaining work**, and **Paused on** sections. The `- [ ] Done` checkbox stays unchecked.
2. Moves the whole `issue<N>_*` group from `.issueflows/01-current-issues/` to `.issueflows/02-partly-solved-issues/`.
3. Offers, as **one** consolidated prompt, a WIP commit and/or `git switch <default>`. Never deletes branches, never force-pushes, never runs tests.

**Result:** The issue is safely archived under `02-partly-solved-issues/` with clear resume notes. Re-open via `/issue-init <N>` (which will ask for the archived-issue confirmation).

---

## 5. `/issue-close` — land the work

**When:** Implementation is done and you want to ship (commit, push, PR). Post-merge branch cleanup is a **separate** step — see `/issue-cleanup` below.

**What you pass:** Optional notes (branch name, PR title, draft PR, or "skip issue doc update"). You can also ask for a **semver bump** in the same line, for example:

- `/issue-close bump` or `/issue-close patch` — bump **patch** (e.g. `1.2.0` → `1.2.1`) using `uv version --bump patch`.
- `/issue-close bump minor` — bump **minor**.
- `/issue-close bump major` or `/issue-close major` — bump **major**.
- Free text that clearly describes the bump level — the assistant infers patch vs minor vs major.
- `/issue-close nohistory` (or `skip history`) — skip the `HISTORY.md` update step for this run.
- `/issue-close log "one-line summary"` (or `note "..."`) — override the `HISTORY.md` bullet summary instead of using the GitHub issue title.

The bump runs **after** tests and **before** issue-folder moves and **before** commit / push / PR so the PR includes the new version. If `pyproject.toml` has no bumpable version, the assistant skips the bump and continues.

**Typical steps the assistant follows:**

1. **Sanity check** — e.g. `uv run pytest`, review the diff.
2. **Optional version bump** — if requested, follow `.cursor/skills/issueflow-version-bump/SKILL.md` and run `uv version --bump …` from the project root.
3. **Update `HISTORY.md`** — unless `nohistory` was passed, follow `.cursor/skills/issueflow-history-update/SKILL.md`. Append a bullet to `## [Unreleased]` (no bump) or promote `## [Unreleased]` to `## [<new_version>] - <YYYY-MM-DD>` and open a fresh empty `## [Unreleased]` above it (with bump). The assistant shows the diff and asks for a single confirm before writing. If `HISTORY.md` is missing at the project root, the step is skipped with a note — never auto-created.
4. **Issue folders** — update status markdown; use `- [x] Done` only when fully resolved. Move completed issue files from `.issueflows/01-current-issues/` to `.issueflows/03-solved-issues/`, or partly done work to `.issueflows/02-partly-solved-issues/`.
5. **Commit** — focused staging and a clear message (include `pyproject.toml` / `uv.lock` if the bump changed them, and `HISTORY.md` when step 3 updated it). Sync with the default branch using `git pull --ff-only`.
6. **Push** — to your usual remote (e.g. `origin`).
7. **Pull request** — open against the default branch; link the GitHub issue (`Closes #n` / `Refs #n`).
8. **After review** — remind you the working copy is still on the issue branch; once the PR merges, run `/issue-cleanup` for the post-merge tidy-up.

**Result:** Commit, push, PR link. No branches are deleted from `/issue-close` itself.

---

## 6. `/issue-cleanup` — post-merge branch hygiene

**When:** The PR opened by `/issue-close` has merged on GitHub.

**What you pass:** Nothing (acts on the current branch) or an explicit branch name.

**What the assistant does:**

1. Detects the default branch.
2. Detects merge state via `gh pr view` (falls back to `git cherry origin/<default> <branch>` to catch squash-merges).
3. If **not merged**: reminds you to stay off the default for unrelated work and re-run after merge.
4. If **merged**: one consolidated yes/no prompt covering `git switch <default>`, `git pull --ff-only`, `git fetch --prune`, and `git branch -d` on every local branch whose tip is already reachable from the default (including squash-merged ones). Never `-D`; if `-d` refuses, reports and moves on.
5. Optional safe folder sweep: moves any `issue<N>_*` group whose status file says `- [x] Done` to `.issueflows/03-solved-issues/`.

**Result:** Working tree on the default, merged local branches deleted (with consent), folders tidy.

---

## 7. `/build` — rebuild the knowledge graph (optional)

**When:** The project has the optional [graphify](https://graphify.net) integration enabled (the `graphify` CLI is on `PATH` and a `graphify-out/` folder is present), and the graph has gone stale relative to the source tree.

**What you pass:** Optional graphify subcommand and args, forwarded verbatim. Common picks:

- *(nothing)* — AST-only build of the project root (`graphify update <project>`). **No LLM API key required**; produces the full `graphify-out/`. The default.
- `extract` — adds the slower semantic LLM pass for richer cross-file relationships. Needs an API key (`GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `MOONSHOT_API_KEY`) or `--backend ollama` for a local LLM via [Ollama](https://ollama.com). Cursor's own LLM is **not** available to subprocesses.
- `watch` — long-running watcher that auto-rebuilds on save.
- `cluster-only` — rerun clustering on the existing `graph.json` without re-extraction (e.g. `cluster-only --no-viz`).
- `./subdir` — restrict the scan to a sub-directory (default subcommand: `update`).

**What the assistant does:**

1. Runs `issue-flow build` (which shells out to the `graphify` CLI). If `issue-flow` is unavailable, falls back to `graphify update .` directly (`graphify .` alone is **not** valid — graphify requires a subcommand).
2. If `graphify` is not installed, prints install hints (`uv tool install graphifyy`) and stops — never silently retries.
3. If `graphify extract` fails with "no LLM API key found", suggests setting one of the supported env vars, or using `--backend ollama`, or dropping back to the default `update` subcommand.
4. Verifies that `graphify-out/graph.html`, `GRAPH_REPORT.md`, and `graph.json` exist after a successful run.

**Result:** A refreshed `graphify-out/` so `/issue-start` can navigate by graph instead of grepping. `/build` is **off-path** — `/iflow`, `/issue-start`, and `/issue-close` may *suggest* a rebuild but never invoke `/build` automatically.

---

## 8. `/issue-yolo` — all-in-one for small issues

**When:** The change is genuinely small and low-risk (typo, one-line fix, doc tweak) and you want to skip the usual checkpoints. For anything bigger, use the individual commands.

**Preflight (any failure aborts before the chain starts):**

- Refuses to run on `main` / `master`.
- Refuses if `git status --porcelain` shows unrelated uncommitted changes.
- Runs `uv run pytest` up front; refuses if anything fails.
- **Single consolidated confirmation** listing the full planned chain (issue, branch, repo, downstream flags).

**Chain:** `/issue-init` → `/issue-plan` (auto-confirmed short plan; aborts if the scope check reveals the change isn't actually small) → `/issue-start` → `uv run pytest` again → `/issue-close` (with any forwarded `bump`/`patch`/`minor`/`major`/`draft`). Does **not** run `/issue-cleanup` — the PR hasn't merged yet.

**Result:** A commit, push, and PR ready for review — or an abort at the first ambiguity.

---

## End-to-end flow

Tip: at any point in the linear flow below, you can just run `/iflow` and it will dispatch to the right step based on current state.

```text
GitHub issue
    │  /issue-init   (or /iflow)
    ▼
.issueflows/01-current-issues/issueN_original.md
    │  /issue-plan
    ▼
issueN_plan.md  (user confirmed)
    │  /issue-start
    ▼
Code + tests (+ status updates during work)
    │  /issue-close  [optional: bump patch/minor/major]
    ▼
Commit → push → PR
    │
    │  (PR merges on GitHub)
    │  /issue-cleanup
    ▼
Default branch, stale local branches deleted (with single confirm)

Detours:
  /issue-pause  — park mid-stream; moves issueN_* to 02-partly-solved-issues/
  /issue-yolo   — chain init → plan → start → close for tiny fixes (safeguarded)
```

The command definitions under `.cursor/commands/` are the source of truth. The skill packages under `.cursor/skills/` repeat the same workflows for explicit invocation. This document is a readable overview only.
