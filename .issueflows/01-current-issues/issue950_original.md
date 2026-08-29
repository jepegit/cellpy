# Issue #950: b.mark_as_bad and  b.drop_cells_marked_bad() not working

Source: https://github.com/jepegit/cellpy/issues/950

## Original issue text

Running:
`b.mark_as_bad("20260515_sig002_04_fccc")
b.mark_as_bad("20260515_sig002_06_fccc")
b.mark_as_bad("20260515_sig002_10_fccc")
b.drop_cells_marked_bad()`
and then
`b.combine_summaries()` or `b.plot()`
creates this error:

---------------------------------------------------------------------------
KeyError                                  Traceback (most recent call last)
Cell In[32], [line 2](vscode-notebook-cell:?execution_count=32&line=2)
      1 # Plot the charge capacity and the C.E. (and resistance and rate) vs. cycle number (standard plot)
----> [2](vscode-notebook-cell:?execution_count=32&line=2) b.plot(rate=True, ir=True, direction="discharge", ce_range=[0,130])

File ~\AppData\Local\miniconda3\envs\cellpy213\Lib\site-packages\cellpy\batch\facade.py:354, in Batch.plot(self, backend, show, **kwargs)
    350 def plot(self, backend: str | None = None, show: bool = False, **kwargs) -> Any:
    351     from cellpy.plotting.batch_summary import batch_summary_plot
    353     return batch_summary_plot(
--> [354](https://file+.vscode-resource.vscode-cdn.net/c%3A/Users/IFE12959/cellpy_data/notebooks/Signal-2/2026_08_25_Analysis_213/~/AppData/Local/miniconda3/envs/cellpy213/Lib/site-packages/cellpy/batch/facade.py:354)         _LegacyExperimentAdapter(self.journal, self._store),
    355         backend=backend,
    356         show=show,
    357         **kwargs,
    358     )

File ~\AppData\Local\miniconda3\envs\cellpy213\Lib\site-packages\cellpy\batch\facade.py:410, in _LegacyExperimentAdapter.__init__(self, journal, store)
    408 per_cell: dict[str, Any] = {}
    409 cycle_col = get_headers_summary().cycle_index
--> [410](https://file+.vscode-resource.vscode-cdn.net/c%3A/Users/IFE12959/cellpy_data/notebooks/Signal-2/2026_08_25_Analysis_213/~/AppData/Local/miniconda3/envs/cellpy213/Lib/site-packages/cellpy/batch/facade.py:410) for label, cell in store.items():
    411     summary = getattr(getattr(cell, "data", None), "summary", None)
    412     if summary is None:

File <frozen _collections_abc>:883, in ItemsView.__iter__(self)
    881 def __iter__(self):
...
     47     self._cache[label] = cell
     48     return cell
---> [49](https://file+.vscode-resource.vscode-cdn.net/c%3A/Users/IFE12959/cellpy_data/notebooks/Signal-2/2026_08_25_Analysis_213/~/AppData/Local/miniconda3/envs/cellpy213/Lib/site-packages/cellpy/batch/store.py:49) raise KeyError(label)

KeyError: '20260515_sig002_04_fccc'
