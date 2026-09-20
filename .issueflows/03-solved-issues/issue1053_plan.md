# Issue #1053 plan

## Goal

Deduplicate `docs/getting_started/mcp.md` so install commands, stdio JSON, and the VS Code `servers` warning each appear once.

## Approach

- Leave Fast path as the only place that shows `cellpy mcp install --client cursor`.
- Cursor (detailed) keeps global vs project, interpreter path, Settings UI, and WSL — no second install recipe.
- One canonical JSON under Cursor (detailed); By-hand JSON points at it.
- One VS Code `servers` warning in Other clients; drop the repeats.

## Files to touch

- `docs/getting_started/mcp.md`

## Test strategy

- Grep the page: one `mcpServers` JSON block, one `servers` warning paragraph.
- Confirm inbound links (`agents.md`, `cli.md`, `how_do_i.md`, `checkup.md`, `zensical.toml`) still match the H1 / anchors.

## Constraints

### Prior art

- None found (toolbox + grep + graph checked). Recipe page already exists from #1051.
