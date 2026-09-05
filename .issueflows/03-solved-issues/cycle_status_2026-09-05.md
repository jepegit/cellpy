# Cycle status

- Queue spec: `yolo` (resolved `label:yolo`)
- Repo: `jepegit/cellpy` (`C:\scripting\cellpy-workspace\cellpy`), default branch `master`
- Failure policy: `onfail:stop`
- Started: 2026-09-05T19:25:00+02:00
- Finished: 2026-09-05T22:20:00+02:00
- Confirmed: yes (single consolidated confirm, 3 issues)

- [x] Done

## Queue (ordered)

- [x] #990 — cellpy new: honour no_input when the project directory does not exist — merged https://github.com/jepegit/cellpy/pull/994
- [x] #991 — Add cli_api.list_templates() returning the batch templates as data — merged https://github.com/jepegit/cellpy/pull/995
- [x] #993 — Docstring cross-references lost their module paths in #968 — merged https://github.com/jepegit/cellpy/pull/996

Blocked: none. Skipped (closed): none. No stop condition tripped.

## Notes

- Leftover `issue985_*` group (`- [ ] Done`) was swept from `01-current-issues/`
  to `02-partly-solved-issues/` by the first `/iflow-init`.
- Every PR needed one `gh pr checks --watch` pass before `gh pr merge --squash`
  succeeded (base branch policy requires the `essential` + `full` checks).
- Local branches `990-no-input-project-dir`, `991-list-templates-data`,
  `993-dotted-docstring-refs` are left for `/iflow-cleanup`.
