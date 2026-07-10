# Issue #466: CI failed on pytest on linux

Source: https://github.com/jepegit/cellpy/issues/466

## Original issue text

CI scheduled failed.

## **Agent suggestion:**


The test `test_legacy_v4_v5_currently_raise_typeerror_on_meta_extract` is failing because it expects a `TypeError` to be raised when loading legacy v4/v5 HDF5 files, but the code is no longer raising that exception.

### Root Cause

The test at line 137 in [`tests/test_cellpy_file_roundtrip.py`](https://github.com/jepegit/cellpy/blob/e984a9d6727054c9ac8ae5b70717eeb048547788/tests/test_cellpy_file_roundtrip.py#L137) expects:

```python
cell = cellreader.CellpyCell()
with pytest.raises(TypeError):
    cell.load(path, accept_old=True)
```

However, the actual behavior has changed—the code is now successfully loading these files without raising a `TypeError`.

### Solution

You have two options:

**Option 1: Update the test to reflect the new behavior**

If the v4/v5 files are now successfully loading, update the test to verify the successful load instead of expecting an exception:

```python
@pytest.mark.parametrize("label,filename", LEGACY_TYPE_ERROR)
def test_legacy_v4_v5_currently_raise_typeerror_on_meta_extract(label, filename):
    """Legacy v4/v5 files now load successfully (previously raised TypeError)."""
    path = HDF5_DIR / filename
    if not path.is_file():
        pytest.skip(f"missing legacy fixture: {path}")
    
    cell = load_cellpy_file(path, accept_old=True)
    # Add assertions to verify successful load
    assert cell.data.raw.shape[0] > 0
    assert cell.data.summary.shape[0] > 0
```

**Option 2: Fix the code to re-raise the TypeError**

If v4/v5 files should still raise `TypeError` during meta extraction, investigate the code path for `cell.load()` and `upgrade_from_to()` to ensure the exception is properly raised when handling these legacy formats.

The comment in the test suggests the issue is related to a missing `upgrade_from_to` call on meta extraction. Check the cellreader's load method to ensure it's being invoked for v4/v5 files.
