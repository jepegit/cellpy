# Create original issue file from GitHub issue

Create an `*_original.md` file in `01-current-issues` from a GitHub issue.

## Input
The user will provide one of:
- an issue number (e.g. `123`)
- or a full GitHub issue URL

Use the text provided after this slash command as the issue reference.

## Steps

1. Resolve the issue reference from the user input.
   - If input is a full URL, extract `owner`, `repo`, and `issue number`.
   - If input is only an issue number:
     - derive `owner/repo` from `git remote` (prefer `origin`)
     - support both SSH and HTTPS remote URL formats
     - if parsing fails, ask the user for either full issue URL or `owner/repo`

2. Fetch issue data using GitHub CLI (explicit repo if needed):
   - title
   - body
   - url
   - number
   - and confirm resolved `owner/repo`

3. Archive existing issue files already in `01-current-issues` (except the current issue number).
   - Inspect issue groups by issue number (for example `issue121_*` belongs to issue 121).
   - Consider all files for that issue in `01-current-issues` (original + status/supplementary files) as one group to move together.
   - Decide destination:
     - move to `03-solved-issues` if the issue is done
     - move to `02-partly-solved-issues` if the issue is not done
  - Determine "done" status from an explicit checkbox marker in a status file:
    - done only if a status markdown file for that issue contains `- [x] Done` (case-insensitive match for `done`)
    - if the checkbox is missing, unchecked (`- [ ] Done`), unclear, or no status file exists, treat as not done
   - Never move files for the issue currently being created.

4. Create this file:
   - `01-current-issues/issue<number>_original.md`
5. File content format:
   ```markdown
   # Issue #<number>: <title>

   Source: <url>

   ## Original issue text

   <body exactly as in GitHub issue>
   ```
6. If `gh` is not authenticated or issue fetch fails:
   - stop and report the exact error
   - suggest `gh auth login`
7. If the target file already exists:
   - do not overwrite silently
   - ask whether to overwrite or keep both

## Output to user
Report:
- issue number fetched
- repository used (`owner/repo`)
- file path created
- archive moves performed (source -> destination, grouped by issue number)
- whether the operation succeeded

## Constraints
- Preserve the issue body exactly as returned by GitHub.
- Use UTF-8 markdown.
- Allowed file modifications for this command:
  - create/update the target `issue<number>_original.md`
  - move pre-existing issue files from `01-current-issues` to `02-partly-solved-issues` or `03-solved-issues` according to the archive rule above
- If `01-current-issues` does not exist, report an error and stop.
- If archive destination directories do not exist, report an error and stop.
- Prefer deterministic behavior: always state which repo was resolved before writing the file.

## Example invocations
- `/create-original-issue-file 123`
- `/create-original-issue-file https://github.com/jepegit/cellpy/issues/123`
- `/create-original-issue-file jepegit/cellpy#123`
