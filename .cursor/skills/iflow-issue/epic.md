# Issue — epic planning (`/iflow-issue epic`)

Read this to plan a change that is **too large for one issue**: divide it into sequential **stages**, each stage into **manageable issues** that flow through the normal lifecycle (`/iflow-pick` → `/iflow-plan` → `/iflow-build` → `/iflow-close`).

The surface has three actions. **Drafting** (the default when the first token is a number) is write-free on GitHub: its deliverable is `.issueflows/05-epics/epic<N>_plan.md`, and it never creates GitHub issues, labels, or milestones. **`publish`** turns a *confirmed* plan into real GitHub issues, stage by stage, behind one consolidated confirm. **`start [N]` / `stop`** is a session router — it writes or clears `epic_session.md` so `/iflow` can **ask** before the next child; it never silent-picks and never becomes a fifth executor.

## Input

Parse the first token **before** the draft path:

- **`start [N]`** — session action (below). Optional `N` is the epic anchor. Never drafts or publishes.
- **`stop`** / **`abort`** — clear `.issueflows/01-current-issues/epic_session.md` and report. No confirm.
- **`<N>`** — the GitHub issue number of the **epic anchor** (an umbrella issue describing the large change). Required for draft/publish: an epic without an anchor has nowhere to track progress. If no anchor issue exists yet, stop and point the user at **`/iflow-issue epic <intent>`** (creates the anchor with an `Epic:` title and the `epic` label when present) — then re-run `/iflow-issue epic <N>` with the new number.
- **`publish [stage <k>]`** — run the publish action (below) instead of drafting. Requires `<N>` first (`/iflow-issue epic <N> publish`). Without a stage number, the earliest stage with unpublished specs is chosen.
- Optional free text — extra context, constraints, or a proposed stage split to seed the draft. Ignored by `start` / `stop`.

> **CLI fast path (optional).** If the `issue-flow` CLI is on `PATH`, run
> `issue-flow agent epic-status <N> --json` for a deterministic picture of an
> existing epic: stages, per-issue state and blockers, the current stage, and
> the next open, unblocked candidates. Use it before re-drafting a stage and
> in the publish action's stage selection. Read-only; add `--local` to skip
> the GitHub lookups.

## Instructions

1. **Gather context (read-only).** Read the epic anchor (`gh issue view <N> --repo <owner/repo>`), skim `.issueflows/04-designs-and-guides/` for relevant design docs (cite them in the plan when they shape the approach), and — when `graphify-out/GRAPH_REPORT.md` exists — skim it before grepping.

2. **Draft the staged plan** at `.issueflows/05-epics/epic<N>_plan.md` using exactly this structure (the publish step parses it):

   ```markdown
   # Epic #<N>: <title>

   Anchor: <GitHub issue URL>
   Status: draft

   ## Goal

   <what the whole epic achieves, and how we know it is done>

   ## Constraints

   <hard boundaries, non-goals, ordering requirements>

   ## Stage 1 — <stage title>

   <one paragraph: what this stage proves or delivers>
   - Goal: <one-line stage / epoch goal>

   ### Issue: <title as it will appear on GitHub>

   - Spec: <self-contained paragraph: context, scope, acceptance criteria>
   - Goal: <crisp acceptance someone else can verify>
   - Model: deep | fast | default
   - Depends on: none | #<M> | stage <j> issue <k>
   - yolo: yes | no — <one-line judgment against the yolo-fitness criteria>

   ### Issue: <next issue title>
   ...

   ## Stage 2 — <stage title>
   ...
   ```

   The `publish` action later appends a `- Published: #<M>` line to each spec it creates — never add those by hand. Older plans without `Goal:` / `Model:` markers still parse (`Model` defaults to `default`).

3. **Sizing rules for issue specs** — every issue must be *manageable*:
   - one issue = one branch = one PR, implementable in roughly a day or less;
   - a **crisp Goal** (and Spec) someone else could verify;
   - **Model:** `deep` (planning / judgment), `fast` (mechanical), or `default` (step profile) — copied into the GitHub issue body on publish;
   - dependencies stated explicitly: `#<M>` for already-published issues, `stage <j> issue <k>` placeholders for unpublished ones (the publish step resolves placeholders to real numbers);
   - a **yolo-fitness judgment** per issue: `yes` only when it is well-specified, mechanical or pattern-following, low blast radius, and guarded by existing tests — umbrella work, design decisions, and flag-day changes are `no`.

4. **Stage discipline** — stages are sequential milestones, each small enough that finishing it can change the plan for the next. Front-load the stage that retires the most risk. Do not plan more than 2–3 stages in detail; sketch later stages as bullets under a `## Later (unstaged)` heading instead of fake-precise issue specs.

5. **Review with the user.** Present the draft (stage titles, issue titles, dependency graph, yolo flags) and iterate until they confirm. Record the confirmation by changing `Status: draft` to `Status: confirmed` in the plan file.

6. **Stop.** Creating the GitHub issues is the `publish` action below, with its own consolidated confirm — never create them from the drafting flow, even if asked to "just create them": run `/iflow-issue epic <N> publish` explicitly so the confirm gates stay distinct.

## Action: start

Opt-in one-and-ask session so `/iflow` asks before the next epic child. Compose only — hand off to `/iflow-pick` (Continue), `/iflow-run cycle`, `/iflow-run auto`, `/iflow-run drive`. Never silent-pick. Never silent-publish. Never silent `worktree-add`.

1. **Resolve `N`.** Explicit number wins. Else scan `.issueflows/05-epics/epic*_plan.md` and run `issue-flow agent epic-status <E> --json` per plan.
   - **Live** = `Status: confirmed` (or already in flight) **and** work left (`next_candidates` non-empty **or** unpublished specs).
   - Exactly one live epic → **preselect it, still confirm**.
   - Several live → numbered list, wait.
   - Zero live → list draft plans (if any) **and** offer `/iflow-issue epic` to create a new anchor. Stop until they pick.
2. **Replace check.** If `.issueflows/01-current-issues/epic_session.md` exists for a **different** epic, confirm replace before writing. Same epic → refresh / continue the menu.
3. **Prepare (deterministic only).** Print `issue-flow agent epic-status <N> --json` (stage, blockers, `next_candidates`, unpublished). No GitHub writes.
4. **State-dependent offer** (one confirm writes the session and/or names the handoff — do **not** run cycle/auto/drive until that confirm):
   - Stay **one-and-ask** → write the session file (step 5) and stop. Next `/iflow` will ask.
   - This stage, yolo each issue → `/iflow-run cycle epic <N> [stage k]`.
   - Rest of epic, review between stages → `/iflow-run auto` / `/iflow-run drive`.
   - **Abort** → write nothing (or run stop if they want the file gone).
   Offer only what the prepare payload supports (no plan / draft / unpublished stage / `next_candidates` / budget ask). Do not invent a new batcher.
5. **Write session** (only after the confirm in step 4 chooses one-and-ask, or they confirmed start-then-handoff that still wants the session):

   ```text
   epic: <N>
   mode: one-and-ask
   ```

   Path: `.issueflows/01-current-issues/epic_session.md`. v1 writes **`one-and-ask` only**. This file is not an `issue<N>_*` group — sweep/doctor ignore it.
6. **Report.** Epic, mode, first `next_candidates` entry if any, and the named handoff (or “run `/iflow`”).

## Action: stop

Delete `.issueflows/01-current-issues/epic_session.md` if present and report. Tokens: `stop` / `abort`. No confirm. Missing file → say so and stop.

## Action: publish

Turn one stage of a **confirmed** plan into real GitHub issues. Requires `Status: confirmed` in `epic<N>_plan.md` — refuse drafts and point at the review step instead.

1. **Select the stage.** A named `stage <k>` publishes exactly that stage; otherwise pick the earliest stage containing specs without a `Published:` line. Specs that already carry `- Published: #<M>` are **skipped** (this makes re-runs idempotent).
2. **Dry-run listing.** Show what would be created: per spec — title, labels (`yolo` when the judgment says yes **and** the label exists per `gh label list`; otherwise note the gap), and the dependency lines after placeholder resolution. `stage <j> issue <k>` placeholders pointing at already-published specs are rewritten to their real `#<M>`; placeholders at still-unpublished specs stay verbatim with a note.
3. **Consolidated confirm** (destructive-ish — outward-facing writes; normal prose, never shortened). One prompt covering exactly: which issues get created, with which labels, and that the anchor issue's task list will be updated. Do not proceed without a clear yes.
4. **Create, in dependency order within the stage.** For each spec: `gh issue create --repo <owner/repo>` with the self-contained body (context, scope, acceptance criteria, **Goal:** and **Model:** lines when present in the plan, resolved `Depends on: #<M>` lines, and a closing `Part of epic #<N>.` line). Immediately record the new number in the plan file as `- Published: #<M>` under that spec.

**Multi-line GitHub text (PowerShell-safe).** Bash `<<'EOF'` heredocs fail in Windows PowerShell (`Missing file specification after redirection operator`). Write the text to a file and pass that file:

- `gh issue create`, `gh issue edit`, and `gh pr create` take `--body-file <path>`.
- `git commit` takes `-F <path>`.

```powershell
@'
line one

line two
'@ | Set-Content -Encoding utf8 body.md
gh issue create --repo owner/repo --title "title" --body-file body.md
```

Bash accepts the same `--body-file` / `-F` flags. Use that pattern for every multi-line body.

5. **Update the anchor issue's task list** (append/patch only — never rewrite the user's own body text): fetch the body, append a `## Stage <k> — <title>` section (or extend it) with one `- [ ] #<M>` line per created issue, and write it back via `gh issue edit <N> --body-file`.
6. **Commit `Published:` lines off default.** The plan-file edits in step 4 must not sit as unpushed commits on home default. If you are on default (or would commit there), use a chore/issue branch (or a tiny dedicated PR). Never leave `Published: #<M>` unpushed on home default — that is what later makes `git pull --ff-only` diverge after a squash.
7. **Report.** Created issues (numbers + titles + labels), skipped already-published specs, unresolved placeholders, and the reminder that the next stage publishes only after this one's issues close.

## Constraints

- **Drafting writes nothing on GitHub**: no `gh issue create`, no label or milestone writes, no task-list edits on the anchor issue. Reading with `gh issue view` / `gh issue list` is always fine. The `publish` action is the single exception and never runs without its consolidated confirm.
- **`start` never silent-picks.** Continue is today’s `/iflow-pick` chain on a later turn. Child `yolo` / `ops` labels still apply via pick.
- Epics decompose **into** the normal single-issue lifecycle, never around it — no issue spec may assume work happens outside a normal issue branch + PR.
- The plan file is user-owned working state under `.issueflows/`: `issue-flow update` never touches it.
