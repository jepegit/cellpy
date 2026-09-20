# Issue #1054: Add llms.txt and llms-short.txt for agent-facing docs

Source: https://github.com/jepegit/cellpy/issues/1054

## Original issue text

## Problem / context

Coding agents already have `docs/getting_started/agents.md` and `AGENTS.md`, but there is no site-root [`llms.txt`](https://llmstxt.org/) (or a short variant) that a crawler / chat client can fetch without walking the HTML nav. Other projects publish `/llms.txt` plus a compressed `/llms-short.txt` so tools can choose budget.

## Spec

Add two plain-text files under `docs/` so the Zensical/RTD build copies them to the site root (`https://cellpy.readthedocs.io/en/latest/llms.txt` and `…/llms-short.txt`):

1. **`docs/llms.txt`** — follow the llmstxt.org shape: H1 project name, one-paragraph blockquote (library + CLI, not a hosted GUI), then markdown link lists to the durable chapters (install/setup, first hour, agents, MCP, batch/ICA how-tos, CLI, API). Use `latest` URLs. Link `AGENTS.md` on GitHub for contributors.
2. **`docs/llms-short.txt`** — tighter: product one-liner, entry (`import cellpy` / `cellpy.get`), frames + `c.schema`, batch vs MCP vs library import, and 4–6 links only (agents, MCP, first hour, CLI). No tutorial dump.

Also:

- One findability line on `docs/getting_started/agents.md` (and a single line in root `AGENTS.md` if that file already lists agent entry points).
- Do not add either file to `zensical.toml` `nav` (they are fetchable text, not HTML chapters).
- Confirm `zensical build` emits them at `site/llms.txt` and `site/llms-short.txt`. If Zensical only copies markdown pages, copy in `.readthedocs.yaml` `post_build` (and the same in local/CI if needed).

Keep the files hand-maintained for this issue. No generator, no `llms-full.txt` concatenation of the whole tree.

## Acceptance criteria

- [ ] `docs/llms.txt` and `docs/llms-short.txt` exist and stay in sync with the current getting-started story (library import vs MCP).
- [ ] After `uv run --group docs zensical build`, both files are at the site root (or an explicit copy step is documented and wired).
- [ ] `agents.md` (and `AGENTS.md` if touched) points at them.
- [ ] Neither file is a second copy of `agents.md`; links, not pasted chapters.

## Out of scope

- Auto-generating the files from `nav` / mkdocstrings.
- A concatenated `llms-full.txt` of every docs page.
- Changing MCP or agents chapter content beyond the one findability link.
