import pandas as pd
import pytest

from core.arrow_safe_editing import dataframe_to_csv_text, parse_csv_editor_text


def test_coordinate_csv_round_trip_without_arrow():
    source = pd.DataFrame([
        {"loop_name": "Structural Polygon 1", "point_no": 1, "x_mm": 0.0, "y_mm": 0.0},
        {"loop_name": "Opening Polygon 1", "point_no": 1, "x_mm": 1000.0, "y_mm": 500.0},
    ])
    text = dataframe_to_csv_text(source, ["loop_name", "point_no", "x_mm", "y_mm"])
    parsed = parse_csv_editor_text(
        text,
        columns=["loop_name", "point_no", "x_mm", "y_mm"],
        numeric_columns=("x_mm", "y_mm"),
        integer_columns=("point_no",),
        allowed_values={"loop_name": ["Structural Polygon 1", "Opening Polygon 1"]},
    )
    assert parsed.to_dict("records") == source.to_dict("records")


def test_sdl_boolean_and_numeric_parsing():
    text = "Component,Single Track (kN/m),Double Track (kN/m),Include,Source,Note\nRails,1.46,2.93,true,BG40,Track\n"
    parsed = parse_csv_editor_text(
        text,
        columns=["Component", "Single Track (kN/m)", "Double Track (kN/m)", "Include", "Source", "Note"],
        numeric_columns=("Single Track (kN/m)", "Double Track (kN/m)"),
        boolean_columns=("Include",),
    )
    assert parsed.loc[0, "Include"] is True or bool(parsed.loc[0, "Include"]) is True
    assert parsed.loc[0, "Double Track (kN/m)"] == pytest.approx(2.93)


def test_rejects_changed_headers():
    with pytest.raises(ValueError, match="columns do not match"):
        parse_csv_editor_text("A,B\n1,2\n", columns=["A", "C"])


def test_dataframe_to_csv_text_accepts_stable_float_format():
    source = pd.DataFrame([{"x_mm": 8134.299999999999, "y_mm": 7387.400000000001}])
    text = dataframe_to_csv_text(source, ["x_mm", "y_mm"], float_format="%.4f")
    assert "8134.3000" in text
    assert "7387.4000" in text
    assert "299999" not in text
