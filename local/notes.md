 ### TODO 0.4.2
-> need to update conf file (arbin to arbin_res)
 ### TODO 0.4.2
-> notebook life concatenate_summaries crashes when cells have no data.

 ### TODO 1.0.0
Implement testing for external files (e.g. ssh://..).

### Note
```python

# When implementing new features, first write a test that will raise
# an NotImplementedError. Then implement the feature and remove the
# NotImplementedError. This way we will not forget to implement the
# feature.

# (this example will raise an error now since it is now implemented)
def test_from_raw_external(cellpy_data_instance, parameters):
    external_raw_file = f"ssh://jepe@my.server.no/home/jepe@ad.ife.no/data/{pathlib.Path(parameters.res_file_path).name}"
    with pytest.raises(NotImplementedError):
        cellpy_data_instance.from_raw(external_raw_file)
```


 ### TODO warnings
-> cellpy/cellpy/utils/batch_tools/batch_journals.py:383: UserWarning:
  invalid decimal literal (<unknown>, line 1)
 ### TODO warnings
 -> cellpy/cellpy/cellpy/readers/dbreader.py:355: UserWarning:
  your database is missing the following key: experiment_type
 ### TODO warnings
 -> cellpy/cellpy/readers/dbreader.py:355: UserWarning:
  your database is missing the following key: nominal_capacity
 ### TODO warnings
 -> tests/test_batch.py::test_cycling_summary_plotter:
  cellpy/cellpy/utils/batch_tools/engines.py:37:
  DeprecationWarning: This utility function will be seriously changed soon and possibly removed
  cellpy/cellpy/utils/batch_tools/batch_plotters.py:690:
  DeprecationWarning: This utility function will be seriously changed soon and possibly removed
 ### TODO warnings
 -> tests/test_biologics.py::test_set_instrument:
  cellpy/cellpy/readers/instruments/biologics_mpr.py:342:
  DeprecationWarning: The binary mode of fromstring is deprecated,
  as it behaves surprisingly on unicode inputs. Use frombuffer instead
 ### TODO warnings
 -> test_neware.py::test_get_neware_from_h5:
  cellpy/cellpy/readers/cellreader.py:1828: UserWarning: no fid_table - you should update your cellpy-file

### TODO Error
-> File c:\scripting\cellpy\.venv\Lib\site-packages\plotly\io\_renderers.py:425, in show(fig, renderer, validate, **kwargs)
    420     raise ValueError(
    421         "Mime type rendering requires ipython but it is not installed"
    422     )
    424 if not nbformat or Version(nbformat.__version__) < Version("4.2.0"):
--> 425     raise ValueError(
    426         "Mime type rendering requires nbformat>=4.2.0 but it is not installed"
    427     )
    429 display_jupyter_version_warnings()
    431 ipython_display.display(bundle, raw=True)

### TODO Batch stuff

- need to fix recalc
- need to fix yanking


## DIV

Seems not to work (so removed it from .bash_profile):

```bash
# >>> mamba initialize >>>
# !! Contents within this block are managed by 'micromamba shell init' !!
export MAMBA_EXE="/c/Users/jepe/.local/bin/micromamba";
export MAMBA_ROOT_PREFIX="/c/Users/jepe/micromamba";
eval "$("$MAMBA_EXE" shell hook --shell bash --root-prefix "$MAMBA_ROOT_PREFIX")"
# <<< mamba initialize <<<
```
