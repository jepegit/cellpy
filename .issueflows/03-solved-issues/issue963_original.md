# Issue #963: Documentation of batch API is confusing and not complete enough

Source: https://github.com/jepegit/cellpy/issues/963

## Original issue text

It is difficult to understand the facade concept vs. the Batch object itself. Most users are interested in what b can do (b = batch.load(something)). The docs should honor that better. It also looks like some methods are missing. For example, b.plot.
Also, make sure that the facade methods have a docstring so that users get help when pressing shift+tab in jupyter lab.
