---
name: gh-ci
description: >-
  Use GitHub CLI to snapshot or wait on CI for a pull request or workflow run.
  Prefer gh pr checks / gh pr checks --watch; fall back to gh run list and
  gh run watch when PR checks are empty or unavailable. Use when waiting for
  CI, checking if checks are green, Actions are pending/failed, or the user
  mentions gh run watch / gh pr checks / "CI green".
issue-flow-version: 0.4.2a4
---

# gh-ci — wait on GitHub CI with `gh`

Teach agents the concrete `gh` commands for **listing** and **watching** CI.
Always pass `--repo <owner/repo>` (never rely on `gh`'s cwd default).

## Primary (PR-attached checks)

Prefer these when a pull request number is known (usual `/iflow-close` path):

```bash
# One-shot snapshot — exit 0 means green (or all pass / skipping)
gh pr checks <number> --repo <owner/repo>

# Wait until checks finish (or fail-fast on red)
gh pr checks <number> --repo <owner/repo> --watch --fail-fast
```

**Budget:** honour **15 minutes** wall-clock for any
`--watch` (from `[issueflow].checks_watch_minutes` /
`ISSUEFLOW_CHECKS_WATCH_MINUTES`, default 15). `gh` has no max-duration flag —
the agent stops the watch when the cap hits.

## Fallback (workflow runs)

When `gh pr checks` returns empty, cannot resolve checks, or there is no PR yet
but a workflow run id is known:

```bash
gh run list --repo <owner/repo> --limit 10
gh run watch <run-id> --repo <owner/repo>
```

Optional: `gh run view <run-id> --repo <owner/repo> --log-failed` after a red
run to surface failing job logs.

## Semantics

| Result | Meaning | Agent action |
|--------|---------|--------------|
| Exit 0 / all `pass` or `skipping` | CI green | Proceed (merge, report green, etc.) |
| Fail / `--fail-fast` | CI red | Stop hands-off paths; report failing check/run URLs |
| Still pending past budget | Unknown | Do not hang; report pending and follow the calling skill (e.g. close yolo may fall back to `--auto`) |

## Where this fits

- **`/iflow-close`** owns the merge / yolo watch-then-merge sequence; this skill
  is the shared cheatsheet for the CI commands themselves.
- Design record: `.issueflows/04-designs-and-guides/gh-list-and-watch.md`
  (issues #172, #220).
