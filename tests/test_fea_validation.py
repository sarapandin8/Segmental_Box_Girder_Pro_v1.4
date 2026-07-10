from __future__ import annotations

from copy import deepcopy

from core.bg40_defaults import BG40_DEFAULT
from core.fea_results import SOURCE_STATE_SINGLE
from core.validation import validate_project


def _payload(stage: str, sha: str) -> dict:
    return {
        "valid": True,
        "stage": stage,
        "bridge_objects": ["B2_SPAN1"],
        "sha256": sha,
        "records": [
            {"SectCutNum": 1, "Distance": 0.0, "LocType": "After"},
            {"SectCutNum": 2, "Distance": 1.0, "LocType": "Before"},
        ],
        "summary": {
            "output_cases": 1,
            "rows_per_cut_min": 1,
            "rows_per_cut_max": 1,
        },
        "source_semantics": {"overall": SOURCE_STATE_SINGLE},
    }


def test_validation_reports_missing_three_stage_sources_with_issue_codes():
    project = deepcopy(BG40_DEFAULT)
    issues = validate_project(project)
    codes = {issue.issue_code for issue in issues}
    assert "FEA_ULS_SOURCE_MISSING" in codes
    assert "FEA_TRANSFER_SOURCE_MISSING" in codes
    assert "FEA_SERVICE_SOURCE_MISSING" in codes


def test_validation_reports_ready_package_but_not_connected():
    project = deepcopy(BG40_DEFAULT)
    project["fea_results"]["stage_imports"] = {
        "uls": _payload("uls", "a"),
        "transfer": _payload("transfer", "b"),
        "service": _payload("service", "c"),
    }
    project["fea_results"]["downstream_connection"]["status"] = "NOT YET CONNECTED"
    issues = validate_project(project)
    codes = {issue.issue_code for issue in issues}
    assert "FEA_DOWNSTREAM_NOT_CONNECTED" in codes
    assert "FEA_STATION_MAP_MISMATCH" not in codes


def test_validation_blocks_station_map_mismatch():
    project = deepcopy(BG40_DEFAULT)
    service = _payload("service", "c")
    service["records"] = [{"SectCutNum": 1, "Distance": 0.0, "LocType": "After"}]
    project["fea_results"]["stage_imports"] = {
        "uls": _payload("uls", "a"),
        "transfer": _payload("transfer", "b"),
        "service": service,
    }
    issues = validate_project(project)
    matching = [issue for issue in issues if issue.issue_code == "FEA_STATION_MAP_MISMATCH"]
    assert matching
    assert matching[0].level == "ERROR"


def test_schema_migration_strips_legacy_license_metadata_and_adds_source_state():
    from core.validation import ensure_project_schema

    project = deepcopy(BG40_DEFAULT)
    project["fea_results"]["stage_imports"]["uls"] = {
        "valid": True,
        "stage": "uls",
        "program_control": {
            "ProgramName": "CSiBridge 2017",
            "Version": "19.2.0",
            "CurrUnits": "KN, m, C",
            "BridgeCode": "AASHTO LRFD 2014",
            "ConcCode": "ACI 318-14",
            "LicenseNum": "PRIVATE",
            "LicenseOS": "Yes",
        },
        "records": [
            {"StepType": "Max", "SectCutNum": 1, "Distance": 0.0, "LocType": "After"},
            {"StepType": "", "SectCutNum": 1, "Distance": 0.0, "LocType": "After"},
        ],
        "envelopes": [],
    }
    migrated = ensure_project_schema(project)
    payload = migrated["fea_results"]["stage_imports"]["uls"]
    assert "LicenseNum" not in payload["program_control"]
    assert "LicenseOS" not in payload["program_control"]
    assert payload["records"][0]["SourceState"] == "COMPONENT ENVELOPE"
    assert payload["records"][1]["SourceState"] == "SINGLE STATE"
    assert payload["source_semantics"]["overall"] == "MIXED"
