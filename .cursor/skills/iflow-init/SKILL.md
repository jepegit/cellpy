---
name: iflow-init
description: >-
  Run the /iflow-init workflow: resolve GitHub issue reference, fetch body
  and comments with gh, triage the comments via the iflow-comments
  skill, write issue<number>_original.md under
  .issueflows/01-current-issues/, and archive other
  current issues by done status.
disable-model-invocation: true
---

# issue-flow — issue init (`/iflow-init`)

Follow this skill when the user wants to **capture a GitHub issue locally**.

## When to use

- The user runs `/iflow-init`, mentions **issue-init**, or asks to pull an issue into `.issueflows/01-current-issues/`.
- You need a repeatable checklist without opening the command file.

## Instructions

> **CLI fast path (optional).** If the `issue-flow` CLI is on `PATH`, two
> mechanical steps have a deterministic shortcut:
> - **Fetch + write (steps 3 & 5):** `issue-flow agent capture <N>` (use `--repo owner/repo` to override the resolved remote, `--force` to overwrite). It writes the `## Original issue text` body deterministically and prints the comments payload — you still triage comments (step 3a) and add the curated section yourself.
> - **Archive (step 4):** `issue-flow agent sweep --except <N>` (add `--dry-run` to preview).
>
> The CLI is optional: if it is missing or errors, fall back to the manual
> instructions below. (`issue-flow` is only present when the user installed it,
> e.g. `uv tool install issue-flow`.)

1. **Folders** — Ensure `.issueflows/00-tools/`, `.issueflows/01-current-issues/`, `.issueflows/02-partly-solved-issues/`, and `.issueflows/03-solved-issues/` exist (create only if the user allows; never delete issue markdown).

2. **Resolve the reference**
   - **URL** — Parse `owner`, `repo`, issue number.
   - **Number only** — Use `git remote get-url origin` (HTTPS or SSH) to derive `owner/repo`. If parsing fails, ask for a full URL or `owner/repo`.
   - **Empty / whitespace** — Run `git branch --show-current`. If empty or `main`/`master` (case-insensitive), **stop** and ask for a number, URL, or `owner/repo/#n`. If the branch is an **issue-style branch** matching `^\d+-.+`, ask: "You have not provided an issue reference. Should I use issue #NN from the current branch `<branchname>`?" Do not proceed without a clear yes/no.
   - **Archived-issue guard** — Before writing, check `.issueflows/02-partly-solved-issues/` and `.issueflows/03-solved-issues/` for existing `issue<n>_*` files. If the issue is already archived, warn and require a second explicit confirmation before re-opening it in `.issueflows/01-current-issues/`.

3. **Fetch** — `gh issue view <n> --repo owner/repo --json title,body,url,number,comments`. The `comments` field returns an array of `{author.login, body, createdAt, ...}` that step 3a consumes. On failure, report the error and suggest `gh auth login`. After confirming `owner/repo`, change the chat/agent tab title to reflect the issue topic on the form "Issue <issue number> <short description of issue>" (e.g. "Issue 74 cell info").

3a. **Triage comments** (skip if `comments` is empty). Follow the [`iflow-comments`](../iflow-comments/SKILL.md) skill. Summary of rules:
   - Process comments chronologically; **later comments win conflicts** with earlier ones.
   - Sort points into three buckets: **Additional tasks**, **Clarifications / constraints**, **Superseded / retracted**.
   - Collapse duplicates; drop chit-chat, emoji-only, "LGTM" and bot messages.
   - Paraphrase — this section is an interpretive summary, not a verbatim dump.
   - If all comments are noise, skip the curated section entirely.
   - On open disagreement with no clear winner, log it under *Clarifications* rather than picking a side.

3.5 **Branch status preflight** (report only) — Run `git fetch --prune`. Report current branch, clean/dirty working tree, and ahead/behind counts vs `origin/<default>` (detect default via `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`, else `git symbolic-ref --quiet --short refs/remotes/origin/HEAD`, else `main`). If the current branch matches `^(\d+)-.+` and files for that issue already live in `.issueflows/02-partly-solved-issues/` or `.issueflows/03-solved-issues/`, note that the branch looks stale. Never delete or move anything at this step.

4. **Archive** — In `.issueflows/01-current-issues/`, group files by issue number (`issue121_*`). For each group **other than** the issue being created: move the whole group to `.issueflows/03-solved-issues/` only if a status file for that issue contains a checked **Done** line matching `- [x] Done` (case-insensitive on "done"). Otherwise move to `.issueflows/02-partly-solved-issues/`. If no status file or checkbox is unclear, treat as **not done**.

5. **Write** — Create `.issueflows/01-current-issues/issue<number>_original.md` with:

   ```markdown
   # Issue #<number>: <title>

   Source: <url>

   ## Original issue text

   <body exactly as returned by GitHub>

   ## Comments (curated summary)

   - **Additional tasks**: <bullets distilled from comments that add real work>
   - **Clarifications / constraints**: <bullets the agent should honour>
   - **Superseded / retracted**: <earlier points later contradicted or walked back>

   _Note: this section is an interpretive summary of the comment thread, not a verbatim dump. Source comments: <count>, last comment by @<login> on <date>._
   ```

   Preserve the body **text** faithfully as returned by GitHub — don't paraphrase or edit it, but don't waste effort on trailing newlines or CRLF vs LF either (no second-pass byte-diffing). The `## Comments (curated summary)` section is **optional** — include it only when step 3a produced at least one bullet, and drop any of the three bullet groups that have no content.

6. **Conflicts** — If `issue<number>_original.md` already exists, do not overwrite silently; ask the user.

7. **Report** — Summarize number, `owner/repo`, branch inference (if used), path written, comment triage counts (fetched vs surfaced vs superseded, or "section omitted" when skipped), archive moves (source → destination), and success or failure.

## Constraints

- Allowed file operations: create/update the target `*_original.md`, and move pre-existing issue groups per the archive rules. Do not modify unrelated project files.
- Use UTF-8 for markdown output.
