from __future__ import annotations

import json

import pytest

from core.bg40_defaults import BG40_DEFAULT
from core.project_io import ProjectJsonLoadError, load_project_json_bytes, project_json_fingerprint, project_load_summary
from core.validation import PROJECT_SCHEMA_VERSION


def test_load_project_json_bytes_migrates_schema_and_keeps_project_data() -> None:
    legacy = json.loads(json.dumps(BG40_DEFAULT))
    legacy["meta"]["schema_version"] = "0.3.8-old"
    legacy["project"]["name"] = "USER_PROJECT"
    raw = json.dumps(legacy).encode("utf-8")
    loaded = load_project_json_bytes(raw, "saved_project.json")
    assert loaded["project"]["name"] == "USER_PROJECT"
    assert loaded["meta"]["schema_version"] == PROJECT_SCHEMA_VERSION
    assert loaded["meta"]["loaded_schema_version"] == "0.3.8-old"
    assert loaded["meta"]["schema_migration_status"] == "Migrated from 0.3.8-old"
    summary = project_load_summary(loaded)
    assert summary["project"] == "USER_PROJECT"
    assert summary["schema_version"] == PROJECT_SCHEMA_VERSION


def test_load_project_json_bytes_rejects_invalid_json() -> None:
    with pytest.raises(ProjectJsonLoadError):
        load_project_json_bytes(b"{not json", "bad.json")


def test_project_json_fingerprint_changes_with_content() -> None:
    a = project_json_fingerprint(b"{}", "project.json")
    b = project_json_fingerprint(b'{"x":1}', "project.json")
    assert a != b


def test_app_project_json_loader_uses_explicit_button_not_auto_rerun_loop() -> None:
    from pathlib import Path

    app_text = Path(__file__).resolve().parents[1].joinpath("app.py").read_text(encoding="utf-8")
    assert 'st.file_uploader("Load Project JSON", type=["json"], key="project_json_upload")' in app_text
    assert 'st.button("Load uploaded project", key="load_project_json_button"' in app_text
    assert 'json.loads(uploaded.read().decode("utf-8"))' not in app_text


def _sample_section_coordinate_rows():
    return [
        {"loop_name": "Structural Polygon 1", "point_no": 1, "x_mm": 0.0, "y_mm": 0.0},
        {"loop_name": "Structural Polygon 1", "point_no": 2, "x_mm": 4000.0, "y_mm": 0.0},
        {"loop_name": "Structural Polygon 1", "point_no": 3, "x_mm": 4000.0, "y_mm": 2000.0},
        {"loop_name": "Structural Polygon 1", "point_no": 4, "x_mm": 0.0, "y_mm": 2000.0},
        {"loop_name": "Opening Polygon 1", "point_no": 1, "x_mm": 1000.0, "y_mm": 500.0},
        {"loop_name": "Opening Polygon 1", "point_no": 2, "x_mm": 3000.0, "y_mm": 500.0},
        {"loop_name": "Opening Polygon 1", "point_no": 3, "x_mm": 3000.0, "y_mm": 1500.0},
        {"loop_name": "Opening Polygon 1", "point_no": 4, "x_mm": 1000.0, "y_mm": 1500.0},
    ]


def test_project_json_save_load_preserves_section_rows_and_adopted_properties() -> None:
    from core.project_io import serialize_project_json_bytes

    project = json.loads(json.dumps(BG40_DEFAULT))
    project["section"]["coordinate_rows"] = _sample_section_coordinate_rows()
    project["section"]["Ac_m2"] = 6.0
    project["section"]["I33_m4"] = 2.333333
    project["section"]["computed_from_coordinates"] = {"A_m2": 6.0, "ycg_from_bottom_m": 1.0}

    saved = serialize_project_json_bytes(project)
    loaded = load_project_json_bytes(saved, "saved_project.json")

    assert len(loaded["section"]["coordinate_rows"]) == 8
    assert loaded["section"]["Ac_m2"] == 6.0
    assert loaded["section"]["I33_m4"] == 2.333333
    assert loaded["section"]["computed_from_coordinates"]["A_m2"] == 6.0
    assert loaded["meta"]["last_save_section_persistence"]["coordinate_rows"] == 8


def test_project_json_migrates_legacy_section_coordinate_locations() -> None:
    legacy = json.loads(json.dumps(BG40_DEFAULT))
    legacy["meta"]["schema_version"] = "0.4.0-old"
    legacy["section"].pop("coordinate_rows", None)
    legacy["section"]["section_coordinates"] = _sample_section_coordinate_rows()

    loaded = load_project_json_bytes(json.dumps(legacy).encode("utf-8"), "legacy_project.json")

    assert len(loaded["section"]["coordinate_rows"]) == 8
    assert loaded["section"]["coordinate_rows"][0]["loop_name"] == "Structural Polygon 1"
    assert loaded["meta"]["schema_version"] == PROJECT_SCHEMA_VERSION


def test_fresh_project_defaults_to_b2_span1_and_loaded_project_span_is_preserved() -> None:
    from core.validation import ensure_project_schema

    assert BG40_DEFAULT["project"]["bridge_object"] == "B2_SPAN1"
    assert BG40_DEFAULT["tendon_layout"]["active_bridge_object"] == "B2_SPAN1"

    loaded = json.loads(json.dumps(BG40_DEFAULT))
    loaded["project"]["bridge_object"] = "USER_SPAN_X"
    loaded["tendon_layout"]["active_bridge_object"] = "USER_SPAN_X"
    migrated = ensure_project_schema(loaded)

    assert migrated["project"]["bridge_object"] == "USER_SPAN_X"
    assert migrated["tendon_layout"]["active_bridge_object"] == "USER_SPAN_X"


def test_fea5d1_project_load_summary_exposes_source_and_app_schema_trace():
    from core.project_io import project_load_summary

    summary = project_load_summary({
        "meta": {
            "schema_version": "0.5.15-commercial-ui32a-structured-sdl-and-trace-presets",
            "loaded_schema_version": "0.5.6-commercial-fea5c1-transfer-signed-governing-display-consistency",
            "schema_migration_status": "Migrated from 0.5.6-commercial-fea5c1-transfer-signed-governing-display-consistency",
        },
        "project": {"name": "BG40", "bridge_object": "B2_SPAN1"},
    })
    assert summary["schema_version"].startswith("0.5.15-")
    assert summary["loaded_schema_version"].startswith("0.5.6-")
    assert summary["schema_migration_status"].startswith("Migrated from")


def test_fea5d1a_declared_file_schema_wins_over_historical_origin() -> None:
    legacy = json.loads(json.dumps(BG40_DEFAULT))
    legacy["meta"].update({
        "schema_version": "0.5.5-commercial-fea5c-transfer-stage-simultaneous-force-review",
        "loaded_schema_version": "0.4.20-commercial-bugfix1-section-save-load-persistence",
    })
    legacy["meta"].pop("migration_complete", None)
    legacy["meta"].pop("migration_target_schema_version", None)

    loaded = load_project_json_bytes(json.dumps(legacy).encode("utf-8"), "legacy.json")
    meta = loaded["meta"]

    assert meta["source_file_schema_version"].startswith("0.5.5-")
    assert meta["loaded_schema_version"].startswith("0.5.5-")
    assert meta["historical_origin_schema_version"].startswith("0.4.20-")
    assert meta["schema_migration_status"].startswith("Migrated from 0.5.5-")
    assert meta["migration_complete"] is True


def test_fea5d1a_current_schema_no_copy_fast_path_returns_same_object() -> None:
    from core.validation import ensure_project_schema, project_schema_is_current

    current = json.loads(json.dumps(BG40_DEFAULT))
    assert project_schema_is_current(current)
    assert ensure_project_schema(current, copy_project=False) is current


def test_fea5d1a_memory_safe_save_does_not_mutate_current_project_meta() -> None:
    from core.project_io import serialize_project_json_bytes

    current = json.loads(json.dumps(BG40_DEFAULT))
    before_meta = dict(current["meta"])
    saved = serialize_project_json_bytes(current)

    assert current["meta"] == before_meta
    assert b'\n  "' not in saved  # compact JSON, not pretty-printed duplicate payload
    reloaded = load_project_json_bytes(saved, "saved-current.json")
    assert reloaded["meta"]["schema_version"] == PROJECT_SCHEMA_VERSION
    assert reloaded["meta"]["schema_migration_status"] == "Current"
