---
name: iflow-cycle
description: >-
  Process many issues hands-off in a row: resolve a queue, then run each
  through the yolo chain under one up-front confirm. Stops only when input is
  strictly necessary.
disable-model-invocation: true
issue-flow-version: 0.4.2a4
---

# issue-flow — issue cycle (`/iflow-cycle`)

Follow this skill to **process a queue of issues hands-off**, one after another, with a **single up-front confirmation** — the batch equivalent of `/iflow-yolo`. Each issue runs the full yolo chain (`init → plan → start → close yolo`, PR auto-merged, switch back to default); the cycle interrupts you only when input is **strictly necessary**.

Use only when every queued issue is genuinely yolo-fit (small, low-risk, well-specified, test-guarded). A queue of risky changes belongs in the individual commands.

## Input — queue spec

- **explicit numbers** — e.g. `12 15 18`.
- **`label:<L>`** — every open issue carrying label `<L>`.
- **`epic <N> [stage <k>]`** — the current stage of epic `<N>` (or stage `<k>`).
- **`resume`** — pick up an interrupted cycle from its state file (see **Resuming** below).
- **`onfail:stop`** (default) / **`onfail:skip`** — failure policy (see step 7).
- **`max:<n>`** — raise the safety cap (default 10) for this run.
- **`stay`** — forward `stay` to each close so the working copy stays on each issue branch (rarely wanted in a cycle).


**Invoke:** type `iflow cycle` in chat, or `/iflow-cycle` from the slash menu (`iflow-cycle` also works).




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

## Instructions

1. **Resolve the queue.** Run `issue-flow agent queue <spec> --json` (numbers, `--label`, or `--epic`). Use its `queue` (ordered), `blocked`, and `skipped_closed` output as the source of truth — do not re-derive the order by hand. If it reports a dependency `cycle`, **stop** and show it; nothing runs. If the CLI is unavailable, fall back to reading the issues and ordering by `Depends on #N` lines yourself, but prefer the CLI.

2. **Cap check.** If the ordered queue is longer than **10** and the input did not pass `max:<n>` raising the limit, **stop** and ask the user to confirm a larger run explicitly. Long unattended runs compound risk.

3. **One consolidated confirm** (the only planned interruption). Present, in normal prose:
   - the **ordered** queue (numbers + titles), and which issues are **skipped** (closed) or **blocked** (open dependency outside the queue) with the reason;
   - that each issue runs the **full yolo chain** and its PR is **auto-merged**;
   - the failure policy (`onfail:stop`, the default, or `onfail:skip` — see step 7);
   - the default-branch preflight that must hold before starting (clean tree, tests passing).
   Require an explicit yes; anything else aborts before any work.

4. **Write the cycle state file.** After the confirm, write `.issueflows/01-current-issues/cycle_status.md` — the durable record that makes the run resumable and visible to `/iflow-status`. Include: the queue spec, the `onfail` policy, an ISO timestamp, and the ordered queue as a checklist with one line per issue (`- [ ] #<N> — <title> — pending`). Update this file as the loop progresses (see step 5); it is a normal tracking file (not an `issue<N>_*` group), so the folder sweep never touches it.

5. **Per-issue loop.** For each issue in order, from a clean default branch:
   - mark it `in-progress` in `cycle_status.md`, then create/switch to its `<N>-<slug>` branch and follow `.cursor/skills/iflow-yolo/SKILL.md` **verbatim** — including its own preflight (refuse on default branch, refuse with dirty unrelated changes, tests pass up front) and its consolidated-confirm step, which the up-front batch confirm in step 3 satisfies (do not re-ask per issue).
   - after the yolo close merges and switches back to the default branch, record the outcome in `cycle_status.md` (`- [x] #<N> — <title> — merged <PR-url>`) and continue to the next issue.
   - Every yolo safeguard stays in force. A safeguard that trips is a **stop condition** (step 6), never a guard to skip.

6. **Strictly-necessary-input rule.** Between issues the cycle runs unattended. **Stop and ask only** when:
   a. tests or lint fail in a way you cannot fix within the current issue's scope;
   b. a merge is refused or a `git pull --ff-only` will not fast-forward (divergence);
   c. the issue spec is ambiguous, contradictory, or turns out **not** small (yolo's scope check aborts);
   d. an action would fall **outside the confirmed queue** (touching an unlisted issue, an unrelated dirty file, a destructive op).
   Anything else — routine implementation choices, passing tests, clean merges — proceeds without asking.

7. **Failure policy** (from the `onfail:` token; default **stop**). When a stop condition (step 6) trips on an issue:
   - **`onfail:stop`** (default) — **halt the cycle**: finish no further issues, leave the repo on the **default branch, clean** (the in-flight issue's branch stays as-is for the user to inspect), record the stop reason and the not-reached issues in `cycle_status.md`, and report. Do not attempt the rest of the queue.
   - **`onfail:skip`** — **park and continue**: record the failure against that issue in `cycle_status.md` (`- [~] #<N> — <title> — failed: <reason>`), park its work per `.cursor/skills/iflow-pause/SKILL.md` conventions (status note + move to `02-partly-solved-issues/`), return to a clean default branch, and proceed to the next queued issue. A skip never bypasses a yolo safeguard — it records the trip and moves on.

8. **Finish.** When the queue is exhausted (or halted), finalize `cycle_status.md` (mark it `- [x] Done`) and move it to `.issueflows/03-solved-issues/cycle_status_<YYYY-MM-DD>.md` so it is archived, not re-detected as in-flight.

9. **Batch report.** Summarize the whole run: per issue — number, title, PR URL, merge result (merged / queued via `--auto` / failed-and-skipped / not reached), and duration if tracked; then the queue items **skipped** (closed), **blocked** (with blockers), and — on a halt — the **stop reason** and which issues were **not reached**. End by reminding the user to run `/iflow-cleanup` once to prune the merged local branches.

## Resuming

`/iflow-cycle resume` picks up an interrupted cycle:

1. Read `.issueflows/01-current-issues/cycle_status.md`. If it is missing, tell the user there is no in-flight cycle and stop.
2. Take the **remaining** issues (those still `pending` / `in-progress`) and **re-verify** them with `issue-flow agent queue <original-spec> --json` — an issue that has since closed, or become blocked, is dropped/deferred with a note (state can move while a cycle is paused).
3. **Do not re-ask the original consolidated confirm** for the unchanged remaining items — the batch was already authorized. Ask again only if the re-verified queue differs materially from what was confirmed (new blockers, added issues), and only about the delta.
4. Continue the per-issue loop (step 5) with the same `onfail` policy recorded in the file.

## Parallel dispatch (experimental, opt-in)

By default the cycle is **sequential** — one issue fully lands before the next starts. When the input passes **`parallel:<n>`** *and* the harness supports background execution, provably independent issues may run concurrently (up to `n` at a time). This is experimental; the sequential path above is always the default and is never weakened to enable it.

- **Only independent issues qualify.** Use `issue-flow agent queue`'s **`independent`** list — issues with *no* dependency relation (either direction) to any other queue member. Everything else runs sequentially.
- **Harness gate.** If you cannot confirm the harness supports background execution (worktrees + parallel agents/subagents), **refuse `parallel:<n>` and run sequentially** — never pretend to parallelize.
- **Worktree per issue.** `git worktree add ../<repo>-<N> <N>-<slug>` so each issue has an isolated tree; run the yolo work there.
- **Serialize merges.** Never merge PRs concurrently — the coordinating session merges them one at a time on the default branch, pulling between merges and rebasing/retrying on a non-fast-forward or CI refusal.
- **Shared files via the coordinator only.** Parallel workers must **not** each edit `HISTORY.md`; each leaves its changelog bullet in its issue status file / PR body, and the coordinator appends them in **merge order** during the serial merge step.

When in doubt, prefer the sequential run — parallel dispatch trades safety for speed and every one of the rules above must hold.

## Constraints

- **Off-path**: `/iflow` never auto-dispatches to `/iflow-cycle`; it is an explicit, deliberate batch action.
- **Sequential is the default and floor.** Parallelism (`parallel:<n>`) is opt-in and experimental; refusing it must always leave a working sequential run.
- Never weaken a yolo safeguard to keep the cycle moving — safeguards are stop conditions, not obstacles.
- Never run `/iflow-cleanup` from this skill; batch branch deletion still needs the user to see the merged PRs first.
- One consolidated confirm covers the batch; never silently expand the queue beyond what was confirmed.
- `cycle_status.md` is the single source of truth for an in-flight cycle: keep it current so `resume` and `/iflow-status` stay accurate. It is not an `issue<N>_*` group, so the folder sweep leaves it alone; archive it (step 8) when the run ends.
