---
name: iflow-run
description: >-
  Run issues hands-off under one up-front confirm. Modes: yolo <N> (one small
  issue), cycle <queue> (many issues), auto <epic> (an epic stage by stage
  with review), drive <N> (compose an epic from an issue and run all of it).
disable-model-invocation: true
issue-flow-version: 0.7.0
---

# issue-flow — run hands-off (`/iflow-run`)

Run the normal lifecycle (pick → plan → build → close) without per-step checkpoints. Every mode asks **once** up front, then stops only when input is strictly necessary. No mode weakens a safeguard to keep moving.


**Invoke:** type `iflow run` in chat, or `/iflow-run` from the slash menu (`iflow-run` also works).




### MODEL & EXECUTION DIRECTIVE


**Profile: reasoning** — Prioritize deep thinking and careful trade-offs over speed or token economy.

In Cursor: switch to a thinking-capable model before invoking this step (not Auto-only).



Keep scope tight to what this step requires.




### Resolve the project root first

Before any `git`, `gh`, or `.issueflows/` operation, settle `<project_root>` and `<owner/repo>`, stopping at the first unambiguous answer: explicit `root:<path>` / `repo:<name>` hints; `issue-flow agent resolve [--json]`; the one workspace repo on a `^\d+-` branch; the one `.issueflows/` scaffold in view; the `issueflow-workspace.toml` default (say you used it). Still ambiguous → **stop and ask**. Then use `git -C <project_root>` (or `issue-flow agent … -C <project_root>`) and pass `--repo <owner/repo>` to every `gh` call (`gh repo view` takes the repo positionally).


## Pick the mode

The first word after `run` selects the mode. Read **only** that mode's file in this skill folder and follow it. Forward the remaining text verbatim.

| Input | Mode file | Scope |
|---|---|---|
| `yolo [<N>]` or a single issue number | `yolo.md` | One small, low-risk issue: capture → plan → build → `close yolo` (PR merged). |
| `cycle <spec>`, or several numbers / `label:<L>` / `yolo` / `epic <N> [stage <k>]` | `cycle.md` | A queue of issues, each through the yolo chain. |
| `auto <N>` | `auto.md` | Confirmed epic `<N>`: run each stage as a cycle, review between stages. |
| `drive <N>` | `drive.md` | Issue `<N>` → draft epic → publish → auto every stage → final review. |

With no input, ask which mode (and which issue or queue) the user means. Do not guess.

## Shared rules

- Never run on a dirty tree with unrelated changes, and never start on a failing test baseline.
- Never run `/iflow-cleanup` from here. Branch deletion waits for the user (except the narrowed `drive` cleanup described in `drive.md`).
- Stop on the first condition that needs a human: unfixable failure, refused merge, non-fast-forward pull, an ambiguous or not-actually-small spec, or anything outside the confirmed scope.
- Leave the repo clean on the default branch when stopping.
