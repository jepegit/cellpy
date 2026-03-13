# Issue #307: Interpolation in get_cap() removes steps (taper, multiple charge/discharge)

Source: https://github.com/jepegit/cellpy/issues/307

## Original issue text

Interpolation in the get_cap()-function removes steps when there are multiple charge or discharge steps in one cycle, e.g. taper steps. In these cases, the interpolation also produces some artefacts in the transition from charge to discharge (when the curve "turns"). This also affects the batchcollectors, which use get_cap() with interpolation turned on as default.

- **cellpy version**: 1.0.1b5
- **Python version**: 3.11
- **Operating System**: Windows 11

**Steps to reproduce:** Run `cellpy.utils.collectors.BatchCyclesCollector()` (which has interpolation turned on as default), for any batch that includes cells with taper steps.

**Milestone:** v1.0.3
