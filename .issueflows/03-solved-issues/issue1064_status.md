# Issue #1064 — status

- [x] Done

## What's done

- Plan accepted (snippets + hard-link tracking in one PR).
- Catalog: `docs/getting_started/agent_prompts.md` (10 prompts).
- Nav + findability: `zensical.toml`, `agents.md`, `mcp.md`, `how_do_i.md`,
  getting-started index, `llms.txt`, `llms-short.txt`, root `AGENTS.md`.
- MCP "Ask your agent" prompt shares wording + `<!-- agent-doc -->`.
- `.issueflows/00-tools/check_rtd_latest_links.py` + docs.yml step.
- `zensical build` — No issues found. Checker green against `site/`.
- `uv run pytest -m essential` — 899 passed, 70 skipped.
- HISTORY Unreleased bullet. Design note: `agent-prompt-links.md`.
- Follow-up: prompts are fenced `text` blocks so `content.code.copy` shows
  a copy button (blockquotes had none).

## Remaining work

None.
