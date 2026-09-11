---
name: iflow-ops
description: >-
  Run ops / no-PR work for the focus issue (staging→prod, flag flips, external
  deploys), then finish via /iflow-close ops.
disable-model-invocation: true
issue-flow-version: 0.4.2a4
---

# issue-flow — ops / no-PR (`/iflow-ops`)

Follow this skill for **work that does not deserve a PR**: promote staging→production, flip a feature flag, run an external deploy checklist, tag-only release steps with no issue-branch product diff, and similar ops.

Do **not** use this for product code changes — those go through the normal lifecycle (or `/iflow-yolo` when small).


**Invoke:** type `iflow ops` in chat, or `/iflow-ops` from the slash menu (`iflow-ops` also works).




### MODEL & EXECUTION DIRECTIVE


**Profile: economy** — Prioritize speed and token economy over deep reasoning.

In Cursor: use **Auto** or a fast model before invoking this step.



Keep scope tight to what this step requires.




### Resolve project root (multi-root workspaces)

Before any `git`, `gh`, or `.issueflows/` path operation in this workflow:

**Resolution order** (stop when unambiguous):

1. **Explicit hints** in slash input — `root:<path>`, `repo:<folder-basename>` (directory name, e.g. `cellpy-core`), or `repo:owner/name`.
2. **CLI fast path** — `issue-flow agent resolve [-C <start>] [--from-file <active-file>] [--json]`. Use the returned `project_root` and `repo`; pass `-C <project_root>` to other `issue-flow agent …` subcommands. When the answer came from the workspace registry, the payload sets `resolved_via_workspace_default: true`.
3. **Branch context** — exactly one workspace repo whose branch matches `^\d+-` → that root.
4. **Single scaffold** — exactly one `.issueflows/` tree visible in the workspace → that root.
5. **Workspace default** — an `issueflow-workspace.toml` at the workspace root (created with `issue-flow workspace init`) may name a `default` member repo; use it when no scaffold matched above. Tell the user the default was used.
6. **Ambiguous** → **stop and ask**; never guess between sibling repos.

After resolution, treat the result as `<project_root>` and `<owner/repo>`:

- **Git:** `git -C <project_root> …` (or `issue-flow agent … -C <project_root>` for supported ops).
- **GitHub:** pass an explicit repo on every `gh` call — never rely on `gh`'s implicit cwd default. For most commands use `--repo <owner/repo>`; **exception:** `gh repo view` takes the repo as a **positional** arg (`gh repo view <owner/repo> …`) and rejects `--repo`.
- **Paths:** all `.issueflows/…` paths are under `<project_root>`.

When `.issueflows/04-designs-and-guides/multi-repo-workspaces.md` exists, read it for layout and cross-repo guidance.


## Instructions

1. **Resolve the issue.** Prefer the focus issue under `.issueflows/01-current-issues/`. If missing, take a number/URL from the command input and run `/iflow-capture` first. Stop if still ambiguous.

2. **Preflight.** Prefer `issue-flow agent preflight --json` (`clean` / `dirty_paths` / `issueflows_only` / branch). Else `git fetch --prune` + `git status --porcelain`.
   - **Product-code dirty** (any path outside `.issueflows/`) → **stop**. Ops path refuses silent no-PR when product files changed; use normal `/iflow-close` or stash/discard.
   - **Issueflows-only dirty** or clean → continue.
   - **Default branch OK** for ops (unlike yolo). Optional issue branch: ask create `<N>-<slug>` vs stay on current/default when not already on a matching issue branch.

3. **Execute the ops work.** Follow the issue body / acceptance criteria (external CLIs, deploy consoles, flag tools). Confirm each risky step with the user. Record what ran in `issue<N>_status.md` (dated bullets under **What's done**).

4. **Hand off to close.** Follow `/iflow-close ops` (aliases `nopr` / `no-pr` also accepted by close). Do **not** duplicate archive / `gh issue close` logic here. Forward any `log "..."` text the user supplied.

## Constraints

- Off-path: never auto-dispatched by `/iflow`, `/iflow-build`, or `/iflow-close`.
- Never open a PR from this skill.
- Never force-push or delete branches.
- If unique unpushed product commits appear on the branch, **abort** and send the user to normal close — ops cannot skip review for those.
- When both `ops` and `yolo` labels are present, **ops wins** (announce the conflict).
