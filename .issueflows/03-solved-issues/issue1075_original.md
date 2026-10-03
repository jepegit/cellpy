# Issue #1075: Parse `<date>_<project><number>` cell filenames

Source: https://github.com/jepegit/cellpy/issues/1075

## Original issue text

## Context

Part of epic #1074 (agent summary-plots SAL cells 10–15 from local files). Stage 1 retires the naming-pattern risk before any finder or MCP tool exists.

## Scope

Add a small helper in `cellpy.readers.filefinder` (sanctioned `cellpy.filefinder` surface) that takes a filename or stem and a project token and returns the integer run number, or `None` if the stem does not match `<date>_<project><number>` with an optional trailing suffix (`_cc`, instrument tag, extension).

Match the project token case-insensitively.

Must match: `20240922_SAL12`, `20240922_SAL12_cc.cellpy`, `20240922_sal15.res`.

Must miss: `20240922_SAL9` when asking for project `BAT`; `notes_SAL12.txt` if the date prefix is required; `20240922_SALAMANDER12` when the token is `SAL` (do not treat a longer word as `SAL`).

Tests only — no I/O, no config.

## Acceptance criteria

- Given a stem and project token, return a run number or a clear miss.
- Inclusive later-range filtering is out of scope (next Stage 1 issue).

Goal: given a stem and project token, get a run number or a clear miss.

Model: fast

Depends on: none

Part of epic #1074.
