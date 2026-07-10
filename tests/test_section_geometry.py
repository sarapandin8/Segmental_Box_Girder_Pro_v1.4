from core.section_geometry import calculate_section_properties, normalize_coordinate_rows
import pandas as pd


def _rect_hole_rows():
    return pd.DataFrame([
        {"loop_name":"Structural Polygon 1","point_no":1,"x_mm":0,"y_mm":0},
        {"loop_name":"Structural Polygon 1","point_no":2,"x_mm":4000,"y_mm":0},
        {"loop_name":"Structural Polygon 1","point_no":3,"x_mm":4000,"y_mm":2000},
        {"loop_name":"Structural Polygon 1","point_no":4,"x_mm":0,"y_mm":2000},
        {"loop_name":"Opening Polygon 1","point_no":1,"x_mm":1000,"y_mm":500},
        {"loop_name":"Opening Polygon 1","point_no":2,"x_mm":3000,"y_mm":500},
        {"loop_name":"Opening Polygon 1","point_no":3,"x_mm":3000,"y_mm":1500},
        {"loop_name":"Opening Polygon 1","point_no":4,"x_mm":1000,"y_mm":1500},
    ])


def test_normalize_csibridge_alias_columns():
    raw = pd.DataFrame([
        {"Shape":"Structural Polygon 1","Point":1,"X":0,"Y":0},
        {"Shape":"Structural Polygon 1","Point":2,"X":1000,"Y":0},
        {"Shape":"Structural Polygon 1","Point":3,"X":0,"Y":1000},
    ])
    out = normalize_coordinate_rows(raw)
    assert list(out.columns) == ["loop_name", "loop_type", "point_no", "x_mm", "y_mm"]
    assert out.iloc[0]["loop_type"] == "outer"


def test_hollow_rectangle_properties_subtract_opening():
    props = calculate_section_properties(_rect_hole_rows())
    assert props["valid"] is True
    assert abs(props["A_m2"] - 6.0) < 1e-9
    assert abs(props["cx_mm"] - 2000.0) < 1e-9
    assert abs(props["cy_mm"] - 1000.0) < 1e-9
    assert abs(props["I33_m4"] - 2.5) < 1e-9
    assert abs(props["I22_m4"] - 10.0) < 1e-9
    assert abs(props["ycg_from_bottom_m"] - 1.0) < 1e-9
    assert abs(props["yt_from_top_m"] - 1.0) < 1e-9


def test_clockwise_loops_are_normalized_by_loop_type():
    rows = _rect_hole_rows()
    # Reverse each loop to simulate clockwise / counter-clockwise export variations.
    rows = pd.concat([
        rows[rows.loop_name == "Structural Polygon 1"].sort_values("point_no", ascending=False),
        rows[rows.loop_name == "Opening Polygon 1"].sort_values("point_no", ascending=False),
    ], ignore_index=True)
    props = calculate_section_properties(rows)
    assert props["valid"] is True
    assert abs(props["A_m2"] - 6.0) < 1e-9


def test_csibridge_excel_style_rows_drop_reference_and_convert_metres_to_mm():
    raw = pd.DataFrame([
        {"Shape": "Reference Point ", "Point": None, "X": 5.6, "Y": 2.5},
        {"Shape": "Insertion Point ", "Point": None, "X": 5.6, "Y": 2.5},
        {"Shape": "Structural Polygon 1", "Point": 1, "X": 0.0, "Y": 0.0},
        {"Shape": None, "Point": 2, "X": 4.0, "Y": 0.0},
        {"Shape": None, "Point": 3, "X": 4.0, "Y": 2.0},
        {"Shape": None, "Point": 4, "X": 0.0, "Y": 2.0},
        {"Shape": "Opening Polygon 1", "Point": 1, "X": 1.0, "Y": 0.5},
        {"Shape": None, "Point": 2, "X": 3.0, "Y": 0.5},
        {"Shape": None, "Point": 3, "X": 3.0, "Y": 1.5},
        {"Shape": None, "Point": 4, "X": 1.0, "Y": 1.5},
    ])
    out = normalize_coordinate_rows(raw)
    assert len(out) == 8
    assert out.iloc[0]["x_mm"] == 0.0
    assert out.iloc[1]["x_mm"] == 4000.0
    assert out["loop_type"].tolist().count("outer") == 4
    assert out["loop_type"].tolist().count("hole") == 4
    props = calculate_section_properties(out)
    assert props["valid"] is True
    assert abs(props["A_m2"] - 6.0) < 1e-9


def test_csibridge_consecutive_duplicate_points_are_ignored_for_properties():
    raw = pd.DataFrame([
        {"Shape": "Structural Polygon 1", "Point": 1, "X": 0.0, "Y": 0.0},
        {"Shape": None, "Point": 2, "X": 4.0, "Y": 0.0},
        {"Shape": None, "Point": 3, "X": 4.0, "Y": 0.0},  # duplicate corner from CSiBridge
        {"Shape": None, "Point": 4, "X": 4.0, "Y": 2.0},
        {"Shape": None, "Point": 5, "X": 0.0, "Y": 2.0},
    ])
    props = calculate_section_properties(raw)
    assert props["valid"] is True
    assert abs(props["A_m2"] - 8.0) < 1e-9
    assert any("consecutive duplicate" in w for w in props["warnings"])



def test_section_properties_include_x_centroid_distances():
    props = calculate_section_properties(_rect_hole_rows())
    assert props["valid"] is True
    assert abs(props["xcg_from_left_m"] - 2.0) < 1e-9
    assert abs(props["xcg_from_right_m"] - 2.0) < 1e-9


def test_thin_walled_j_estimate_for_single_cell_hollow_rectangle():
    from core.section_geometry import estimate_thin_walled_closed_box_j
    props = estimate_thin_walled_closed_box_j(_rect_hole_rows(), t_top_m=0.5, t_bot_m=0.5, t_web_m=0.5)
    assert props["valid"] is True
    assert props["J_m4"] > 0
    assert props["Am_m2"] > 0
    assert props["sum_l_over_t"] > 0
    assert len(props["segment_rows"]) == 4
