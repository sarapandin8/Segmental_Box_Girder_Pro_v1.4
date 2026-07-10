from __future__ import annotations

import pandas as pd

from core.tendon_layout import (
    build_tendon_layout_model,
    tendon_model_to_profile_frame,
    tendon_model_to_station_match_frame,
    normalize_general_tendon_rows,
    normalize_tendon_profile_rows,
    tendon_points_at_station,
)


def _raw_general() -> pd.DataFrame:
    return pd.DataFrame([
        ["TABLE: Bridge Object Definitions 11 - Prestress 1 - General", None, None, None, None, None, None, None, None, None, None, None, None],
        ["BridgeObj", "Tendon", "LoadName", "StartSpan", "StartType", "EndSpan", "EndType", "PreType", "JackFrom", "Material", "TendonArea", "LoadType", "Force"],
        ["Text", "Text", "Text", "Text", "Text", "Text", "Text", "Text", "Text", "Text", "m2", "Text", "KN"],
        ["B2_SPAN1", "T1-L", "PS_Primary", "Span 1", "Start", "Span 1", "End", "Post Tension", "Start", "A416Gr270", 0.00336, "Force", 4687],
        ["B2_SPAN1", "T1-R", "PS_Primary", "Span 1", "Start", "Span 1", "End", "Post Tension", "Start", "A416Gr270", 0.00336, "Force", 4687],
        ["B2_SPAN1", "T2-L", "PS_Primary", "Span 1", "Start", "Span 1", "End", "Post Tension", "Start", "A416Gr270", 0.00336, "Force", 4687],
        ["B2_SPAN1", "T2-R", "PS_Primary", "Span 1", "Start", "Span 1", "End", "Post Tension", "Start", "A416Gr270", 0.00336, "Force", 4687],
    ])


def _raw_vertical() -> pd.DataFrame:
    rows = [
        ["TABLE: Bridge Object Definitions 12 - Prestress 2 - Vertical Layout", None, None, None, None],
        ["BridgeObj", "Tendon", "SegType", "TendonDist", "VertOff"],
        ["Text", "Text", "Text", "m", "m"],
    ]
    for tendon in ["T1-L", "T1-R", "T2-L", "T2-R"]:
        for x, dp in [(0.0, -1.89), (20.0, -2.15), (40.0, -1.89)]:
            rows.append(["B2_SPAN1", tendon, "Linear", x, dp])
    return pd.DataFrame(rows)


def _raw_horizontal(mismatch: bool = False) -> pd.DataFrame:
    rows = [
        ["TABLE: Bridge Object Definitions 13 - Prestress 3 - Horizontal Layout", None, None, None, None],
        ["BridgeObj", "Tendon", "SegType", "TendonDist", "HorizOff"],
        ["Text", "Text", "Text", "m", "m"],
    ]
    hmap = {"T1-L": 1.45, "T1-R": -1.45, "T2-L": 0.95, "T2-R": -0.95}
    bridge = "B2_SPAN2" if mismatch else "B2_SPAN1"
    for tendon, off in hmap.items():
        for x in [0.0, 20.0, 40.0]:
            rows.append([bridge, tendon, "Linear", x, off])
    return pd.DataFrame(rows)


def test_csibridge_tendon_tables_normalize_general_and_profiles():
    general = normalize_general_tendon_rows(_raw_general())
    vertical = normalize_tendon_profile_rows(_raw_vertical(), profile="vertical")
    horizontal = normalize_tendon_profile_rows(_raw_horizontal(), profile="horizontal")
    assert len(general) == 4
    assert general.iloc[0]["Aps_mm2"] == 3360.0
    assert general.iloc[0]["strand_count_140mm2"] == 24.0
    assert vertical.iloc[0]["dp_top_m"] == 1.89
    assert horizontal.iloc[0]["horiz_off_m"] == 1.45


def test_build_tendon_model_group_summary_and_eccentricity():
    general = normalize_general_tendon_rows(_raw_general())
    vertical = normalize_tendon_profile_rows(_raw_vertical(), profile="vertical")
    horizontal = normalize_tendon_profile_rows(_raw_horizontal(), profile="horizontal")
    model = build_tendon_layout_model(general, vertical, horizontal, active_bridge_object="B2_SPAN1", y_t_from_top_m=0.839)
    assert model["valid"] is True
    assert len(model["tendons"]) == 4
    assert abs(model["dp_avg_midspan_m"] - 2.15) < 1e-9
    assert abs(model["eccentricity_midspan_m"] - (2.15 - 0.839)) < 1e-9
    assert model["group_summary"][0]["Group"] == "T1–T2"
    assert model["group_summary"][0]["Count"] == 4
    pts = tendon_points_at_station(model, 20.0)
    assert len(pts) == 4
    assert abs(pts[pts["Tendon"] == "T1-L"].iloc[0]["HorizOff (m)"] - 1.45) < 1e-9


def test_tendon_model_bridgeobj_mismatch_can_be_mapped_to_active():
    general = normalize_general_tendon_rows(_raw_general())
    vertical = normalize_tendon_profile_rows(_raw_vertical(), profile="vertical")
    horizontal = normalize_tendon_profile_rows(_raw_horizontal(mismatch=True), profile="horizontal")
    model = build_tendon_layout_model(general, vertical, horizontal, active_bridge_object="B2_SPAN1", map_to_active_bridge_object=True, y_t_from_top_m=0.839)
    assert model["valid"] is True
    assert model["mapped_to_active_bridge_object"] is True
    assert "B2_SPAN2" in model["imported_bridge_objects"]
    assert model["active_bridge_object"] == "B2_SPAN1"
    assert any(row["Check"] == "BridgeObj adopted" and row["Status"] == "MAPPED" for row in model["qa_rows"])



def test_tendon_model_builds_complete_merged_profile_table():
    general = normalize_general_tendon_rows(_raw_general())
    vertical = normalize_tendon_profile_rows(_raw_vertical(), profile="vertical")
    horizontal = normalize_tendon_profile_rows(_raw_horizontal(), profile="horizontal")
    model = build_tendon_layout_model(general, vertical, horizontal, active_bridge_object="B2_SPAN1", y_t_from_top_m=0.839)
    profile = tendon_model_to_profile_frame(model)
    station_match = tendon_model_to_station_match_frame(model)
    assert len(profile) == 12
    assert {"Tendon", "Point No.", "x_m", "dp_top_m", "horiz_off_m", "Status"}.issubset(profile.columns)
    t1l_mid = profile[(profile["Tendon"] == "T1-L") & (profile["x_m"] == 20.0)].iloc[0]
    assert abs(t1l_mid["dp_top_m"] - 2.15) < 1e-9
    assert abs(t1l_mid["horiz_off_m"] - 1.45) < 1e-9
    assert len(station_match) == 4
    assert set(station_match["Station match status"]) == {"MATCH"}
    assert any(row["Check"] == "Merged profile rows" and row["Value"] == 12 for row in model["qa_rows"])


def test_tendon_section_void_classification_for_overlay_qa():
    from core.section_geometry import classify_point_in_section_void, normalize_coordinate_rows

    coords = normalize_coordinate_rows(pd.DataFrame([
        {"loop_name": "Structural Polygon 1", "point_no": 1, "x_mm": 0.0, "y_mm": 0.0},
        {"loop_name": "Structural Polygon 1", "point_no": 2, "x_mm": 1000.0, "y_mm": 0.0},
        {"loop_name": "Structural Polygon 1", "point_no": 3, "x_mm": 1000.0, "y_mm": 1000.0},
        {"loop_name": "Structural Polygon 1", "point_no": 4, "x_mm": 0.0, "y_mm": 1000.0},
        {"loop_name": "Opening Polygon 1", "point_no": 1, "x_mm": 250.0, "y_mm": 250.0},
        {"loop_name": "Opening Polygon 1", "point_no": 2, "x_mm": 750.0, "y_mm": 250.0},
        {"loop_name": "Opening Polygon 1", "point_no": 3, "x_mm": 750.0, "y_mm": 750.0},
        {"loop_name": "Opening Polygon 1", "point_no": 4, "x_mm": 250.0, "y_mm": 750.0},
    ]))

    inside_void = classify_point_in_section_void((500.0, 500.0), coords)
    inside_concrete = classify_point_in_section_void((100.0, 100.0), coords)
    outside = classify_point_in_section_void((1200.0, 500.0), coords)

    assert inside_void["status"] == "PASS"
    assert inside_void["location"] == "INSIDE VOID"
    assert abs(inside_void["min_clearance_to_inner_boundary_mm"] - 250.0) < 1e-9
    assert inside_concrete["status"] == "FAIL"
    assert inside_concrete["location"] == "INSIDE CONCRETE"
    assert outside["status"] == "FAIL"
    assert outside["location"] == "OUTSIDE SECTION"
