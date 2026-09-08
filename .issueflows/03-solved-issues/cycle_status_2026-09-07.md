# Cycle status

- queue: yolo
- resolved: label:yolo
- repo: jepegit/cellpy
- onfail: stop
- started: 2026-09-07T19:33:00Z
- stopped: 2026-09-07T20:10:00Z

## Queue

- [x] #937 — Notebook tooling (ipykernel, matplotlib) is a hard runtime dependency — ~90 MB in a headless server image — merged https://github.com/jepegit/cellpy/pull/1002
- [~] #938 — Missing external tools fail silently: mdb-export raises bare FileNotFoundError, pyodbc ImportError hides two loaders — failed: not yolo-small (three independent deliverables; see 02-partly-solved-issues)
- [ ] #960 — Possible bugs in cellpy setup and configuration — not reached
- [ ] #982 — Default group name from cellpy_db — not reached
- [ ] #1000 — prepare for changes in batch journal json file — not reached

## Stop reason

Yolo scope check on #938 aborted: issue body is two features (mdb-export typed error + `list_instruments` availability API) plus an owner comment adding a third (`examplesdir` default). Cycle `onfail:stop`. Branch `938-missing-external-tools` holds the capture.

- [x] Done
