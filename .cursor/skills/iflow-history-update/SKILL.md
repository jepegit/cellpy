---
name: iflow-history-update
description: >-
  Update the changelog when landing an issue: append a bullet to
  [Unreleased], or promote it to a release section after a version bump.
disable-model-invocation: true
issue-flow-version: 0.4.2a4
---

# issue-flow — history update

Use this skill to update the project's changelog file (default **`HISTORY.md`**, overridable via `ISSUEFLOW_HISTORY_FILE` in `.env`) as part of `/iflow-close`. It never runs on its own schedule; it is driven by the "update HISTORY" step, and does not run when the user passed `nohistory` / `skip history`.


### MODEL & EXECUTION DIRECTIVE


**Profile: economy** — Prioritize speed and token economy over deep reasoning.

In Cursor: use **Auto** or a fast model before invoking this step.



Keep scope tight to what this step requires.



## Preconditions

1. The changelog file (`HISTORY.md`) exists at the **project root**. If it does not, **skip** this step, print "no `HISTORY.md` — skipping changelog update" and continue the rest of `/iflow-close`. Never create the file from this skill.
2. The file is in **Keep a Changelog** shape: a top-level `## [Unreleased]` heading, with released versions below as `## [x.y.z] - YYYY-MM-DD` headings. If the shape does not match, **stop and report the mismatch** instead of guessing — let the user fix the file or pass `nohistory`.

## Inputs from `/iflow-close`

| From | Used for |
|---|---|
| Issue number `N` | Reference suffix on the new bullet, e.g. `(#42)`. |
| Issue title (from `.issueflows/01-current-issues/issue<N>_original.md`) | Default bullet summary. |
| `log "..."` / `note "..."` input token | Override the bullet summary verbatim. |
| Version-bump outcome (from step 2 of `/iflow-close`) | Decides **append** vs **promote** (see below). |

## Operation modes

### A. No version bump — append to `[Unreleased]`

1. Read `HISTORY.md`. Locate the first `## [Unreleased]` heading. The block ends at the next `## [` heading (or EOF).
2. Compose the new bullet:

   ```
   - <summary>. (#<N>)
   ```

   Summary = `log "..."` override if provided, else the issue title with sentence case, trailing period trimmed before the `.` we add.
3. Append the bullet to the end of the Unreleased bullet list. Preserve existing formatting (blank lines, list markers). Do not reorder existing entries.
4. Show the user the proposed diff of `HISTORY.md` and confirm once before writing.

### B. Version bump happened — promote `[Unreleased]` to a new release section

Only runs when step 2 of `/iflow-close` actually changed `pyproject.toml` to a new version `NEW_VERSION`.

1. Determine `NEW_VERSION` (e.g. read from `pyproject.toml`, or from the `uv version` command output). Determine `TODAY` as `YYYY-MM-DD` in the user's local timezone.
2. Read `HISTORY.md`. Find `## [Unreleased]`.
3. Compose the new bullet (same shape as mode A). If `[Unreleased]` was empty when the bump happened, still create the new release section with this bullet inside it — a version bump implies a release, and the focus issue's bullet is always meaningful.
4. Rename the existing heading from `## [Unreleased]` to `## [<NEW_VERSION>] - <TODAY>` and add the new bullet at the end of that section's bullet list.
5. Prepend a fresh, empty `## [Unreleased]` section above the just-closed release, with one blank line separating them:

   ```markdown
   ## [Unreleased]

   ## [NEW_VERSION] - TODAY

   - …existing bullets from before the promote…
   - <new bullet for this issue> (#N)
   ```

6. Show the user the proposed diff and confirm once before writing.

## Staging

When `/iflow-close` reaches its commit step:

- Stage `HISTORY.md` alongside the issue's other changes.
- If a version bump also ran, `HISTORY.md` is staged in the same commit as `pyproject.toml` (and `uv.lock` if it changed).

## Constraints

- Read/write only `HISTORY.md` at the project root. Do not touch any other file from this skill.
- Never create `HISTORY.md` from scratch — scaffolding a starter changelog is out of scope for `issue-flow init` / `update`.
- If the confirm prompt in mode A or mode B is declined, leave `HISTORY.md` untouched and print a short "skipped changelog update" note. The rest of `/iflow-close` continues normally.
- Preserve existing formatting conventions (bullet style, sentence case, trailing punctuation). Match the style of the nearest existing entries when in doubt.
- The new bullet's `(#<N>)` suffix is always GitHub issue `#N`, matching the focus issue's number in `.issueflows/01-current-issues/issue<N>_original.md`.
