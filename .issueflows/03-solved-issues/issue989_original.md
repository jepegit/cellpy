# Issue #989: Check capacity calculation behavior

Source: https://github.com/jepegit/cellpy/issues/989

## Original issue text

I have some data which directly imported into cellpy 1.x produced this plot (the problem existed both for charge and discharge):

<img width="1905" height="501" alt="Image" src="https://github.com/user-attachments/assets/01b53418-3f4c-408c-960a-2a49014d07c3" />

In cellpy 2.1.3.post 2, I get this:

<img width="897" height="328" alt="Image" src="https://github.com/user-attachments/assets/aba3b5c5-63ea-4345-9669-ef096492f787" />

The initial double capacity was caused by forgetting to reset the capacity in a given step where it should have been reset. Somehow cellpy 2.x handles this automatically. Is this documented? Additionally, a message indicating that this correction was performed would be nice to have.

## Comments (curated summary)

- **Additional tasks**: Issue re-opened — the capacity doubling is back. Most
  likely the user loaded already pre-processed data (`.cellpy` files) instead of
  the raw data. Investigate which of these holds: (1) the per-cycle reset to 0
  is not implemented / `normalize_reset_granularity` does not work on that
  path, (2) `normalize_reset_granularity` is not run for `.cellpy` loads (maybe
  gated by a config setting), or (3) the cycles in the file already start at
  zero and the doubling has another cause.
- **Clarifications / constraints**: Reproduction file (local, not in repo):
  `local/data/20260316_nor108_01_MLP01.cellpy` (Inger Emma's data). The first
  round (closed 2026-09-07) added the `UserWarning` + docs for raw loads; see
  `.issueflows/03-solved-issues/issue989_status.md`.

_Note: this section is an interpretive summary of the comment thread, not a verbatim dump. Source comments: 1, last comment by @jepegit on 2026-09-10._
