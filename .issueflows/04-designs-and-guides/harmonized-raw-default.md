# Harmonized-raw default load path (#560)

**Context.** Stage 3.3 finishes the loader port: vendor files go through
`parse()` → `harmonize(declarations)` into native raw. Phase B (#621) wired
this behind `Reader.use_harmonized_raw` (default off). Phase C hardens the
regressions that blocked default-on, then flips the default.

**Decision.** Single-file raw loads use `harmonize(parse())` by default
(`use_harmonized_raw=True`). Set `False` for the emergency `loader()+to_native`
fallback. Multi-file merges still use legacy `_append` + `to_native` (follow-up).

**Load ordering (no double vendor read).** `from_raw` runs
`harmonize(parse())` **before** the legacy loader for single-file + flip-on.
Loaders that share a parse cache (`AutoLoader._parsed_frame`,
`arbin_res._parsed_data`, biologics `mpr_data`) reuse that read when building
the Data shell (summary/meta/FID). Without the cache, default-on was ~2× slower
on the single-cell Arbin benchmark (CI gate fail at +100%).

**Hardening that unlocked the default**

- Arbin wide-aux columns declared via `aux_map` (`aux_0_u_C` → `aux_temperature_0`).
- Vendor `datapoint_num` preserved (not synthesized as `0..n-1`).
- `batmo_bdf.parse()` runs the BDF decode (hours→seconds, signed current, …).
- `arbin_sql_h5` keeps all distinct loader-stage rows.

**Alternatives considered**

- Allow-list of verified loaders under the flip — rejected; harden `batmo_bdf`
  instead so default-on is safe for in-tree loaders.
- Delete `to_native` entirely — rejected; still needed for cellpy-file / merge
  boundaries and the emergency off-switch.
- Skip the legacy loader entirely once harmonize succeeds — deferred; still need
  its Data shell (summary/meta/FID). Parse-first + cache is enough for the
  double-read.

**Refs.** jepegit/cellpy#560; PR #623; loader plan in `cellpy-design-and-development/archive/foundations/cellpy2-loader-port-and-extraction-plan.md`.

## Cycle-cumulative capacity rebase (#989)

1.x kept the vendor capacity column as-is. If a tester step forgot to
reset, `get_cap` / cycle plots showed doubled capacity. Both 1.x and 2.x
still take the cycle's last point for per-cycle summary capacity.

2.x `harmonize()` always runs `normalize_reset_granularity` so **each
cycle starts at 0**. It handles every cumulative column present in the frame
(capacity + energy, both directions); an undeclared column counts as
`PER_CYCLE`:

- `PER_CYCLE` (declared or default) — *forgotten-reset guard*: a cycle whose
  first value exceeds `CYCLE_START_RTOL` (1 %) of the column's largest
  magnitude did not start at 0; subtract that first value for that cycle
  only. Cycles already starting at ~0 are untouched.
- `PER_TEST` — subtract the first value of each cycle (that first point
  becomes 0).
- `PER_STEP` — re-accumulate completed steps within the cycle.

When a rebase actually changes values, one `UserWarning` names the columns
(guard entries add "N of M cycles carried over"). Identity rebases stay
silent. Kit check 7 (`testing.check_reset_granularity`) asserts the
cycle-starts-at-0 property on every conforming loader.

**Round 2 (2026-09-10).** The first fix assumed the rebase always ran. It did
not: the function returned early when a loader declared no granularity, and
no Arbin loader declares any (Arbin resets per cycle by schedule). A schedule
that skipped the reset on every other cycle produced doubled summary capacity
on 405 of 902 cycles. Why the guard rather than declaring `PER_TEST` for
Arbin: the real-world failure is *mixed* (reset on some cycles, not on
others), so an unconditional first-value subtraction would also eat the
legitimate first-sample increment on every well-behaved cycle and warn on
every file. `cellpycore`'s `TEST` mode (diff + cum_sum) assumes *never*
resets and is wrong for the mixed case too.

Persisted `.cellpy` files are never rewritten on read; files made by ≤ 2.1.5
must be regenerated from raw.

This is cellpy-only (loader declarations). Do not confuse with
`cellpycore.summarizers.normalize_capacity_granularity`.
