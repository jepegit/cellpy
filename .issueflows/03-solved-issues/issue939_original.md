# Issue #939: from_cells silently drops values that are not cells

Source: https://github.com/jepegit/cellpy/issues/939

## Original issue text

`cellpy.collect.from_cells` does not validate the mapping it is given. A value that is not a `CellpyCell` — a `Path`, an `int`, anything — simply does not appear downstream: no exception, no warning, not even a log line.

Reproduced on **cellpy 2.1.3** (Python 3.13, clean `uv run --script` environment).

```python
# /// script
# requires-python = ">=3.13"
# dependencies = ["cellpy"]
# ///
import warnings
warnings.simplefilter("ignore")

from cellpy.collect import collect_summaries, from_cells
from cellpy.utils import example_data

cell = example_data.cellpy_file()

with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    batch = from_cells({
        "good": cell,
        "a_path": example_data.rate_file(),   # returns a Path, not a cell
        "an_int": 42,
    })
    print("warnings:", [str(w.message) for w in caught])

collection = collect_summaries(batch, columns=("discharge_capacity_gravimetric",))
print("3 entries in ->", collection.data["cell"].unique().to_list(), "out")
```

```text
warnings: []
3 entries in -> ['good'] out
```

## Why it is worth guarding

The failure surfaces to a *user* as a chart with fewer lines than they have cells, which reads as a data problem rather than a type error. Nothing points back at the call that dropped them.

The easy way in is real rather than hypothetical: `example_data.cellpy_file()` returns a **cell** while its sibling `example_data.rate_file()` returns a **path**. Adjacent functions, same naming family, asymmetric return types — and `from_cells` accepts the mistake without comment. Any code that builds the mapping from something dynamic (a file picker, a glob, a journal) can hit this and never know.

## Suggestion

Raise on a value that is not a `CellpyCell`, naming the offending keys — or, if silence is deliberate for some caller, at minimum a warning listing what was skipped. Silently narrowing a collection is unlikely to be what anyone meant.

## Context

Found while writing task-shaped guides for building on cellpy, in a repository where every documentation code block is executed by CI — this turned up as a print that did not match its expected output. Two independent agents given the same "load these cells" task hit it, and both reported the `rate_file()` / `cellpy_file()` asymmetry as the thing most likely to burn someone.

Notes: https://github.com/cellpy/cellpy-simple-gui/blob/main/CELLPY_PAINPOINTS.md (§34)
