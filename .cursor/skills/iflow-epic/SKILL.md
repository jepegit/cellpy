---
name: iflow-epic
description: >-
  Plan a larger change as a staged epic: draft epic<N>_plan.md with stages of
  manageable issue specs, then publish confirmed stages as GitHub issues.
disable-model-invocation: true
issue-flow-version: 0.4.2a4
---

# issue-flow — epic planning (`/iflow-epic`)

Follow this skill to plan a change that is **too large for one issue**: divide it into sequential **stages**, each stage into **manageable issues** that flow through the normal lifecycle (`/iflow-init` → `/iflow-plan` → `/iflow-start` → `/iflow-close`).

The surface has two actions. **Drafting** (the default) is write-free on GitHub: its deliverable is `.issueflows/05-epics/epic<N>_plan.md`, and it never creates GitHub issues, labels, or milestones. **`publish`** is the single exception — it turns a *confirmed* plan into real GitHub issues, stage by stage, behind one consolidated confirm.

## Input

- **`<N>`** — the GitHub issue number of the **epic anchor** (an umbrella issue describing the large change). Required: an epic without an anchor has nowhere to track progress. If no anchor issue exists yet, stop and ask the user to create one (title prefixed `Epic:`, label `epic` when available) — creating it is the user's call, not this skill's.
- **`publish [stage <k>]`** — run the publish action (below) instead of drafting. Without a stage number, the earliest stage with unpublished specs is chosen.
- Optional free text — extra context, constraints, or a proposed stage split to seed the draft.


**Invoke:** type `iflow epic` in chat, or `/iflow-epic` from the slash menu (`iflow-epic` also works).




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

   ### Issue: <title as it will appear on GitHub>

   - Spec: <self-contained paragraph: context, scope, acceptance criteria>
   - Depends on: none | #<M> | stage <j> issue <k>
   - yolo: yes | no — <one-line judgment against the yolo-fitness criteria>

   ### Issue: <next issue title>
   ...

   ## Stage 2 — <stage title>
   ...
   ```

   The `publish` action later appends a `- Published: #<M>` line to each spec it creates — never add those by hand.

3. **Sizing rules for issue specs** — every issue must be *manageable*:
   - one issue = one branch = one PR, implementable in roughly a day or less;
   - a **crisp acceptance criterion** someone else could verify;
   - dependencies stated explicitly: `#<M>` for already-published issues, `stage <j> issue <k>` placeholders for unpublished ones (the publish step resolves placeholders to real numbers);
   - a **yolo-fitness judgment** per issue: `yes` only when it is well-specified, mechanical or pattern-following, low blast radius, and guarded by existing tests — umbrella work, design decisions, and flag-day changes are `no`.

4. **Stage discipline** — stages are sequential milestones, each small enough that finishing it can change the plan for the next. Front-load the stage that retires the most risk. Do not plan more than 2–3 stages in detail; sketch later stages as bullets under a `## Later (unstaged)` heading instead of fake-precise issue specs.

5. **Review with the user.** Present the draft (stage titles, issue titles, dependency graph, yolo flags) and iterate until they confirm. Record the confirmation by changing `Status: draft` to `Status: confirmed` in the plan file.

6. **Stop.** Creating the GitHub issues is the `publish` action below, with its own consolidated confirm — never create them from the drafting flow, even if asked to "just create them": run `/iflow-epic <N> publish` explicitly so the confirm gates stay distinct.

## Action: publish

Turn one stage of a **confirmed** plan into real GitHub issues. Requires `Status: confirmed` in `epic<N>_plan.md` — refuse drafts and point at the review step instead.

1. **Select the stage.** A named `stage <k>` publishes exactly that stage; otherwise pick the earliest stage containing specs without a `Published:` line. Specs that already carry `- Published: #<M>` are **skipped** (this makes re-runs idempotent).
2. **Dry-run listing.** Show what would be created: per spec — title, labels (`yolo` when the judgment says yes **and** the label exists per `gh label list`; otherwise note the gap), and the dependency lines after placeholder resolution. `stage <j> issue <k>` placeholders pointing at already-published specs are rewritten to their real `#<M>`; placeholders at still-unpublished specs stay verbatim with a note.
3. **Consolidated confirm** (destructive-ish — outward-facing writes; normal prose, never shortened). One prompt covering exactly: which issues get created, with which labels, and that the anchor issue's task list will be updated. Do not proceed without a clear yes.
4. **Create, in dependency order within the stage.** For each spec: `gh issue create --repo <owner/repo>` with the self-contained body (context, scope, acceptance criteria, resolved `Depends on: #<M>` lines, and a closing `Part of epic #<N>.` line). Immediately record the new number in the plan file as `- Published: #<M>` under that spec.
5. **Update the anchor issue's task list** (append/patch only — never rewrite the user's own body text): fetch the body, append a `## Stage <k> — <title>` section (or extend it) with one `- [ ] #<M>` line per created issue, and write it back via `gh issue edit <N> --body-file`.
6. **Report.** Created issues (numbers + titles + labels), skipped already-published specs, unresolved placeholders, and the reminder that the next stage publishes only after this one's issues close.

## Constraints

- **Drafting writes nothing on GitHub**: no `gh issue create`, no label or milestone writes, no task-list edits on the anchor issue. Reading with `gh issue view` / `gh issue list` is always fine. The `publish` action is the single exception and never runs without its consolidated confirm.
- **Off-path**: `/iflow` never auto-dispatches to `/iflow-epic`; the user opts in explicitly.
- Epics decompose **into** the normal single-issue lifecycle, never around it — no issue spec may assume work happens outside a normal issue branch + PR.
- The plan file is user-owned working state under `.issueflows/`: `issue-flow update` never touches it.
