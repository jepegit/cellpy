# Issue #1164 — plan

_Written after the fix (found during a bug sweep); records the approach taken._

## Approach

1. `DataLoader._parse_mpr_log_data` (`src/cellpy/readers/instruments/biologics_mpr.py`):
   decode every `bl_log_pos_dtype` field whenever the log module's `data`
   is present, instead of skipping keys that were never in `mpr_log`. Skip a
   field when the log data is too short for it. Strip trailing nulls from
   byte-string fields before decoding (`errors="replace"`).
2. `bl_log_pos_dtype` (`loader_specific_modules/biologic_file_format.py`):
   replace the `a<n>` dtype codes, which numpy 2 rejects, with `S<n>`.
3. Keep the fallback to the settings date when there is no `VMP LOG` module.
4. Tests: regression test in `tests/test_biologics.py` (first `date_time`
   is `2017-03-15 10:22:54`); regenerate the `loader_biologics_mpr` golden
   with `dev/regenerate_goldens.py`.
