# Issue #971: Bug in template or cellpy for ica

Source: https://github.com/jepegit/cellpy/issues/971

## Original issue text

This cell in the template (04 ica):
```python
# ica.dqdv returns one long frame with the columns
# cycle | direction | voltage | capacity | dqdv
ica_1 = ica.dqdv(cycle, voltage_resolution=0.01)
ica_2 = ica.dqdv(cycle, voltage_resolution=0.05)
ica_1.head()
```

Results in this error:
```python
---------------------------------------------------------------------------
ValueError                                Traceback (most recent call last)
Cell In[8], line 3
      1 # ica.dqdv returns one long frame with the columns
      2 # cycle | direction | voltage | capacity | dqdv
----> 3 ica_1 = ica.dqdv(cycle, voltage_resolution=0.01)
      4 ica_2 = ica.dqdv(cycle, voltage_resolution=0.05)
      5 ica_1.head()

File [C:\scripting\cellpy-workspace\cellpy\cellpy\ica.py:811](file:///C:/scripting/cellpy-workspace/cellpy/cellpy/ica.py#line=810), in dqdv(source, cycles, direction, options, strict, cycle_mode, number_of_points, **overrides)
    773 def dqdv(
    774     source,
    775     cycles=None,
   (...)    782     **overrides,
    783 ) -> pd.DataFrame:
    784     """Incremental capacity analysis: dQ/dV against voltage.
    785 
    786     Args:
   (...)    809         >>> charge = frame[frame.direction == "charge"]
    810     """
--> 811     return _transform_all(
    812         source,
    813         "dqdv",
    814         cycles,
    815         direction,
    816         options,
    817         strict,
    818         cycle_mode,
    819         number_of_points,
    820         overrides,
    821     )

File [C:\scripting\cellpy-workspace\cellpy\cellpy\ica.py:692](file:///C:/scripting/cellpy-workspace/cellpy/cellpy/ica.py#line=691), in _transform_all(source, derivative, cycles, direction, options, strict, cycle_mode, number_of_points, overrides)
    689 if overrides:
    690     options = options.replace(**overrides)
--> 692 half_cycles, resolved_mode = _resolve_source(
    693     source, cycles, direction, cycle_mode, number_of_points
    694 )
    696 x_name, y_name = (
    697     (ICA_COLS.voltage, ICA_COLS.dqdv)
    698     if derivative == "dqdv"
    699     else (ICA_COLS.capacity, ICA_COLS.dvdq)
    700 )
    701 partner_name = ICA_COLS.capacity if derivative == "dqdv" else ICA_COLS.voltage

File [C:\scripting\cellpy-workspace\cellpy\cellpy\ica.py:640](file:///C:/scripting/cellpy-workspace/cellpy/cellpy/ica.py#line=639), in _resolve_source(source, cycles, direction, cycle_mode, number_of_points)
    637     return list(_half_cycles_from_frame(frame, mode, direction)), mode
    639 if isinstance(source, pd.DataFrame):
--> 640     return list(_half_cycles_from_frame(source, cycle_mode, direction)), cycle_mode
    642 if isinstance(source, (tuple, list)) and len(source) == 2:
    643     voltage, capacity = source

File [C:\scripting\cellpy-workspace\cellpy\cellpy\ica.py:589](file:///C:/scripting/cellpy-workspace/cellpy/cellpy/ica.py#line=588), in _half_cycles_from_frame(frame, cycle_mode, direction)
    587 missing = required - set(frame.columns)
    588 if missing:
--> 589     raise ValueError(
    590         f"curve frame is missing column(s): {', '.join(sorted(missing))}. "
    591         "Pass a frame from get_cap(categorical_column=True, "
    592         "label_cycle_number=True)."
    593     )
    595 if _CCOLS.cycle_num in frame.columns:
    596     groups: Any = frame.groupby(_CCOLS.cycle_num)

ValueError: curve frame is missing column(s): capacity, direction, potential. Pass a frame from get_cap(categorical_column=True, label_cycle_number=True).
```

## Comments (curated summary)

- **Clarifications / constraints**:
  - Root cause was missing cycle data (cycle 4), not a template/API column-name bug.
  - `ica.dqdv` must raise a clearer error when the cycle frame is empty, instead of claiming missing `capacity` / `direction` / `potential` columns.

_Note: this section is an interpretive summary of the comment thread, not a verbatim dump. Source comments: 1, last comment by @jepegit on 2026-08-29._
