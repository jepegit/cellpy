# Issue — review and label issues (`/iflow-issue review`)

Read this to **review open GitHub issues and apply labels**. It is
extendable by review *kind*; v1 supports **`yolo`** only (apply the configured
`yolo` label to issues that pass the yolo-fitness judgment).

## Input

- **(nothing)** — list supported review kinds and ask which to run.
- **`yolo`** — examine open issues; propose adding the configured
  `yolo_label` (default `"yolo"`) where fitness says yes.

Trailing text after the kind is reserved for future filters; ignore unknown
tokens with a warning rather than inventing behaviour.

## Review kinds (extendable)

| Kind | Label applied | Fitness criteria |
|------|---------------|------------------|
| `yolo` | resolved `[issueflow].yolo_label` (default `"yolo"`) | Same as `/iflow-issue epic`: well-specified, mechanical or pattern-following, low blast radius, guarded by existing tests — umbrella work, design decisions, and flag-day changes are **no**. |

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
   that labelled issues are picked up by `/iflow-pick` → `/iflow-run yolo` when
   `label_flows` is on. If any labels were added (or already present and kept),
   hint the batch path: **to auto-process them, run `/iflow-run cycle yolo`**
   (alias for `label:yolo`).

## Constraints

- **Confirm before writes** — label create and label apply each need explicit
  user confirmation (may be one combined confirm when both are needed).
- **No removals / no issue create** in v1.
- Always pass `--repo <owner/repo>` to `gh`; never rely on cwd defaults.
- Degrade gracefully when `gh` is missing (report and stop; suggest
  `gh auth login`).
