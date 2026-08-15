# Issue #916: Iterative fixes: add progress bars for batch

Source: https://github.com/jepegit/cellpy/issues/916

## Original issue text

Interactive `/iflow-fix` session. Individual fixes are recorded in the status markdown and landed together via `/iflow-close`.

Hook already exists: `batch.runner.run(..., on_progress=)`. The runner never imports tqdm or prints. This session wires visible progress for `batch.load` / first-load waits (copy + parse + save).
