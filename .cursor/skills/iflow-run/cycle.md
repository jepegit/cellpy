# Run — cycle (`/iflow-run cycle`)

Read this to **process a queue of issues hands-off**, one after another, with a **single up-front confirmation** — the batch equivalent of `/iflow-run yolo`. Each issue runs the full yolo chain (`capture → plan → build → close yolo`, PR auto-merged, switch back to default); the cycle interrupts you only when input is **strictly necessary**.

Best when every queued issue is yolo-fit (small, low-risk, well-specified, test-guarded). Issues the queue marks `yolo: false` (an epic plan's `yolo: no` judgment, or no yolo label) still run — on the **non-yolo lane** below — but a queue of genuinely risky changes belongs in the individual commands.

## Lanes — yolo vs non-yolo

`issue-flow agent queue --json` tags every queued item with `yolo: true|false` and lists the non-yolo ones under `nonyolo` / `nonyolo_count`. The lane decides only **how the PR lands**; the chain itself (`capture → plan → build → close`) and every safeguard are identical.

| Lane | Runs when | Chain | Merge |
|------|-----------|-------|-------|
| **yolo** | `yolo: true` | `iflow-run yolo` verbatim (auto-plan, auto-build, `close yolo`) | auto-merged (`gh pr merge --squash`), back to default |
| **non-yolo** | `yolo: false` | same chain, same safeguards; plan/build write the normal `issue<N>_*` files | per **`nonyolo:` policy** (default **`merge`**) |

Non-yolo merge policy:

- **`merge`** — land the PR exactly like the yolo lane. The up-front batch confirm already covers it; a `yolo: no` judgment means “needs a plan on record”, which the lane produces, not “needs a human at merge time”.
- **`pr-only`** — open the PR (normal `/iflow-close`, no merge), record `- [~] #<N> — <title> — PR open <url> (pr-only)` in `cycle_status.md`, and **continue**. The next queued issue branches from the **default branch**, not the open PR; if it depends on the open one (`Depends on #N`), branch from that PR's head instead and note `stacked on #N` in `cycle_status.md` so close can pass `issue-flow agent sync-branch --base <parent>` when the parent squash-lands first.
- **`stop`** — halt at the first `yolo: false` issue before starting it (the pre-`nonyolo` behaviour). Record `stopped: non-yolo lane disabled` and the not-reached issues; leave the repo clean on default.

The lane never changes a **stop condition** (step 6): tests failing, a scope check aborting, or an action outside the confirmed queue stops the cycle on either lane.

## Input — queue spec

- **explicit numbers** — e.g. `12 15 18`.
- **`yolo`** — alias for **`label:yolo`**: every open issue carrying the configured yolo trigger label (default `"yolo"`). Case-insensitive. This is the one-token path for “auto-process all yolo issues.”
- **`label:<L>`** — every open issue carrying label `<L>` (use for labels other than the yolo trigger).
- **`epic <N> [stage <k>]`** — the current stage of epic `<N>` (or stage `<k>`).
- **`resume`** — pick up an interrupted cycle from its state file (see **Resuming** below).
- **`onfail:stop`** / **`onfail:skip`** — failure policy (see step 7). Default from config **`stop`** (`cycle_onfail` under `[issueflow]`); an explicit token wins for this run.
- **`nonyolo:merge`** / **`nonyolo:pr-only`** / **`nonyolo:stop`** — merge policy for `yolo: no` issues in the queue (see **Lanes** below). Default from config **`merge`** (`cycle_nonyolo` under `[issueflow]`); an explicit token wins for this run.
- **`max:<n>`** — raise the safety cap (default 10) for this run.
- **`stay`** — forward `stay` to each close so the working copy stays on each issue branch (rarely wanted in a cycle).

## Instructions

0. **Expand aliases.** If the queue spec is exactly `yolo` (case-insensitive), treat it as `label:yolo` (the baked config value; if `.issueflows/config.toml` has a different `yolo_label` than this skill's bake, prefer the live config). Keep the original token in `cycle_status.md` for humans (`queue: yolo` → resolved `label:yolo`).

1. **Resolve the queue.** Run `issue-flow agent queue --label yolo --json` when the alias applied, else `issue-flow agent queue <spec> --json` (numbers, `--label`, or `--epic`). Use its `queue` (ordered), `blocked`, and `skipped_closed` output as the source of truth — do not re-derive the order by hand. If it reports a dependency `cycle`, **stop** and show it; nothing runs. If the CLI is unavailable, fall back to reading the issues and ordering by `Depends on #N` lines yourself, but prefer the CLI. An empty queue → report “nothing to queue” and stop (no confirm needed).

2. **Cap check.** If the ordered queue is longer than **10** and the input did not pass `max:<n>` raising the limit, **stop** and ask the user to confirm a larger run explicitly. Long unattended runs compound risk.

3. **One consolidated confirm** (the only planned interruption). Present, in normal prose:
   - the **ordered** queue (numbers + titles), and which issues are **skipped** (closed) or **blocked** (open dependency outside the queue) with the reason;
   - that each issue runs the **full chain** and — on the yolo lane — its PR is **auto-merged**;
   - the **non-yolo lane**: list the `nonyolo` issues from the queue payload (numbers + titles, or “none”) and the policy that applies to them (`nonyolo:merge|pr-only|stop`; default **`merge`** unless a token overrides). With `merge`, say explicitly that these PRs are auto-merged too;
   - the failure policy (`onfail:stop` or `onfail:skip`; default from config is **`stop`** unless overridden by a token — see step 7);
   - the default-branch preflight that must hold before starting (clean tree, tests passing).
   Require an explicit yes; anything else aborts before any work.


4. **Write the cycle state file.** After the confirm, write `.issueflows/01-current-issues/cycle_status.md` — the durable record that makes the run resumable and visible to `/iflow-status`. Include: the queue spec, the `onfail` policy, the `nonyolo` policy, an ISO timestamp, and the ordered queue as a checklist with one line per issue (`- [ ] #<N> — <title> — pending` — append ` (non-yolo)` for `yolo: false` items). Update this file as the loop progresses (see step 5); it is a normal tracking file (not an `issue<N>_*` group), so the folder sweep never touches it.

5. **Per-issue loop.** For each issue in order, from a clean default branch:
   - mark it `in-progress` in `cycle_status.md`, then create/switch to its `<N>-<slug>` branch.
   - **yolo lane** (`yolo: true`): follow `.cursor/skills/iflow-run/yolo.md` **verbatim** — including its own preflight (refuse on default branch, refuse with dirty unrelated changes, tests pass up front) and its consolidated-confirm step, which the up-front batch confirm in step 3 satisfies (do not re-ask per issue).
   - **non-yolo lane** (`yolo: false`): apply the `nonyolo` policy. `stop` → step 7 with reason `non-yolo lane disabled`, before any work on the issue. Otherwise run the same chain as yolo (`capture → plan → build`, the batch confirm standing in for the plan's confirm) and then `close yolo` (policy `merge`) or plain `close` (policy `pr-only`). Same preflight, same scope check, same test gate — the lane changes nothing about safeguards.
   - after close merges (or, for `pr-only`, opens the PR) and the working copy is back on the default branch, record the outcome in `cycle_status.md` (`- [x] #<N> — <title> — merged <PR-url>` / `- [~] … — PR open <url> (pr-only)`) and continue to the next issue.
   - A merge attempt that reports the PR is **already merged** (someone landed it while checks ran) is a **success**: pull the default branch and record `merged` normally.
   - Every yolo safeguard stays in force. A safeguard that trips is a **stop condition** (step 6), never a guard to skip.

6. **Strictly-necessary-input rule.** Between issues the cycle runs unattended. **Stop and ask only** when:
   a. tests or lint fail in a way you cannot fix within the current issue's scope;
   b. a merge is refused, or a sync with the default branch will not complete — **but** a refusal whose only conflicts are **bookkeeping** is **not** a stop: additive `HISTORY.md` bullets, additive bullets / table rows in `.issueflows/04-designs-and-guides/*.md`, or an `issue<N>_status.md` file. Close's sync step (`issue-flow agent sync-branch`) resolves those keep-both and retries the merge once; when the branch is stacked on a squash-landed parent the sync auto-detects it (`base_detected`) and replays only the child's commits. Stop only when the sync itself exits 1 (a product-code conflict, or a heading/prose conflict the resolver refuses), or the retry is refused again;
   c. the issue spec is ambiguous, contradictory, or turns out **not** small (the scope check aborts). On the **non-yolo lane** the “not small” half is advisory: `yolo: no` already said the issue is not small, so the size itself is not a stop — ambiguity or contradiction still is;
   d. an action would fall **outside the confirmed queue** (touching an unlisted issue, an unrelated dirty file, a destructive op).
   Anything else — routine implementation choices, passing tests, clean merges — proceeds without asking.

7. **Failure policy** (from the `onfail:` token when present; otherwise config **`stop`**). When a stop condition (step 6) trips on an issue:
   - **`onfail:stop`** — **halt the cycle**: finish no further issues, leave the repo on the **default branch, clean** (the in-flight issue's branch stays as-is for the user to inspect), record the stop reason and the not-reached issues in `cycle_status.md`, and report. Do not attempt the rest of the queue.
   - **`onfail:skip`** — **park and continue**: record the failure against that issue in `cycle_status.md` (`- [~] #<N> — <title> — failed: <reason>`), park its work per `.cursor/skills/iflow-pause/SKILL.md` conventions (status note + move to `02-partly-solved-issues/`), return to a clean default branch, and proceed to the next queued issue. A skip never bypasses a yolo safeguard — it records the trip and moves on.

8. **Finish.** When the queue is exhausted (or halted), finalize `cycle_status.md` (mark it `- [x] Done`) and move it to `.issueflows/03-solved-issues/cycle_status_<YYYY-MM-DD>.md` so it is archived, not re-detected as in-flight.

9. **Batch report.** Summarize the whole run: per issue — number, title, PR URL, merge result (merged / queued via `--auto` / failed-and-skipped / not reached), and duration if tracked; then the queue items **skipped** (closed), **blocked** (with blockers), and — on a halt — the **stop reason** and which issues were **not reached**.

## Resuming

`/iflow-run cycle resume` picks up an interrupted cycle:

1. Read `.issueflows/01-current-issues/cycle_status.md`. If it is missing, tell the user there is no in-flight cycle and stop.
2. Take the **remaining** issues (those still `pending` / `in-progress`) and **re-verify** them with `issue-flow agent queue <original-spec> --json` — an issue that has since closed, or become blocked, is dropped/deferred with a note (state can move while a cycle is paused).
3. **Do not re-ask the original consolidated confirm** for the unchanged remaining items — the batch was already authorized. Ask again only if the re-verified queue differs materially from what was confirmed (new blockers, added issues), and only about the delta.
4. Continue the per-issue loop (step 5) with the same `onfail` and `nonyolo` policies recorded in the file.

## Parallel dispatch (experimental, opt-in)

By default the cycle is **sequential** — one issue fully lands before the next starts. When the input passes **`parallel:<n>`** *and* the harness supports background execution, provably independent issues may run concurrently (up to `n` at a time). This is experimental; the sequential path above is always the default and is never weakened to enable it.

- **Only independent issues qualify.** Use `issue-flow agent queue`'s **`independent`** list — issues with *no* dependency relation (either direction) to any other queue member. Everything else runs sequentially.
- **Harness gate.** If you cannot confirm the harness supports background execution (worktrees + parallel agents/subagents), **refuse `parallel:<n>` and run sequentially** — never pretend to parallelize.
- **Worktree per issue.** `issue-flow agent worktree-add <N> --slug <slug> --json` so each issue has an isolated tree (its `path` honours `worktrees_dir`; default `../<repo>-<N>`); run the yolo work there.
- **Print the worktree path.** After each `worktree add`, run `issue-flow agent open-workspace <worktree-path> --json` (print-only) and show the path. Do not launch a window. Continue with worktree-only parallel.
- **Serialize merges.** Never merge PRs concurrently — the coordinating session merges them one at a time on the default branch, pulling between merges and rebasing/retrying on a non-fast-forward or CI refusal.
- **Shared files via the coordinator only.** Parallel workers must **not** each edit `HISTORY.md`. Each close puts its bullet in commit-message trailers (`Changelog` / `Changelog-Date` / `Changelog-Id`); the coordinator does not append changelog bullets at merge time. `issue-flow changelog release` on the default branch collects them. If a worker PR does go `DIRTY` on a leftover `[Unreleased]` section, the coordinator resolves it with `issue-flow agent sync-branch` rather than hand-editing markers.

When in doubt, prefer the sequential run — parallel dispatch trades safety for speed and every one of the rules above must hold.

## All yolo issues + merge conflicts

`/iflow-run cycle yolo` (or `label:yolo`) is the supported way to
**auto-process every open yolo-labelled issue**. No separate batch skill.

**Conflict stance (sequential default):** each issue's yolo close merges its PR
and returns to a **clean default branch** before the next issue starts, so
within the cycle shared files (`HISTORY.md`, etc.) stay single-writer.
Stop-on-fail leaves the tree clean on default.

That single-writer property does **not** protect against the default branch
moving **externally** — another session or an already-open PR merging while one
queued issue is in its test/CI window. The collision is almost always the same:
two additive bullets under `## [Unreleased]`. Close's sync step owns that
(`issue-flow agent sync-branch`: rebase onto `origin/<default>`, keep both
bullet sets with the in-flight one last, force-with-lease push, retry the merge
once), so a changelog-only conflict no longer halts a batch. The same resolver
covers additive bullets / table rows in `04-designs-and-guides/*.md` and
`issue<N>_status.md`, and a child branch stacked on a squash-landed parent
(`sync-branch --base <parent>`, auto-detected when the parent is provably
landed). Everything else still trips step 6b. For experimental concurrent work, see
**Parallel dispatch** above (merges stay serialized there too). Labelling first is optional via
`/iflow-issue review yolo` — then run `/iflow-run cycle yolo`.

## Constraints

- **Sequential is the default and floor.** Parallelism (`parallel:<n>`) is opt-in and experimental; refusing it must always leave a working sequential run.
- Never weaken a yolo safeguard to keep the cycle moving — safeguards are stop conditions, not obstacles. The non-yolo lane changes *how a PR lands*, never which safeguards run.
- A `yolo: false` issue is **not** a stop condition by itself unless the policy is `nonyolo:stop`; list the non-yolo issues in the confirm so the operator sees the lane before the run starts.
- Never run `/iflow-cleanup` from this skill; batch branch deletion still needs the user to see the merged PRs first.

- One consolidated confirm covers the batch; never silently expand the queue beyond what was confirmed.
- `cycle_status.md` is the single source of truth for an in-flight cycle: keep it current so `resume` and `/iflow-status` stay accurate. It is not an `issue<N>_*` group, so the folder sweep leaves it alone; archive it (step 8) when the run ends.
