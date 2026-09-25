# Issue #164: Allow for c.update()

- GitHub: https://github.com/jepegit/cellpy/issues/164
- Labels: enhancement, v2, cellpy2-stage4, cellpy2-stage5
- Epic: #783 (Epic L, live/incremental), Stage 2. Depends on: #780.

## Original description

After loading a file (e.g. a cellpyfile), it should be possible to update it by

```python
c = cellpy.get("cellpyfile.h5)
# the cellpy file contains the paths to the original raw files
c.update()
# only the new data will be loaded and processed
```

To achieve this, cellpy will need to have an easy way to find the last loaded
data and load from that. And update summaries from starting from the first new
step (or the last old if it is not complete) etc. This means that a smart way
of lookup and merging if several raw files are used is needed.
