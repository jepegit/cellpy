# Agent copy-paste prompts and tracked RTD links

**Context.** Issue #1064. Humans paste a short prompt into a coding agent;
the prompt must include a durable `latest` Read the Docs URL.

**Decision.** Catalog lives at `docs/getting_started/agent_prompts.md`. Each
hard `https://cellpy.readthedocs.io/en/latest/…` URL is preceded by
`<!-- agent-doc: <path-under-docs.md> -->`. After `zensical build`,
`.issueflows/00-tools/check_rtd_latest_links.py` (wired in `docs.yml`)
asserts every `latest` URL exists under `site/` and each comment matches
the next URL.

**Alternatives.** Generate the page from YAML (rejected: ten snippets do
not need a generator). Use only relative markdown links (rejected: a
pasted prompt needs an absolute URL).

**Related.** #1054 (`llms.txt`), [docs-on-master.md](docs-on-master.md).
