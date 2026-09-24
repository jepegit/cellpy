# Copy-paste prompts for your agent

Paste one of these into Cursor, VS Code, Claude, or another coding agent.
Use the copy button on the prompt. Each names a checkable outcome and a
**latest** docs URL. The HTML `agent-doc` comment above a URL is for
maintainers: it names the source page so a move fails
[docs CI](https://github.com/jepegit/cellpy/blob/master/.github/workflows/docs.yml)
instead of leaving a stale link in the quote.

To **import cellpy as a library**, start at [Using cellpy from an agent](index.md).
To **wire an MCP client**, start at [Connect an agent IDE to cellpy](mcp.md)
(the first prompt below is the same text as that page's "Ask your agent" box).

## How to install cellpy MCP

<!-- agent-doc: agents/mcp.md -->
```text
Install the cellpy MCP server, register it with Cursor, and run
`cellpy mcp check --client cursor` to prove it works. Follow
https://cellpy.readthedocs.io/en/latest/agents/mcp/.
```

## How to install cellpy and prove it works

<!-- agent-doc: getting_started/installation.md -->
```text
Install cellpy with pip or conda on this machine, then run
`cellpy info --check` so the CLI is on PATH. Follow
https://cellpy.readthedocs.io/en/latest/getting_started/installation/.
```

## How to load a cycler file

<!-- agent-doc: getting_started/basic_usage.md -->
```text
Load the user's cycler file with `cellpy.get`, set mass and instrument,
and print `c.data.summary.head()`. Follow
https://cellpy.readthedocs.io/en/latest/getting_started/basic_usage/.
```

## How to try cellpy without a data file

<!-- agent-doc: getting_started/first_hour.md -->
```text
Load the bundled example cell with `example_data.raw_file()` and show the
first summary rows. Follow
https://cellpy.readthedocs.io/en/latest/getting_started/first_hour/.
```

## How to run a batch from the Excel database

<!-- agent-doc: guides/batch_database.md -->
```text
Set up the Excel cellpy database and load a batch with `batch.load`. Follow
https://cellpy.readthedocs.io/en/latest/guides/batch_database/.
```

## How to plot one cell

<!-- agent-doc: guides/plotting.md -->
```text
Plot one loaded cell with the plotting families (cycles or summary). Follow
https://cellpy.readthedocs.io/en/latest/guides/plotting/.
```

## How to compute ICA / DVA

<!-- agent-doc: guides/ica.md -->
```text
Compute ICA/DVA with `cellpy.ica` (`dqdv` / `dvdq`) and plot it. Follow
https://cellpy.readthedocs.io/en/latest/guides/ica/.
```

## How to fix capacities or units that look wrong

<!-- agent-doc: troubleshooting.md -->
```text
The capacities or units look wrong. Diagnose from the troubleshooting
page (charge/discharge swap, rebase, units). Follow
https://cellpy.readthedocs.io/en/latest/troubleshooting/.
```

## How to use schema names instead of hardcoded headers

<!-- agent-doc: agents/index.md -->
```text
Use `c.schema` for column names, not hardcoded header strings. Follow
https://cellpy.readthedocs.io/en/latest/agents/.
```

## How to summary-plot SAL cells 10–15

<!-- agent-doc: agents/mcp.md -->
```text
Using cellpy MCP, find project SAL cells numbered 10–15 (names like
<date>_SAL<number>), load them, and write a summary plot. Call find_cells
first (kind=cellpy). If found is 0 and offer_raw is true, ask before
searching raw — do not crawl rawdatadir yourself. If the user says yes,
call find_cells again with kind=raw. Use needs_metadata: ask for mass and
nominal capacity; do not guess. Then load_cell with those values, collect
kind=summary with a plot family, and render. Follow
https://cellpy.readthedocs.io/en/latest/agents/mcp/.
```

## How to fetch the agent docs map

<!-- agent-doc: agents/index.md -->
```text
Fetch the agent-facing docs map (`llms.txt` / this chapter) before changing
cellpy usage. Follow
https://cellpy.readthedocs.io/en/latest/agents/.
```
