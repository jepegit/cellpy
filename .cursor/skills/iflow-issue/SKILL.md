---
name: iflow-issue
description: >-
  Create and shape GitHub issues. Modes: (default) one well-specified issue,
  fix (iterative small-fixes session), epic (staged multi-issue plan, publish,
  session), split (cut an issue into sub-issues), review (label triage).
disable-model-invocation: true
issue-flow-version: 0.7.0
---

# issue-flow — issues (`/iflow-issue`)

Create or reshape GitHub issues. Every mode shows what it will create or change and asks before writing to GitHub.


**Invoke:** type `iflow issue` in chat, or `/iflow-issue` from the slash menu (`iflow-issue` also works).




### MODEL & EXECUTION DIRECTIVE


**Profile: reasoning** — Prioritize deep thinking and careful trade-offs over speed or token economy.

In Cursor: switch to a thinking-capable model before invoking this step (not Auto-only).



Keep scope tight to what this step requires.




### Resolve the project root first

Before any `git`, `gh`, or `.issueflows/` operation, settle `<project_root>` and `<owner/repo>`, stopping at the first unambiguous answer: explicit `root:<path>` / `repo:<name>` hints; `issue-flow agent resolve [--json]`; the one workspace repo on a `^\d+-` branch; the one `.issueflows/` scaffold in view; the `issueflow-workspace.toml` default (say you used it). Still ambiguous → **stop and ask**. Then use `git -C <project_root>` (or `issue-flow agent … -C <project_root>`) and pass `--repo <owner/repo>` to every `gh` call (`gh repo view` takes the repo positionally).


## Pick the mode

The first word after `issue` selects the mode. Read **only** that mode's file in this skill folder and follow it. Forward the remaining text verbatim.

| Input | Mode file | What it does |
|---|---|---|
| free text, or nothing | `new.md` | Draft and create **one** well-specified issue (context / spec / acceptance criteria), then optionally branch and capture it. |
| `fix [<N>]` | `fix.md` | Interactive iterative-fixes session: one issue + long-lived branch, many small confirmed fixes, ends with `/iflow-close`. |
| `epic <N>` / `epic <N> publish [stage <k>]` / `epic start [N]` / `epic stop` | `epic.md` | Plan a change too large for one issue as staged sub-issues; publish a stage; start or stop a one-and-ask epic session. |
| `epic <free text>` | `new.md` (epic-anchor mode) | Create the epic anchor issue first, then offer `epic <N>`. |
| `split <N>` | `split.md` | Cut one over-large existing issue into 2–5 flat GitHub sub-issues. |
| `review` | `review.md` | Review open issues and apply labels (v1: the `yolo` label). |

## Shared rules

- Never create, edit, or label a GitHub issue without an explicit yes on the exact text.
- Staged work with dependencies goes through `epic`; flat children through `split`. Other skills may *offer* these modes but never create children themselves.
- Epics decompose into the normal single-issue lifecycle; they never bypass it.
