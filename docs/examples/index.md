---
icon: material/school
---

# Examples & tutorials

Here we provide a few basic examples to get you started with cellpy - from reading the data to creating some basic plots. These notebooks, the used datafiles and a little more can be found in the [examples
folder](https://github.com/jepegit/cellpy/tree/master/examples) in the cellpy GitHub repository.

!!! warning
    This is a release candidate and notebooks used for the examples
    have not been thoroughly checked yet.

[Contributions](../contributing/contributing.md) to more example notebooks are of course very welcome!

- [Loading data](01_loading_data.md)
- [Other file formats](06_loading_different_formats.md)
- [Writing a custom loader](07_custom_loaders.md)
- [First look at your data](02_Initial_data_inspection.md)
- [Capacity vs voltage](03_capacity_vs_voltage.md)
- [Incremental capacity analysis](04_incremental_capacity_analysis.md)
- [GITT](05_GITT.md)
- [Batch processing](batch_utility/cellpy_batch_processing_docs.md)
- [Templates](templates/tutorial_templates.md)

## About these pages

The pages here are rendered from the notebooks in
[`docs/examples/`](https://github.com/jepegit/cellpy/tree/master/docs/examples)
and show the outputs their authors saved. Interactive plotly figures are
replaced by their static renderings — grab the `.ipynb` from the repository if
you want to pan and zoom.

To re-render after changing a notebook:

```shell
uv run --group docs python dev/render_example_notebooks.py
```
