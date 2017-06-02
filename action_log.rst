==========
Action log
==========

2017.05.23
==========

Div
---

* add dev_data to .gitignore (done)
* work on individual rst-files (atomisation) (prepared by jepe 05.17)

Naming
------

Rename tests to datasets
........................

(done by jepe 28.05.17)
tests -> datasets

Create property for picking dataset
...................................

(done by jepe 28.05.17)

.. example::
    cellpy.dataset = dataset[0]

    @property
    def dataset(self,...i=None):
        i = self.dataset_number
        return cellpy.datasets[i]


.. todo::
    test it

Make pickers for getting the DataFrames
.......................................

pick_normal_data : self.tests[0].dfdata, self.dataset.dfdata (check)
pick_summary_data: dfsummary
pick_xxx : get the dataframe

get_xxx: helpers for looking and getting stuff

Make putters for setting back the DataFrames
............................................

put_xxx: put dataframes back

Rename the save, load, etc
..........................

save: hdf5
load_cellpy -> load

export: others
load_raw -> import_raw

Scheme
------

Utils "similar" way

- make object
(- set properties)
- feed object
(- set properties)
- run object
- create reports, figures
- export data, etc
- jupyter notebook compatible

Version control
---------------

work with few files (AU)
