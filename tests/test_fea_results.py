from __future__ import annotations

from io import BytesIO

import pandas as pd
import pytest

from core.fea_results import (
    FEAResultImportError,
    SOURCE_STATE_COMPONENT_ENVELOPE,
    SOURCE_STATE_SINGLE,
    cross_stage_station_consistency,
    read_csibridge_force_workbook,
    source_package_gate,
    stage_source_status,
)


def _workbook_bytes(rows: list[list[object]], *, include_step: bool = True) -> bytes:
    headers = ["BridgeObj", "SectCutNum", "Distance", "LocType", "OutputCase", "CaseType"]
    if include_step:
        headers.append("StepType")
    headers += ["P", "V2", "T", "M3"]
    units = ["Text", "Unitless", "m", "Text", "Text", "Text"]
    if include_step:
        units.append("Text")
    units += ["KN", "KN", "KN-m", "KN-m"]
    force = pd.DataFrame([["TABLE:  Bridge Object Forces"] + [None] * (len(headers) - 1), headers, units, *rows])
    program = pd.DataFrame(
        [
            ["TABLE:  Program Control", None, None, None, None, None],
            ["ProgramName", "Version", "CurrUnits", "BridgeCode", "ConcCode", "LicenseNum"],
            ["Text", "Text", "Text", "Text", "Text", "Text"],
            ["CSiBridge 2017", "19.2.0", "KN, m, C", "AASHTO LRFD 2014", "ACI 318-14", "PRIVATE-LICENSE"],
        ]
    )
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        force.to_excel(writer, sheet_name="Bridge Object Forces", header=False, index=False)
        program.to_excel(writer, sheet_name="Program Control", header=False, index=False)
    return output.getvalue()


def test_uls_import_preserves_candidates_and_component_sources():
    rows = [
        ["B2_SPAN1", 1, 0.0, "After", "U1", "Combination", "Max", -10, 30, -5, 100],
        ["B2_SPAN1", 1, 0.0, "After", "U1", "Combination", "Min", -40, -20, 8, 50],
        ["B2_SPAN1", 1, 0.0, "After", "U2", "Combination", "Max", -5, 10, 2, 120],
        ["B2_SPAN1", 1, 0.0, "After", "U2", "Combination", "Min", -25, -35, -9, 40],
        ["B2_SPAN1", 2, 1.0, "Before", "U1", "Combination", "Max", -12, 22, 3, 90],
        ["B2_SPAN1", 2, 1.0, "Before", "U1", "Combination", "Min", -30, -18, -4, 45],
        ["B2_SPAN1", 2, 1.0, "Before", "U2", "Combination", "Max", -9, 19, 2, 95],
        ["B2_SPAN1", 2, 1.0, "Before", "U2", "Combination", "Min", -28, -24, -6, 42],
    ]
    payload = read_csibridge_force_workbook(_workbook_bytes(rows), filename="uls.xlsx", stage="uls")
    assert payload["valid"] is True
    assert payload["summary"]["rows"] == 8
    assert payload["summary"]["sect_cuts"] == 2
    assert payload["source_semantics"]["overall"] == SOURCE_STATE_COMPONENT_ENVELOPE
    assert payload["source_semantics"]["component_envelope_rows"] == 8
    assert len(payload["records"]) == 8
    assert all(row["SourceState"] == SOURCE_STATE_COMPONENT_ENVELOPE for row in payload["records"])
    assert len(payload["envelopes"]) == 2
    cut1 = payload["envelopes"][0]
    assert cut1["P_min"] == -40.0
    assert cut1["P_min_source"]["OutputCase"] == "U1"
    assert cut1["M3_max"] == 120.0
    assert cut1["M3_max_source"]["OutputCase"] == "U2"
    assert cut1["V2_min"] == -35.0
    assert cut1["V2_min_source"]["StepType"] == "Min"


def test_transfer_import_accepts_single_state_without_step_type():
    rows = [
        ["B2_SPAN1", 1, 0.0, "After", "Transfer stage", "Combination", -100, -20, 2, -50],
        ["B2_SPAN1", 2, 1.0, "Before", "Transfer stage", "Combination", -110, 18, -1, -40],
    ]
    payload = read_csibridge_force_workbook(
        _workbook_bytes(rows, include_step=False),
        filename="transfer.xlsx",
        stage="transfer",
    )
    assert payload["summary"]["rows_per_cut_min"] == 1
    assert payload["records"][0]["StepType"] == ""
    assert payload["records"][0]["SourceState"] == SOURCE_STATE_SINGLE
    assert payload["source_semantics"]["overall"] == SOURCE_STATE_SINGLE
    assert payload["source_semantics"]["simultaneous_pairing_allowed"] is True
    assert payload["envelopes"][0]["P_min"] == payload["envelopes"][0]["P_max"]


def test_uls_import_rejects_missing_step_type():
    rows = [["B2_SPAN1", 1, 0.0, "After", "U1", "Combination", -10, 20, 1, 50]]
    with pytest.raises(FEAResultImportError, match="StepType"):
        read_csibridge_force_workbook(_workbook_bytes(rows, include_step=False), filename="uls.xlsx", stage="uls")


def test_span_source_status_and_cross_stage_station_gate():
    base = {
        "valid": True,
        "bridge_objects": ["B2_SPAN1"],
        "records": [
            {"SectCutNum": 1, "Distance": 0.0, "LocType": "After"},
            {"SectCutNum": 2, "Distance": 1.0, "LocType": "Before"},
        ],
    }
    assert stage_source_status(base, "B2_SPAN1")["status"] == "READY"
    assert stage_source_status(base, "B2_SPAN2")["status"] == "SPAN SOURCE REVIEW"
    ready = cross_stage_station_consistency({"uls": base, "transfer": base})
    assert ready["status"] == "READY"
    changed = {**base, "records": [{"SectCutNum": 1, "Distance": 0.0, "LocType": "After"}]}
    review = cross_stage_station_consistency({"uls": base, "service": changed})
    assert review["status"] == "REVIEW"
    assert review["mismatch_count"] == 1


def test_transfer_rejects_multiple_output_cases():
    rows = [
        ["B2_SPAN1", 1, 0.0, "After", "Transfer A", "Combination", -100, -20, 2, -50],
        ["B2_SPAN1", 1, 0.0, "After", "Transfer B", "Combination", -101, -21, 3, -51],
    ]
    with pytest.raises(FEAResultImportError, match="exactly one OutputCase"):
        read_csibridge_force_workbook(_workbook_bytes(rows, include_step=False), filename="transfer.xlsx", stage="transfer")


def test_transfer_rejects_max_min_step_rows():
    rows = [
        ["B2_SPAN1", 1, 0.0, "After", "Transfer stage", "Combination", "Max", -100, -20, 2, -50],
        ["B2_SPAN1", 1, 0.0, "After", "Transfer stage", "Combination", "Min", -110, 20, -2, -60],
    ]
    with pytest.raises(FEAResultImportError, match="must not contain Max/Min"):
        read_csibridge_force_workbook(_workbook_bytes(rows, include_step=True), filename="transfer.xlsx", stage="transfer")


def test_program_control_persists_only_engineering_metadata():
    rows = [["B2_SPAN1", 1, 0.0, "After", "Transfer stage", "Combination", -100, -20, 2, -50]]
    payload = read_csibridge_force_workbook(_workbook_bytes(rows, include_step=False), filename="transfer.xlsx", stage="transfer")
    assert payload["program_control"] == {
        "ProgramName": "CSiBridge 2017",
        "Version": "19.2.0",
        "CurrUnits": "KN, m, C",
        "BridgeCode": "AASHTO LRFD 2014",
        "ConcCode": "ACI 318-14",
    }
    assert "LicenseNum" not in payload["program_control"]


def test_source_package_gate_requires_three_ready_sources_and_station_match():
    base = {
        "valid": True,
        "stage": "uls",
        "bridge_objects": ["B2_SPAN1"],
        "sha256": "a",
        "records": [{"SectCutNum": 1, "Distance": 0.0, "LocType": "After"}],
        "summary": {"output_cases": 1, "rows_per_cut_min": 1, "rows_per_cut_max": 1},
        "source_semantics": {"overall": SOURCE_STATE_SINGLE},
    }
    transfer = {**base, "stage": "transfer", "sha256": "b"}
    service = {**base, "stage": "service", "sha256": "c"}
    pending = source_package_gate({"uls": base, "transfer": transfer}, "B2_SPAN1")
    assert pending["ready"] is False
    ready = source_package_gate({"uls": base, "transfer": transfer, "service": service}, "B2_SPAN1")
    assert ready["ready"] is True
    assert ready["status"] == "READY"
