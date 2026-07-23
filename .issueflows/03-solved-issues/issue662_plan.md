# Plan: Issue #662 — OtherPath credentials / env not seen after config lazy-load

## Goal

Restore remote `OtherPath` / `batch` journal creation (`auto_use_file_list=True`) so a configured `.env_cellpy` (or exported `CELLPY_*` vars) is enough for SSH auth again on the **`v1.x`** line. If the same defect still exists on **`master`**, land a **separate, minimal** PR there too.

## Constraints

- **Branch / PR targets:** work on `662-otherpath-env-credentials` off `v1.x` (issue label `v1x`). Primary PR → `v1.x`.
- **Dual-line fix (required):** after root cause is confirmed and fixed on `v1.x`, **check `origin/master` for the same bug**. If present, open a **second PR to `master` that contains only that fix** (cherry-pick or re-apply the minimal commit — no unrelated v1.x/v2 churn). If master already resolved it (e.g. via `cellpy.config.credentials`), document that in the status file and skip the master PR.
- **Label `v1 and v2`:** coordinate mentally with master/v2; do not merge a fat cross-branch diff.
- **Back-compat:** keep `CELLPY_PASSWORD` / `CELLPY_KEY_FILENAME` (and host/user) as the public env contract; do not invent new variable names.
- **KISS:** prefer the smallest bridge that reconnects env file → what `OtherPath` reads. Avoid porting the whole master UPath rewrite onto `v1.x`.
- **No secrets in git / logs.**

### Prior art

- `prmreader._load_env_file()` — `dotenv.load_dotenv` into `os.environ`; docstring already says “legacy OtherPath consumers” ([`cellpy/parameters/prmreader.py`](cellpy/parameters/prmreader.py)).
- `load_config` / `_collect_env_overrides` — reads `.env` via `dotenv_values` into `config.secrets` **without** mutating `os.environ` ([`cellpy/config/loader.py`](cellpy/config/loader.py)).
- Issue **#453** (esp. M3) — removed import-time `prmreader.initialize()` from [`cellpy/__init__.py`](cellpy/__init__.py); lazy first `config` touch only.
- v1.x `OtherPath._get_connection_info` / legacy twin — bare `os.getenv("CELLPY_PASSWORD"|"CELLPY_KEY_FILENAME")` ([`cellpy/internals/otherpath.py`](cellpy/internals/otherpath.py)); same pattern in [`cellpy/internals/connections.py`](cellpy/internals/connections.py).
- Fail path in report: `filefinder.find_in_raw_file_directory` → `OtherPath.connection_info()` ([`cellpy/readers/filefinder.py`](cellpy/readers/filefinder.py)), triggered from `batch.create_journal(auto_use_file_list=True)`.
- Tests already nearby: `test_prms_env_file_loads_secrets`, `test_prms_env_reaches_otherpath_connection_info` ([`tests/test_prms.py`](tests/test_prms.py)); env fixtures in [`tests/conftest.py`](tests/conftest.py).
- **Master (already different):** `cellpy.config.credentials` resolves session secrets then env; `OtherPath` / `connections` call that helper — likely already immune to “secrets in config, empty `os.environ`”. Confirm during build; do not assume without a check.
- Toolbox (`00-tools/`): nothing for env/OtherPath — no helper to reuse.
- Graph: OtherPath / `_credentials_from_env` / filefinder / batch journal communities — aligns with the call chain above.

## Approach

1. **Reproduce / confirm root cause (read-only then targeted probes in build)**
   - Starting hypothesis (strong): after #453, first config access loads `.env` into **`config.secrets`** only; **`os.environ` stays empty** unless something calls `_load_env_file()`. v1.x `OtherPath` only looks at `os.environ` → exact error in the issue.
   - Confirm by: clear `CELLPY_*` from the process env, point `paths.env_file` at a temp `.env_cellpy` with password/key, touch config (no `_load_env_file`), call `OtherPath(...).connection_info(testing=True)` — expect `UnderDefined`. Then call `_load_env_file()` (or the chosen fix) and expect success.
   - Also verify `env_file` path resolution (relative `.env_cellpy` vs home) is not a second failure mode for this report; fix only if evidence shows it.

2. **Fix on `v1.x` (pick smallest correct option after confirmation)**
   - **Preferred:** when the config session loads/reloads, also push the env-file layer into `os.environ` for legacy consumers (reuse / call `_load_env_file()`, or equivalent `load_dotenv` from the resolved env path). Keeps OtherPath unchanged.
   - **Alternative (only if preferred is wrong):** teach v1.x `OtherPath`/`connections` to read `config.secrets` (thin helper, not a full master cherry of UPath). Larger surface — avoid unless needed.
   - Keep error text recognizable (`CELLPY_PASSWORD` / `CELLPY_KEY_FILENAME`).

3. **Master parity check (mandatory before close)**
   - On `origin/master`, re-run the same “secrets in session / empty process env” probe against `OtherPath.connection_info` (and the batch/`find_in_raw_file_directory` path if cheap).
   - **If still broken:** branch from `master`, apply **only** the credential-visibility fix, open PR → `master`. Cross-link both PRs to #662.
   - **If already fixed:** note commit/mechanism in status; no master PR.

4. **Docs / UX (only if needed)**
   - If users must still call `prmreader.initialize()` for some path, say so in remote-paths / config docs — prefer making lazy load sufficient so “config + env file set” keeps working as before.

## Files to touch

| Path | Change |
|------|--------|
| `cellpy/config/session.py` and/or `cellpy/parameters/prmreader.py` (likely) | Ensure env file reaches `os.environ` (or shared credential resolve) on lazy reload |
| `cellpy/internals/otherpath.py` / `connections.py` | Only if option B; otherwise leave |
| `tests/test_prms.py` (and/or `tests/test_otherpaths.py`) | Regression: config load alone → `connection_info` works with empty prior `os.environ`; mark `@pytest.mark.essential` if it guards this merge |
| `.issueflows/01-current-issues/issue662_status.md` | Record root cause + whether master needed a second PR |
| Docs (`docs/getting_started/remote_paths.md` etc.) | Only if behavior/contract wording must change |

## Test strategy

- Inner loop: `uv run pytest tests/test_prms.py tests/test_otherpaths.py -q` (plus any new focused test).
- Gate: `uv run pytest -m essential`.
- Manual (optional, reporter path): `batch`/`create_journal` with `auto_use_file_list=True` and remote `rawdatadir` after env-only setup — not required for CI if unit regression is solid.
- Master check: same unit probe on a temporary checkout/branch of `master` (or `git show` + targeted test run).

## Open questions

1. **Reporter version string** — issue says `v1.0.1post1`; current `v1.x` HISTORY highlights **1.1.0 / 1.1.0.post1** with the config lazy-load change. Treat as “current 1.x after #453” unless you confirm an older pin?
2. **Fix style on v1.x** — OK to prefer “`load_dotenv` on config reload” over porting `cellpy.config.credentials` from master?
3. **Master second PR** — confirm: always open a master PR **only when the bug still reproduces there**; if already fixed, status note is enough (per Approach §3).

## Preflight (plan time)

- Repo: `jepegit/cellpy`
- Branch: `662-otherpath-env-credentials` (from `v1.x`)
- vs `origin/master`: ahead/behind reported by preflight as dirty + divergent (expected — v1.x line); work targets `v1.x`, not ff from master
- Working tree: untracked locals ignored (`cellpy_batch_test.json`, `dump/`, `site/`, hdf5 fixtures)
