(utils-batch)=

# Using the batch utilities

The steps given in this tutorial describes how to use the new version of the
batch utility. The part presented here is chosen such that it resembles how
the old utility worked. However, under the hood, the new batch utility is very
different from the old. A more detailed guide will come soon.

So, with that being said, here is the promised description.

## Starting (setting things up)

### A database

Currently, the only supported "database" is Excel (yes, I am not kidding). So,
there is definitely room for improvements if you would like to contribute to
the code-base.

The Excel work-book must contain a page called `db_table`. And the top row
of this page should consist of the correct headers as defined in your cellpy
config file. You then have to give an identification name for the cells you
would like to investigate in one of the columns labelled as batch columns (
typically "b01", "b02", ..., "b07"). You can find an example of such an Excel
work-book in the test-data.

### A tool for running the job

Jupyter Notebooks is the recommended "tool" for running the cellpy batch
feature. The first step is to import the `cellpy.utils.batch.Batch`
class from `cellpy`.  The `Batch` class is a utility class for
pipe-lining batch processing of cell cycle data.

```python
from cellpy.utils import batch, plotutils
from cellpy import prms
from cellpy import prmreader
```

The next step is to initialize it:

```python
project = "experiment_set_01"
name = "new_exiting_chemistry"  # the name you set in the database
batch_col = "b01"
b = batch.init(name, project, batch_col=batch_col)
```

and set some parameters that `Batch` needs:

```python
# setting additional parameters if the defaults are not to your liking:
b.experiment.export_raw = True
b.experiment.export_cycles = True
b.experiment.export_ica = True
b.experiment.all_in_memory = True  # store all data in memory, defaults to False
b.save_cellpy_file = True

b.force_raw_file = False
b.force_cellpy_file = True
```

## Extracting meta-data

The next step is to extract and collect the information needed from your data-base into a DataFrame,
and create an appropriate folder structure (`outdir/project_name/batch_name/raw_data`)

```python
# load info from your db and write the journal pages
b.create_journal()
b.paginate()
```

## Processing data

To run the processing, you should then use the convenience function `update`. This function
loads all your data-files and saves csv-files of the results.

```python
b.update()
```

The next step is to create some summary csv-files (*e.g.* containing charge capacities *vs.* cycle number for
all your data-files) and plot the results.

```python
b.make_summaries()
b.plot_summaries()
```

Now it is time to relax and maybe drink a cup of coffee.

## Further investigations and analyses

There are several paths to go from here. I recommend looking at the raw data
for the different cells briefly to check if everything looks sensible.
You can get the names of the different datasets (cells) by issuing:

```python
b.experiment.cell_names
```

You can get the CellpyCell-object for a given cell by writing:

```python
cell = b.experiment.data[name_of_cell]
plotutils.raw_plot(my_cell)
```

If you want to investigate further, you can either use one of the available
analysis-engines (they work on batch objects processing all the cells at once)
or you can continue on a single cell basis (latter is currently recommended).

Another tip is to make new Notebooks for each type of "investigation" you would
like to perform. You can load the info-df-file you created in the initial steps,
or you could load the individual cellpy-files (if you did not turn off
automatic saving to cellpy-format).

You should be able to find examples of processing either by downloading the
examples or by looking in the [repo.](https://github.com/jepegit/cellpy)
