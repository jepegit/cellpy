---
name: iflow
description: >-
  Smart dispatcher: detect where the focus issue stands and dispatch to
  /iflow-init, /iflow-plan, /iflow-start, or /iflow-close.
disable-model-invocation: true
issue-flow-version: 0.4.2a4
---

# issue-flow — iflow smart dispatcher (`/iflow`)

Follow this skill to run **the right next step** in the issue-flow lifecycle: it detects state and routes to `/iflow-init`, `/iflow-plan`, `/iflow-start`, or `/iflow-close`, forwarding trailing args verbatim.

Do **not** use this skill for `/iflow-pick`, `/iflow-pause`, `/iflow-cleanup`, `/iflow-yolo`, or `/iflow-fix`. Those are explicit-only commands. (`/iflow-pick` is the front door *before* `/iflow-init`, for when no issue has been chosen yet. `/iflow-fix` runs an interactive iterative-fixes session, driven by `/iflow-fix` + `/iflow-close`.)


**Invoke:** type `iflow` in chat, or `/iflow` from the slash menu.




### MODEL & EXECUTION DIRECTIVE


**Profile: economy** — Prioritize speed and token economy over deep reasoning.

In Cursor: use **Auto** or a fast model before invoking this step.



Keep scope tight to what this step requires.




### Resolve project root (multi-root workspaces)

Before any `git`, `gh`, or `.issueflows/` path operation in this workflow:

**Resolution order** (stop when unambiguous):

1. **Explicit hints** in slash input — `root:<path>`, `repo:<folder-basename>` (directory name, e.g. `cellpy-core`), or `repo:owner/name`.
2. **CLI fast path** — `issue-flow agent resolve [-C <start>] [--from-file <active-file>] [--json]`. Use the returned `project_root` and `repo`; pass `-C <project_root>` to other `issue-flow agent …` subcommands. When the answer came from the workspace registry, the payload sets `resolved_via_workspace_default: true`.
3. **Branch context** — exactly one workspace repo whose branch matches `^\d+-` → that root.
4. **Single scaffold** — exactly one `.issueflows/` tree visible in the workspace → that root.
5. **Workspace default** — an `issueflow-workspace.toml` at the workspace root (created with `issue-flow workspace init`) may name a `default` member repo; use it when no scaffold matched above. Tell the user the default was used.
6. **Ambiguous** → **stop and ask**; never guess between sibling repos.

After resolution, treat the result as `<project_root>` and `<owner/repo>`:

- **Git:** `git -C <project_root> …` (or `issue-flow agent … -C <project_root>` for supported ops).
- **GitHub:** always `gh … --repo <owner/repo>` — never rely on `gh`'s implicit cwd default.
- **Paths:** all `.issueflows/…` paths are under `<project_root>`.

When `.issueflows/04-designs-and-guides/multi-repo-workspaces.md` exists, read it for layout and cross-repo guidance.

## Instructions

> **CLI fast path (optional).** If the `issue-flow` CLI is on `PATH`, run
> `issue-flow agent state --json` to resolve the focus issue, its lifecycle
> stage, and the suggested `next_command` in one deterministic step (covers
> instructions 1–2), then dispatch to that command. The CLI is optional: if it
> is not installed or it errors, fall back to the manual instructions below.
> (`issue-flow` is only present when the user installed it, e.g.
> `uv tool install issue-flow`.)

1. **Resolve the focus issue number `N`.**
   - `git branch --show-current`. If it matches `^(\d+)-.+`, the leading digits are the **authoritative** `N`.
   - List `issue<n>_*` groups in `.issueflows/01-current-issues/`, and also check `.issueflows/02-partly-solved-issues/` and `.issueflows/03-solved-issues/` for archived groups matching `N`.
   - Pick `N` by precedence:
     1. **Branch-derived `N` wins**, regardless of whether a group for `N` exists in `01-current-issues/`. State **A** will apply when no `issue<N>_*` files are present yet. If `issue<N>_*` is archived under `02-partly-solved-issues/` or `03-solved-issues/`, warn the user that `/iflow-init`'s archived-issue guard will ask for an explicit confirmation before re-opening.
     2. No branch-derived `N`, exactly one group exists in `01-current-issues/` → use it.
     3. No branch-derived `N`, no groups at all → state **A** (dispatch `/iflow-init`; it will ask for a number).
     4. No branch-derived `N`, multiple groups → **stop and ask**.

2. **Detect state and choose the dispatch target** (first match wins):

   - **A** — no `issue<N>_original.md` (or no focus issue) → dispatch to **`/iflow-init`**. Reason: "no `*_original.md` yet".
   - **B** — original exists, no `issue<N>_plan.md` → dispatch to **`/iflow-plan`**. Reason: "no plan file yet".
   - **C** — plan exists, and status file is missing or its `- [x] Done` is unchecked → dispatch to **`/iflow-start`**. Reason: "plan is confirmed but status is not `- [x] Done`".
   - **D** — status file contains `- [x] Done` (case-insensitive on `done`) → dispatch to **`/iflow-close`**. Reason: "status marks the issue `- [x] Done`".


3. **Announce and dispatch.** Print one line like `/iflow -> /iflow-plan  (issue #N: no plan file yet)` and then follow the chosen command's playbook. Forward the user's trailing text verbatim.

4. **Respect downstream checkpoints.** Never suppress the downstream command's own prompts (plan confirmation, unrelated-changes prompt, etc.). `/iflow` adds no new confirmation layer of its own.

5. **Report.** Summarize: focus issue `N` and how it was resolved, which command was dispatched and why, the downstream output, and a one-line hint when an off-path command is the natural next step:
   - state **D** + PR likely merged → "after the PR merges, run `/iflow-cleanup`"
   - mid-stream context switch needed → "to park this work, run `/iflow-pause`"
   - tiny fix that would benefit from a single-shot chain → "consider `/iflow-yolo` next time"

## Constraints

- Never auto-dispatch to `/iflow-pick`, `/iflow-pause`, `/iflow-cleanup`, `/iflow-yolo`, `/iflow-fix`, `/iflow-epic`, or `/iflow-cycle`.
- If the focus issue cannot be resolved (multiple groups, branch ambiguous), stop and ask.
- Do not modify files beyond what the downstream command would normally modify. `/iflow` itself writes nothing — all file changes come from the dispatched command.
- Dispatch to at most one command per `/iflow` invocation.
