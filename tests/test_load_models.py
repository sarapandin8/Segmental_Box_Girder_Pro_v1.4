from core.bg40_defaults import BG40_DEFAULT
from core.dpt_seismic import dpt_general_spectrum, lookup_general_ss_s1, seismic_design_category_from_sd1, seismic_design_category_from_sds
from core.load_models import en_dynamic_factor_standard_maintenance, hunting_force_en1991, longitudinal_force_en1991, sdl_totals, wind_load_en1991_dpt, wind_load_en1991_dpt_auto, wind_load_factor_c_bridge


def test_dead_load_report_unit_weights_are_in_default_schema():
    dl = BG40_DEFAULT["load_components"]
    assert "dead_load_definition" in dl
    assert "weight of the entire structure" in dl["dead_load_definition"]
    weights = {row["Material"]: row for row in dl["dead_load_unit_weights"]}
    assert weights["Steel"]["Unit Weight (kN/m³)"] == 76.9
    assert weights["Cast iron"]["Mass Density (kg/m³)"] == 7200
    assert weights["Plain concrete"]["Unit Weight (kN/m³)"] == 23.5
    assert weights["Reinforced concrete"]["Unit Weight (kN/m³)"] == 24.5
    assert weights["Prestressed concrete"]["Mass Density (kg/m³)"] == 2500
    assert weights["Ballast"]["Unit Weight (kN/m³)"] == 18.6


def test_sdl_totals_read_from_single_component_table():
    out = sdl_totals(BG40_DEFAULT["load_components"]["sdl_components"])
    assert abs(out["single_total"] - 62.14) < 0.02
    assert abs(out["double_total"] - 84.19) < 0.02


def test_dynamic_factor_bg40_report_value():
    out = en_dynamic_factor_standard_maintenance(35.0, 40.0)
    assert abs(out["Lphi_m"] - 35.0) < 1e-9
    assert abs(out["phi"] - 1.1079) < 0.001


def test_longitudinal_force_bg40():
    out = longitudinal_force_en1991(40.0, 40.0)
    assert out["Qlak_raw_kn"] == 1320.0
    assert out["Qlak_kn"] == 1000.0
    assert out["Qlbk_kn"] == 800.0
    assert out["LF_design_kn"] == 1000.0
    assert out["LF_design_kn_m"] == 25.0


def test_hunting_force_is_not_reduced_for_alpha_below_one_by_default():
    out = hunting_force_en1991(100.0, 0.8, False)
    assert out["HF_adopted_kn"] == 100.0
    assert "not reduced" in out["decision_basis"]


def test_wind_load_bg40_values():
    out = wind_load_en1991_dpt(1.25, 25.0, 4.6, 5.7, 3.9, 6.8, 40.0)
    assert abs(out["WSsuper_kn_m"] - 7.01) < 0.05
    assert abs(out["WSsuper_WL_kn_m"] - 15.14) < 0.10


def test_dpt_seed_lookup_sadao_songkhla():
    out = lookup_general_ss_s1("สงขลา", "สะเดา")
    assert out["found"] is True
    assert abs(float(out["Ss"]) - 0.079) < 1e-9
    assert abs(float(out["S1"]) - 0.084) < 1e-9


def test_dpt_seismic_general_workflow_sadao_soil_d():
    out = dpt_general_spectrum(0.079, 0.084, "D", 0.835, 1.25, 2.0)
    assert abs(out["Fa"] - 1.6) < 1e-9
    assert abs(out["Fv"] - 2.4) < 1e-9
    assert out["Cs"] >= 0.01
    assert out["category_governing"] in {"ก", "ข", "ค", "ง"}


def test_dpt_design_category_tables_reproduce_boundaries():
    assert seismic_design_category_from_sds(0.10, 1.0) == "ก"
    assert seismic_design_category_from_sds(0.20, 1.25) == "ข"
    assert seismic_design_category_from_sds(0.40, 1.5) == "ง"
    assert seismic_design_category_from_sd1(0.08, 1.0) == "ข"
    assert seismic_design_category_from_sd1(0.16, 1.25) == "ค"


def test_dpt_m3b_full_database_contains_many_general_rows():
    from core.dpt_seismic import load_general_location_database
    db = load_general_location_database()
    assert len(db) >= 800
    assert "source_table" in db.columns
    assert "source_standard_page" in db.columns


def test_dpt_m3b_lookup_sadao_from_full_database():
    from core.dpt_seismic import lookup_general_ss_s1
    out = lookup_general_ss_s1("สงขลา", "สะเดา")
    assert out["found"] is True
    assert abs(out["Ss"] - 0.079) < 1e-9
    assert abs(out["S1"] - 0.084) < 1e-9
    assert out["source_table"] == "Table 1.4-1"


def test_dpt_m3b_bangkok_basin_zone_detection():
    from core.dpt_seismic import lookup_bangkok_basin_zone
    out = lookup_bangkok_basin_zone("กรุงเทพมหานคร", "บางรัก")
    assert out["found"] is True
    assert out["region"] == "Bangkok Basin"
    assert int(out["zone"]) == 5


def test_dpt_m3b_bangkok_equiv_static_zone5_5_percent():
    from core.dpt_seismic import dpt_bangkok_basin_spectrum
    out = dpt_bangkok_basin_spectrum(zone=5, T_s=1.0, I=1.25, R=2.0, damping_percent=5.0)
    assert abs(out["SDS"] - 0.191) < 1e-9
    assert abs(out["SD1"] - 0.199) < 1e-9
    assert abs(out["Sa"] - 0.199) < 1e-9
    assert out["region"] == "Bangkok Basin"


def test_dpt_m3b_general_category_period_rule():
    from core.dpt_seismic import dpt_general_spectrum
    out = dpt_general_spectrum(0.176, 0.045, "D", 0.835, 1.25, 2.0)
    assert out["category_governing"] in {"ก", "ข", "ค", "ง"}
    assert "category_basis" in out


def test_dpt_m3b_qa_equivalent_static_fig_141_no_dynamic_ramp():
    from core.dpt_seismic import dpt_general_spectrum, response_spectrum_points

    # BG40-style case has SD1 <= SDS.  DPT Fig. 1.4-1 for equivalent
    # static keeps Sa = SDS from T=0 to Ts; it must not start at 0.4SDS.
    out = dpt_general_spectrum(0.176, 0.045, "D", 0.05, 1.25, 2.0)
    assert out["spectrum_figure"].startswith("DPT Fig. 1.4-1")
    assert out["spectrum_branch"] == "Fig. 1.4-1: T ≤ Ts, Sa = SDS"
    assert abs(out["Sa"] - out["SDS"]) < 1e-12

    pts = response_spectrum_points(out["SDS"], out["SD1"], t_max=2.0, n=5)
    assert abs(float(pts.iloc[0]["Sa (g)"]) - out["SDS"]) < 1e-12


def test_dpt_m3b_qa_equivalent_static_fig_142_linear_branch():
    from core.dpt_seismic import equivalent_static_sa_general

    out_low = equivalent_static_sa_general(0.20, 0.40, 0.1)
    assert out_low["spectrum_figure"].startswith("DPT Fig. 1.4-2")
    assert abs(out_low["Sa"] - 0.20) < 1e-12

    out_mid = equivalent_static_sa_general(0.20, 0.40, 0.6)
    # Linear from 0.20 at T=0.2 to 0.40 at T=1.0.
    assert abs(out_mid["Sa"] - 0.30) < 1e-12
    assert "linear" in out_mid["spectrum_branch"]

    out_high = equivalent_static_sa_general(0.20, 0.40, 2.0)
    assert abs(out_high["Sa"] - 0.20) < 1e-12
    assert out_high["spectrum_branch"] == "Fig. 1.4-2: T > 1.0 s, Sa = SD1/T"


def test_aashto_m3c_response_modification_table_values():
    from core.aashto_seismic import recommended_substructure_r

    assert recommended_substructure_r("single_column_or_pier", "Essential")["R"] == 2.0
    assert recommended_substructure_r("multiple_column_bent", "Other")["R"] == 5.0
    assert recommended_substructure_r("wall_type_pier_larger_dimension", "Other")["R"] == 2.0
    assert recommended_substructure_r("steel_composite_pile_bent_vertical_piles", "Essential")["R"] == 3.5


def test_aashto_m3c_importance_presets_are_traceable():
    from core.aashto_seismic import importance_value_from_preset

    bg40 = importance_value_from_preset("bg40_default")
    assert bg40["I"] == 1.25
    assert "BG40" in bg40["preset_label"]
    manual = importance_value_from_preset("manual", 1.35)
    assert manual["I"] == 1.35
    assert manual["preset_key"] == "manual"


def test_wind_load_factor_interpolation_bg40():
    c_ws = wind_load_factor_c_bridge(11.2 / 3.9, 10.0)
    c_wl = wind_load_factor_c_bridge(11.2 / 6.8, 10.0)
    assert abs(c_ws["C"] - 4.6) < 0.02
    assert abs(c_wl["C"] - 5.7) < 0.05
    assert "linear interpolation" in c_ws["ratio_note"]


def test_wind_auto_calculation_bg40_values():
    out = wind_load_en1991_dpt_auto(1.25, 25.0, 1.0, 1.0, 11.2, 3.9, 6.8, 10.0, 40.0)
    assert abs(out["vb_m_s"] - 25.0) < 1e-9
    assert abs(out["C_ws"] - 4.6) < 0.02
    assert abs(out["C_ws_wl"] - 5.7) < 0.05
    assert abs(out["WSsuper_kn_m"] - 7.01) < 0.05
    assert abs(out["WSsuper_WL_kn_m"] - 15.14) < 0.10
