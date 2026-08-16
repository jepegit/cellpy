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
| tests/test_collect.py::test_batch_collector_to_image | yes | yes | collect.collector.BatchCollector.to_image | #926 | proxies Collection.to_image |
| tests/test_collect.py::test_batch_collector_save_figure_writes_a_file | yes | yes | collect.collector.BatchCollector.save_figure | #926 | suffix defaults to .png |
| tests/test_collect.py::test_save_help_says_data_only_and_names_the_figure_api | yes | yes | Collection.save / BatchCollector.save docstrings | #926 | `.save?` must name the figure API |
| tests/test_collect.py::test_group_it_averages_multi_when_mixed_with_singleton | yes | yes | collect.summary group_it mixed | #816 | multi avg + singleton long |
| tests/test_cellpy.py::test_get_h5_instrument_skips_native_autopick | yes | yes | cellreader.get auto_pick vs instrument | #819 | monkeypatch load/from_raw routing |
| tests/test_collected_app_hooks.py::test_pretty_facet_annotation_cycles_and_cells | yes | yes | plotting.collected._pretty_facet_annotation | #820 | unit helper |
| tests/test_collected_app_hooks.py::test_cycles_per_cell_facet_strips_are_pretty | yes | yes | plotting.collected collected_plot per_cell | #820 | no cell= strip |
| tests/test_collected_app_hooks.py::test_cycles_per_cycle_facet_strips_are_pretty | yes | yes | plotting.collected collected_plot per_cycle | #820 | Cycle N strips |
| tests/test_collected_summary_axes.py::test_spread_share_y_true_matches_axes | yes | yes | plotting.collected summary spread + share_y | #817 | Group avg + Spread |
| tests/test_collected_summary_axes.py::test_spread_mean_traces_have_hovertemplate | yes | yes | plotting.collected.spread_plot hover | #875 | mean hover + bounds skip |
| tests/test_collected_summary_axes.py::test_spread_default_independent_y_axes | yes | yes | plotting.collected summary spread default | #817 | |
| tests/test_collected_summary_axes.py::test_spread_y_ranges_forces_independent_when_share_y_true | yes | yes | plotting.collected spread y_ranges | #817 | no re-link over limits |
| tests/test_collected_summary_axes.py::test_collected_plot_spread_share_y | yes | yes | plotting.collected collected_plot spread | #817 | public entry |
| tests/test_collected_ica_direction.py::test_select_direction_both_leaves_frame_unchanged | yes | yes | plotting.collected._select_direction | #821 | both = no filter |
| tests/test_collected_ica_direction.py::test_ica_line_direction_charge_filters_half_cycles | yes | yes | plotting.collected ica_plotter line | #821 | |
| tests/test_collected_ica_direction.py::test_ica_line_direction_discharge_differs_from_charge | yes | yes | plotting.collected ica_plotter line | #821 | |
| tests/test_collected_ica_direction.py::test_ica_line_direction_both_overlays_without_coerce | yes | yes | plotting.collected ica both line_dash | #821 | |
| tests/test_collected_ica_direction.py::test_ica_invalid_direction_warns_and_coerces | yes | yes | plotting.collected ica_plotter warn | #821 | |
| tests/test_collected_ica_direction.py::test_collected_plot_ica_per_cell_honours_direction | yes | yes | plotting.collected collected_plot ica | #821 | public entry |
| tests/test_resolve_collected_layout_kind.py (module) | yes | yes | plotting.collected.resolve_collected_layout_kind | #874 | validate + film alias |
| tests/test_collected_cycle_colorbar.py (module) | yes | yes | plotting.collected.sequence_plotter fig_pr_cell | #928 | collected cycle legend vs colorbar |
| tests/test_batch_v3_runner.py::test_auto_uses_existing_cellpy_without_raw | yes | yes | batch.runner._get_kwargs AUTO | #825 | prefer local .cellpy |
| tests/test_batch_v3_runner.py::test_auto_falls_back_to_raw_when_cellpy_missing | yes | yes | batch.runner._get_kwargs AUTO | #825 | |
| tests/test_batch_v3_runner.py::test_newest_passes_both_paths | yes | yes | batch.runner._get_kwargs NEWEST | #825 | freshness check |
| tests/test_batch_v3_runner.py::test_recalc_remakes_steps_and_summary | yes | yes | batch.runner.load_cell recalc | #825 | force_recalc |
| tests/test_batch_v3_runner.py::test_no_recalc_skips_remake | yes | yes | batch.runner.load_cell | #825 | |
| tests/test_batch.py::test_persist_skips_rewrite_when_loaded_from_cellpy | yes | yes | batch.facade._persist_cells | #825 | skip redundant save |
| tests/test_batch.py::test_persist_rewrites_when_loaded_from_raw | yes | yes | batch.facade._persist_cells | #825 | |
| tests/test_batch.py::test_export_project_writes_cells_and_relative_journal | yes | yes | batch.facade.Batch.export_project | #878 | relative posix journal paths |
| tests/test_batch.py::test_export_project_force_rewrites_existing_cellpy | yes | yes | batch.facade._persist_cells force_rewrite | #878 | export overwrites |
| tests/test_batch.py::test_export_project_raises_on_unloaded_cells | yes | yes | batch.facade.Batch.export_project | #878 | fail fast |
| tests/test_cli_light_import.py::test_info_version_avoids_cellreader_import | yes | yes | cellpy.__init__ / cli / cli_api light path | #837 | subprocess; cellreader must stay out of sys.modules |
| tests/test_cli_light_import.py::test_setup_default_avoids_cellreader_and_optional_deps | yes | yes | cli_api.setup_config default light | #839 | no cellreader / lmfit |
| tests/test_cli_light_import.py::test_setup_check_imports_cellreader | yes | yes | cli_api.setup_config --check | #839 | opt-in check loads readers |
| tests/test_refresh_after_meta.py::test_refresh_after_mass_updates_gravimetric | yes | yes | CellpyCell.refresh_after / SUMMARY_META_DEPENDENCIES | #846 | mass → gravimetric rescale |
| tests/test_config_secrets.py::test_legacy_arbin_sql_credentials_are_not_in_the_file_dump | yes | yes | CellpyConfig.model_dump_for_file scrub | #849 | SQL_PWD/UID stripped |
| tests/test_config_secrets.py::test_instrument_credentials_in_a_user_toml_are_rejected | yes | yes | loader instrument credential reject | #849 | TOML load guard |
| tests/test_config.py::test_config_override_is_thread_isolated | yes | yes | config.session.override ContextVar | #850 | ThreadPoolExecutor isolation |
| tests/test_config.py::test_active_config_file_reports_project_toml | yes | yes | config.loader.active_config_file project_path | #853 | |
| tests/test_cellpy_cmd.py::test_info_configloc_reports_project_toml | yes | yes | cli_api._configloc project notice | #853 | |
| tests/test_cli_light_import.py::test_setup_deps_probes_optional_modules | yes | yes | cli_api.setup_config --deps | #839 | opt-in optional probe |
| tests/test_cli_light_import.py::test_importing_cli_ui_does_not_import_rich | yes | yes | cli_ui lazy rich import | #891 | subprocess; keeps cold start off rich |
| tests/test_cli_ui.py (whole file) | yes | yes | cli_ui.Reporter vocabulary | #891 | colour/symbol/level/stream decisions; injected streams |
| tests/test_cli_flags.py::test_global_flags_install_the_matching_level | yes | yes | cli.main root callback -> cli_ui.Level | #891 | parametrised over -q/--verbose |
| tests/test_cli_flags.py::test_quiet_still_answers_a_question | yes | yes | cli.info payload echo | #891 | --quiet must not silence `info` |
| tests/test_cli_flags.py::test_usage_errors_go_to_stderr | yes | yes | cli.run usage errors | #891 | stderr + exit 2, not stdout + 255 |
| tests/test_cli_flags.py::test_run_list_still_works_without_a_name | yes | yes | cli.run NAME optionality | #891 | guards `run --list` against a required NAME |
| tests/test_cli_surface.py::test_the_global_options_are_unchanged | yes | yes | root CLI options | #891 | snapshot now covers root params |
| tests/test_cli_info.py::test_a_failing_check_exits_non_zero | yes | yes | cli_api._check / cli.info exit code | #891 | --check was always exit 0 |
| tests/test_cli_info.py::test_check_does_not_shout_or_draw_banners | yes | yes | cli_api._check rendering | #891 | no ===/---/!!!! |
| tests/test_cli_info.py::test_check_keeps_the_probe_narration_for_verbose | yes | yes | cli_api._debug gating | #891 | diagnostics only under --verbose |
| tests/test_cli_info.py::test_quiet_reports_only_what_is_broken | yes | yes | check rendering under --quiet | #891 | failures survive quiet |
| tests/test_cli_info.py::test_a_local_path_in_a_remote_capable_setting_is_still_checked | yes | yes | cli_api._check_config_file OTHERPATHS | #891 | local value in a remote-capable setting |
| tests/test_cli_api.py::test_show_info_is_quiet_by_default | yes | yes | cli_api._ui / _silent binding | #891 | library prints nothing without echo |
| tests/test_cellpy_cmd.py::test_info_check | yes | yes | cli info --check exit code | #891 | exit code must match the printed verdict |
| tests/test_cellpy_file_v9.py::test_v9_parquet_members_use_zstd | yes | yes | v9._frame_to_parquet_bytes | #912 | new writes are zstd + ZIP_STORED |
| tests/test_cellpy_file_v9.py::test_v9_loads_snappy_parquet_members | yes | yes | v9.load / _read_parquet_member | #912 | #898-era snappy members still load |
| tests/test_cellpy_file_v9.py::test_failed_resave_keeps_the_old_file | yes | yes | cellpy_file.atomic.atomic_write / v9.save / CellpyCell.save | #845 | data-loss guard: interrupted re-save must not destroy the old file |
| tests/test_cellpy_file_v9.py::test_failed_first_save_leaves_no_file | yes | yes | cellpy_file.atomic.atomic_write / v9.save | #845 | no half-written archive on a fresh path |
| tests/test_ica_plot_prepare.py::test_ica_dva_plotly_both_direction_dash_differs | yes | yes | plotting.backends.plotly._render_ica_dva | #862 | charge solid / discharge dot |
| tests/test_ica_plot_prepare.py::test_ica_dva_plotly_single_direction_stays_solid | yes | yes | plotting.backends.plotly._render_ica_dva | #862 | single direction stays solid |
| tests/test_ica_plot_prepare.py::test_ica_dva_matplotlib_both_direction_linestyle_differs | yes | yes | plotting.backends.mpl._render_ica_dva | #862 | "-" / ":" linestyle |
| tests/test_collect_dva.py::test_dva_collector_uses_the_specced_frame | yes | yes | collect.dva.collect_dva | #863 | specced frame cols |
| tests/test_collect_dva.py::test_collect_dva_returns_a_dva_collection | yes | yes | collect.dva.collect_dva | #863 | kind="dva" |
| tests/test_collect_dva.py::test_collect_dva_forwards_capacity_resolution_not_voltage_resolution | yes | yes | collect.dva.collect_dva / ica.dvdq | #863 | resolution-knob guard |
| tests/test_collect_dva.py::test_dva_collection_plot_uses_the_dva_family_not_cycles | yes | yes | collect.collection.Collection._FAMILY | #863 | family wiring guard |
| tests/test_collect_dva.py::test_dva_collector_fig_pr_cycle | yes | yes | plotting.collected.dva_plotter | #863 | per-cycle layout |
| tests/test_cellpy_file_v9.py::test_incomplete_archive_is_rejected_before_replace | yes | yes | v9._verify_members | #845 | missing zip member never replaces a good file |
| tests/test_cellpy_file_v9.py::test_failed_hdf5_resave_keeps_the_old_file | no | no | cellpy_file.write.save (v8/HDF5) | #845 | same guard for the legacy writer; unmarked to keep Tier 1 fast |
| tests/test_config.py::test_active_config_file_prefers_toml | yes | yes | config.loader.active_config_file | #851 | "which config am I using" must stay honest |
| tests/test_config.py::test_active_config_file_falls_back_to_legacy | yes | yes | config.loader.active_config_file | #851 | legacy-only setups unchanged |
| tests/test_config.py::test_active_config_file_flags_shadowed_legacy | yes | yes | config.loader.active_config_file | #851 | migrated user: .conf on disk but ignored |
| tests/test_config.py::test_active_config_file_agrees_with_load_config | no | yes | config.loader.active_config_file / load_config | #851 | anti-drift: helper and loader pick the same file |
| tests/test_cellpy_cmd.py::test_info_configloc_reports_the_toml | yes | yes | cli_api._configloc | #851 | CLI reports the winning file |
| tests/test_cellpy_cmd.py::test_info_configloc_flags_shadowed_legacy_file | yes | yes | cli_api._configloc | #851 | never point at the dead .conf |
| tests/test_batch_progress.py::test_run_emits_cell_start_parse_done | yes | yes | batch.runner emit + on_progress | #916 | event bus + 3-arg callback |
| tests/test_batch_progress.py::test_on_progress_still_wins_with_event_hook | yes | yes | batch.runner on_progress | #916 | BC: 3-arg hook still fires |
| tests/test_batch_progress.py::test_tqdm_display_disable_tracks_cells | yes | yes | batch.progress.TqdmBatchProgress | #916 | overall n without TTY |
| tests/test_batch_v3_runner.py::test_dispatch_lite_saves_raw_then_strips | yes | yes | batch.runner._dispatch_lite | #920 | process worker saves raw load |
| tests/test_batch_v3_runner.py::test_persist_skips_none_placeholder_from_processes | yes | yes | batch.facade._persist_cells / CellStore.is_loaded | #920 | None.save guard |
| tests/test_collected_summary_groups.py (module) | yes | yes | plotting.collected.summary_plotter / Collection.plot | #923 | facet order, group labels, legend title |
| tests/test_collected_backend_alias.py (module) | yes | yes | plotting.collected.collected_plot backend alias | #925 | matplotlib -> seaborn, warn_once signature |

**Columns**

- **Essential?** — currently marked with the configured pytest marker.
- **Always?** — should stay essential even after the originating issue closes.
- **Code under test** — modules/symbols (graphify can help).
- **Issue** — GitHub number that introduced or last reviewed the test.
- **Notes / demote?** — why essential, or candidate for demotion.
