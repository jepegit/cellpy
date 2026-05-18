---
name: issueflow-issue-comments
description: >-
  Triage a GitHub issue's comment thread into a curated, bucketed summary
  (additional tasks, clarifications, superseded) for inclusion in
  issue<N>_original.md. Invoked by /issue-init; also reusable when re-triaging
  comments later in an issue's lifecycle.
disable-model-invocation: true
---

# issue-flow — issue comments triage

Follow this skill when you need to turn a GitHub issue's comment thread into a short, decision-useful summary that lives next to the original issue body under `.issueflows/01-current-issues/issue<N>_original.md`.

It is the playbook that `/issue-init` (and the `issueflow-issue-init` skill) delegate to for anything beyond fetching raw comments.

## When to use

- `/issue-init` just fetched an issue with a non-empty `comments` array and needs to write the `## Comments (curated summary)` section.
- You are re-running triage on an already-captured issue because new comments have arrived (the issue body must stay byte-for-byte; only the curated section is rewritten).
- Any workflow that needs to understand "what does the comment thread actually ask us to do?" without pasting the raw thread into a file.

## Inputs

A JSON array of comments as returned by:

```
gh issue view <N> --repo owner/repo --json comments -q .comments
```

Each element has at least:

- `author.login` — commenter handle
- `body` — markdown text
- `createdAt` — ISO timestamp

If you only have raw comment text, ask for the structured form (author + date matter for tie-breaking and for the footer).

## Triage rules

1. **Chronological precedence.** Walk the comments oldest → newest. If a later comment contradicts or walks back an earlier point, the earlier point moves to **Superseded / retracted** and the later one takes its place in the appropriate bucket.

2. **Three buckets, pick exactly one per surviving point.**
   - **Additional tasks** — new, concrete work that is not already in the issue body. Phrase as imperatives ("also update X", "add Y to Z"). If the point is vague ("maybe do something about caching"), either sharpen it into a task or drop it.
   - **Clarifications / constraints** — guidance on *how* to do the existing work: scope boundaries, non-goals, must-keep behaviors, stylistic or architectural preferences, acceptance criteria. Useful phrase: "when doing X, make sure Y".
   - **Superseded / retracted** — earlier tasks, preferences, or decisions that a later comment explicitly or implicitly walked back. Keep these visible (don't silently delete them) so the agent doesn't redo retracted work.

3. **Drop the noise.** Do not include:
   - Bot comments (CI, coverage bots, auto-assign bots, etc.).
   - Pure chit-chat, "LGTM", "+1", emoji-only reactions.
   - Status pings ("any update?") without new content.
   - Comments that only quote earlier ones without adding anything.

4. **Collapse duplicates.** If two commenters make the same point, record it once.

5. **Paraphrase; quote sparingly.** Short direct quotes are fine when exact wording matters (e.g. a feature name, an error message). Otherwise rewrite in your own words so the summary is scannable.

6. **Handle open disagreement honestly.** If two authors openly disagree and no later comment resolves it, record the disagreement under *Clarifications* (for example: "author A prefers option X, author B prefers option Y — no resolution in thread"). Do not guess a winner.

7. **Respect maintainer authority when obvious.** If the repo owner or a maintainer explicitly overrides an earlier suggestion, treat that as the winning position and move the overridden suggestion to *Superseded*.

## Output contract

Write exactly this block into `issue<N>_original.md`, immediately after the `## Original issue text` section:

```markdown
## Comments (curated summary)

- **Additional tasks**: <bullets distilled from comments that add real work>
- **Clarifications / constraints**: <bullets the agent should honour>
- **Superseded / retracted**: <earlier points later contradicted or walked back>

_Note: this section is an interpretive summary of the comment thread, not a verbatim dump. Source comments: <count>, last comment by @<login> on <date>._
```

Formatting rules:

- Each bucket's bullet is itself a list if there is more than one item — nest concrete bullets under the bold label.
- **Drop any bucket that is empty** — do not leave `- **Additional tasks**: ` with no content.
- **Always keep the `_Note: ..._` footer** when the section exists. Use the total `comments` length for `<count>` and the `author.login` + date of the most recent non-dropped comment for `@<login>` / `<date>`.
- Use UTF-8 markdown. No leading/trailing blank lines inside the section beyond what's shown.

## Edge cases

- **Zero comments** — skip the whole section. Do not write an empty `## Comments (curated summary)` header.
- **All comments are noise** (bot-only, pure chit-chat, emoji) — skip the whole section. Note this in the command's final report ("N comments fetched, all filtered as noise — section omitted").
- **Every surviving point lands in a single bucket** — that's fine; just emit that one bucket.
- **Multi-author thread with heated disagreement** — log the disagreement under *Clarifications*, do not invent a resolution.
- **Comments reference external PRs, gists, or linked issues** — keep the reference (shortened URL or `owner/repo#N`) in the bullet, but do not fetch the linked content; it's out of scope for this skill.
- **Comments include code blocks the agent will need later** — summarize the intent in the bullet and mention that the full snippet is in the linked comment; do not paste large blocks into the summary.

## Constraints

- This skill only writes into the `## Comments (curated summary)` section of `issue<N>_original.md`. It never touches the issue body, the status file, or the plan file.
- It never calls `gh` itself — it expects the caller (`/issue-init` or similar) to provide the comments JSON.
- It never talks to the network beyond what the caller has already fetched.
