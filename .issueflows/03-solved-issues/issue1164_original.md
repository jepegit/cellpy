# Issue #1164: Bio-Logic `.mpr` loader ignores the acquisition start time, so all timestamps fall at midnight

Source: https://github.com/jepegit/cellpy/issues/1164

## Original issue text

## Problem

When loading a Bio-Logic `.mpr` file, the acquisition start time stored in the
`VMP LOG` module is never read. The loader falls back to the date in the
settings module, which carries no time of day. As a result, every
`date_time` / `epoch_time_utc` value starts at 00:00:00 on the test date, so
absolute timestamps are early by the real start time of day.

Example with `testdata/data/biol.mpr`:

| | first `date_time` |
|---|---|
| current | 2017-03-15 00:00:00 |
| expected (acquisition start) | 2017-03-15 10:22:54 |

## Cause

`DataLoader._parse_mpr_log_data` (`src/cellpy/readers/instruments/biologics_mpr.py`)
loops over `bl_log_pos_dtype`, but skips every entry with
`if key not in self.mpr_log: continue`. `mpr_log` only holds the module header
fields (`end_date`, `length2`, …, `data`), never the field names it is about to
decode. So nothing is decoded: "Acquisition started on", "User", "Directory",
"File", "Host" and "Comments" are all dropped.

Fixing just that check exposes a second problem: the string fields in
`bl_log_pos_dtype` use the `"a<n>"` dtype codes, which numpy 2 rejects
(`TypeError: data type 'a45' not understood`).

## Reproduce

```python
import cellpy
c = cellpy.get("testdata/data/biol.mpr", instrument="biologics_mpr")
print(c.data.raw["date_time"].iloc[0])  # 2017-03-15 00:00:00
```

## Fix

- Decode the log fields whenever the log module's `data` is present (guard
  against log data that is too short).
- Use `"S<n>"` instead of `"a<n>"` in `bl_log_pos_dtype`; strip trailing nulls
  when decoding the text fields.
- Regenerate the `loader_biologics_mpr` golden, which recorded the midnight
  timestamps.

## Acceptance criteria

- [ ] `cellpy.get("testdata/data/biol.mpr", instrument="biologics_mpr")` gives a
      first `date_time` of `2017-03-15 10:22:54`.
- [ ] A regression test in `tests/test_biologics.py` asserts this.
- [ ] `tests/test_loader_goldens.py` passes with the regenerated golden.
- [ ] Files without a `VMP LOG` module still load (fallback to the settings date).
