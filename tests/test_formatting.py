from core.formatting import format_engineering_table, format_engineering_value
import pandas as pd


def test_force_and_moment_display_without_decimals():
    assert format_engineering_value(12153.49, "kN") == "12,153"
    assert format_engineering_value(9211.9, "kN·m") == "9,212"


def test_stress_and_length_display_rules():
    assert format_engineering_value(-13.961, "MPa") == "-13.96"
    assert format_engineering_value(75.4, "mm") == "75"
    assert format_engineering_value(40, "m") == "40.000"


def test_coefficient_and_area_display_rules():
    assert format_engineering_value(0.053912, "-") == "0.054"
    assert format_engineering_value(0.1877333333, "g") == "0.188"
    assert format_engineering_value(17400.4, "mm²") == "17,400"
    assert format_engineering_value(5.6981, "m²") == "5.698"


def test_engineering_table_formats_by_unit_column():
    df = pd.DataFrame([
        ["Vu", 12153.49, "kN"],
        ["Mu", 121146.2, "kN·m"],
        ["Stress", -13.961, "MPa"],
        ["Length", 40.0, "m"],
        ["Cover", 75.4, "mm"],
        ["Cs", 0.053912, "-"],
    ], columns=["Item", "Value", "Unit"])
    out = format_engineering_table(df)
    assert list(out["Value"]) == ["12,153", "121,146", "-13.96", "40.000", "75", "0.054"]


def test_line_load_display_uses_two_decimals():
    assert format_engineering_value(7.012345, "kN/m") == "7.01"
    assert format_engineering_value(15.10, "kN/m") == "15.10"
