# The fundamentals of cellpy
`cellpy` is implemented in Python and can be used as either a library within Python scripts,
or as a stand-alone application for analysing battery cell test data. Internally, `cellpy` utilises the rich
ecosystem of scientific tools available for Python. In particular, `cellpy` uses `pandas` DataFrames as the
“storage containers” for the collected data within the `cellpy` Data object. This offers full flexibility and
makes it easy for the user to apply advanced methods, analyses of or transformations to the data in addition
to the features implemented in `cellpy`.

The core of `cellpy` is the **CellpyCell** object (see [](#fig2)) that contains both the data
(stored in the **Data** object) as well as central methods required to read, process and store battery testing data.
The CellpyCell provides the appropriate interface and coordination of the resources needed, such as loading
configurations (*e.g* default reader, default raw-data location), selecting readers for different data formats and
exporters for saving the data.

```{figure} figures/CellpyCell.jpg
:name: fig2
:alt: cellpycell-object
:align: center

Illustration of the core object within ``cellpy``, the **CellpyCell** 😎.
```


![Illustration of the core object within ``cellpy``, the **CellpyCell**.\label{fig:2}](..\figures\CellpyCell.jpg)

The **CellpyCell Data** object stores both the battery test data as well as the corresponding metadata
(see \autoref{fig:3}). In addition to the central DataFrame containing the raw data (*raw*),
the DataFrames *steps* and *summary* provide step- (*e.g.*, maximum current, mean voltage,
type-of-step *vs.* step number) and cycle-based (*e.g.*, gravimetric charge capacity, coulombic
efficiency, C-rates *vs.* cycle number) summaries and statistics respectively.

![Summary of the types of contents in a **CellpyCell Data** object.\label{fig:3}](Figures/CellpyData.jpg)

The most common data processing routines, such as extraction of charge/discharge voltage curves in different
formats or selecting data for specified step-types, are implemented as methods on the CellpyCell object. In
addition, the `cellpy` library also consists of a rich set of utilities (\autoref{fig:4}) that can be used for
further processing the data, both individually and within batch routines. Utility functions include *e.g.*,
ICA tools, assisting in creating dQ/dV graphs (employing different data-smoothing algorithms), or tools for
OCV relaxation analysis.

![The `cellpy` library contains multiple utilities that assists in data analysis.
A utility can work on (A) a single **CellpyCell** object, or (B) a set of CellpyCell
objects such as the Batch utility that helps the user in automating
and comparing results from many data sets.\label{fig:4}](Figures/Cellpy-Utils.jpg)

The `cellpy`-file format (usually stored in HDF5 format) contains all the data contained in
the Data object together with additional relevant metadata, including information about the file version.

(Ref: [paper.md](https://github.com/jepegit/cellpy/tree/master/paper))
