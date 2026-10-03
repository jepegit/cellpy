# Issue #782: L5 — batch live refresh

- GitHub: https://github.com/jepegit/cellpy/issues/782
- Epic: #783 (Epic L), Stage 3. Depends on: #164.

## Original description

Epic L of cellpy 2.2 (Stage 5). Design: live-incremental §6. Depends on L3 (#164).

`b.update(live=True)` iterates the journal cells calling `c.update()`;
`b.poll(interval=, until=)` wraps the loop and re-runs the collectors/report
each tick. Rides entirely on the cell-level `update()` — no new core.
