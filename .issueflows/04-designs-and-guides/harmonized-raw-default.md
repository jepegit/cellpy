# Harmonized-raw default load path (#560)

**Context.** Stage 3.3 finishes the loader port: vendor files go through
`parse()` → `harmonize(declarations)` into native raw. Phase B (#621) wired
this behind `Reader.use_harmonized_raw` (default off). Phase C hardens the
regressions that blocked default-on, then flips the default.

**Decision.** Single-file raw loads use `harmonize(parse())` by default
(`use_harmonized_raw=True`). Set `False` for the emergency `loader()+to_native`
fallback. Multi-file merges still use legacy `_append` + `to_native` (follow-up).

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

**Refs.** jepegit/cellpy#560; PR #623; loader plan in `architecture-plan/`.
