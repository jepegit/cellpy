# Issue #949: b.plot not showing ir

Source: https://github.com/jepegit/cellpy/issues/949

## Original issue text

`b.plot(rate=True, ir=True, direction="discharge")`

does not display the IR. The plot looks fine otherwise, and other optional parameters I know of works.

## Comments (curated summary)

- **Additional tasks**:
  - Re-check both `direction="charge"` and `direction="discharge"` — collaborator
    still sees no IR panel on cellpy 2.1.4 (after the first pick/fallback shipped).
- **Clarifications / constraints**:
  - Report is on 2.1.4, which already contains the `_select_ir_column` warn/fallback.

_Note: this section is an interpretive summary of the comment thread, not a verbatim dump. Source comments: 1, last comment by @inger-emma on 2026-09-18._
