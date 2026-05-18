---
name: issueflow-build
description: >-
  Run the /build slash command: rebuild the graphify knowledge graph for the
  project (graphify-out/graph.html, GRAPH_REPORT.md, graph.json) by shelling out
  to `issue-flow build` (or `graphify` directly). Off-path: never auto-dispatched
  by /iflow. Forwards trailing args verbatim to graphify.
disable-model-invocation: true
---

# issue-flow — graph rebuild (`/build`)

Follow this skill when the user wants to refresh the project's [graphify](https://graphify.net) knowledge graph. Matches `.cursor/commands/build.md`.

## When to use

- The user runs `/build`, mentions "rebuild the graph", "refresh graphify", "regenerate `GRAPH_REPORT.md`", or similar.
- The project has a `graphify-out/` folder that is stale (large refactor, new modules, new docs/papers added) and the user asks to update it.
- The user installed `graphifyy` for the first time and wants to produce the initial graph.

Do **not** use this skill from `/issue-start`, `/issue-close`, or `/iflow`. `/build` is opt-in only.

## Instructions

1. **Prefer `issue-flow build`** from the project root:

   ```bash
   issue-flow build
   ```

   With no extra args this runs `graphify extract <project>` (full AST + semantic LLM build). To pick a different graphify subcommand, pass it as the first arg: `issue-flow build update` (fast, code-only re-extract), `issue-flow build watch` (live rebuild), `issue-flow build cluster-only --no-viz`, etc. A leading `./subdir` overrides the scan path. Trailing flags pass through verbatim. Do not invent new wrapper flags.

2. **Fallback to `graphify` directly** when `issue-flow` is unavailable:

   ```bash
   graphify extract .
   ```

   `graphify` is subcommand-based — `graphify .` on its own is **not** valid (graphify reports `unknown command '.'`). Always pick a subcommand: `extract` for a full build, `update` for a fast incremental, `watch` for a long-running watcher, etc.

3. **Handle missing graphify gracefully.** If the run reports `graphify` is not on PATH, do **not** retry blindly. Tell the user to install it once:

   ```bash
   uv tool install graphifyy   # recommended
   pipx install graphifyy
   pip install graphifyy
   ```

   `graphifyy` (double-y) is the official PyPI package; the CLI is still `graphify`. After installing, suggest `issue-flow update` so `graphify cursor install` registers the graphify Cursor skill alongside this one.

4. **Verify and report.**
   - Confirm `graphify-out/graph.json`, `graphify-out/graph.html`, and `graphify-out/GRAPH_REPORT.md` exist after a successful run.
   - Surface non-zero exit codes verbatim; do not silently retry.
   - When the user asks "what changed?", skim `GRAPH_REPORT.md` (god nodes, surprising connections) for a short summary.

## Constraints

- Never auto-dispatch `/build` from another slash command. The user opts in explicitly.
- Never commit `graphify-out/cost.json` or `graphify-out/manifest.json`; they are local-only.
- Long-running modes (`watch`) keep the process alive; ask the user before launching them in an agent context.
- Forward extra arguments verbatim. Do **not** translate or rewrite graphify's flag set inside issue-flow.
