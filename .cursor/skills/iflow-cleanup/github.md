# Cleanup — Phase B: GitHub remote audit

Runs only when Phase B is enabled (`include github` token, and no `no github` / `local only` token).

Prefer the CLI fast path; fall back to manual `git`/`gh` when the CLI is missing.

   - **CLI:** `issue-flow agent branches --json -C <project_root>` (add `--no-fetch` only if `git fetch --prune` just ran). Payload buckets: `deletable`, `unique_work`, `skipped`.
   - **Manual fallback:** `git fetch --prune`; list `refs/remotes/origin/*` (skip `HEAD` and the default); for each tip run `git cherry origin/<default> origin/<branch>` (`+` = unique); `git log --oneline origin/<default>..origin/<branch>` (cap ~20) + `git diff --shortstat`; `gh pr list --repo <owner/repo> --state all --head <branch> --json number,title,state,url,mergedAt`. Treat open-PR heads as unique work (never deletable). Protected branches (when `gh api …/branches/<name>` reports `protected: true`) go to skipped.
   - **Report** the three buckets. For unique-work branches, summarise commit subjects (and open PR titles/URLs) in prose for the user.
   - **Second consolidated confirm** (never folded into Phase A's yes): list every proposed action, then ask once:
     - Optional: for each **deletable** name, `git push origin --delete <branch>` (or `gh api -X DELETE repos/<owner>/<repo>/git/refs/heads/<branch>`). Never `--force`. Never delete the default. On push failure (e.g. protection), report and continue.
     - Optional: create a findings issue with `gh issue create --repo <owner/repo>` after showing the draft title/body (deletable list + unique-work summaries). Suggested title: `chore: remote branch audit (<YYYY-MM-DD>)`. Create only on yes.

**Multi-line GitHub text (PowerShell-safe).** Bash `<<'EOF'` heredocs fail in Windows PowerShell (`Missing file specification after redirection operator`). Write the text to a file and pass that file:

- `gh issue create`, `gh issue edit`, and `gh pr create` take `--body-file <path>`.
- `git commit` takes `-F <path>`.

```powershell
@'
line one

line two
'@ | Set-Content -Encoding utf8 body.md
gh issue create --repo owner/repo --title "title" --body-file body.md
```

Bash accepts the same `--body-file` / `-F` flags. Use that pattern for every multi-line body.

   - Phase B is **read-only until that second confirm**. Declining leaves remotes untouched.
