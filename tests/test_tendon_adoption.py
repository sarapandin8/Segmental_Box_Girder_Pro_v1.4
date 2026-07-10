from __future__ import annotations

import pandas as pd

from core.tendon_adoption import (
    adopt_tendon_model,
    build_tendon_downstream_summary,
    build_tendon_detailed_qa_integrity,
    build_tendon_source_trace,
    build_tendon_stressing_basis_summary,
    summarize_tendon_source_provenance,
    clear_adopted_tendon_model,
    tendon_model_fingerprint,
    tendon_model_status,
)
from core.tendon_layout import build_tendon_layout_model, normalize_general_tendon_rows, normalize_tendon_profile_rows


def _raw_general() -> pd.DataFrame:
    return pd.DataFrame([
        ["BridgeObj", "Tendon", "JackFrom", "Material", "TendonArea", "Force"],
        ["Text", "Text", "Text", "Text", "m2", "KN"],
        ["B2_SPAN1", "T1-L", "Start", "A416Gr270", 0.00336, 4687],
        ["B2_SPAN1", "T1-R", "Start", "A416Gr270", 0.00336, 4687],
    ])


def _raw_vertical() -> pd.DataFrame:
    rows = [["BridgeObj", "Tendon", "SegType", "TendonDist", "VertOff"], ["Text", "Text", "Text", "m", "m"]]
    for tendon in ["T1-L", "T1-R"]:
        for x, dp in [(0.0, -1.0), (20.0, -2.0), (40.0, -1.0)]:
            rows.append(["B2_SPAN1", tendon, "Linear", x, dp])
    return pd.DataFrame(rows)


def _raw_horizontal() -> pd.DataFrame:
    rows = [["BridgeObj", "Tendon", "SegType", "TendonDist", "HorizOff"], ["Text", "Text", "Text", "m", "m"]]
    for tendon, off in {"T1-L": 1.2, "T1-R": -1.2}.items():
        for x in [0.0, 20.0, 40.0]:
            rows.append(["B2_SPAN1", tendon, "Linear", x, off])
    return pd.DataFrame(rows)


def _model() -> dict:
    general = normalize_general_tendon_rows(_raw_general())
    vertical = normalize_tendon_profile_rows(_raw_vertical(), profile="vertical")
    horizontal = normalize_tendon_profile_rows(_raw_horizontal(), profile="horizontal")
    return build_tendon_layout_model(general, vertical, horizontal, active_bridge_object="B2_SPAN1", y_t_from_top_m=0.8)


def test_tendon_model_fingerprint_and_status_change_after_adoption():
    model = _model()
    tl = {"general_rows": [1, 2], "vertical_rows": [1], "horizontal_rows": [1]}
    assert tendon_model_fingerprint(model)
    assert tendon_model_status(model, tl)["status"] == "NOT ADOPTED"
    summary = adopt_tendon_model(tl, {"tendon_friction_groups": []}, model, y_t_from_top_m=0.8)
    assert summary["tendon_count"] == 2
    assert summary["Aps_total_mm2"] == 6720.0
    assert tendon_model_status(model, tl)["status"] == "LOCKED"


def test_tendon_adoption_updates_prestress_summary_and_can_clear_snapshot():
    model = _model()
    tl = {"general_rows": [1, 2], "vertical_rows": [1], "horizontal_rows": [1]}
    prestress = {"tendon_friction_groups": [{"group": "T1", "n": 2}]}
    adopt_tendon_model(tl, prestress, model, y_t_from_top_m=0.8)
    assert prestress["num_tendons"] == 2
    assert prestress["Aps_total_mm2"] == 6720.0
    assert abs(prestress["eccentricity_midspan_m"] - 1.2) < 1e-9
    assert tl["adopted_model"]
    clear_adopted_tendon_model(tl)
    assert "adopted_model" not in tl
    assert "NOT ADOPTED" in tl["adopted_status"]


def test_tendon_source_trace_and_downstream_summary_are_report_ready():
    model = _model()
    tl = {
        "general_rows": [{}, {}],
        "vertical_rows": [{}, {}, {}],
        "horizontal_rows": [{}, {}, {}],
        "source_meta": {
            "general": {"filename": "gen.xlsx", "sha256_12": "abc123abc123"},
            "vertical": {"filename": "vert.xlsx", "sha256_12": "def456def456"},
            "horizontal": {"filename": "horiz.xlsx", "sha256_12": "789abc789abc"},
        },
    }
    trace = build_tendon_source_trace(tl, model)
    assert trace[0]["Source table"] == "General"
    assert trace[0]["Filename"] == "gen.xlsx"
    assert trace[0]["Status"] == "READY"
    assert summarize_tendon_source_provenance(trace)["status"] == "READY"
    summary = build_tendon_downstream_summary(model, y_t_from_top_m=0.8)
    assert summary["source"] == "Adopted CSiBridge tendon layout model"
    assert summary["model_fingerprint"] == tendon_model_fingerprint(model)


def test_stressing_basis_is_auto_detected_from_jackfrom_and_added_to_summary():
    model = _model()
    basis = build_tendon_stressing_basis_summary(model)
    assert basis["status"] == "READY"
    assert basis["detected_mode"] == "One-end stressing from Start"
    assert basis["jack_from_display"] == "Start"
    assert "does not double" in basis["force_policy"]

    summary = build_tendon_downstream_summary(model, y_t_from_top_m=0.8)
    assert summary["jack_from_display"] == "Start"
    assert summary["stressing_mode"] == "One-end stressing from Start"
    assert summary["stressing_status"] == "READY"


def test_stressing_basis_flags_missing_or_mixed_jackfrom_for_review():
    model = _model()
    model["tendons"][0]["jack_from"] = "End"
    mixed = build_tendon_stressing_basis_summary(model)
    assert mixed["status"] == "REVIEW"
    assert mixed["detected_mode"] == "Mixed one-end stressing by tendon"

    for tendon in model["tendons"]:
        tendon["jack_from"] = ""
    missing = build_tendon_stressing_basis_summary(model)
    assert missing["status"] == "MISSING"
    assert missing["ready"] is False


def test_detailed_adopted_qa_integrity_register_is_ready_for_complete_model():
    model = _model()
    tl = {
        "general_rows": [{}, {}],
        "vertical_rows": [{}, {}, {}, {}, {}, {}],
        "horizontal_rows": [{}, {}, {}, {}, {}, {}],
        "source_meta": {
            "general": {"filename": "gen.xlsx", "sha256_12": "abc123abc123"},
            "vertical": {"filename": "vert.xlsx", "sha256_12": "def456def456"},
            "horizontal": {"filename": "horiz.xlsx", "sha256_12": "789abc789abc"},
        },
    }
    summary = adopt_tendon_model(tl, {}, model, y_t_from_top_m=0.8)
    rows = build_tendon_detailed_qa_integrity(model, tl, summary)
    by_item = {row["Item"]: row for row in rows}

    assert by_item["Tendon-by-tendon table"]["Available"] == 2
    assert by_item["Merged profile table"]["Available"] == 6
    assert by_item["Merged profile table"]["Expected / basis"] == 6
    assert by_item["Tendon group summary"]["Available"] >= 1
    assert by_item["Downstream summary"]["Status"] == "READY"
    assert by_item["Source trace rows"]["Available"] >= 4
    assert by_item["Source metadata provenance"]["Status"] == "READY"
    assert {row["Status"] for row in rows} == {"READY"}


def test_project_snapshot_source_trace_is_usable_but_metadata_partial():
    model = _model()
    tl = {
        "general_rows": [{}, {}],
        "vertical_rows": [{}, {}, {}, {}, {}, {}],
        "horizontal_rows": [{}, {}, {}, {}, {}, {}],
    }
    summary = adopt_tendon_model(tl, {}, model, y_t_from_top_m=0.8)
    trace = build_tendon_source_trace(tl, model)
    by_source = {row["Source table"]: row for row in trace}
    assert by_source["General"]["Status"] == "RESTORED FROM PROJECT SNAPSHOT"
    assert by_source["Vertical"]["Status"] == "RESTORED FROM PROJECT SNAPSHOT"
    assert by_source["Horizontal"]["Status"] == "RESTORED FROM PROJECT SNAPSHOT"
    provenance = summarize_tendon_source_provenance(trace)
    assert provenance["status"] == "PARTIAL"
    rows = build_tendon_detailed_qa_integrity(model, tl, summary)
    by_item = {row["Item"]: row for row in rows}
    assert by_item["Source trace rows"]["Status"] == "READY"
    assert by_item["Source metadata provenance"]["Status"] == "PARTIAL"
