---
icon: material/school
---

# Examples & tutorials

Here we provide a few basic examples to get you started with cellpy - from reading the data to creating some basic plots. These notebooks, the used datafiles and a little more can be found in the [examples
folder](https://github.com/jepegit/cellpy/tree/master/examples) in the cellpy GitHub repository.

!!! note
    Most of these notebooks were originally written for cellpy 1.x. The
    [Incremental capacity analysis](04_incremental_capacity_analysis.md) and
    [Batch processing](batch_utility/cellpy_batch_processing.md) pages have been
    brought up to the 2.1 API and re-executed; the others may still show 1.x idioms.
    If something looks off, [let us know](https://github.com/jepegit/cellpy/issues).

[Contributions](../contributing/contributing.md) to more example notebooks are of course very welcome!

- [Loading data](01_loading_data.md)
- [Other file formats](06_loading_different_formats.md)
- [BatMo BDF files](08_batmo_bdf.md)
- [PEC data](09_loading_pec_data.md)
- [Writing a custom loader](07_custom_loaders.md)
- [First look at your data](02_Initial_data_inspection.md)
- [Capacity vs voltage](03_capacity_vs_voltage.md)
- [Incremental capacity analysis](04_incremental_capacity_analysis.md)
- [GITT](05_GITT.md)
- [Batch processing](batch_utility/cellpy_batch_processing.md)
- [Templates](templates/tutorial_templates.md)

## About these pages

Every page here is rendered from the Jupyter notebook of the same name in the
[`examples/`](https://github.com/jepegit/cellpy/tree/master/examples) folder,
which is the single maintained copy — the one you download above. The pages show
the outputs the notebook authors saved; interactive plotly figures are replaced
by their static renderings, so grab the `.ipynb` if you want to pan and zoom.

To re-render after changing a Jupyter notebook:

```shell
uv run --group docs python dev/render_example_notebooks.py
```
