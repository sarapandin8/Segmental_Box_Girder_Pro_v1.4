from __future__ import annotations

from io import BytesIO

import pandas as pd
import pytest

from core.fea_results import (
    FEAResultImportError,
    SOURCE_STATE_COMPONENT_ENVELOPE,
    SOURCE_STATE_SINGLE,
    cross_stage_station_consistency,
    package_integrity_gates,
    read_csibridge_force_workbook,
    source_package_gate,
    stage_source_status,
    trace_component_extremum,
)
from visualization.fea_figures import (
    FORCE_COMPONENT_META,
    component_envelope_frame,
    dominant_component_sources,
    governing_component_envelope,
    governing_transfer_component,
    service_component_envelope_figure,
    transfer_component_figure,
    transfer_component_frame,
    uls_component_envelope_figure,
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


def test_fea5b_component_review_frame_governing_point_and_chart_style():
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
    frame = component_envelope_frame(payload, "M3")
    assert list(frame["SectCutNum"]) == [1, 2]
    assert frame.loc[0, "Upper"] == 120.0
    assert "U2 / Max" in frame.loc[0, "UpperSource"]
    governing = governing_component_envelope(payload, "M3")
    assert governing["absolute"] == 120.0
    assert governing["sect_cut_num"] == 1
    assert governing["side"] == "MAX"

    fig = uls_component_envelope_figure(payload, "M3", bridge_object="B2_SPAN1")
    assert len(fig.data) == 3
    assert fig.data[0].name == "M3 max"
    assert fig.data[1].line.dash == "dash"
    assert fig.data[2].name == "Governing |M3| (Mx)"
    assert fig.layout.title.x == 0.5
    assert fig.layout.legend.y < 0
    assert "CSiBridge scalar component envelope" in fig.layout.title.text
    assert "M3 → Mx" in fig.layout.title.text
    assert fig.layout.yaxis.title.text == "Bending moment, M3 = Mx (kN·m)"
    assert "%{x:.4f}" in fig.data[0].hovertemplate


def test_fea5b2_governing_annotation_moves_inward_at_right_edge():
    rows = [
        ["B2_SPAN1", 1, 0.0, "After", "U1", "Combination", "Max", 0, 1, 1, 10],
        ["B2_SPAN1", 1, 0.0, "After", "U1", "Combination", "Min", 0, -1, -1, -10],
        ["B2_SPAN1", 2, 39.95, "Before", "U1", "Combination", "Max", 0, 100, 80, 20],
        ["B2_SPAN1", 2, 39.95, "Before", "U1", "Combination", "Min", 0, -20, -10, -15],
    ]
    payload = read_csibridge_force_workbook(_workbook_bytes(rows), filename="uls.xlsx", stage="uls")
    fig = uls_component_envelope_figure(payload, "V2", bridge_object="B2_SPAN1")
    annotation = fig.layout.annotations[0]
    assert annotation.ax < 0
    assert annotation.xanchor == "right"



def test_fea5b_rejects_unknown_force_component():
    with pytest.raises(ValueError, match="Unsupported FEA force component"):
        component_envelope_frame({"envelopes": []}, "V3")


def test_fea5b1_axis_convention_metadata_and_dominant_sources():
    assert FORCE_COMPONENT_META["P"]["title"] == "P (Axial)"
    assert FORCE_COMPONENT_META["V2"]["axis"] == "Vertical shear, V2 = Vy (kN)"
    assert FORCE_COMPONENT_META["T"]["title"] == "T (Torsion)"
    assert FORCE_COMPONENT_META["M3"]["mapping"] == "M3 → Mx"

    rows = [
        ["B2_SPAN1", 1, 0.0, "After", "U1", "Combination", "Max", -10, 30, -5, 100],
        ["B2_SPAN1", 1, 0.0, "After", "U1", "Combination", "Min", -40, -20, 8, 50],
        ["B2_SPAN1", 1, 0.0, "After", "U2", "Combination", "Max", -8, 25, -3, 80],
        ["B2_SPAN1", 1, 0.0, "After", "U2", "Combination", "Min", -35, -18, 6, 55],
        ["B2_SPAN1", 2, 1.0, "Before", "U1", "Combination", "Max", -12, 22, 3, 90],
        ["B2_SPAN1", 2, 1.0, "Before", "U1", "Combination", "Min", -30, -18, -4, 45],
        ["B2_SPAN1", 2, 1.0, "Before", "U2", "Combination", "Max", -9, 19, 2, 85],
        ["B2_SPAN1", 2, 1.0, "Before", "U2", "Combination", "Min", -28, -24, -6, 48],
        ["B2_SPAN1", 3, 2.0, "After", "U1", "Combination", "Max", -11, 20, 1, 88],
        ["B2_SPAN1", 3, 2.0, "After", "U1", "Combination", "Min", -29, -19, -5, 40],
        ["B2_SPAN1", 3, 2.0, "After", "U2", "Combination", "Max", -9, 19, 2, 95],
        ["B2_SPAN1", 3, 2.0, "After", "U2", "Combination", "Min", -28, -24, -6, 42],
    ]
    payload = read_csibridge_force_workbook(_workbook_bytes(rows), filename="uls.xlsx", stage="uls")
    dominant = dominant_component_sources(payload, "M3")
    assert dominant["max"]["label"].startswith("U1 / Max")
    assert dominant["max"]["count"] == 2
    assert dominant["max"]["total"] == 3
    assert dominant["min"]["label"].startswith("U1 / Min")


def test_fea5c_transfer_simultaneous_component_review_and_chart():
    rows = [
        ["B2_SPAN1", 1, 0.0, "After", "Transfer stage", "Combination", -100, -20, 2, -50],
        ["B2_SPAN1", 2, 39.95, "Before", "Transfer stage", "Combination", -110, 45, -8, 120],
    ]
    payload = read_csibridge_force_workbook(
        _workbook_bytes(rows, include_step=False), filename="transfer.xlsx", stage="transfer"
    )
    frame = transfer_component_frame(payload, "M3")
    assert list(frame["SectCutNum"]) == [1, 2]
    assert frame.loc[1, "Value"] == 120.0
    assert frame.loc[1, "P"] == -110.0
    assert frame.loc[1, "SourceState"] == SOURCE_STATE_SINGLE

    governing = governing_transfer_component(payload, "M3")
    assert governing["absolute"] == 120.0
    assert governing["sect_cut_num"] == 2
    assert governing["distance_m"] == 39.95
    assert governing["vector"] == {"P": -110.0, "V2": 45.0, "T": -8.0, "M3": 120.0}

    fig = transfer_component_figure(payload, "M3", bridge_object="B2_SPAN1")
    assert len(fig.data) == 2
    assert fig.data[0].name == "M3 (Mx)"
    assert fig.data[1].name == "Governing M3 (Mx)"
    assert "CSiBridge SINGLE STATE force vector" in fig.layout.title.text
    assert "M3 → Mx" in fig.layout.title.text
    assert "%{x:.4f}" in fig.data[0].hovertemplate
    assert "P (Axial)" in fig.data[0].hovertemplate
    assert fig.layout.annotations[0].ax < 0
    assert fig.layout.annotations[0].xanchor == "right"


def test_fea5c1_transfer_negative_governing_value_stays_signed_in_chart_labels():
    rows = [
        ["B2_SPAN1", 1, 0.0, "After", "Transfer stage", "Combination", -100, -20, 2, -150],
        ["B2_SPAN1", 2, 39.95, "Before", "Transfer stage", "Combination", -110, 45, -8, 120],
    ]
    payload = read_csibridge_force_workbook(
        _workbook_bytes(rows, include_step=False), filename="transfer.xlsx", stage="transfer"
    )
    governing = governing_transfer_component(payload, "M3")
    assert governing["value"] == -150.0
    assert governing["absolute"] == 150.0

    fig = transfer_component_figure(payload, "M3", bridge_object="B2_SPAN1")
    assert fig.data[1].y[0] == -150.0
    assert fig.data[1].name == "Governing M3 (Mx)"
    assert "Governing M3 (Mx)" in fig.data[1].hovertemplate
    assert fig.layout.annotations[0].text == "Governing M3 (Mx)"
    assert fig.layout.annotations[0].y == -150.0
    assert FORCE_COMPONENT_META["M3"]["transfer_metric"] == "GOVERNING M3 (Mx)"
    assert FORCE_COMPONENT_META["M3"]["metric"] == "GOVERNING |M3| (Mx)"


def test_fea5c_transfer_rejects_unknown_component():
    with pytest.raises(ValueError, match="Unsupported FEA force component"):
        transfer_component_frame({"records": []}, "V3")


def test_fea5d_final_service_mixed_source_scalar_review_and_chart():
    rows = [
        ["B2_SPAN1", 1, 0.0, "After", "S1A", "Combination", "Max", -10, 25, 2, 80],
        ["B2_SPAN1", 1, 0.0, "After", "S1A", "Combination", "Min", -40, -30, -4, -60],
        ["B2_SPAN1", 1, 0.0, "After", "S2", "Combination", "", -20, 10, 1, 50],
        ["B2_SPAN1", 2, 39.95, "Before", "S1A", "Combination", "Max", -12, 45, 3, 150],
        ["B2_SPAN1", 2, 39.95, "Before", "S1A", "Combination", "Min", -35, -25, -5, -90],
        ["B2_SPAN1", 2, 39.95, "Before", "S2", "Combination", "", -18, 15, 2, 70],
    ]
    payload = read_csibridge_force_workbook(_workbook_bytes(rows), filename="service.xlsx", stage="service")
    assert payload["source_semantics"]["overall"] == "MIXED"
    assert payload["source_semantics"]["single_state_rows"] == 2
    assert payload["source_semantics"]["component_envelope_rows"] == 4

    frame = component_envelope_frame(payload, "M3")
    assert list(frame["SectCutNum"]) == [1, 2]
    assert frame.loc[1, "Upper"] == 150.0
    assert "S1A / Max" in frame.loc[1, "UpperSource"]
    governing = governing_component_envelope(payload, "M3")
    assert governing["absolute"] == 150.0
    assert governing["distance_m"] == 39.95
    assert "COMPONENT ENVELOPE" in governing["source"]

    fig = service_component_envelope_figure(payload, "M3", bridge_object="B2_SPAN1")
    assert len(fig.data) == 3
    assert fig.data[0].name == "M3 max"
    assert fig.data[1].line.dash == "dash"
    assert fig.data[2].name == "Governing |M3| (Mx)"
    assert "Final Service SLS M3 (Mx) Envelope" in fig.layout.title.text
    assert "CSiBridge mixed-source scalar envelope" in fig.layout.title.text
    assert "M3 → Mx" in fig.layout.title.text
    assert fig.layout.annotations[0].ax < 0
    assert fig.layout.annotations[0].xanchor == "right"


def test_fea5d_final_service_figure_rejects_unknown_component():
    with pytest.raises(ValueError, match="Unsupported FEA force component"):
        service_component_envelope_figure({"envelopes": []}, "V3")



def _qa_three_stage_payloads() -> dict[str, dict]:
    uls_rows = [
        ["B2_SPAN1", 1, 0.0, "After", "U1", "Combination", "Max", -10, 30, -5, 100],
        ["B2_SPAN1", 1, 0.0, "After", "U1", "Combination", "Min", -40, -20, 8, 50],
        ["B2_SPAN1", 1, 0.0, "After", "U2", "Combination", "Max", -5, 10, 2, 120],
        ["B2_SPAN1", 1, 0.0, "After", "U2", "Combination", "Min", -25, -35, -9, 40],
        ["B2_SPAN1", 2, 1.0, "Before", "U1", "Combination", "Max", -12, 22, 3, 90],
        ["B2_SPAN1", 2, 1.0, "Before", "U1", "Combination", "Min", -30, -18, -4, 45],
        ["B2_SPAN1", 2, 1.0, "Before", "U2", "Combination", "Max", -9, 19, 2, 95],
        ["B2_SPAN1", 2, 1.0, "Before", "U2", "Combination", "Min", -28, -24, -6, 42],
    ]
    transfer_rows = [
        ["B2_SPAN1", 1, 0.0, "After", "Transfer stage", "Combination", -100, -20, 2, -50],
        ["B2_SPAN1", 2, 1.0, "Before", "Transfer stage", "Combination", -110, 18, -1, -40],
    ]
    service_rows = [
        ["B2_SPAN1", 1, 0.0, "After", "S1", "Combination", "Max", -20, 12, 1, 60],
        ["B2_SPAN1", 1, 0.0, "After", "S1", "Combination", "Min", -50, -14, -2, -70],
        ["B2_SPAN1", 1, 0.0, "After", "S2", "Combination", "", -15, 9, 0.5, 55],
        ["B2_SPAN1", 2, 1.0, "Before", "S1", "Combination", "Max", -22, 15, 2, 65],
        ["B2_SPAN1", 2, 1.0, "Before", "S1", "Combination", "Min", -55, -16, -3, -75],
        ["B2_SPAN1", 2, 1.0, "Before", "S2", "Combination", "", -18, 10, 1.0, 58],
    ]
    return {
        "uls": read_csibridge_force_workbook(_workbook_bytes(uls_rows), filename="uls.xlsx", stage="uls"),
        "transfer": read_csibridge_force_workbook(_workbook_bytes(transfer_rows, include_step=False), filename="transfer.xlsx", stage="transfer"),
        "service": read_csibridge_force_workbook(_workbook_bytes(service_rows), filename="service.xlsx", stage="service"),
    }


def test_fea5e_package_integrity_recomputes_all_stage_and_cross_stage_gates():
    imports = _qa_three_stage_payloads()
    gates = package_integrity_gates(imports, "B2_SPAN1", span_m=1.0)
    assert gates
    assert all(row["Status"] == "READY" for row in gates)
    assert any(row["Gate"] == "Transfer simultaneous-vector contract" for row in gates)
    assert any(row["Gate"] == "Compact-envelope source trace" for row in gates)
    assert any(row["Stage"] == "Cross-stage package" and row["Gate"] == "Three-stage source package" for row in gates)


def test_fea5e_integrity_detects_persisted_payload_tampering():
    imports = _qa_three_stage_payloads()
    imports["uls"]["records"].append(dict(imports["uls"]["records"][0]))
    gates = package_integrity_gates(imports, "B2_SPAN1", span_m=1.0)
    by_gate = {(row["Stage"], row["Gate"]): row for row in gates}
    assert by_gate[("ULS", "Inventory reconciliation")]["Status"] == "SOURCE BLOCKED"
    assert by_gate[("ULS", "Unique source-row identity")]["Status"] == "SOURCE BLOCKED"


def test_fea5e_governing_trace_links_envelope_to_original_row_and_semantics():
    imports = _qa_three_stage_payloads()
    trace = trace_component_extremum(imports["uls"], "M3", "absolute")
    assert trace["value"] == 120.0
    assert trace["OutputCase"] == "U2"
    assert trace["StepType"] == "Max"
    assert trace["SourceState"] == SOURCE_STATE_COMPONENT_ENVELOPE
    assert trace["envelope_source_matches"] is True
    assert trace["companion_vector_status"] == "NOT A SIMULTANEOUS FORCE VECTOR"
    assert trace["companion_values"]["P"] == -5.0

    transfer_trace = trace_component_extremum(imports["transfer"], "P", "absolute")
    assert transfer_trace["value"] == -110.0
    assert transfer_trace["SourceState"] == SOURCE_STATE_SINGLE
    assert transfer_trace["companion_vector_status"] == "SIMULTANEOUS SOURCE VECTOR"
    assert transfer_trace["envelope_source_matches"] is True

    service_trace = trace_component_extremum(imports["service"], "P", "maximum")
    assert service_trace["value"] == -15.0
    assert service_trace["OutputCase"] == "S2"
    assert service_trace["StepType"] == ""
    assert service_trace["SourceState"] == SOURCE_STATE_SINGLE
    assert service_trace["companion_vector_status"] == "SIMULTANEOUS SOURCE VECTOR"
    assert service_trace["companion_values"]["M3"] == 55.0
    assert service_trace["envelope_source_matches"] is True



def test_fea5e1_integrity_gate_severity_is_not_current_blocking_status():
    gates = package_integrity_gates(_qa_three_stage_payloads(), "B2_SPAN1", span_m=1.0)
    assert gates
    assert all("Gate severity" in row for row in gates)
    assert all("Blocking" not in row for row in gates)
    assert {row["Gate severity"] for row in gates} == {"BLOCKING"}
    assert all(row["Status"] == "READY" for row in gates)


def test_fea5e_trace_rejects_unknown_component_and_selection():
    payload = _qa_three_stage_payloads()["uls"]
    with pytest.raises(ValueError, match="Unsupported force component"):
        trace_component_extremum(payload, "V3", "absolute")
    with pytest.raises(ValueError, match="Unsupported extremum selection"):
        trace_component_extremum(payload, "P", "median")
