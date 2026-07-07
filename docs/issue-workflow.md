# Cursor issue workflow (Agent Skills)

This repo uses Cursor **Agent Skills** under `.cursor/skills/` that line up with how we track GitHub issues in `.issueflows/01-current-issues/`. Skills appear in the slash menu, so the normal entry points are still `/iflow`, `/iflow-plan`, and friends.

**Quick start: just run `/iflow`.** It inspects the state of the focus issue and dispatches to the right linear-flow skill (`/iflow-init`, `/iflow-plan`, `/iflow-start`, or `/iflow-close`) — so you don't have to remember which step is next. Haven't chosen an issue yet? Start with **`/iflow-pick`**.

`issue-flow init` also creates a durable project brief at `.issueflows/04-designs-and-guides/this-project.md` when it is missing. Edit it by hand with project-specific context; `issue-flow update` and `issue-flow init --force` leave existing content untouched.

It also seeds `.issueflows/00-tools/README.md` — the index of the project's **shared toolbox**. Drop reusable helper scripts there during issue work and add a one-line index entry; check the folder before writing a new one-off helper. Like the project brief, this README is never overwritten by `issue-flow update`, so its index grows over time.

**Multi-root workspaces:** when several sibling repos share one editor workspace, resolve the target repo first (`root:` / `repo:` hints, or `issue-flow agent resolve`). Never let `git` or `gh` infer the repository from cwd alone. See `.issueflows/04-designs-and-guides/multi-repo-workspaces.md` when present.


| Entry point | File | Role |
|--------|------|------|
| `/iflow-pick` | `iflow-pick/SKILL.md` | **Front door.** Help choose the next issue (parked work first, else ranked open GitHub issues), create the branch, and run `/iflow-init`. Off-path; never auto-dispatched. |
| `/iflow` | `iflow/SKILL.md` | **Smart dispatcher.** Detect current state and run `/iflow-init`, `/iflow-plan`, `/iflow-start`, or `/iflow-close` automatically. Never auto-dispatches to pick / pause / cleanup / yolo / fix / status / graphify. |
| `/iflow-init` | `iflow-init/SKILL.md` | Pull an issue from GitHub into the repo as a local markdown file and tidy older current issues. |
| `/iflow-plan` | `iflow-plan/SKILL.md` | Write a structured `issue<N>_plan.md` and get explicit user confirmation before any code is touched. |
| `/iflow-start` | `iflow-start/SKILL.md` | Implement the confirmed plan (no planning step of its own any more). |
| `/iflow-pause` | `iflow-pause/SKILL.md` | Park work safely: update status, move the issue group to `02-partly-solved-issues/`, optional WIP commit and branch switch. |
| `/iflow-close` | `iflow-close/SKILL.md` | Finish: tests, optional semver bump (`uv version --bump …`), `HISTORY.md` update, issue-folder housekeeping, commit, push, PR, and switch back to default when clean unless `stay` is passed. |
| `/iflow-cleanup` | `iflow-cleanup/SKILL.md` | Post-merge hygiene: switch to default, `git pull --ff-only`, `git fetch --prune`, delete merged local branches (single consolidated confirm). |
| `/iflow-yolo` | `iflow-yolo/SKILL.md` | All-in-one for small, low-risk issues: chains `init → plan → start → close` with up-front safeguards and a single confirmation. |
| `/iflow-fix` | `iflow-fix/SKILL.md` | **Off-path.** Interactive iterative-fixes session: create one issue + long-lived branch, then loop over many small fixes (short plan each, recorded in `issue<N>_status.md`), ending with `/iflow-close`. |
| `/iflow-status` | `iflow-status/SKILL.md` | **Off-path, read-only.** Snapshot of where every issue stands — local tracking state (focus / parked / solved) plus open GitHub issues cross-referenced against it. Changes nothing. |
| `/iflow-archive` | `iflow-archive/SKILL.md` | **Off-path, destructive (gated).** Condense old solved issue groups into a dated `YYYY-MM-DD_archived_issues.md` summary (recording the pre-archive git ref for recovery), then delete the original files after one consolidated confirm. |
| `/iflow-graphify` | `iflow-graphify/SKILL.md` | **Off-path.** Rebuild the [graphify](https://iflow-graphify.net) knowledge graph (`graphify-out/graph.html`, `GRAPH_REPORT.md`, `graph.json`). Wraps `issue-flow graphify` / `graphify`. Optional: only meaningful when `graphifyy` is installed. |



---

## Agent Skills

`issue-flow init` / `issue-flow update` install **Cursor Agent Skills** under `.cursor/skills/` — longer, on-demand playbooks (plus a small helper for version bumps):

| Skill folder | Invoke (examples) | Role |
|--------------|-------------------|------|
| `iflow-pick` | `/iflow-pick` | Front door — same flow as `/iflow-pick` (choose issue, branch, init, hand off). |
| `iflow` | `/iflow` or attach `@iflow` | Smart dispatcher — same state machine as `/iflow`. |
| `iflow-init` | `/iflow-init` or attach `@iflow-init` | Same flow as `/iflow-init`. |
| `iflow-plan` | `/iflow-plan` | Same flow as `/iflow-plan` (write & confirm plan). |
| `iflow-start` | `/iflow-start` | Read the plan, implement from `.issueflows/01-current-issues/`. |
| `iflow-pause` | `/iflow-pause` | Update status, move issue group to `02-partly-solved-issues/`, optional WIP commit + branch switch. |
| `iflow-close` | `/iflow-close` | Tests, optional bump, status checkboxes, move issue docs, commit, push, PR, and safe default-branch switch. |
| `iflow-cleanup` | `/iflow-cleanup` | Post-merge cleanup (single consolidated confirm, never `-D`). |
| `iflow-yolo` | `/iflow-yolo` | Chain `init → plan → start → close` with safeguards. |
| `iflow-fix` | `/iflow-fix` | Same flow as `/iflow-fix`: set up an interactive iterative-fixes session, loop over small fixes, finish with `/iflow-close`. Off-path. |
| `iflow-status` | `/iflow-status` | Same flow as `/iflow-status`: read-only overview of focus / parked / solved issues plus open GitHub issues. Off-path; writes nothing. |
| `iflow-archive` | `/iflow-archive` | Same flow as `/iflow-archive`: summarise selected solved issue groups into a dated archive file (with the pre-archive git ref), then delete the originals. Off-path; destructive with one consolidated confirm. |
| `iflow-version-bump` | `@iflow-version-bump` (often used from `/iflow-close`) | Bump `[project]` version in `pyproject.toml` via `uv version --bump <level>` (any uv level: `major`/`minor`/`patch`/`stable`/`alpha`/`beta`/`rc`/`post`/`dev`); a bare `bump` stays on the current pre-release channel. |
| `iflow-history-update` | `@iflow-history-update` (used from `/iflow-close`) | Append an entry to `## [Unreleased]` in `HISTORY.md`, or promote it to a new `## [x.y.z] - YYYY-MM-DD` release section when a version bump happened. |
| `iflow-graphify` | `/iflow-graphify` | Same flow as `/iflow-graphify`: rebuild the graphify knowledge graph for the project. Off-path; never auto-dispatched. |

Each skill sets `disable-model-invocation: true` so it is included when you **explicitly** invoke it, not on every chat. See [Agent Skills](https://cursor.com/help/customization/skills) in the Cursor docs.

Lifecycle skills also carry a **`### MODEL & EXECUTION DIRECTIVE`** — **economy** (speed/token savings) or **reasoning** (design depth) — baked at `issue-flow update` from `[issueflow]` / `[issueflow.step_profiles]` in `.issueflows/config.toml`. `/iflow-pick` can announce label-based session overrides when `model_label_flows` is enabled (`deep_model_label` / `fast_model_label`).


---

## Branch and folder hygiene

Two recurring pain points the workflows actively help with:

- **Stale local branches that look "several commits ahead of main" after a squash-merged PR.** `/iflow-close` switches back to the default branch after opening or updating the PR when the tree is clean, unless you pass `stay` / `don't switch`. `/iflow-cleanup` detects merge status after the PR is merged and offers (with one consolidated confirm) to `git fetch --prune` and run `git branch -d` on every local branch whose commits are already in the default branch (including squash-merges). Destructive flags like `-D` are never used automatically.
- **Left-overs in `.issueflows/01-current-issues/`.** Both `/iflow-init` (when a new issue is captured) and `/iflow-start` (before implementation begins) sweep that folder: every `issue<n>_*` group **other than the focus issue** is moved automatically to `.issueflows/03-solved-issues/` if a status file contains `- [x] Done`, otherwise to `.issueflows/02-partly-solved-issues/`.

All workflows that touch git also run a short **branch-status preflight**: `git fetch --prune`, current branch, ahead/behind vs the default branch, and a warning when the current branch's leading digits refer to an issue already archived in `02-`/`03-`.

---

## 0a. `/iflow-pick` — choose the next issue (front door)

**When:** You are on the default branch with nothing in progress and want help deciding what to work on next.

**What you pass:** Nothing (survey + ask), `fix` (create a new general-fixes issue every time), or a hint (`milestone v0.4`, a topic) to bias ranking.

**What the assistant does (three phases):**

1. **Choose.** Prefers parked work in `.issueflows/02-partly-solved-issues/`; otherwise lists open GitHub issues (`gh issue list`) ranked by **milestone**, **labels**, and **topical similarity** to recently solved issues, then asks you to confirm a pick from a short shortlist. `fix` skips the survey and creates a new `chore: general fixes` issue.
2. **Branch.** Requires a clean tree, branches off the default with the GitHub numeric convention `git switch -c <N>-<short-slug>`, then runs the `/iflow-init` flow automatically for `<N>`.
3. **Hand off.** Asks whether to continue with `/iflow-plan` (never auto-runs it).

**Out of scope (Phase B follow-up):** automated breakdown of an over-large issue into sub-issues created on GitHub and parked under `02-partly-solved-issues/`. `/iflow-pick` only *mentions* the option for now.

**Off-path:** `/iflow` never auto-dispatches to `/iflow-pick`; it creates GitHub issues and branches, so you opt in explicitly.

**Result:** A chosen issue captured on a fresh `<N>-<slug>` branch, ready for `/iflow-plan`.

---

## 0. `/iflow` — smart dispatcher (quick start)

**When:** Any time you want the next right step without remembering which specific command applies.

**What you pass:** Nothing, or the same arguments the target command would take (e.g. `/iflow 42` on a fresh branch, `/iflow bump minor` when the issue is done). `/iflow` forwards the trailing text verbatim.

**How it decides:**

| State of the focus issue | Dispatches to |
|--------------------------|---------------|
| No `issue<N>_original.md` (or no focus issue yet) | `/iflow-init` |
| `original` exists, no `issue<N>_plan.md` | `/iflow-plan` |
| Plan exists, status file missing or `- [ ] Done` | `/iflow-start` |
| Status file contains `- [x] Done` | `/iflow-close` |

**Focus-issue resolution:** prefer the leading digits of the current branch when it matches `^<N>-.+`; else the single group in `.issueflows/01-current-issues/`; else ask.

**Not auto-dispatched:** `/iflow-pause`, `/iflow-cleanup`, `/iflow-yolo`, `/iflow-fix`, `/iflow-status`, and `/iflow-archive`. `/iflow` will mention them in its output when relevant (e.g. "after the PR merges, run `/iflow-cleanup`") but never picks them for you.

**Result:** One of the four linear commands runs, with its own normal checkpoints intact.

---

## 1. `/iflow-init` — capture the issue locally

**When:** You have a GitHub issue you want to work on (or archive older "current" issues before starting a new one).

**What you pass:** Either an issue number (e.g. `42`), a full GitHub issue URL, or nothing after `/iflow-init`—in that case, on a branch named like `42-short-description`, the assistant may ask to use `#42` from the branch (and refuses to guess on `main`/`master`). The assistant resolves `owner/repo` from `git remote origin` when you only pass a number.

**What happens:**

- The assistant uses **GitHub CLI** (`gh`) to fetch title, body, URL, and number. You need `gh` authenticated (`gh auth login` if needed).
- It creates **`.issueflows/01-current-issues/issue<number>_original.md`** with the title, source URL, and the **exact** issue body from GitHub.
- **Archive:** Other files already in `.issueflows/01-current-issues/` (grouped by issue number, e.g. `issue121_*`) may be **moved** to `.issueflows/02-partly-solved-issues/` or `.issueflows/03-solved-issues/`, based on whether a status file for that issue contains a checked **Done** line (`- [x] Done`). The new issue's files are never moved as part of this step.
- If the target `issue<number>_original.md` already exists, the assistant should not overwrite it without asking.

**Result:** One canonical "original issue" file under `.issueflows/01-current-issues/` plus optional archive moves.

---

## 2. `/iflow-plan` — design the approach

**When:** The issue is captured (`*_original.md` exists) and you want a confirmed plan **before** any code changes.

**What you pass:** Optional free-form hints (constraints, design preferences).

**What the assistant does:**

1. Finds the focus issue in `.issueflows/01-current-issues/`.
2. Runs the branch-status preflight (non-destructive).
3. Reads the original issue and any prior status; reads `.issueflows/04-designs-and-guides/this-project.md` when present and consults other files under `.issueflows/04-designs-and-guides/` when relevant.
4. **Prior-art discovery** — skim `.issueflows/00-tools/` for an existing helper; if `graphify-out/GRAPH_REPORT.md` exists, skim God Nodes / Communities / Suggested Questions for the affected area; grep for adjacent helpers; record findings under **`### Prior art`** in **`## Constraints`** (or `- None found (toolbox + grep + graph checked).`). Strong overlaps become **Open questions**.
5. Explores read-only, then writes **`issue<N>_plan.md`** with sections: **Goal**, **Constraints** (including **Prior art**), **Approach**, **Files to touch**, **Test strategy**, **Open questions**.
6. Runs a scope check — if the change is broad, proposes splitting into smaller issues or phases.
7. **Stops and asks for explicit confirmation**: accept, revise, or abort. `/iflow-plan` never implements code itself.

**Result:** A confirmed `issue<N>_plan.md` ready for `/iflow-start` to execute.

---

## 3. `/iflow-start` — implement the plan

**When:** The issue has a confirmed `issue<N>_plan.md` (from `/iflow-plan`) and you are ready to code.

**What you pass:** Optional implementation hints.

**What the assistant does:**

1. Confirms **which** issue file applies if several exist or things are ambiguous.
2. **Branch status preflight** — `git fetch --prune`, report current branch and ahead/behind vs the default branch, warn if the current branch looks stale or if you are still on the default branch.
3. **Sweeps stale current issues** — moves every `issue<n>_*` group **other than the focus issue** to `.issueflows/03-solved-issues/` (done) or `.issueflows/02-partly-solved-issues/` (not done).
4. **Plan precondition** — reads `issue<N>_plan.md`. If missing, asks the user to choose: run `/iflow-plan` now, proceed without a plan (note in status file), or abort. Does **not** hard-stop.
5. **Seeds `issue<N>_status.md` up front** (unchecked `- [ ] Done`, **What's done** / **Remaining work**) and keeps it current as work progresses — it lives *during* the work, not just at close.
6. **Implements** the plan, using `.issueflows/04-designs-and-guides/this-project.md` and relevant design docs for project context when present. Reuses helpers from `.issueflows/00-tools/` and contributes new reusable ones back there.

**Result:** Implementation aligned with the confirmed plan and project rules (tests with `uv run`, dependency management with `uv`, etc.).

---

## 4. `/iflow-pause` — park work safely

**When:** You need to stop partway through an issue (context switch, blocked on input) without closing it.

**What you pass:** Optional short note that becomes the **Remaining work** text.

**What the assistant does:**

1. Updates `issue<N>_status.md` with **Done so far**, **Remaining work**, and **Paused on** sections. The `- [ ] Done` checkbox stays unchecked.
2. Moves the whole `issue<N>_*` group from `.issueflows/01-current-issues/` to `.issueflows/02-partly-solved-issues/`.
3. Offers, as **one** consolidated prompt, a WIP commit and/or `git switch <default>`. Never deletes branches, never force-pushes, never runs tests.

**Result:** The issue is safely archived under `02-partly-solved-issues/` with clear resume notes. Re-open via `/iflow-init <N>` (which will ask for the archived-issue confirmation).

---

## 5. `/iflow-close` — land the work

**When:** Implementation is done and you want to ship (commit, push, PR). Post-merge branch cleanup is a **separate** step — see `/iflow-cleanup` below.

**What you pass:** Optional notes (branch name, PR title, draft PR, or "skip issue doc update"). You can also ask for a **semver bump** in the same line, for example:

- `/iflow-close bump` — **pre-release-aware default**: stays on the current channel (alpha→alpha, beta→beta, rc→rc, dev→dev) or `patch` when the version is already stable.
- `/iflow-close <level>` — any uv level: `patch`, `minor`, `major`, `stable`, `alpha`, `beta`, `rc`, `post`, `dev` (e.g. `/iflow-close minor`, `/iflow-close beta`). `dev` must be paired, e.g. `/iflow-close bump patch dev`.
- Free text that clearly describes the bump level — the assistant infers the level (e.g. "bugfix release" → `patch`, "promote to beta" → `beta`); it never auto-picks `major`.
- `/iflow-close nohistory` (or `skip history`) — skip the `HISTORY.md` update step for this run.
- `/iflow-close log "one-line summary"` (or `note "..."`) — override the `HISTORY.md` bullet summary instead of using the GitHub issue title.
- `/iflow-close stay` (or `stay on branch`, `don't switch`, `dont switch to main`) — skip the safe default-branch switch after the PR step.

The bump runs **after** tests and **before** issue-folder moves and **before** commit / push / PR so the PR includes the new version. If `pyproject.toml` has no bumpable version, the assistant skips the bump and continues.

**Typical steps the assistant follows:**

1. **Sanity check** — e.g. `uv run pytest`, review the diff.
2. **Optional version bump** — if requested, follow `.cursor/skills/iflow-version-bump/SKILL.md` and run `uv version --bump …` from the project root.
3. **Update `HISTORY.md`** — unless `nohistory` was passed, follow `.cursor/skills/iflow-history-update/SKILL.md`. Append a bullet to `## [Unreleased]` (no bump) or promote `## [Unreleased]` to `## [<new_version>] - <YYYY-MM-DD>` and open a fresh empty `## [Unreleased]` above it (with bump). The assistant shows the diff and asks for a single confirm before writing. If `HISTORY.md` is missing at the project root, the step is skipped with a note — never auto-created.
4. **Issue folders** — update status markdown; use `- [x] Done` only when fully resolved. Move completed issue files from `.issueflows/01-current-issues/` to `.issueflows/03-solved-issues/`, or partly done work to `.issueflows/02-partly-solved-issues/`.
5. **Commit** — focused staging and a clear message (include `pyproject.toml` / `uv.lock` if the bump changed them, and `HISTORY.md` when step 3 updated it). Sync with the default branch using `git pull --ff-only`.
6. **Push** — to your usual remote (e.g. `origin`).
7. **Pull request** — open against the default branch; link the GitHub issue (`Closes #n` / `Refs #n`).
8. **Switch back when safe** — unless `stay` / `don't switch` was passed, run `git status --porcelain`; if clean, `git switch <default>` and `git pull --ff-only`; if dirty, stay put and report why switching is unsafe.
9. **After review** — if switched back, return to the PR branch before review fixes; once the PR merges, run `/iflow-cleanup` for the post-merge tidy-up.

**Result:** Commit, push, PR link, and either a clean switch back to the default branch or a clear reason for staying on the issue branch. No branches are deleted from `/iflow-close` itself.

---

## 6. `/iflow-cleanup` — post-merge branch hygiene

**When:** The PR opened by `/iflow-close` has merged on GitHub.

**What you pass:** Nothing (acts on the current branch) or an explicit branch name.

**What the assistant does:**

1. Detects the default branch.
2. Detects merge state via `gh pr view` (falls back to `git cherry origin/<default> <branch>` to catch squash-merges).
3. If **not merged**: reminds you to stay off the default for unrelated work and re-run after merge.
4. If **merged**: one consolidated yes/no prompt covering `git switch <default>`, `git pull --ff-only`, `git fetch --prune`, and `git branch -d` on every local branch whose tip is already reachable from the default (including squash-merged ones). Never `-D`; if `-d` refuses, reports and moves on.
5. Optional safe folder sweep: moves any `issue<N>_*` group whose status file says `- [x] Done` to `.issueflows/03-solved-issues/`.

**Result:** Working tree on the default, merged local branches deleted (with consent), folders tidy.

---

## 7. `/iflow-graphify` — rebuild the knowledge graph (optional)

**When:** The project has the optional [graphify](https://iflow-graphify.net) integration enabled (the `graphify` CLI is on `PATH` and a `graphify-out/` folder is present), and the graph has gone stale relative to the source tree.

**What you pass:** Optional graphify subcommand and args, forwarded verbatim. Common picks:

- *(nothing)* — AST-only build of the project root (`graphify update <project>`). **No LLM API key required**; produces the full `graphify-out/`. The default.
- `extract` — adds the slower semantic LLM pass for richer cross-file relationships. Needs an API key (`GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `MOONSHOT_API_KEY`) or `--backend ollama` for a local LLM via [Ollama](https://ollama.com). Cursor's own LLM is **not** available to subprocesses.
- `watch` — long-running watcher that auto-rebuilds on save.
- `cluster-only` — rerun clustering on the existing `graph.json` without re-extraction (e.g. `cluster-only --no-viz`).
- `./subdir` — restrict the scan to a sub-directory (default subcommand: `update`).

**What the assistant does:**

1. Runs `issue-flow graphify` (which shells out to the `graphify` CLI). If `issue-flow` is unavailable, falls back to `graphify update .` directly (`graphify .` alone is **not** valid — graphify requires a subcommand).
2. If `graphify` is not installed, prints install hints (`uv tool install graphifyy`) and stops — never silently retries.
3. If `graphify extract` fails with "no LLM API key found", suggests setting one of the supported env vars, or using `--backend ollama`, or dropping back to the default `update` subcommand.
4. Verifies that `graphify-out/graph.html`, `GRAPH_REPORT.md`, and `graph.json` exist after a successful run.

**Result:** A refreshed `graphify-out/` so `/iflow-start` can navigate by graph instead of grepping. `/iflow-graphify` is **off-path** — `/iflow`, `/iflow-start`, and `/iflow-close` may *suggest* a rebuild but never invoke `/iflow-graphify` automatically.

---

## 8. `/iflow-yolo` — all-in-one for small issues

**When:** The change is genuinely small and low-risk (typo, one-line fix, doc tweak) and you want to skip the usual checkpoints. For anything bigger, use the individual commands.

**Preflight (any failure aborts before the chain starts):**

- Refuses to run on `main` / `master`.
- Refuses if `git status --porcelain` shows unrelated uncommitted changes.
- Runs `uv run pytest` up front; refuses if anything fails.
- **Single consolidated confirmation** listing the full planned chain (issue, branch, repo, downstream flags).

**Chain:** `/iflow-init` → `/iflow-plan` (auto-confirmed short plan; aborts if the scope check reveals the change isn't actually small) → `/iflow-start` → `uv run pytest` again → `/iflow-close` (with any forwarded `bump`/`patch`/`minor`/`major`/`draft`/`stay`). Does **not** run `/iflow-cleanup` — the PR hasn't merged yet.

**Result:** A commit, push, and PR ready for review, with the final branch reported — or an abort at the first ambiguity.

---

## 9. `/iflow-fix` — interactive iterative-fixes session

**When:** You have a bucket of small, iterative fixes (little bugs, typos, chores, polish) to knock out on one branch, rather than a single well-defined deliverable.

**What you pass:** An optional session name (used for the issue title and branch slug). No name → defaults to `iterative-small-fixes`. During an active session, a `/iflow-fix <description>` (or just describing a fix) means "run the next fix".

**What the assistant does:**

1. **Set up (once).** Preflight (default branch, `git fetch --prune`, clean tree); create a GitHub issue with `gh issue create` (always, after confirmation) and capture `N`; create branch `<N>-<slug>` (off the default, or — when already on a non-default branch — ask whether to branch from current or default); delegate local capture to `/iflow-init`; seed `issue<N>_status.md` with an unchecked `- [ ] Done` and an empty **`## Iterative fixes log`**.
2. **Loop.** For each proposed fix: restate it, write a short inline plan, implement **only on confirmation**, and append a dated bullet to the **Iterative fixes log**. A fix that turns out to be a real feature is split out into its own issue instead.
3. **Finish.** Tells you to run `/iflow-close` to land the session (it never auto-runs it); reminds you about `/iflow-cleanup` after the PR merges.

**Coexists with `/iflow-pick fix`:** that command is a one-shot setup back into the normal `/iflow-plan` → `/iflow-start` flow; `/iflow-fix` stays and drives the loop until close.

**Off-path:** `/iflow` never auto-dispatches to `/iflow-fix`. While a session is active, drive it with `/iflow-fix` + `/iflow-close`, not `/iflow`. GitHub only (`gh`); GitLab is not supported.

**Result:** A session issue + branch with a running fixes log, ready to land via `/iflow-close`.

---

## 10. `/iflow-status` — status overview of all issues (read-only)

**When:** You want a bird's-eye view of where every issue stands, rather than acting on the single focus issue.

**What you pass:** Nothing (full report), `local` (skip the GitHub query), or a hint like `milestone v0.4` to bias the GitHub section.

**What the assistant does (all read-only):**

1. **Context** — current branch, default branch, clean/dirty tree, ahead/behind; focus issue `N` derived from the branch when it matches `^<N>-.+`.
2. **Focus issue** — the active group in `.issueflows/01-current-issues/` and its lifecycle stage (init / plan / start / close) using the same file-presence logic as `/iflow`, plus the suggested next step.
3. **Parked work** — each `issue<n>_*` group under `.issueflows/02-partly-solved-issues/` with title and one-line status.
4. **Solved archive** — count of distinct solved issues under `.issueflows/03-solved-issues/` and the most recent few.
5. **Open GitHub issues** — `gh issue list` cross-referenced against the local folders, tagged **focus** / **parked** / **solved-locally** / **untracked**. Skipped gracefully when `gh` is unavailable or `local` was passed.
6. **Summary** — one terse line.

**Off-path:** `/iflow` never auto-dispatches to `/iflow-status`. It writes nothing, moves no files, and creates no branches, commits, or GitHub issues.

**Result:** A consolidated, read-only status report. Nothing on disk or GitHub changes.

---

## 11. `/iflow-archive` — condense the solved-issues archive (destructive, gated)

**When:** `.issueflows/03-solved-issues/` has grown large and most of its `issue<N>_*` groups are no longer worth keeping as individual files.

**What you pass:** Nothing (archive all but the 5 most recent solved groups), `keep <K>` (keep the `<K>` most recent), an explicit list of issue numbers, or `all`.

**What the assistant does:**

1. **Preflight** — requires a **clean working tree** (stop if dirty) and records the pre-archive ref via `git rev-parse HEAD`.
2. **Select** — lists every solved group (number + title), applies your input rule, and shows the candidate list for you to adjust.
3. **Consolidated confirm** — one prompt covering exactly which issues get summarised and that their files will be **deleted**; nothing proceeds without a clear yes.
4. **Summarise** — appends to `.issueflows/03-solved-issues/YYYY-MM-DD_archived_issues.md`: a header with the pre-archive ref and recovery recipe (`git show <ref>:<path>`), then one section per issue with source URL, archived file names, and a 2–4 sentence outcome summary.
5. **Delete** — removes the archived groups' files (`issue-flow agent archive <N> ...` when the CLI is installed, else `git rm`).
6. **Commit offer** — proposes a single commit so the deletion lands right after the recorded ref; asks first, never pushes.

**Off-path:** `/iflow` never auto-dispatches to `/iflow-archive`. It deletes files, so you opt in explicitly.

**Result:** One dated summary file replaces the archived groups; every original file remains recoverable from git history via the recorded ref.

---

## End-to-end flow

Tip: at any point in the linear flow below, you can just run `/iflow` and it will dispatch to the right step based on current state.

```text
(no issue chosen yet)
    │  /iflow-pick   → choose issue, create branch, run /iflow-init
    ▼
GitHub issue
    │  /iflow-init   (or /iflow)
    ▼
.issueflows/01-current-issues/issueN_original.md
    │  /iflow-plan
    ▼
issueN_plan.md  (user confirmed)
    │  /iflow-start
    ▼
Code + tests (+ status updates during work)
    │  /iflow-close  [optional: bump <patch|minor|major|alpha|beta|rc|…>]
    ▼
Commit → push → PR
    │
    │  (PR merges on GitHub)
    │  /iflow-cleanup
    ▼
Default branch, stale local branches deleted (with single confirm)

Detours:
  /iflow-pick   — front door: choose the next issue, branch, init (before the linear flow)
  /iflow-pause  — park mid-stream; moves issueN_* to 02-partly-solved-issues/
  /iflow-yolo   — chain init → plan → start → close for tiny fixes (safeguarded)
  /iflow-fix    — interactive session: one branch, many small fixes, then /iflow-close
  /iflow-status — read-only overview of all issues (focus / parked / solved + GitHub)
  /iflow-archive — condense old solved issues into a dated summary file (gated deletion)
```

The skill packages under `.cursor/skills/` are the primary workflow surface. This document is a readable overview only.
