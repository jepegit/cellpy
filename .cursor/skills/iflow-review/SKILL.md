---
name: iflow-review
description: >-
  Review open GitHub issues and apply labels (extendable kinds; v1: yolo).
disable-model-invocation: true
issue-flow-version: 0.4.2a4
---

# issue-flow — review and label issues (`/iflow-review`)

Follow this skill to **review open GitHub issues and apply labels**. It is
extendable by review *kind*; v1 supports **`yolo`** only (apply the configured
`yolo` label to issues that pass the yolo-fitness judgment).

Do **not** auto-dispatch from `/iflow`, `/iflow-build`, or `/iflow-close`. Off-path
only. Do **not** create new GitHub issues here (use `/iflow-issue`,
`/iflow-pick fix`, or `/iflow-epic … publish`). Do **not** remove labels in v1.


**Invoke:** type `iflow review` in chat, or `/iflow-review` from the slash menu (`iflow-review` also works).




### MODEL & EXECUTION DIRECTIVE


**Profile: reasoning** — Prioritize deep thinking and careful trade-offs over speed or token economy.

In Cursor: switch to a thinking-capable model before invoking this step (not Auto-only).



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


## Input

- **(nothing)** — list supported review kinds and ask which to run.
- **`yolo`** — examine open issues; propose adding the configured
  `yolo_label` (default `"yolo"`) where fitness says yes.

Trailing text after the kind is reserved for future filters; ignore unknown
tokens with a warning rather than inventing behaviour.

## Review kinds (extendable)

| Kind | Label applied | Fitness criteria |
|------|---------------|------------------|
| `yolo` | resolved `[issueflow].yolo_label` (default `"yolo"`) | Same as `/iflow-epic`: well-specified, mechanical or pattern-following, low blast radius, guarded by existing tests — umbrella work, design decisions, and flag-day changes are **no**. |

Future kinds (e.g. model-profile labels) add a row here + optional CLI
`--kind` support — do not rename this skill.

## Instructions

> **CLI fast path (optional).** If the `issue-flow` CLI is on `PATH`:
> - **List:** `issue-flow agent label-candidates [--kind yolo] [--json]`
> - **Apply (after confirm):** `issue-flow agent label-apply <N> [<N>…] --label <name> [--dry-run] [--json]`
>
> The CLI never judges fitness. Judgment stays in this skill. If the CLI is
> missing or errors, fall back to the manual instructions below
> (`gh issue list` / `gh issue edit --add-label` with `--repo <owner/repo>`).

1. **Resolve kind.** If the user omitted a kind, print the kinds table above
   and **ask** which to run. Stop until they pick. Unknown kind → error and stop.

2. **Resolve config.** Read `yolo_label` and `label_flows` from
   `.issueflows/config.toml` (or use
   `issue-flow agent label-candidates --json`, which includes both). If
   `label_flows` is false, **still allow** labelling, but warn that
   `/iflow-pick` will not route on the label until `label_flows` is true and
   surfaces are re-rendered (`issue-flow update`).

3. **Ensure the label exists.** `gh label list --repo <owner/repo>` (or the
   `label_exists` field from `label-candidates`). If missing: propose
   `gh label create '<name>' --color FBCA04 --repo <owner/repo>` (or
   equivalent) under an explicit confirm; on decline, **stop**. On accept,
   create then continue.

4. **List candidates.** Load **all open issues** (include those that already
   carry the target label — re-score; adds are no-ops when already present).
   Prefer `issue-flow agent label-candidates --kind yolo --json`.

5. **Judge.** For each open issue, decide **add** / **keep** / **skip**:
   - **add** — fitness yes, label absent → propose `--add-label`.
   - **keep** — fitness yes, label already present → no write.
   - **skip** — fitness no → no write. Never auto-remove the label in v1 even
     if the issue looks unfit.
   Present a short table: `#N`, title, current labels, action, one-line reason.

6. **Consolidated confirm** (writes; normal prose, never shortened). One prompt
   covering exactly which issues get the label. Do not proceed without a clear
   yes. Empty **add** set → report and stop (no confirm needed).

7. **Apply.** `issue-flow agent label-apply <N>… --label <yolo_label>` (or
   `gh issue edit <N> --add-label <name> --repo <owner/repo>` per issue). Prefer
   `--dry-run` once when the set is large, then the real apply after confirm.

8. **Report.** Applied / failed / skipped / already-labelled (keep). Remind
   that labelled issues are picked up by `/iflow-pick` → `/iflow-yolo` when
   `label_flows` is on. If any labels were added (or already present and kept),
   hint the batch path: **to auto-process them, run `/iflow-cycle yolo`**
   (alias for `label:yolo`).

## Constraints

- **Off-path.** Never auto-dispatch from `/iflow` or other lifecycle steps.
- **Confirm before writes** — label create and label apply each need explicit
  user confirmation (may be one combined confirm when both are needed).
- **No removals / no issue create** in v1.
- Always pass `--repo <owner/repo>` to `gh`; never rely on cwd defaults.
- Degrade gracefully when `gh` is missing (report and stop; suggest
  `gh auth login`).
