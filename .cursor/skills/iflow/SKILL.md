---
name: iflow
description: >-
  Smart dispatcher: detect where the focus issue stands and dispatch to
  /iflow-pick <N> (capture), /iflow-plan, /iflow-build, or /iflow-close.
disable-model-invocation: true
issue-flow-version: 0.7.0
---

# issue-flow — iflow smart dispatcher (`/iflow`)

Run **the right next step**: detect state and route to `/iflow-pick <N>` (capture), `/iflow-plan`, `/iflow-build`, or `/iflow-close`, forwarding trailing args verbatim. Every other command is explicit-only; `/iflow` never dispatches to it.


**Invoke:** type `iflow` in chat, or `/iflow` from the slash menu.




### MODEL & EXECUTION DIRECTIVE


**Profile: economy** — Prioritize speed and token economy over deep reasoning.

In Cursor: use **Auto** or a fast model before invoking this step.



Keep scope tight to what this step requires.




### Resolve the project root first

Before any `git`, `gh`, or `.issueflows/` operation, settle `<project_root>` and `<owner/repo>`, stopping at the first unambiguous answer: explicit `root:<path>` / `repo:<name>` hints; `issue-flow agent resolve [--json]`; the one workspace repo on a `^\d+-` branch; the one `.issueflows/` scaffold in view; the `issueflow-workspace.toml` default (say you used it). Still ambiguous → **stop and ask**. Then use `git -C <project_root>` (or `issue-flow agent … -C <project_root>`) and pass `--repo <owner/repo>` to every `gh` call (`gh repo view` takes the repo positionally).

## Instructions

> **CLI fast path (optional).** If the `issue-flow` CLI is on `PATH`, run
> `issue-flow agent state --json` to resolve the focus issue, its lifecycle
> stage, the suggested `next_command`, and (when there is no focus)
> `epic_hint` / `epic_session` in one deterministic step (covers instructions 1–2), then
> dispatch — or stop for the epic gap. The CLI is optional: if it is not
> installed or it errors, fall back to the manual instructions below.
> (`issue-flow` is only present when the user installed it, e.g.
> `uv tool install issue-flow`.)

1. **Resolve the focus issue number `N`.**
   - Prefer `issue-flow agent state --json` when the CLI is on `PATH` (fields `focus`, `next_command`, `epic_hint`, `epic_session`, `cli_version`, `skills_version`, `version_drift`).
   - **Version drift.** If the payload reports `version_drift: true`, print one warning line before anything else — `skills stamped <skills_version>, CLI <cli_version> — run `issue-flow update`` — and keep going with the dispatch. Stale skill text is how a newer CLI ends up driven by old instructions; the warning is the fix, not a stop. Never run `issue-flow update` yourself from here.
   - Manual fallback: `git branch --show-current`. If it matches `^(\d+)-.+`, the leading digits are the **authoritative** `N`.
   - List `issue<n>_*` groups in `.issueflows/01-current-issues/`, and also check `.issueflows/02-partly-solved-issues/` and `.issueflows/03-solved-issues/` for archived groups matching `N`.
   - Pick `N` by precedence:
     1. **Branch-derived `N` wins**, regardless of whether a group for `N` exists in `01-current-issues/`. State **A** will apply when no `issue<N>_*` files are present yet. If `issue<N>_*` is archived under `02-partly-solved-issues/` or `03-solved-issues/`, warn the user that capture's archived-issue guard will ask for an explicit confirmation before re-opening.
     2. No branch-derived `N`, exactly one group exists in `01-current-issues/` → use it.
     3. No branch-derived `N`, no groups at all → **epic gap check** (step 1a), else state **A**.
     4. No branch-derived `N`, multiple groups → **stop and ask**.

1a. **Epic gap (no focus)** — when step 1 finds no focus (`focus` is null / empty `01-current-issues/` and no `^\d+-.+` branch):
   - Prefer `epic_hint` and `epic_session` from `issue-flow agent state --json` (lists epics with non-empty `next_candidates`). Fallback: scan `.issueflows/05-epics/epic*_plan.md` and run `issue-flow agent epic-status <N> --json` per plan. Read `.issueflows/01-current-issues/epic_session.md` if state omitted it (`epic:` / `mode: one-and-ask`; unknown mode → treat as missing).
   - If the user's trailing text is already an explicit issue number `N`, then dispatch `/iflow-pick <N>` (capture) instead of stopping.
   - **Session present** + that epic has `next_candidates`: **stop**. Ask: next `#<M>` (`<M>` = first `next_candidates` entry for the session epic) — **continue** / switch to cycle|auto|drive / **stop**. This turn writes nothing and creates no branch. Continue on a **later turn** follows `/iflow-pick` for `#<M>` (user said continue / `yes` / the number). Never silent-pick. `stop`/`abort` → `/iflow-issue epic stop`. cycle|auto|drive → name the handoff; do not run it until that confirm.
   - Else if **any** `next_candidates` (no session): **stop**. Print epic + stage + candidate numbers/titles. Recommend **`/iflow-pick`**. Do **not** dispatch yet, even when there is only one candidate (never pick silently).
   - If **no** epic candidates → continue to state **A** (`/iflow-pick`, which asks for a number).

2. **Detect state and choose the dispatch target** (first match wins):

   - **A** — no `issue<N>_original.md` (or no focus issue, after the epic gap check) → dispatch to **`/iflow-pick <N>`** (capture only; with no `N` it asks). Reason: "no `*_original.md` yet".
   - **B** — original exists, no `issue<N>_plan.md` → dispatch to **`/iflow-plan`**. Reason: "no plan file yet".
   - **C** — plan exists, and status file is missing or its `- [x] Done` is unchecked → dispatch to **`/iflow-build`**. Reason: "plan is confirmed but status is not `- [x] Done`".
   - **D** — status file contains `- [x] Done` (case-insensitive on `done`) → dispatch to **`/iflow-close`**. Reason: "status marks the issue `- [x] Done`".


3. **Announce and dispatch.** Print one line like `/iflow -> /iflow-plan  (issue #N: no plan file yet)` and then follow the chosen command's playbook. Forward the user's trailing text verbatim.

4. **Respect downstream checkpoints.** Never suppress the downstream command's own prompts (plan confirmation, unrelated-changes prompt, etc.). `/iflow` adds no new confirmation layer of its own.

5. **Report.** Summarize: focus issue `N` and how it was resolved, which command was dispatched and why, the downstream output, and a one-line hint when an off-path command is the natural next step:
   - mid-stream context switch needed → "to park this work, run `/iflow-pause`"
   - tiny fix that would benefit from a single-shot chain → "consider `/iflow-run yolo` next time"
   - state **D** / between issues, and an active epic still has `next_candidates` → session present: "epic #<E> stage still has #<…> — run `/iflow`"; else "run `/iflow-pick` when ready"
   - `graphify-out/GRAPH_REPORT.md` looks stale (large refactor, new modules) → "consider `/iflow-status graph` to refresh the graph"


## Constraints

- Never auto-dispatch to any command other than the four above (pick-to-capture, plan, build, close).
- Epic gap (step 1a) without a session only **suggests** `/iflow-pick`; it never runs pick or silently picks a candidate. With a session it **asks** (one-and-ask) before the pick chain; it never silent-picks.
- If the focus issue cannot be resolved (multiple groups, branch ambiguous), stop and ask.
- Do not modify files beyond what the downstream command would normally modify. `/iflow` itself writes nothing — all file changes come from the dispatched command.
- Dispatch to at most one command per `/iflow` invocation.
