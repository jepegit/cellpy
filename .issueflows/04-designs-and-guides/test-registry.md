# Test registry

Living index of notable tests for the optional **essential tests** paradigm
(see [essential-tests.md](./essential-tests.md)). Seeded once by issue-flow;
**never overwritten** on `issue-flow update` — agents and humans grow the table.

When `[issueflow].essential_tests` is true, `/iflow-close` / `/iflow-build`
(per `essential_review`) should add or update rows for tests **touched by the
current issue**. `/iflow-doctor` may audit the whole suite against this table.

| Test (node id or path::name) | Essential? | Always? | Code under test | Issue | Notes / demote? |
| --- | --- | --- | --- | --- | --- |
| tests/test_plot_image_bytes.py::test_write_image_returns_bytes | yes | yes | plotting.figures.write_image | #818 | monkeypatch to_image |
| tests/test_plot_image_bytes.py::test_write_image_missing_kaleido | yes | yes | plotting.figures.write_image | #818 | OptionalDependencyError |
| tests/test_plot_image_bytes.py::test_collection_to_image_uses_plot | yes | yes | Collection.to_image | #818 | |
| tests/test_collect.py::test_group_it_averages_multi_when_mixed_with_singleton | yes | yes | collect.summary group_it mixed | #816 | multi avg + singleton long |
| tests/test_cellpy.py::test_get_h5_instrument_skips_native_autopick | yes | yes | cellreader.get auto_pick vs instrument | #819 | monkeypatch load/from_raw routing |
| tests/test_collected_app_hooks.py::test_pretty_facet_annotation_cycles_and_cells | yes | yes | plotting.collected._pretty_facet_annotation | #820 | unit helper |
| tests/test_collected_app_hooks.py::test_cycles_per_cell_facet_strips_are_pretty | yes | yes | plotting.collected collected_plot per_cell | #820 | no cell= strip |
| tests/test_collected_app_hooks.py::test_cycles_per_cycle_facet_strips_are_pretty | yes | yes | plotting.collected collected_plot per_cycle | #820 | Cycle N strips |
| tests/test_collected_summary_axes.py::test_spread_share_y_true_matches_axes | yes | yes | plotting.collected summary spread + share_y | #817 | Group avg + Spread |
| tests/test_collected_summary_axes.py::test_spread_default_independent_y_axes | yes | yes | plotting.collected summary spread default | #817 | |
| tests/test_collected_summary_axes.py::test_spread_y_ranges_forces_independent_when_share_y_true | yes | yes | plotting.collected spread y_ranges | #817 | no re-link over limits |
| tests/test_collected_summary_axes.py::test_collected_plot_spread_share_y | yes | yes | plotting.collected collected_plot spread | #817 | public entry |
| tests/test_collected_ica_direction.py::test_select_direction_both_leaves_frame_unchanged | yes | yes | plotting.collected._select_direction | #821 | both = no filter |
| tests/test_collected_ica_direction.py::test_ica_line_direction_charge_filters_half_cycles | yes | yes | plotting.collected ica_plotter line | #821 | |
| tests/test_collected_ica_direction.py::test_ica_line_direction_discharge_differs_from_charge | yes | yes | plotting.collected ica_plotter line | #821 | |
| tests/test_collected_ica_direction.py::test_ica_line_direction_both_overlays_without_coerce | yes | yes | plotting.collected ica both line_dash | #821 | |
| tests/test_collected_ica_direction.py::test_ica_invalid_direction_warns_and_coerces | yes | yes | plotting.collected ica_plotter warn | #821 | |
| tests/test_collected_ica_direction.py::test_collected_plot_ica_per_cell_honours_direction | yes | yes | plotting.collected collected_plot ica | #821 | public entry |
| tests/test_batch_v3_runner.py::test_auto_uses_existing_cellpy_without_raw | yes | yes | batch.runner._get_kwargs AUTO | #825 | prefer local .cellpy |
| tests/test_batch_v3_runner.py::test_auto_falls_back_to_raw_when_cellpy_missing | yes | yes | batch.runner._get_kwargs AUTO | #825 | |
| tests/test_batch_v3_runner.py::test_newest_passes_both_paths | yes | yes | batch.runner._get_kwargs NEWEST | #825 | freshness check |
| tests/test_batch_v3_runner.py::test_recalc_remakes_steps_and_summary | yes | yes | batch.runner.load_cell recalc | #825 | force_recalc |
| tests/test_batch_v3_runner.py::test_no_recalc_skips_remake | yes | yes | batch.runner.load_cell | #825 | |
| tests/test_batch.py::test_persist_skips_rewrite_when_loaded_from_cellpy | yes | yes | batch.facade._persist_cells | #825 | skip redundant save |
| tests/test_batch.py::test_persist_rewrites_when_loaded_from_raw | yes | yes | batch.facade._persist_cells | #825 | |
| tests/test_cli_light_import.py::test_info_version_avoids_cellreader_import | yes | yes | cellpy.__init__ / cli / cli_api light path | #837 | subprocess; cellreader must stay out of sys.modules |
| tests/test_cli_light_import.py::test_setup_default_avoids_cellreader_and_optional_deps | yes | yes | cli_api.setup_config default light | #839 | no cellreader / lmfit |
| tests/test_cli_light_import.py::test_setup_check_imports_cellreader | yes | yes | cli_api.setup_config --check | #839 | opt-in check loads readers |
| tests/test_cli_light_import.py::test_setup_deps_probes_optional_modules | yes | yes | cli_api.setup_config --deps | #839 | opt-in optional probe |
| tests/test_cellpy_file_v9.py::test_failed_resave_keeps_the_old_file | yes | yes | cellpy_file.atomic.atomic_write / v9.save / CellpyCell.save | #845 | data-loss guard: interrupted re-save must not destroy the old file |
| tests/test_cellpy_file_v9.py::test_failed_first_save_leaves_no_file | yes | yes | cellpy_file.atomic.atomic_write / v9.save | #845 | no half-written archive on a fresh path |
| tests/test_cellpy_file_v9.py::test_incomplete_archive_is_rejected_before_replace | yes | yes | v9._verify_members | #845 | missing zip member never replaces a good file |
| tests/test_cellpy_file_v9.py::test_failed_hdf5_resave_keeps_the_old_file | no | no | cellpy_file.write.save (v8/HDF5) | #845 | same guard for the legacy writer; unmarked to keep Tier 1 fast |
| tests/test_config.py::test_active_config_file_prefers_toml | yes | yes | config.loader.active_config_file | #851 | "which config am I using" must stay honest |
| tests/test_config.py::test_active_config_file_falls_back_to_legacy | yes | yes | config.loader.active_config_file | #851 | legacy-only setups unchanged |
| tests/test_config.py::test_active_config_file_flags_shadowed_legacy | yes | yes | config.loader.active_config_file | #851 | migrated user: .conf on disk but ignored |
| tests/test_config.py::test_active_config_file_agrees_with_load_config | no | yes | config.loader.active_config_file / load_config | #851 | anti-drift: helper and loader pick the same file |
| tests/test_cellpy_cmd.py::test_info_configloc_reports_the_toml | yes | yes | cli_api._configloc | #851 | CLI reports the winning file |
| tests/test_cellpy_cmd.py::test_info_configloc_flags_shadowed_legacy_file | yes | yes | cli_api._configloc | #851 | never point at the dead .conf |

**Columns**

- **Essential?** — currently marked with the configured pytest marker.
- **Always?** — should stay essential even after the originating issue closes.
- **Code under test** — modules/symbols (graphify can help).
- **Issue** — GitHub number that introduced or last reviewed the test.
- **Notes / demote?** — why essential, or candidate for demotion.
