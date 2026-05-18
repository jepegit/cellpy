---
name: issueflow-version-bump
description: >-
  Bump semantic version in pyproject.toml using uv (patch, minor, or major)
  from the project root.
disable-model-invocation: true
---

# issue-flow — version bump

Use when the user wants to **bump the project version** with **uv** before landing work (often invoked from `/issue-close`).

## When to use

- The user asks for a **patch**, **minor**, or **major** semver bump.
- The repo is a **Python + uv** project whose `pyproject.toml` has a `[project]` `version` field (standard for packages using issue-flow).

## Preconditions

1. Run from the **project root** (the directory that contains `pyproject.toml`).
2. If `pyproject.toml` is missing or has no `[project]` `version`, **skip** the bump, explain why, and continue other work (for example the rest of `/issue-close`) without failing the whole flow.

## Command

Use **only** `uv` with a bump level (`patch`, `minor`, or `major`). Example for a patch release (e.g. `1.2.0` → `1.2.1`):

```bash
uv version --bump patch
```

Use `uv version --bump minor` or `uv version --bump major` when that is what the user requested.

## After bumping

1. Confirm the new version in `pyproject.toml` (or from the `uv` command output).
2. When committing later, stage **`pyproject.toml`**. If **`uv.lock`** changed as well, stage it too; otherwise do not assume it changed.

## Constraints

- Do not substitute `pip` or hand-edit the version unless `uv version` fails and the user agrees to an alternative.
- Prefer one clear bump level; if the user is ambiguous, ask once rather than guessing **major**.
