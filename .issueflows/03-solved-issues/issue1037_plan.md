# Issue #1037 — plan

## Goal

Find why an experienced user can run `cellpy setup` and still have no `raw/`
folder, then close that hole so setup creates the local `raw` directory
(unless the configured path is a remote `OtherPath`).

## Constraints

- Do not create remote `ssh`/`sftp`/`scp` raw paths locally (`_create_dir`
  already skips `OtherPath.is_external`).
- First-time `--silent` setup must keep creating the default
  `~/cellpy_data/{out,raw,cellpyfiles,...}` tree
  (`test_cli_setup_creates_dirs_and_files`).
- `--reset` still means “ignore current config and use the default layout”.
- Setup stays light by default (no reader import) — [cli-light-startup.md](../04-designs-and-guides/cli-light-startup.md).
- Docs already promise that setup “tries to create the usual directory
  layout” including `raw/` ([configuration.md](../../docs/getting_started/configuration.md)).

### Prior art

- `setup_config` / `_update_paths` / `_create_dir` in
  [`cellpy/cli_api.py`](../../cellpy/cli_api.py) — only non-interactive
  path that mkdir’s is `if reset: _update_paths(...)`. First missing
  `cellpy.toml` forces `reset = True`; a later `cellpy setup` does not.
- `_create_dir` — mkdir local paths; return immediately for external
  `OtherPath`. Confirm prompt only fires when the *parent* is missing.
- [`tests/test_cellpy_cmd.py`](../../tests/test_cellpy_cmd.py)
  `test_cli_setup_creates_dirs_and_files` — first-time `--silent` +
  `--test_user` asserts `cellpy_data/raw` exists. No test for “config
  already present, folders missing”.
- Related: #960 (setup writes toml, not legacy `.conf`), #891 (setup
  output / `--silent`), #990 (`cellpy new` create-dir without prompt).
- Toolbox + graph: none that create setup folders
  (`00-tools/` helpers are AST/header scanners; no `GRAPH_REPORT.md`).

## Approach

1. **Treat the skip as the bug.** Non-interactive `cellpy setup` with an
   existing `cellpy.toml` never calls `_update_paths`, so it rewrites
   toml/env and creates **no** directories. That matches an experienced
   user (already configured, or just ran `cellpy setup migrate`). Docs
   say re-run setup after upgrades; that path currently cannot create
   `raw/`.
2. **Always ensure local dirs.** Call `_update_paths` from both the
   interactive and non-interactive branches. Keep `reset` as “use default
   names under `cellpy_data`”; when `reset` is false, mkdir the paths
   already in config (after the existing `h / path` join and optional
   `-i` prompts). Still skip remotes.
3. **Fix the `instrumentsdir` typo** in the non-reset branch
   (`config.paths.instrumentsdir` → `instrumentdir`). Today
   `cellpy setup -i` with an existing config raises `AttributeError`
   before any mkdir.
4. **Do not invent a second raw location.** If the existing config points
   `rawdatadir` at cwd or another existing path, do not also create
   `~/cellpy_data/raw` unless `--reset` / first-time. Missing *configured*
   `raw` is what we create.
5. **Regression tests** (essential): existing first-time test stays;
   add “toml exists, `raw/` absent → `cellpy setup --silent` creates it”;
   add “external `rawdatadir` is not mkdir’d”; add “`-i` with existing
   config does not crash on `instrumentdir`” (dry-run is enough).
6. **Docs:** one sentence that a re-run creates any missing *configured*
   local folders, and that `--reset` rebuilds the default `cellpy_data`
   tree (including `raw/`).

## Files to touch

- [`cellpy/cli_api.py`](../../cellpy/cli_api.py) — always call
  `_update_paths`; fix `instrumentsdir` typo.
- [`tests/test_cellpy_cmd.py`](../../tests/test_cellpy_cmd.py) — new
  essential cases above (reuse `isolated_user_dir`).
- [`docs/getting_started/configuration.md`](../../docs/getting_started/configuration.md)
  — re-run / `--reset` behaviour.
- [`docs/getting_started/agents.md`](../../docs/getting_started/agents.md)
  + root `AGENTS.md` only if the setup surface agents rely on changes
  (likely a one-line “setup creates missing local path dirs”).

## Test strategy

```bash
uv run pytest tests/test_cellpy_cmd.py tests/test_cli_setup_output.py -m essential
uv run pytest -m essential
```

No new fixtures beyond the existing isolated user-dir pattern.

## Open questions

- **Re-run policy (recommended: yes):** should `cellpy setup` without
  `--reset` create missing configured local directories? Alternative:
  leave the skip and only document `--reset`. The issue title is “look
  into possible missing creation”, so the recommended fix is to create
  them.
- If you have the reporter’s exact command (`setup`, `setup -i`,
  `setup migrate`, already had toml?), that would confirm the skip
  path — not required to start if the policy above is accepted.
