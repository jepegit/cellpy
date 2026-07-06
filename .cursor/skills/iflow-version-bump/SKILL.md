---
name: iflow-version-bump
description: >-
  Bump the project version in pyproject.toml using uv, with a
  pre-release-aware default when no level is given.
disable-model-invocation: true
---

# issue-flow — version bump

Use this skill to **bump the project version** with **uv** before landing work (often invoked from `/iflow-close`) — either at a specific level, or with the default rule below when none is given. It targets a **Python + uv** project whose `pyproject.toml` has a `[project]` `version` field.


### MODEL & EXECUTION DIRECTIVE


**Profile: economy** — Prioritize speed and token economy over deep reasoning.

In Cursor: use **Auto** or a fast model before invoking this step.



Keep scope tight to what this step requires.



## Preconditions

1. Run from the **project root** (the directory that contains `pyproject.toml`).
2. If `pyproject.toml` is missing or has no `[project]` `version`, **skip** the bump, explain why, and continue other work (for example the rest of `/iflow-close`) without failing the whole flow.

## Bump levels

Use **only** `uv` with `--bump <level>`. Every level `uv` supports is allowed:

| Level | Effect (example from `0.4.1a4`) |
|---|---|
| `major` | `1.0.0` |
| `minor` | `0.5.0` |
| `patch` | `0.4.2` |
| `stable` | `0.4.1` — drop the pre-release/dev segment |
| `alpha` | `0.4.1a5` — next alpha pre-release |
| `beta` | `0.4.1b1` — promote/advance to beta |
| `rc` | `0.4.1rc1` — promote/advance to release candidate |
| `post` | `0.4.1a4.post1` — post-release |
| `dev` | dev release — **must** be paired with another component, e.g. `uv version --bump patch --bump dev` |

```bash
uv version --bump patch     # 0.4.1a4 -> 0.4.2
uv version --bump alpha     # 0.4.1a4 -> 0.4.1a5
uv version --bump minor --bump alpha   # combine: 0.4.1a4 -> 0.5.0a1
```

Tip: preview without writing using `uv version --dry-run --bump <level> --short`.

## Choosing the level

1. **The user named a level** (`patch`, `minor`, `major`, `stable`, `alpha`, `beta`, `rc`, `post`, `dev`) → use exactly that.
2. **The user asked to bump/release but gave no level** → apply the **pre-release-aware default**, based on the *current* version in `pyproject.toml`:
   - current is an **alpha** (e.g. `aN`) → `uv version --bump alpha`
   - current is a **beta** (`bN`) → `uv version --bump beta`
   - current is a **release candidate** (`rcN`) → `uv version --bump rc`
   - current is a **dev** release (`.devN`) → `uv version --bump dev` paired with the component being advanced (default `patch`, i.e. `--bump patch --bump dev`)
   - current is a **stable** release (no pre-release segment) → `uv version --bump patch`
3. **Free-text intent** (e.g. "bugfix release", "promote to beta") → map to the matching level (bugfix → `patch`, "to beta" → `beta`); if genuinely ambiguous, ask once rather than guessing **major**.

## After bumping

1. Confirm the new version in `pyproject.toml` (or from the `uv` command output).
2. When committing later, stage **`pyproject.toml`**. If **`uv.lock`** changed as well, stage it too; otherwise do not assume it changed.

## Constraints

- Do not substitute `pip` or hand-edit the version unless `uv version` fails and the user agrees to an alternative.
- Never silently jump release channels: don't promote an alpha to stable (or bump major/minor) just because no level was given — the default keeps you on the current pre-release channel.
