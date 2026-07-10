from pathlib import Path

APP_SOURCE = Path(__file__).resolve().parents[1] / "app.py"
VALIDATION_SOURCE = Path(__file__).resolve().parents[1] / "core" / "validation.py"
README_SOURCE = Path(__file__).resolve().parents[1] / "README.md"
DEFAULTS_SOURCE = Path(__file__).resolve().parents[1] / "core" / "bg40_defaults.py"
REPORT_SCHEMA_SOURCE = Path(__file__).resolve().parents[1] / "core" / "report_schema.py"


def _src() -> str:
    return APP_SOURCE.read_text(encoding="utf-8")


def test_m21_header_uses_safe_commercial_card():
    src = _src()
    assert ".block-container {padding-top: 2.10rem" in src
    assert "app-header-card" in src
    assert "app-header-title" in src
    assert "Segmental Box Girder Pro" in src


def test_dashboard_uses_professional_wording_without_chapter_prompt():
    src = _src()
    assert "Reference baseline loaded" in src
    assert "Review current workspace" in src
    assert "Baseline keyed" not in src
    assert "Review chapter UI" not in src


def test_navigation_keeps_single_source_of_truth_keys():
    src = _src()
    assert 'st.radio("WORKSPACE", WORKSPACE_LABELS, key="current_workspace")' in src
    assert 'key="current_subpage", on_change=_sync_sidebar_subpage_to_loads_inline' in src
    assert "old_nav" not in src


def test_m22_layout_balances_main_container_leftward():
    src = _src()
    assert "max-width: 1680px" in src
    assert "margin-left: 0" in src
    assert "margin-right: auto" in src
    assert "padding-left: 2.0rem" in src


def test_m22_sidebar_readability_css_is_explicit():
    src = _src()
    assert '[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {font-size: 0.84rem' in src
    assert "sidebar-context-row" in src
    assert "sidebar-context-value" in src


def test_m22_status_wording_distinguishes_baseline_and_app_results():
    src = _src()
    assert "Baseline Ready" in src
    assert "Baseline PASS" in src
    assert "App PASS" in src or "app_status" in src
    assert "Status wording separates R10 baseline readiness" in src


def test_fea5a_dashboard_status_tracks_source_package_and_honest_downstream_state():
    src = _src()
    assert "Source package ready" in src
    assert "Complete and reconcile Section 5 sources" in src
    assert "NOT YET CONNECTED" in src
    assert "source_package_gate" in src


def test_m3d_schema_version_is_updated():
    validation_src = VALIDATION_SOURCE.read_text(encoding="utf-8")
    assert 'PROJECT_SCHEMA_VERSION = "0.5.3-commercial-fea5b1-axis-convention-uls-review-polish"' in validation_src


def test_readme_documents_m3g_section_wind_csp_formatting_and_seismic_foundation():
    readme = README_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.M3" in readme or "COMMERCIAL.M3H" in readme
    assert "Display formatting rules" in readme
    assert "1.3.7 Wind Load" in readme
    assert "DPT seismic database" in readme
    assert "Bangkok Basin Zone 1–10" in readme
    assert "AASHTO LRFD 2020 Table 3.10.7.1-1" in readme
    assert "EN 1991-1-4" in readme
    assert "Table 2.5" in readme
    assert "Full station-by-station FEA import remains pending" in readme
    assert "Coordinate-driven section properties" in readme
    assert "COMMERCIAL.CODE.1" in readme
    assert "AASHTO LRFD Bridge Design Specifications, 9th Edition, 2020" in readme
    assert "Structural Polygon 1" in readme
    assert "Opening Polygon 1" in readme


def test_m3b_load_pages_use_editable_tables_and_code_basis():
    src = _src()
    assert "st.data_editor" in src
    assert "sdl_component_editor" in src
    assert "Code basis:" in src
    assert "EN 1991-2 Art. 6.4.3" in src
    assert "EN 1991-2 Art. 6.5.3" in src
    assert "EN 1991-2 Art. 6.5.2" in src
    assert "EN 1991-2 Art. 6.5.1" in src
    assert "DPT 1301/1302-61" in src



def test_loads_dead_load_info_page_is_report_only():
    src = _src()
    assert '"3.1 Dead Load"' in src
    assert 'code_basis_card("3.1 Dead Load (DL)"' in src
    assert 'dead_load_definition' in src
    assert 'dead_load_unit_weights' in src
    assert 'no duplicate dead-load input' in src
    assert 'Report note: these unit weights are provided for information and report traceability only' in src

def test_m3a_load_figures_and_plotly_modebar_are_present():
    src = _src()
    assert "u20_loading_diagram" in src
    assert "rail_horizontal_forces_diagram" in src
    assert "wind_bridge_direction_diagram" in src
    assert "response_spectrum_figure" in src
    assert "PLOTLY_CONFIG" in src

def test_ui1_engineering_figure_system_backend_and_sidebar2_defaults_are_present():
    src = _src()
    figure_src = (APP_SOURCE.resolve().parents[0] / "visualization" / "figure_system.py").read_text(encoding="utf-8")
    readme = README_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.UI.1" in readme
    assert "COMMERCIAL.UI.SIDEBAR.2" in readme
    assert "visualization/figure_system.py" in readme
    assert "DEFAULT_SCREEN_FIGURE_VIEW_MODE" in src
    assert "REPORT_FIGURE_VIEW_MODE" in src
    assert "report_plotly_config" in src
    assert "Report figure mode" in src
    assert "plotly_config_for_view_mode" in src
    assert "**FIGURE SYSTEM**" not in src
    assert 'key="global_figure_view_mode"' not in src
    assert "ENGINEERING_REVIEW_CONFIG" in figure_src
    assert "ENGINEERING_REPORT_CONFIG" in figure_src
    assert "apply_engineering_figure_layout" in figure_src


def test_m3a_no_duplicate_sdl_summary_input_pattern():
    src = _src()
    assert 'D["load_components"]["sdl_components"] = edited.to_dict("records")' in src
    assert "FEA Load Input Summary reads from the same load schema" in src


def test_m3c_aashto_ir_controls_are_present_once_in_eq_page():
    src = _src()
    assert "AASHTO bridge seismic parameters" in src
    assert "eq_aashto_operational_category" in src
    assert "eq_aashto_substructure_type" in src
    assert "eq_importance_factor_preset" in src
    assert "eq_manual_response_modification_factor" in src
    assert "seismic_R_source" in src
    assert "AASHTO LRFD 2020 Table 3.10.7.1-1" in src

def test_m3c_aashto_reference_data_files_exist():
    root = APP_SOURCE.resolve().parents[0]
    assert (root / "data" / "aashto_lrfd_2014" / "response_modification_factors_substructures_3_10_7_1_1.csv").exists()
    assert (root / "data" / "aashto_lrfd_2014" / "response_modification_factors_connections_3_10_7_1_2.csv").exists()


def test_m3d_uses_csp_aligned_ui_system_classes_and_table_formatter():
    src = _src()
    assert "input-card" in src
    assert "calc-card" in src
    assert "result-card" in src
    assert "show_engineering_table" in src
    assert "format_engineering_value" in src


def test_m3d_global_engineering_formatting_rules_are_documented_in_code():
    formatting_src = (APP_SOURCE.resolve().parents[0] / "core" / "formatting.py").read_text(encoding="utf-8")
    assert "Force/load and moment/torque: no decimals" in formatting_src
    assert "Stress in MPa: 2 decimals" in formatting_src
    assert "Length in mm: no decimals; length in m: 3 decimals" in formatting_src


def test_m3e_wind_report_figures_and_auto_factor_ui_are_present():
    src = _src()
    assert "fig_1_2_dpt_wind_speed_map.png" in src
    assert "fig_1_3_en_wind_direction_bridge.png" in src
    assert "User-provided refined bridge wind-direction sketch" in src
    assert "max_height_px=340" in src
    assert "fig_ws_factor_table_and_ze.png" not in src
    assert "ze_bridge_reference_card" in src
    assert "fig_ws_bridge_cross_section_load.png" in src
    assert "User-provided refined WS/WL wind application sketch" in src
    assert "max_height_px=360" in src
    assert "wind_parameter_editor" in src
    assert "wind_reference_group_select" in src
    assert "wind_load_en1991_dpt_auto" in src
    assert "C factors are not duplicate manual inputs" in src


def test_m3f_workspace_reorganization_is_present():
    schema_src = (APP_SOURCE.resolve().parents[0] / "core" / "report_schema.py").read_text(encoding="utf-8")
    assert '"label": "1 Criteria"' in schema_src
    assert '"label": "2 Bridge Geometry / Section Properties"' in schema_src
    assert '"label": "3 Loads"' in schema_src
    assert '"2.2 Geometry and Analysis Model"' in schema_src
    assert '"3.10 FEA Load Input Summary"' in schema_src
    assert '"1 Criteria / Loads"' not in schema_src
    assert '"2 Bridge Model"' not in schema_src
    assert '"3 Section Properties"' not in schema_src


def test_m3f_analysis_model_scope_note_is_present():
    src = _src()
    assert "the finite element analysis model is created externally" in src
    assert "This app records geometry, modelling assumptions" in src
    assert "It is not an FEA solver" in src or "The app does not replace or regenerate the external FEA model" in src
    assert "fea_program_select" in src
    assert "fea_model_figure_status" in src


def test_m3f_router_uses_new_workspace_ids():
    src = _src()
    assert 'elif workspace["id"] == "criteria"' in src
    assert 'elif workspace["id"] == "bridge_geometry"' in src
    assert 'elif workspace["id"] == "loads"' in src
    assert 'page_bridge_geometry(subpage)' in src
    assert 'page_loads(subpage)' in src


def test_m3g_coordinate_section_engine_ui_is_present():
    src = _src()
    assert "Coordinate-driven section engine" in src
    assert "section_coordinate_editor" in src
    assert "section_polygon_figure" in src
    assert "calculate_section_properties" in src
    assert "CSV / Excel" in src
    assert "read_coordinate_table" in src
    assert "Use calculated A / I / S / centroid as adopted properties" in src
    assert "Thin-walled closed-box J" in src
    assert "section_origin_display_mode" in src
    assert "section_point_label_mode" in src
    assert "QA Comparison: App Calculated vs Adopted Values" in src


def test_m3g_bridge_geometry_page_no_workspace_title_duplication_in_active_router():
    src = _src()
    bridge_def = src.split("def page_bridge_geometry(sub: str) -> None:", 1)[1].split("def page_prestress_losses", 1)[0]
    assert 'st.subheader(get_workspace("2 Bridge Geometry / Section Properties")' not in bridge_def
    assert "render_section_properties()" in bridge_def
    assert 'section_title("2.3 Section Properties")' in src



def test_m3g4_section_properties_j_adoption_controls_are_simple_and_explicit():
    src = _src()
    assert "Adopted Properties for Design" in src
    assert "Adopted Section Properties for Design" in src
    assert "USED BY DESIGN CHECKS" in src
    assert "J input source / method" in src
    assert 'j_options = ["User override", "Thin-walled estimate adopted"]' in src
    assert "User override J (m⁴)" in src
    assert "Apply user override J to adopted properties" in src
    assert "Use thin-walled estimate as adopted J" in src
    assert "Torsion / Advanced" not in src.split("st.tabs([", 1)[1].split("])" , 1)[0]


def test_m3h1_tendon_import_summary_cards_and_trace_are_present():
    src = _src()
    assert "_render_tendon_import_summary_cards" in src
    assert "Imported Tendon Model" in src
    assert "Strand / Area" in src
    assert "Jacking Basis" in src
    assert "0.75fpu" in src
    assert "General tendon table" in src
    assert "Vertical layout table" in src
    assert "Horizontal layout table" in src
    assert "Build / refresh imported tendon layout model" in src
    assert "tendon_elevation_figure" in src
    assert "tendon_plan_figure" in src
    assert "tendon_section_overlay_figure" in src
    assert "BridgeObj mismatch detected" in src
    assert "Adopt / Re-adopt tendon model as design source" in src


def test_m3h_tendon_layout_core_module_exists():
    root = APP_SOURCE.resolve().parents[0]
    tendon_src = (root / "core" / "tendon_layout.py").read_text(encoding="utf-8")
    assert "build_tendon_layout_model" in tendon_src
    assert "normalize_general_tendon_rows" in tendon_src
    assert "normalize_tendon_profile_rows" in tendon_src
    assert "BridgeObj mismatch" in tendon_src


def test_project_json_load_uses_pending_state_before_widget_keys():
    src = APP_SOURCE.read_text(encoding="utf-8")
    assert "def _apply_pending_project_json_load" in src
    assert "st.session_state._pending_project_json_load" in src
    load_handler = src.split('if st.button("Load uploaded project"', 1)[1].split('except ProjectJsonLoadError', 1)[0]
    assert "st.session_state.current_workspace =" not in load_handler
    assert "st.session_state.current_subpage =" not in load_handler
    assert '"workspace": WORKSPACE_LABELS[0]' in load_handler
    assert '"subpage": get_workspace(WORKSPACE_LABELS[0])["subpages"][0]' in load_handler



def test_m3h4_tendon_adopted_tables_are_complete_and_raw_tables_are_qa_only():
    src = _src()
    assert "Adopt / Re-adopt tendon model as design source" in src
    assert "Merged Tendon Profile Table — vertical + horizontal" in src
    assert "Raw import data / QA only" in src
    assert "_tendon_summary_display_frame" in src
    assert "_tendon_profile_display_frame" in src
    assert "tendon_model_to_profile_frame" in src
    assert "Vertical / horizontal station matching QA" in src


def test_m3h5_tendon_overlay_polish_controls_are_present():
    app_src = APP_SOURCE.read_text(encoding="utf-8")
    assert "Quick station" in app_src
    assert "Tendon label mode" in app_src
    assert "Centerline origin (CL = 0)" in app_src
    assert "Tendon location QA" in app_src
    assert "classify_point_in_section_void" in app_src


def test_m3h7_tendon_overlay_uses_csp_canvas_language():
    src = _src()
    assert "Live Tendon Section Preview" in src
    assert "canvas-panel" in src
    assert "External tendon QA" in src
    assert "Figure 2.x" in src
    tendon_fig_src = (APP_SOURCE.resolve().parents[0] / "visualization" / "tendon_figures.py").read_text(encoding="utf-8")
    assert "Concrete" in tendon_fig_src
    assert "Inner void" in tendon_fig_src
    assert "Station =" in tendon_fig_src


def test_m3h7_1_tendon_overlay_call_keeps_station_outside_plot_body():
    src = _src()
    call_block = src.split('fig = tendon_section_overlay_figure(', 1)[1].split('fig.update_layout(', 1)[0]
    assert 'station_label=' not in call_block
    assert 'station_m=' not in call_block
    assert 'canvas-station-badge' in src
    assert 'Selected station' in src
    assert 'fig.add_annotation(' not in call_block


def test_m3h8_tendon_overlay_uses_card_contained_canvas_layout():
    src = _src()
    assert "COMMERCIAL.M3H.8" in README_SOURCE.read_text(encoding="utf-8")
    assert "st.container(border=True)" in src
    assert "canvas-legend-strip" in src
    assert "canvas-footer-grid" in src
    assert "showlegend=False" in src
    assert "Live Tendon Section Preview" in src


def test_m3h9_tendon_overlay_dimension_mode_and_station_badge_are_present():
    src = _src()
    tendon_fig_src = (APP_SOURCE.resolve().parents[0] / "visualization" / "tendon_figures.py").read_text(encoding="utf-8")
    readme = README_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.M3H.9" in readme
    assert "Dimension mode" in src
    assert "tendon_overlay_dimension_mode" in src
    assert "canvas-station-badge" in src
    assert "canvas-meta-strip" in src
    assert "_add_tendon_overlay_dimension_layer" in tendon_fig_src
    assert "clean: B, D, CL, and centroid guides only" in tendon_fig_src
    assert "hide dimensions: no dimension guide layer" in tendon_fig_src



def test_m3h10_tendon_overlay_viewport_uses_report_canvas_config():
    src = _src()
    tendon_fig_src = (APP_SOURCE.resolve().parents[0] / "visualization" / "tendon_figures.py").read_text(encoding="utf-8")
    readme = README_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.M3H.10" in readme
    assert "PLOTLY_TENDON_REPORT_CONFIG" in src
    assert '"displayModeBar": False' in tendon_fig_src
    assert "report preview" in tendon_fig_src.lower()
    assert "rgba(148,163,184,0.09)" in src


def test_m3h11_tendon_overlay_has_interactive_and_report_view_modes():
    src = _src()
    tendon_fig_src = (APP_SOURCE.resolve().parents[0] / "visualization" / "tendon_figures.py").read_text(encoding="utf-8")
    readme = README_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.M3H.11" in readme
    assert "Figure view mode" in src
    assert "Interactive review" in src
    assert "Report preview" in src
    assert "canvas-view-badge" in src
    assert "DEFAULT_SCREEN_FIGURE_VIEW_MODE" in src
    assert "REPORT_FIGURE_VIEW_MODE" in src
    assert "tendon_canvas_config" in src
    assert "st.plotly_chart(fig, use_container_width=True, config=tendon_canvas_config)" in src
    assert '"displayModeBar": True' in tendon_fig_src
    assert "_apply_tendon_overlay_viewport" in tendon_fig_src

def test_m3h10_tendon_dimension_helpers_use_polished_labels():
    tendon_fig_src = (APP_SOURCE.resolve().parents[0] / "visualization" / "tendon_figures.py").read_text(encoding="utf-8")
    assert "cg_line_color" in tendon_fig_src
    assert "rgba(255,255,255,0.96)" in tendon_fig_src
    assert "cx + 0.070 * width" in tendon_fig_src
    assert "ymax + 0.085 * depth" in tendon_fig_src



def test_bugfix1_project_load_clears_section_editor_widget_cache_and_versions_editor_key():
    src = _src()
    assert "_bump_project_widget_epoch_and_clear_stale_editors" in src
    assert "project_widget_epoch" in src
    assert "section_coordinate_editor_{_project_widget_epoch()}" in src
    assert "section_coordinate_file_upload" in src


def test_bugfix1_project_save_is_rendered_after_active_page_syncs_editors():
    src = _src()
    assert "serialize_project_json_bytes" in src
    assert "def render_project_save_panel" in src
    assert "Save is rendered after the active page syncs editable tables" in src
    assert src.rfind("render_project_save_panel()") > src.rfind("page_report_qa(subpage)")


def test_bugfix1_section_data_gate_is_present():
    src = _src()
    assert "Section Data Gate" in src
    assert "Coordinate rows" in src
    assert "Computed section" in src
    assert "Adopted properties" in src


def test_m41a_interactive_3d_tendon_view_is_present_after_plan_view():
    src = _src()
    readme = README_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.M4.1A" in readme
    assert '"Plan View", "3D Tendon View", "Section Overlay"' in src
    assert "Interactive 3D Tendon Review" in src
    assert "tendon_3d_review_figure" in src
    assert "Show outer shell" in src
    assert "Show inner void" in src
    assert "Tendon focus" in src
    assert "preview only" in src


def test_m41b_3d_view_presets_and_aspect_controls_are_present():
    src = _src()
    tendon_src = (APP_SOURCE.resolve().parents[0] / "visualization" / "tendon_figures.py").read_text(encoding="utf-8")
    assert "COMMERCIAL.M4.1B" in README_SOURCE.read_text(encoding="utf-8") or "Orthographic Isometric" in README_SOURCE.read_text(encoding="utf-8")
    assert "Isometric · Orthographic" in src
    assert "Isometric · Perspective" in src
    assert "Report isometric" in src
    assert "Aspect mode" in src
    assert "Presentation scale" in src
    assert "True scale" in src
    assert "projection" in tendon_src
    assert "orthographic" in tendon_src
    assert "_aspectratio_for_3d" in tendon_src


def test_m41c_3d_half_shell_and_tendon_isolation_controls_are_present():
    src = _src()
    tendon_src = (Path(__file__).resolve().parents[1] / "visualization" / "tendon_figures.py").read_text(encoding="utf-8")
    assert "COMMERCIAL.M4.1C" in README_SOURCE.read_text(encoding="utf-8")
    assert "Shell display" in src
    assert "Left half shell" in src
    assert "Right half shell" in src
    assert "Tendon isolate" in src
    assert "Outer shell opacity" in src
    assert "Inner void opacity" in src
    assert "shell_display_mode" in tendon_src
    assert "_clip_yz_polygon_to_half_plane" in tendon_src
    assert "tendon_filter" in tendon_src


def test_m41d_3d_inspection_presets_and_focus_controls_are_present():
    src = _src()
    tendon_src = (Path(__file__).resolve().parents[1] / "visualization" / "tendon_figures.py").read_text(encoding="utf-8")
    assert "COMMERCIAL.M4.1D" in README_SOURCE.read_text(encoding="utf-8")
    assert "Inspection preset" in src
    assert "Left inspection" in src
    assert "Right inspection" in src
    assert "Single tendon focus" in src
    assert "Report clean" in src
    assert "Focus tendon" in src
    assert "Fade non-focused tendons" in src
    assert "Tendon line thickness" in src
    assert "Station markers" in src
    assert "focus_tendon" in tendon_src
    assert "fade_unfocused_tendons" in tendon_src
    assert "station_marker_mode" in tendon_src


def test_m41e_3d_control_panel_ux_and_smart_presets_are_present():
    src = _src()
    assert "COMMERCIAL.M4.1E" in README_SOURCE.read_text(encoding="utf-8")
    assert 'preset_options = ["Overview", "Left inspection", "Right inspection", "Single tendon focus", "Report clean", "Custom"]' in src
    assert "Advanced 3D display controls" in src
    assert 'preset_managed = inspection_preset != "Custom"' in src
    assert 'focus_control_enabled = inspection_preset in {"Custom", "Single tendon focus"}' in src
    assert "tendon_3d_fade_unfocused_inactive" in src
    assert "effective_fade_unfocused_tendons = fade_unfocused_tendons if effective_focus_tendon else False" in src
    assert "visible_families" in src
    assert "_tendon_3d_legend_items" in src


def test_code1_aashto_2020_section5_unit_safe_basis_ui_is_present():
    src = _src()
    assert "render_aashto_2020_unit_safe_basis_panel" in src
    assert "AASHTO LRFD Bridge Design Specifications, 9th Edition, 2020" in src
    assert "Section 5 Concrete Structures" in src
    assert "unit-safe wrapper" in src
    assert "standard_conversion_table" in src
    assert "psi_sqrt_fc_coefficient_to_ksi" in src
    assert "concrete_strength_guard_mpa" in src


def test_loads23_en_factors_no_duplicate_report_images():
    src = _src()
    readme = README_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.LOADS.30" in readme
    assert "wind_group_map_figure_card" in src
    assert "clean color reference map" in src
    assert "fig_ze_bridge_reference.svg" in src
    assert "V in this sketch is not wind velocity" in src
    assert "wind velocity is handled by V50, vb,0, and vb" in src
    assert "ze_bridge_reference_card" in src
    assert "height:255px" in src
    assert "object-fit:contain" in src
    assert "Compact separate card added" in src
    assert "user-provided bridge profile reference" in src
    assert "DPT wind group source" in src
    assert "loads_inline_subpage" in src
    assert "Figure note:" in src
    assert "without duplicate right-side report figures" in src
    assert 'show_report_image("fig_ws_factor_table_and_ze.png"' not in src


def test_loads30_cf_two_mode_track_alignment():
    src = _src()
    readme = README_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.LOADS.30" in readme
    assert "CF one-source rule" in src
    assert "Track alignment condition" in src
    assert "Straight track / no horizontal curve" in src
    assert "Curved track / finite radius" in src
    assert "condition_options = [\"Straight track / no horizontal curve\", \"Curved track / finite radius\"]" in src
    assert "R = ∞" in src
    assert "Zero for straight track" in src
    assert "Include CF in FEA adoption summary" in src
    assert "Assessment threshold (% LL)" in src
    assert "Reduction factor f" in src
    assert "FEA adoption" in src
    assert "Factor-only status" in src
    assert "V in km/h, R in m, and Lf in m" in src


def test_loads31_cf_assessment_adoption_status_split():
    src = _src()
    readme = README_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.LOADS.31" in readme
    assert "Engineering assessment" in src
    assert "FEA adoption status" in src
    assert "cf_engineering_assessment" in src
    assert "cf_fea_adoption_status" in src
    assert "Below threshold" in src
    assert "Above threshold / review" in src
    assert "Factor-only / not adopted in FEA" in src
    assert "Adopted in FEA summary" in src
    assert "cf_fea_adoption_mode" in src

def test_loads32_cf_straight_mode_hides_irrelevant_inputs():
    src = _src()
    readme = README_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.LOADS.32" in readme
    assert "Straight-track input mode" in src
    assert "No finite-radius CF inputs are active" in src
    assert "design speed V, curve radius R, loaded length Lf, assessment threshold, and Adopt span as Lf are hidden" in src
    assert "finite-radius CF inputs are not required" in src
    assert "Use only when the project explicitly adopts the finite-radius centrifugal action" in src


def test_loads33_crsh_minimal_input_geometry_trace():
    src = _src()
    defaults = (APP_SOURCE.parent / "core" / "bg40_defaults.py").read_text(encoding="utf-8")
    readme = README_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.LOADS.33" in readme
    assert "3.8 Creep and Shrinkage Parameters" in src
    assert "1.3.8 Creep and Shrinkage Parameters" not in src
    assert "CR&SH one-source rule" in src
    assert "CR&SH input assistant" in src
    assert "Relative humidity RH (%)" in src
    assert "Drying perimeter basis" in src
    assert "Outer perimeter only" in src
    assert "Outer + inner void perimeter" in src
    assert "update_crsh_derived_parameters" in src
    assert "V/S=\\frac{A_c}{u_{total}}" in src
    assert "h_0=\\frac{2A_c}{u_{total}}" in src
    assert "AASHTO unit-conversion / factor preview" in src
    assert "Prestress Losses handoff" in src
    assert "crsh_drying_perimeter_basis" in defaults


def test_loads34_crsh_drying_perimeter_guidance_and_tf_years():
    src = _src()
    readme = README_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.LOADS.34" in readme
    assert "Drying perimeter basis guidance" in src
    assert "inner void perimeter is included only when the void surface is exposed or ventilated" in src
    assert "Use <b>Outer perimeter only</b> when the internal void is sealed" in src
    assert "tf_days / 365.25" in src
    assert "tf_years" in src
    assert "≈ {tf_years:.1f} yr" in src


def test_loads35_eq_summary_and_fea_adoption_panel():
    src = _src()
    defaults = (APP_SOURCE.resolve().parents[0] / "core" / "bg40_defaults.py").read_text(encoding="utf-8")
    readme = README_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.LOADS.35" in readme
    assert "render_eq_result_summary_and_fea_adoption" in src
    assert "EQ result summary" in src
    assert "FEA adoption" in src
    assert "EQX = Cs × W" in src
    assert "EQY = Cs × W" in src
    assert "AASHTO LRFD 2020 Table 3.10.7.1-1" in src
    assert "seismic_fea_adoption_mode" in defaults
    assert "seismic_weight_source" in defaults


def test_loads36_eq_ui_polish_schema_and_adoption_clarity():
    src = _src()
    defaults = (APP_SOURCE.resolve().parents[0] / "core" / "bg40_defaults.py").read_text(encoding="utf-8")
    readme = README_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.LOADS.36" in readme
    assert "render_sidebar_schema_status" not in src
    assert "COEFFICIENT TRACE" in src
    assert "NUMERIC EQ FORCE" in src
    assert "NOT GENERATED HERE" in src
    assert "No duplicate W input is created in Loads" in src
    assert "render_eq_response_spectrum_canvas" in src
    assert "DPT Equivalent-Static Response Spectrum" in src
    assert "Coefficient trace only — numeric EQ force generated in FEA model" in defaults


def test_loads37_fea_load_input_summary_renaming_and_handoff_table():
    src = _src()
    schema_src = (APP_SOURCE.resolve().parents[0] / "core" / "report_schema.py").read_text(encoding="utf-8")
    readme = README_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.LOADS.37" in readme
    assert "3.10 FEA Load Input Summary" in schema_src
    assert "3.10 FEA Load Input Summary" in src
    assert "3.10 FEA Summary" in src  # migration alias for old UI/session state
    assert "single handoff table for load patterns, coefficients, and parameter traces" in src
    assert "Quantity type" in src
    assert "Source:" in src
    assert "EQX/EQY = Cs × W" in src
    assert "Do not duplicate self-weight" in src
    assert "CR&SH" in src and "Long-term parameter handoff" in src


def test_loads38_fea_load_input_summary_table_polish():
    src = _src()
    readme = README_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.LOADS.38" in readme
    assert "render_fea_load_input_handoff_table" in src
    assert "HANDOFF READY" in src
    assert "Ready for FEA input review; not a second calculator" in src
    assert "Quantity type" in src
    assert "Adopted value / basis" in src
    assert "Required FEA action / engineer check" in src
    assert "Do not enter W here" in src
    assert "not as an additive duplicate of WS" in src
    assert "This table is display-only" in src


def test_loads39_fea_load_input_summary_legend_and_checklist():
    src = _src()
    readme = README_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.LOADS.39" in readme
    assert "render_fea_handoff_status_legend" in src
    assert "Handoff status legend" in src
    assert "FEA-owned" in src
    assert "Adopted envelope" in src
    assert "Coefficient trace" in src
    assert "render_fea_load_input_review_checklist" in src
    assert "FEA input review checklist" in src
    assert "Map load patterns" in src
    assert "Confirm directions" in src
    assert "Preserve source ownership" in src
    assert "Document overrides" in src
    assert "page-break-inside:avoid" in src
    assert "does not create new load inputs" in src



def test_loads40_loads_closeout_and_reportqa_handoff():
    src = _src()
    validation_src = VALIDATION_SOURCE.read_text(encoding="utf-8")
    readme = README_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.LOADS.40" in readme
    assert 'PROJECT_SCHEMA_VERSION = "0.5.3-commercial-fea5b1-axis-convention-uls-review-polish"' in validation_src
    assert "render_loads_workspace_closeout_panel" in src
    assert "Loads workspace closeout and Report / QA handoff" in src
    assert "Closed for load-source scope" in src
    assert "render_report_qa_loads_handoff_snapshot" in src
    assert "3 Loads — Report / QA handoff" in src
    assert "Report / QA now consumes the Loads closeout rows" in src
    assert "does not rerun load calculations" in src
    assert "Formula logic for DL, SDL, LL+IM, LF/HF, CF, Wind, CR&SH, EQ, and detailed prestress losses was not changed" in src



def test_psloss1_source_gate_and_jacking_force_guard():
    src = _src()
    defaults = (APP_SOURCE.resolve().parents[0] / "core" / "bg40_defaults.py").read_text(encoding="utf-8")
    readme = README_SOURCE.read_text(encoding="utf-8")
    validation_src = VALIDATION_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.PSLOSS.1" in readme
    assert 'PROJECT_SCHEMA_VERSION = "0.5.3-commercial-fea5b1-axis-convention-uls-review-polish"' in validation_src
    assert "render_prestress_losses_source_gate_panel" in src
    assert "Prestress Losses Source Gate" in src
    assert "SOURCE BLOCKED" in src
    assert "READY FOR LOSS CALCULATION" in src
    assert "Adopted tendon source" in src
    assert "CR&SH parameters" in src
    assert "Jacking-force interpretation" in src
    assert "do not double" in src.lower()
    assert "render_report_qa_prestress_losses_handoff_snapshot" in src
    assert "jacking_operation_basis" in defaults
    assert "jacking_force_interpretation" in defaults


def test_psloss2_stressing_basis_gate_and_tendon_action():
    src = _src()
    defaults = (APP_SOURCE.resolve().parents[0] / "core" / "bg40_defaults.py").read_text(encoding="utf-8")
    readme = README_SOURCE.read_text(encoding="utf-8")
    validation_src = VALIDATION_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.PSLOSS.2" in readme
    assert 'PROJECT_SCHEMA_VERSION = "0.5.3-commercial-fea5b1-axis-convention-uls-review-polish"' in validation_src
    assert "_psloss_stressing_basis_state" in src
    assert "STRESSING BASIS" in src
    assert "Tendon adoption action required" in src
    assert "Tendon adoption and blocked-input checklist" in src
    assert "Stressing basis / JackFrom gate" in src
    assert "One-end stressing" in src
    assert "Two-end stressing" in src
    assert "Mixed one-end stressing by tendon" in src
    assert "do not double Aps,total" in src or "must not double Aps,total" in src
    assert "stressing_basis_gate_status" in defaults
    assert "stressing_mode_basis" in defaults


def test_psloss3_adopted_tendon_and_formula_readiness_register():
    src = _src()
    defaults = (APP_SOURCE.resolve().parents[0] / "core" / "bg40_defaults.py").read_text(encoding="utf-8")
    readme = README_SOURCE.read_text(encoding="utf-8")
    validation_src = VALIDATION_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.PSLOSS.3" in readme
    assert 'PROJECT_SCHEMA_VERSION = "0.5.3-commercial-fea5b1-axis-convention-uls-review-polish"' in validation_src
    assert "_psloss_adopted_tendon_readiness_rows" in src
    assert "_psloss_formula_readiness_rows" in src
    assert "PSLOSS.25 calculation-readiness snapshot" in src
    assert "Adopted tendon source readiness" in src
    assert "Loss calculation readiness register" in src
    assert "PREVIEW READY — HANDOFF TO 4.6" in src
    assert "STAGE REVIEW REQUIRED" in src
    assert "effective-prestress" in src
    assert "loss_calculation_readiness_status" in defaults
    assert "loss_readiness_basis" in defaults


def test_psloss4_friction_source_model_and_preview_gate():
    src = _src()
    defaults = (APP_SOURCE.resolve().parents[0] / "core" / "bg40_defaults.py").read_text(encoding="utf-8")
    readme = README_SOURCE.read_text(encoding="utf-8")
    validation_src = VALIDATION_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.PSLOSS.4" in readme
    assert 'PROJECT_SCHEMA_VERSION = "0.5.3-commercial-fea5b1-axis-convention-uls-review-polish"' in validation_src
    assert "render_prestress_friction_source_model" in src
    assert "4.2 Friction Loss Source Model" in src
    assert "Friction coefficient input assistant" in src
    assert "External tendon friction coefficient μ" in src
    assert "Wobble coefficient K (1/m)" in src
    assert "Tendon-by-tendon friction preview" in src
    assert "adopted station profile" in src
    assert "not from keyed BG40 friction groups" in src
    assert "two-end; nearer-end preview" in src
    assert "do not double Pj" in src
    assert "friction_source_model_status" in defaults
    assert "friction_preview_basis" in defaults


def test_tendon2_jackfrom_source_note_visible_and_traced():
    src = _src()
    readme = README_SOURCE.read_text(encoding="utf-8")
    validation_src = VALIDATION_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.TENDON.2" in readme
    assert 'PROJECT_SCHEMA_VERSION = "0.5.3-commercial-fea5b1-axis-convention-uls-review-polish"' in validation_src
    assert "Stressing-basis source note" in src
    assert "General tendon table · JackFrom field" in src
    assert "not a duplicate Prestress Losses input" in src


def test_psloss5_friction_formula_trace_and_report_summary():
    src = _src()
    defaults = (APP_SOURCE.resolve().parents[0] / "core" / "bg40_defaults.py").read_text(encoding="utf-8")
    readme = README_SOURCE.read_text(encoding="utf-8")
    validation_src = VALIDATION_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.PSLOSS.5" in readme
    assert 'PROJECT_SCHEMA_VERSION = "0.5.3-commercial-fea5b1-axis-convention-uls-review-polish"' in validation_src
    assert "Physical friction design-basis summary" in src
    assert "Friction formula and variable trace" in src
    assert "Governing tendon calculation walkthrough" in src
    assert "Tendon-by-tendon friction calculation trace" in src
    assert "ΔfpF = fpj[1 − exp{−(Kx + μα)}]" in src
    assert "exp[-(Kx+μα)]" in src
    assert "_psloss_friction_calculation_rows" in src
    assert "_psloss_friction_report_summary_rows" in src
    assert "_psloss_friction_governing_walkthrough_rows" in src
    assert "friction_formula_trace_status" in defaults
    assert "friction_formula_trace_basis" in defaults


def test_psloss6_friction_equation_cards_and_consistent_formula_block():
    src = _src()
    defaults = (APP_SOURCE.resolve().parents[0] / "core" / "bg40_defaults.py").read_text(encoding="utf-8")
    readme = README_SOURCE.read_text(encoding="utf-8")
    validation_src = VALIDATION_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.PSLOSS.6" in readme
    assert 'PROJECT_SCHEMA_VERSION = "0.5.3-commercial-fea5b1-axis-convention-uls-review-polish"' in validation_src
    assert "Friction loss result summary" in src
    assert "_render_loss_result_summary_cards_for_friction" in src
    assert "FRICTION LOSS SUMMARY" in src
    assert "MAX FRICTION LOSS" in src
    assert "MIN fpx AFTER FRICTION" in src
    assert "_render_psloss_friction_equation_block" in src
    assert "st.latex(r\"\\Delta f_{pF}" in src
    assert "Governing tendon substitution" in src
    assert "Substitution blocked" in src
    assert "friction_loss_summary_card_status" in defaults
    assert "friction_loss_summary_card_basis" in defaults


def test_psloss7_friction_governing_tie_and_full_tendon_report_polish():
    src = _src()
    defaults = (APP_SOURCE.resolve().parents[0] / "core" / "bg40_defaults.py").read_text(encoding="utf-8")
    readme = README_SOURCE.read_text(encoding="utf-8")
    validation_src = VALIDATION_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.PSLOSS.7" in readme
    assert 'PROJECT_SCHEMA_VERSION = "0.5.3-commercial-fea5b1-axis-convention-uls-review-polish"' in validation_src
    assert "_psloss_friction_governing_tie_results" in src
    assert "_psloss_friction_governing_label" in src
    assert "_show_full_tendon_report_table" in src
    assert "Governing tendon(s)" in src
    assert "Governing tie set" in src
    assert "showing {total_rows} of {total_rows} rows" in src
    assert "friction_governing_tie_status" in defaults
    assert "friction_full_tendon_report_status" in defaults


def test_psloss9_anchor_set_distribution_and_friction_coupling_preview():
    src = _src()
    readme = README_SOURCE.read_text(encoding="utf-8")
    validation_src = VALIDATION_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.PSLOSS.9" in readme
    assert 'PROJECT_SCHEMA_VERSION = "0.5.3-commercial-fea5b1-axis-convention-uls-review-polish"' in validation_src
    assert "_psloss_anchor_distribution_results" in src
    assert "_render_psloss_anchor_distribution_equation_block" in src
    assert "Anchor-set distribution / friction-coupling preview" in src
    assert "\\Delta f_{pA}(s)=\\max" in src
    assert "Minimum fpx after F+A" in src
    assert "equivalent quick check" in src
    assert "not final effective-prestress adoption" in src


def test_psloss10_anchor_set_distribution_wording_and_variable_trace_polish():
    src = _src()
    readme = README_SOURCE.read_text(encoding="utf-8")
    validation_src = VALIDATION_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.PSLOSS.10" in readme
    assert 'PROJECT_SCHEMA_VERSION = "0.5.3-commercial-fea5b1-axis-convention-uls-review-polish"' in validation_src
    assert "Equivalent quick-check route" in src
    assert "The position-dependent friction-coupled distribution preview is shown below" in src
    assert "_psloss_anchor_distribution_variable_rows" in src
    assert "2ΔfpF(s)" in src
    assert "ΔfpA,0" in src
    assert "s_a" in src
    assert "fpx,F+A(s)" in src
    assert "1000" in src
    assert "Distribution-variable definition" in src


def test_psloss11_elastic_shortening_source_model_and_stage_preview():
    src = _src()
    readme = README_SOURCE.read_text(encoding="utf-8")
    validation_src = VALIDATION_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.PSLOSS.11" in readme
    assert 'PROJECT_SCHEMA_VERSION = "0.5.3-commercial-fea5b1-axis-convention-uls-review-polish"' in validation_src
    assert "render_prestress_elastic_shortening_source_model" in src
    assert "_psloss_elastic_shortening_source_state" in src
    assert "_psloss_elastic_shortening_sequence_rows" in src
    assert "Elastic-shortening equation block" in src
    assert "\\Delta f_{pES,avg}" in src
    assert "f_cgp" in src
    assert "stage-controlled engineering input" in src
    assert "Not final effective prestress" in src

def test_psloss12_elastic_shortening_summary_consistency_and_sequence_basis():
    src = _src()
    readme = README_SOURCE.read_text(encoding="utf-8")
    validation_src = VALIDATION_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.PSLOSS.12" in readme
    assert 'PROJECT_SCHEMA_VERSION = "0.5.3-commercial-fea5b1-axis-convention-uls-review-polish"' in validation_src
    assert "MAX SEQUENCE ES LOSS" in src
    assert "fpx,avg" in src
    assert "fpx after average ES" in src
    assert "Minimum fpx after sequence ES" in src
    assert "Sequence basis" in src
    assert "Transparent preview order only" in src
    assert "average-vs-sequence" in src or "average-vs-sequence reporting" in src
    assert "Stage/sequence review required" in src



def test_psloss13_loss_percent_basis_non_cumulative_standard():
    src = _src()
    readme = README_SOURCE.read_text(encoding="utf-8")
    validation_src = VALIDATION_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.PSLOSS.13" in readme
    assert 'PROJECT_SCHEMA_VERSION = "0.5.3-commercial-fea5b1-axis-convention-uls-review-polish"' in validation_src
    assert "_loss_percent_basis_rows" in src
    assert "_render_loss_percent_basis_note" in src
    assert "_append_loss_percent_basis_report_rows" in src
    assert "Average %loss basis" in src
    assert "area-weighted average loss / f<sub>pj</sub> × 100" in src
    assert "Do not add percentages" in src
    assert "Final effective-prestress combination is controlled by <b>4.6 Effective Prestress</b>" in src
    assert "Combination / adoption rule" in src



def test_psloss14_header_and_next_step_consistency_cleanup():
    src = _src()
    readme = README_SOURCE.read_text(encoding="utf-8")
    validation_src = VALIDATION_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.PSLOSS.14" in readme
    assert 'PROJECT_SCHEMA_VERSION = "0.5.3-commercial-fea5b1-axis-convention-uls-review-polish"' in validation_src
    assert "PSLOSS.22 keeps the friction report trace closed" in src
    assert "PSLOSS.22 keeps the anchor-set distribution trace closed" in src
    assert "PSLOSS.22 keeps the elastic-shortening preview closed" in src
    assert "PSLOSS.25 calculation-readiness snapshot" in src
    assert "EFFECTIVE PRESTRESS" in src
    assert "4.6 Effective Prestress final combination gate is next" in src
    assert "segmental_box_girder_ui_bridge1_summary.md" in src


def test_psloss16_18_creep_shrinkage_complete_preview():
    src = _src()
    readme = README_SOURCE.read_text(encoding="utf-8")
    validation_src = VALIDATION_SOURCE.read_text(encoding="utf-8")
    defaults_src = DEFAULTS_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.PSLOSS.16–18" in readme
    assert 'PROJECT_SCHEMA_VERSION = "0.5.3-commercial-fea5b1-axis-convention-uls-review-polish"' in validation_src
    assert '"segment_age_at_transport_days": 30.0' in defaults_src
    assert "render_prestress_creep_shrinkage_stage_source_map" in src
    assert "Segment age at transport (days)" in src
    assert "default = 30 days" in src
    assert "span assembly duration" in src.lower()
    assert "t_{jack}=t_{transport}+t_{assembly}" in src
    assert "3.8 ti RECONCILIATION" in src
    assert "Calculation route" in src
    assert "Refined / time-step — Recommended" in src
    assert "Approximate — Quick check only" in src
    assert "Advanced segment-age table — Future / gated" in src
    assert "Creep / shrinkage loss result summary" in src
    assert "Refined / time-step equation trace" in src
    assert "Approximate quick-check comparison" in src
    assert "Effective-prestress handoff" in src


def test_psloss20_route_dependent_handoff_and_selected_age_symbol_polish():
    src = _src()
    readme = README_SOURCE.read_text(encoding="utf-8")
    validation_src = VALIDATION_SOURCE.read_text(encoding="utf-8")
    defaults_src = DEFAULTS_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.PSLOSS.20" in readme
    assert 'PROJECT_SCHEMA_VERSION = "0.5.3-commercial-fea5b1-axis-convention-uls-review-polish"' in validation_src
    assert '"crsh_time_step_age_source": "Adopt computed prestressing age t_jack from 4.5 construction map"' in defaults_src
    assert "Time-step age source" in src
    assert "Use computed t_jack from 4.5 construction map" in src
    assert "Use 3.8 CR&SH ti" in src
    assert "Keep REVIEW / do not adopt" in src
    assert "_psloss_crsh_handoff_rows" in src
    assert "NOT ELIGIBLE FOR FINAL" in src
    assert "Comparison only because approximate route is currently selected" in src
    assert "Selected time-step age source" in src

    assert "t_start as the selected time-step start-age symbol" in src
    assert "\\psi(t_f,t_{start})" in src
    assert "\\Delta f_{pCR}=\\frac{E_p}{E_{ci}} f_{cgp}\\,\\psi(t_f,t_{start})" in src
    assert "ψ selected" in src
    assert "ktd(tf) − ktd(t_start)" in src


def test_psloss21_relaxation_source_model_and_gated_preview():
    src = _src()
    readme = README_SOURCE.read_text(encoding="utf-8")
    defaults_src = DEFAULTS_SOURCE.read_text(encoding="utf-8")
    validation_src = VALIDATION_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.PSLOSS.21" in readme
    assert 'PROJECT_SCHEMA_VERSION = "0.5.3-commercial-fea5b1-axis-convention-uls-review-polish"' in validation_src
    assert '"relaxation_calculation_method": "BG40 low-relaxation interaction cap — Recommended audit route"' in defaults_src
    assert '"relaxation_steel_type": "Low-relaxation strand"' in defaults_src
    assert '"relaxation_stress_basis": "Use fpj / jacking-stress preview"' in defaults_src
    assert "Relaxation source model and gated preview" in src
    assert "Relaxation calculation method" in src
    assert "Prestressing steel relaxation class" in src
    assert "Relaxation stress basis" in src
    assert "BG40 low-relaxation interaction cap — Recommended audit route" in src
    assert "AASHTO refined R1/R2 preview — Diagnostic" in src
    assert "Low-relaxation 2.4 ksi quick check" in src
    assert "Manufacturer relaxation data — Future / gated" in src
    assert "\\Delta f_{pR1}=\\frac{f_{pt}}{K_L}" in src
    assert "\\Delta f_{pR2}=\\Delta f_{pR1}" in src
    assert "Relaxation preview" in src
    assert "4.6 must combine relaxation" in src
    assert "segmental_box_girder_ui_bridge1_summary.md" in src


def test_psloss22_time_dependent_loss_tabs_and_rename():
    src = _src()
    readme = README_SOURCE.read_text(encoding="utf-8")
    validation_src = VALIDATION_SOURCE.read_text(encoding="utf-8")
    report_schema_src = REPORT_SCHEMA_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.PSLOSS.22" in readme
    assert 'PROJECT_SCHEMA_VERSION = "0.5.3-commercial-fea5b1-axis-convention-uls-review-polish"' in validation_src
    assert "4.5 Time-Dependent Losses" in report_schema_src
    assert "4.5 Creep / Shrinkage" not in report_schema_src
    assert "4.5 Time-Dependent Losses Source Model" in src
    assert "Overview" in src
    assert "Creep" in src
    assert "Shrinkage" in src
    assert "Relaxation" in src
    assert "Handoff to 4.6" in src
    assert "Internal tabs: Creep / Shrinkage / Relaxation" in src
    assert "_render_time_dependent_overview_tab" in src
    assert "_render_time_dependent_creep_tab" in src
    assert "_render_time_dependent_shrinkage_tab" in src
    assert "_render_time_dependent_handoff_tab" in src
    assert "Time-dependent loss result summary" in src
    assert "AVG TD LOSS" in src


def test_psloss23_time_dependent_handoff_summary_and_relaxation_wording_polish():
    src = _src()
    readme = README_SOURCE.read_text(encoding="utf-8")
    validation_src = VALIDATION_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.PSLOSS.23" in readme
    assert 'PROJECT_SCHEMA_VERSION = "0.5.3-commercial-fea5b1-axis-convention-uls-review-polish"' in validation_src
    assert "PSLOSS.26D organizes relaxation as a BG40 low-relaxation interaction-cap audit" in src
    assert "PSLOSS.23 keeps route-dependent time-dependent-loss handoff behavior" in src
    assert "TD preview subtotal" in src
    assert "fpx after TD preview" in src
    assert "Selected time-dependent subtotal = creep + shrinkage + relaxation" in src
    assert "Refined TD preview subtotal" in src
    assert "fpx after refined TD preview" in src
    assert "segmental_box_girder_ui_bridge1_summary.md" in src


def test_psloss24_crsh_source_gate_compatibility_fix():
    src = _src()
    readme = README_SOURCE.read_text(encoding="utf-8")
    validation_src = VALIDATION_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.PSLOSS.24" in readme
    assert 'PROJECT_SCHEMA_VERSION = "0.5.3-commercial-fea5b1-axis-convention-uls-review-polish"' in validation_src
    assert "def _psloss_crsh_source_gate_handoff_rows" in src
    assert 'if "factors" not in state:' in src
    assert "Compatibility-safe 4.1 CR&SH source-gate handoff rows" in src
    assert "SOURCE PARTIAL" in src
    assert "def _psloss_crsh_handoff_rows" in src
    assert "f = state.get(\"factors\", {})" in src
    assert "segmental_box_girder_ui_bridge1_summary.md" in src


def test_psloss25_general_readiness_register_next_step_polish():
    src = _src()
    readme = README_SOURCE.read_text(encoding="utf-8")
    validation_src = VALIDATION_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.PSLOSS.25" in readme
    assert "COMMERCIAL.UI.PSLOSS.1" in readme
    assert 'PROJECT_SCHEMA_VERSION = "0.5.3-commercial-fea5b1-axis-convention-uls-review-polish"' in validation_src
    assert "PSLOSS.25 calculation-readiness snapshot" in src
    assert "EFFECTIVE PRESTRESS" in src
    assert "4.6 Effective Prestress final combination gate is next" in src
    assert "PREVIEW READY — HANDOFF TO 4.6" in src
    assert "DISTRIBUTION PREVIEW READY — HANDOFF TO 4.6" in src
    assert "PREVIEW READY / AGE SOURCE REVIEW REQUIRED" in src
    assert "PREVIEW READY / SOURCE REVIEW REQUIRED" in src
    assert "NEXT MILESTONE" in src
    assert "component-combination rule" in src
    assert "segmental_box_girder_ui_bridge1_summary.md" in src


def test_ui_psloss1_prestress_losses_uses_loads_style_horizontal_subpage_nav():
    src = _src()
    readme = README_SOURCE.read_text(encoding="utf-8")
    validation_src = VALIDATION_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.UI.PSLOSS.1" in readme
    assert 'PROJECT_SCHEMA_VERSION = "0.5.3-commercial-fea5b1-axis-convention-uls-review-polish"' in validation_src
    assert "def _sync_psloss_inline_subpage_to_sidebar" in src
    assert "psloss_inline_subpage" in src
    assert 'st.radio(\n        "Prestress Losses subpage"' in src
    assert "horizontal=True" in src
    assert "label_visibility=\"collapsed\"" in src
    assert "on_change=_sync_psloss_inline_subpage_to_sidebar" in src
    assert "Dedicated Prestress Losses workspace" in src
    assert "Active subpage = {selected_psloss_subpage}" in src

def test_ui_bridge1_bridge_geometry_uses_loads_style_horizontal_subpage_nav():
    src = _src()
    readme = README_SOURCE.read_text(encoding="utf-8")
    validation_src = VALIDATION_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.UI.BRIDGE.1" in readme
    assert 'PROJECT_SCHEMA_VERSION = "0.5.3-commercial-fea5b1-axis-convention-uls-review-polish"' in validation_src
    assert "def _sync_bridge_inline_subpage_to_sidebar" in src
    assert "bridge_inline_subpage" in src
    assert 'st.radio(\n        "Bridge Geometry / Section Properties subpage"' in src
    assert "horizontal=True" in src
    assert 'label_visibility="collapsed"' in src
    assert "on_change=_sync_bridge_inline_subpage_to_sidebar" in src
    assert "Dedicated Bridge Geometry / Section Properties workspace" in src
    assert "Active subpage = {selected_bridge_subpage}" in src


def test_ui_header1_removes_global_project_context_banner_card():
    src = _src()
    validation_src = VALIDATION_SOURCE.read_text(encoding="utf-8")
    readme = README_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.UI.HEADER.1" in readme
    assert 'PROJECT_SCHEMA_VERSION = "0.5.3-commercial-fea5b1-axis-convention-uls-review-polish"' in validation_src
    assert "hero-card" not in src
    assert "Active workspace:" not in src
    assert 'small_context("Workspace"' in src
    assert 'small_context("Subpage"' in src


def test_ui_sidebar2_removes_project_status_and_global_figure_system_from_sidebar():
    src = _src()
    readme = README_SOURCE.read_text(encoding="utf-8")
    validation_src = VALIDATION_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.UI.SIDEBAR.1" in readme
    assert "COMMERCIAL.UI.SIDEBAR.2" in readme
    assert 'PROJECT_SCHEMA_VERSION = "0.5.3-commercial-fea5b1-axis-convention-uls-review-polish"' in validation_src
    assert "PROJECT STATUS" not in src
    assert "QA gate ready" not in src
    assert "ULS Flexure max DCR" not in src
    assert "Shear/Torsion D/C" not in src
    assert "render_sidebar_schema_status" not in src
    assert "**FIGURE SYSTEM**" not in src
    assert "global Figure System control" in src
    assert "ACTIVE CONTEXT" in src
    assert "Load Project JSON" in src
    assert "COMMERCIAL.UI.SIDEBAR.2 removes the global Figure System control" in src


def test_psloss26a_effective_prestress_loss_audit_and_formula_polish():
    src = _src()
    readme = README_SOURCE.read_text(encoding="utf-8")
    validation_src = VALIDATION_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.PSLOSS.26A" in readme
    assert 'PROJECT_SCHEMA_VERSION = "0.5.3-commercial-fea5b1-axis-convention-uls-review-polish"' in validation_src
    assert "4.6 Effective Prestress Source Map, Loss Audit, and Root-Cause Diagnosis" in src
    assert "Loss audit against calculation report" in src
    assert "Calculation report comparison inputs (% of fpi)" in src
    assert "_psloss_effective_report_comparison_rows" in src
    assert "_psloss_effective_driver_rows" in src
    assert "_psloss_effective_fcgp_sensitivity_rows" in src
    assert "REPRESENTATIVE TOTAL LOSS" in src
    assert "REPRESENTATIVE fpe" in src
    assert "Formula trace:" in src
    assert "Total loss (%) = (fpi − fpe) / fpi × 100" in src
    assert "f_cgp BASIS" in src
    assert "ES + creep driver" in src
    assert "station/tendon effective-prestress basis is not yet locked" in src



def test_psloss26b_high_loss_root_cause_diagnosis():
    src = _src()
    readme = README_SOURCE.read_text(encoding="utf-8")
    validation_src = VALIDATION_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.PSLOSS.26B" in readme
    assert 'PROJECT_SCHEMA_VERSION = "0.5.3-commercial-fea5b1-axis-convention-uls-review-polish"' in validation_src
    assert "4.6 Effective Prestress Source Map, Loss Audit, and Root-Cause Diagnosis" in src
    assert "High-loss root-cause diagnosis" in src
    assert "_psloss_effective_root_cause_rows" in src
    assert "_psloss_effective_fcgp_stage_sweep_rows" in src
    assert "f_cgp stage-basis sweep" in src
    assert "Dominant contributor" in src
    assert "ROOT-CAUSE DRIVER" in src
    assert "f_cgp coupling evidence" in src
    assert "Trial stage-stress basis" in src
    assert "The app can identify the driver without report inputs" in src


def test_psloss26d_creep_relaxation_report_match_audit():
    src = _src()
    readme = README_SOURCE.read_text(encoding="utf-8")
    validation_src = VALIDATION_SOURCE.read_text(encoding="utf-8")
    defaults_src = DEFAULTS_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.PSLOSS.26D" in readme
    assert 'PROJECT_SCHEMA_VERSION = "0.5.3-commercial-fea5b1-axis-convention-uls-review-polish"' in validation_src
    assert '"crsh_creep_time_basis": "BG40 report-match incremental Δktd — Recommended audit route"' in defaults_src
    assert '"relaxation_calculation_method": "BG40 low-relaxation interaction cap — Recommended audit route"' in defaults_src
    assert "_psloss_crsh_creep_basis_options" in src
    assert "BG40 report-match incremental Δktd" in src
    assert "AASHTO direct elapsed ktd — Diagnostic comparison" in src
    assert "_psloss_crsh_creep_basis_audit_rows" in src
    assert "ψ report-match" in src
    assert "creep_loss_delta_mpa" in src
    assert "BG40 low-relaxation interaction cap" in src
    assert "interaction_raw_mpa" in src
    assert "CAPPED AT 0.0 MPa" in src
    assert "0.30[20.0" in src
    assert "BG40 capped interaction relaxation" in src
    assert "psloss26a_report_friction_pct" in src
    assert "psloss26a_report_fpe_mpa" in src
    assert "PREVIEW / REVIEW REQUIRED" in src


def test_tendon24p_cleans_print_text_layer_and_verifies_detailed_qa_payload():
    src = _src()
    assert 'Detailed adopted tendon tables / QA' in src
    assert 'Compact design-use summary' in src
    assert '[data-testid="stSidebarCollapseButton"]' in src
    assert 'button[aria-label="Open sidebar"]' in src
    assert 'button[aria-label="Close sidebar"]' in src
    assert '::-webkit-scrollbar-button' in src
    assert 'scrollbar-width:none' in src
    assert '[data-testid="stIconMaterial"]' in src
    assert 'Detailed QA integrity' in src
    assert 'build_tendon_detailed_qa_integrity' in src
    assert 'TENDON.2.4Q' in src
def test_fea5b_uls_force_review_charts_and_nested_subpages():
    src = _src()
    readme = README_SOURCE.read_text(encoding="utf-8")
    validation_src = VALIDATION_SOURCE.read_text(encoding="utf-8")
    report_schema_src = REPORT_SCHEMA_SOURCE.read_text(encoding="utf-8")
    defaults_src = DEFAULTS_SOURCE.read_text(encoding="utf-8")
    assert "COMMERCIAL.FEA.5B1" in readme
    assert 'PROJECT_SCHEMA_VERSION = "0.5.3-commercial-fea5b1-axis-convention-uls-review-polish"' in validation_src
    assert '"stage_imports"' in defaults_src
    assert '"5.1 Import / Data Hub"' in report_schema_src
    assert '"5.2 ULS Force Review"' in report_schema_src
    assert '"5.3 Transfer Stage"' in report_schema_src
    assert '"5.4 Final Service SLS"' in report_schema_src
    assert "read_csibridge_force_workbook" in src
    assert "COMPONENT ENVELOPE" in src
    assert "SINGLE STATE" in src
    assert "Sections 6–8 are not yet connected" in src
    assert "previously validated source remains active" in src
    assert "P (Axial)" in src
    assert "V2 (Vy)" in src
    assert "T (Torsion)" in src
    assert "M3 (Mx)" in src
    assert "uls_component_envelope_figure" in src
    assert "Axis / force convention" in src
    assert "P → Axial" in src
    assert "V2 → Vy" in src
    assert "M3 → Mx" in src
    assert "Dominant sources across section cuts" in src
    assert "Detailed {meta['title']} scalar envelope / QA" in src
    assert "Sections 6–7 remain disconnected" in src
