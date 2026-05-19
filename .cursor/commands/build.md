# Rebuild the project's knowledge graph (`/build`)

`/build` rebuilds the [graphify](https://graphify.net) knowledge graph for this project so the assistant can navigate by graph instead of grepping through files. Outputs land in `graphify-out/` (`graph.html`, `GRAPH_REPORT.md`, `graph.json`).

This is an **off-path** command — the lifecycle dispatcher (`/iflow`) never auto-runs it. Invoke it explicitly when the project's structure has changed enough that the existing graph is stale (new modules, large refactors, new docs/papers added).

## Input

Optional free-form text after the command. The first word, if it is a recognized graphify build subcommand, picks the action; otherwise the default is `extract`. Trailing tokens forward verbatim. Common combinations:

- **No extra text** — full rebuild (`graphify extract <project>`); requires an LLM API key for graphify's semantic pass.
- **`update`** — fast incremental re-extract of changed code files only, no LLM (`graphify update <project>`).
- **`watch`** — long-running file watcher that auto-rebuilds on save (`graphify watch <project>`).
- **`cluster-only`** — rerun clustering on the existing `graph.json` without re-extraction (`graphify cluster-only <project>`).
- **`./subdir`** — scan a sub-directory instead of the project root (`graphify extract ./subdir`).
- **Trailing flags** (e.g. `--no-cluster`, `--force`, `--no-viz`) — passed straight through to the chosen subcommand. See `graphify --help` for the per-subcommand flag set.

See the [graphify CLI reference](https://graphify.net/graphify-cli-commands.html) for the full subcommand and flag list.

## Steps

1. **Preferred path: `issue-flow build`**. From the project root, run:

   ```bash
   issue-flow build
   ```

   To pick a non-default subcommand or pass flags, append them after the project dir, e.g. `issue-flow build update` or `issue-flow build cluster-only --no-viz`. Extra args are forwarded verbatim.

2. **Fallback: call `graphify` directly** if `issue-flow` is not on PATH:

   ```bash
   graphify extract .
   ```

   `graphify` is subcommand-based — `graphify .` on its own is **not** valid and will fail with `unknown command '.'`. Always pick a subcommand (`extract`, `update`, `watch`, `cluster-only`, …).

3. **Verify outputs.** After a successful run there should be a `graphify-out/` folder with at least `graph.html`, `GRAPH_REPORT.md`, and `graph.json`. Skim `GRAPH_REPORT.md` once to confirm the run picked up new modules or docs.

4. **If `graphify` is not installed** (`issue-flow build` exits with a "not on PATH" error), suggest the user install it:

   ```bash
   uv tool install graphifyy   # recommended
   pipx install graphifyy
   pip install graphifyy
   ```

   `graphifyy` (double-y) is the official PyPI package; the CLI is still `graphify`. After installing, re-run `issue-flow init` (or `issue-flow update`) so `graphify cursor install` registers the graphify Cursor skill.

## Constraints

- Do **not** run `/build` automatically from `/issue-start`, `/issue-close`, or `/iflow`. The user opts in.
- Do **not** commit `graphify-out/cost.json` or `graphify-out/manifest.json`; both are local-only. The graph itself (`graph.json`, `graph.html`, `GRAPH_REPORT.md`) is fine to commit so teammates start with a map.
- Long-running modes (`watch`) keep the process running; ask the user before launching them in an agent context.

## Output to user

Report:
- whether the build ran (or was skipped because graphify is missing)
- the exit code from `graphify`
- the size / mtime of `graphify-out/graph.json` (rough freshness check)
- a short summary of new highlights from `GRAPH_REPORT.md` if the user asked for one
