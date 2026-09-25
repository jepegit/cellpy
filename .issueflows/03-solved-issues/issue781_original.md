# Issue #781: L4 — live.py poll loop; retire processor.py

- GitHub: https://github.com/jepegit/cellpy/issues/781
- Epic: #783 (Epic L), Stage 3. Depends on: #164.

## Original description

Epic L of cellpy 2.2 (Stage 5). Design: live-incremental §5. Depends on L3 (#164).

- `utils/live.py`: replace the stub with
  `poll(cell_or_path, interval, on_update=, stop_when_complete=True)` calling `c.update()`.
- Delete `utils/processor.py` — fold its one real idea (thread-pool `cellpy.get`
  fan-out) into `batch.runner`'s existing executor path.
- Fix the `batch_core.py:180` `accessor_label.lstrip(self.accessor_pre)` →
  `removeprefix(...)` bug if it still exists post-batch-v3.
