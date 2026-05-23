# Rebuild the project's knowledge graph (`/build`)

`/build` rebuilds the [graphify](https://graphify.net) knowledge graph for this project so the assistant can navigate by graph instead of grepping through files. Outputs land in `graphify-out/` (`graph.html`, `GRAPH_REPORT.md`, `graph.json`).

This is an **off-path** command — the lifecycle dispatcher (`/iflow`) never auto-runs it. Invoke it explicitly when the project's structure has changed enough that the existing graph is stale (new modules, large refactors, new docs/papers added).

## Input

Optional free-form text after the command. The first word, if it is a recognized graphify build subcommand, picks the action; otherwise the default is `update`. Trailing tokens forward verbatim. Common combinations:

- **No extra text** — AST-only build (`graphify update <project>`). **No LLM API key required**, so this works on a fresh machine. Produces the full `graphify-out/` (graph.json, graph.html, GRAPH_REPORT.md). The default.
- **`extract`** — AST + semantic LLM pass (`graphify extract <project>`). Richer cross-file relationships, but **requires an LLM backend**: set `GEMINI_API_KEY` / `GOOGLE_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, or `MOONSHOT_API_KEY` — or pass `--backend ollama` for a local LLM via [Ollama](https://ollama.com). Use after large refactors or when the AST-only graph misses important relationships.
- **`watch`** — long-running file watcher that auto-rebuilds on save (`graphify watch <project>`).
- **`cluster-only`** — rerun clustering on the existing `graph.json` without re-extraction (`graphify cluster-only <project>`).
- **`./subdir`** — scan a sub-directory instead of the project root (`graphify update ./subdir`).
- **Trailing flags** (e.g. `--force`, `--no-cluster`, `--no-viz`, `--backend ollama`) — passed straight through to the chosen subcommand. See `graphify --help` for the per-subcommand flag set.

See the [graphify CLI reference](https://graphify.net/graphify-cli-commands.html) for the full subcommand and flag list.

## Steps

1. **Preferred path: `issue-flow build`**. From the project root, run:

   ```bash
   issue-flow build
   ```

   This runs `graphify update .` — no API key needed. To pick a different subcommand or pass flags, append them, e.g. `issue-flow build extract` (full LLM pass), `issue-flow build cluster-only --no-viz`, or `issue-flow build extract --backend ollama` (local LLM). To scan a project other than the current directory, use `issue-flow build -C <project_dir>`. Extra args are forwarded verbatim.

2. **Fallback: call `graphify` directly** if `issue-flow` is not on PATH:

   ```bash
   graphify update .
   ```

   `graphify` is subcommand-based — `graphify .` on its own is **not** valid and will fail with `unknown command '.'`. Always pick a subcommand (`update`, `extract`, `watch`, `cluster-only`, …).

3. **Verify outputs.** After a successful run there should be a `graphify-out/` folder with at least `graph.html`, `GRAPH_REPORT.md`, and `graph.json`. Skim `GRAPH_REPORT.md` once to confirm the run picked up new modules or docs.

4. **If `graphify` is not installed** (`issue-flow build` exits with a "not on PATH" error), suggest the user install it:

   ```bash
   uv tool install graphifyy   # recommended
   pipx install graphifyy
   pip install graphifyy
   ```

   `graphifyy` (double-y) is the official PyPI package; the CLI is still `graphify`. After installing, re-run `issue-flow init` (or `issue-flow update`) so `graphify cursor install` registers the graphify Cursor skill.

5. **If `graphify extract` complains about a missing LLM API key**, the user picked the semantic-pass subcommand without configuring a backend. Suggest one of:

   - Set an API key for one of the supported backends (`GEMINI_API_KEY` / `GOOGLE_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `MOONSHOT_API_KEY`) and re-run.
   - Use a local LLM: `issue-flow build extract --backend ollama` (requires [Ollama](https://ollama.com) installed and a model pulled, e.g. `ollama pull qwen2.5-coder`).
   - Drop the `extract` arg and use the default `issue-flow build` (AST-only `update`, no LLM).

   Cursor's own LLM is **not** available to subprocesses, so graphify cannot reuse it.

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
