# Essential tests (pytest)

**Context.** Large suites (especially agent-written tests) make "run everything on
every PR" expensive. A common pattern: mark a small **essential** subset for
PR/push CI; run the full suite on a schedule and at release.

**Opt-in.** Controlled by `[issueflow]` knobs (baked at `issue-flow update`):

| Key | Default | Role |
|-----|---------|------|
| `essential_tests` | `false` | Master switch — skills ignore this guide when false |
| `test_runner` | `"pytest"` | v1 only `"pytest"`; other values → unsupported + invite PRs |
| `essential_marker` | `"essential"` | pytest mark name (`@pytest.mark.<name>`) |
| `essential_review` | `"close"` | When to triage issue-touched tests: `close` \| `build` \| `both` \| `never` |

See also [skill-behaviour-knobs.md](./skill-behaviour-knobs.md) and the living
[test-registry.md](./test-registry.md).

## Contract

1. **Marker.** Register in `pyproject.toml` / `pytest.ini`, e.g.
   `[tool.pytest.ini_options] markers = ["essential: …"]`.
2. **Dual CI (docs recipe, not auto-written):**
   - PR/push workflow: `pytest -m essential` (plus lint as usual).
   - Scheduled / release workflow: full `pytest`.
3. **Per-issue review** (when `essential_review` includes the step): agents
   triage **tests added or changed by this issue only** — propose
   `@pytest.mark.essential` vs leave unmarked, update the registry
   row, confirm before bulk edits.
4. **Doctor sweep:** full-suite audit vs registry (drift, suite-too-large,
   demotions) — off-path, consolidated confirm before marker churn.
5. **Close sanity when enabled:** run essential (`pytest -m essential`);
   *remind* that full/scheduled coverage exists. Do not skip a failing essential
   suite.

## Non-goals (v1)

- Non-pytest runners.
- Silently rewriting unrelated tests.
- Auto-writing consumer `.github/workflows/` (copy from this doc / recipes).
- Graphify bulk classification of an existing huge suite.

## CI recipe (copy-paste)

**PR / push (`ci.yml` excerpt):**

```yaml
- name: Essential tests
  run: uv run pytest -m essential -v
```

**Scheduled full suite (`ci-scheduled.yml` sketch):**

```yaml
on:
  schedule:
    - cron: "0 3 * * 1"  # weekly; adjust
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      # … setup …
      - name: Full test suite
        run: uv run pytest -v
```

Link: issue #213.
