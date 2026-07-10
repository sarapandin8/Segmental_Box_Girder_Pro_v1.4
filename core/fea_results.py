from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from io import BytesIO
from typing import Any, BinaryIO, Iterable

import pandas as pd


FORCE_COMPONENTS = ("P", "V2", "T", "M3")
STAGE_LABELS = {
    "uls": "ULS",
    "transfer": "Transfer Stage",
    "service": "Final Service SLS",
}
SOURCE_STATE_SINGLE = "SINGLE STATE"
SOURCE_STATE_COMPONENT_ENVELOPE = "COMPONENT ENVELOPE"
PROGRAM_CONTROL_ALLOWLIST = ("ProgramName", "Version", "CurrUnits", "BridgeCode", "ConcCode")
REQUIRED_BASE_COLUMNS = (
    "BridgeObj",
    "SectCutNum",
    "Distance",
    "LocType",
    "OutputCase",
    "CaseType",
    "P",
    "V2",
    "T",
    "M3",
)
EXPECTED_UNITS = {
    "Distance": "m",
    "P": "KN",
    "V2": "KN",
    "T": "KN-m",
    "M3": "KN-m",
}


class FEAResultImportError(ValueError):
    """Raised when a CSiBridge force workbook is not safe to adopt."""


def _read_source_bytes(source: bytes | bytearray | BinaryIO | Any) -> bytes:
    if isinstance(source, (bytes, bytearray)):
        return bytes(source)
    if hasattr(source, "getvalue"):
        return bytes(source.getvalue())
    if hasattr(source, "read"):
        raw = source.read()
        return raw if isinstance(raw, bytes) else bytes(raw)
    raise FEAResultImportError("The selected FEA source cannot be read as an Excel workbook.")


def _find_header_row(raw: pd.DataFrame) -> int:
    required = set(REQUIRED_BASE_COLUMNS)
    for idx in range(min(len(raw), 30)):
        row = {str(value).strip() for value in raw.iloc[idx].tolist() if not pd.isna(value)}
        if required.issubset(row):
            return idx
    raise FEAResultImportError(
        "Could not find the CSiBridge Bridge Object Forces header. "
        "Required columns are BridgeObj, SectCutNum, Distance, LocType, OutputCase, "
        "CaseType, P, V2, T, and M3."
    )


def _clean_text(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def _normalise_force_sheet(raw: pd.DataFrame, *, stage: str) -> tuple[pd.DataFrame, dict[str, str]]:
    header_row = _find_header_row(raw)
    headers = [_clean_text(value) for value in raw.iloc[header_row].tolist()]
    if len(headers) != len(set(headers)):
        raise FEAResultImportError("The Bridge Object Forces table contains duplicate column headers.")

    missing = [name for name in REQUIRED_BASE_COLUMNS if name not in headers]
    if missing:
        raise FEAResultImportError(f"Missing required Bridge Object Forces columns: {', '.join(missing)}.")
    if stage in {"uls", "service"} and "StepType" not in headers:
        raise FEAResultImportError(f"{STAGE_LABELS[stage]} requires the StepType column for Max/Min traceability.")

    unit_row = header_row + 1
    if unit_row >= len(raw):
        raise FEAResultImportError("The Bridge Object Forces unit row is missing.")
    units = {name: _clean_text(raw.iloc[unit_row, headers.index(name)]) for name in EXPECTED_UNITS}
    unit_issues = [
        f"{name}={units.get(name) or '-'} (expected {expected})"
        for name, expected in EXPECTED_UNITS.items()
        if (units.get(name) or "").upper() != expected.upper()
    ]
    if unit_issues:
        raise FEAResultImportError("Unsupported FEA units: " + "; ".join(unit_issues) + ".")

    data = raw.iloc[unit_row + 1 :].copy()
    data.columns = headers
    data = data.dropna(how="all")
    if data.empty:
        raise FEAResultImportError("The Bridge Object Forces table contains no result rows.")
    if "StepType" not in data.columns:
        data["StepType"] = ""

    keep = [
        "BridgeObj",
        "SectCutNum",
        "Distance",
        "LocType",
        "OutputCase",
        "CaseType",
        "StepType",
        *FORCE_COMPONENTS,
    ]
    data = data[keep].copy()
    data.insert(0, "SourceRow", range(unit_row + 2, unit_row + 2 + len(data)))

    for name in ("BridgeObj", "LocType", "OutputCase", "CaseType", "StepType"):
        data[name] = data[name].map(_clean_text)
    for name in ("SectCutNum", "Distance", *FORCE_COMPONENTS):
        data[name] = pd.to_numeric(data[name], errors="coerce")

    bad_numeric = {name: int(data[name].isna().sum()) for name in ("SectCutNum", "Distance", *FORCE_COMPONENTS)}
    bad_numeric = {name: count for name, count in bad_numeric.items() if count}
    if bad_numeric:
        detail = ", ".join(f"{name}: {count}" for name, count in bad_numeric.items())
        raise FEAResultImportError(f"Non-numeric or blank required FEA values were found ({detail}).")
    if (data["SectCutNum"] <= 0).any() or not (data["SectCutNum"] % 1 == 0).all():
        raise FEAResultImportError("SectCutNum must contain positive integer identifiers.")
    data["SectCutNum"] = data["SectCutNum"].astype(int)

    blank_required = {
        name: int((data[name] == "").sum())
        for name in ("BridgeObj", "LocType", "OutputCase", "CaseType")
        if int((data[name] == "").sum())
    }
    if blank_required:
        detail = ", ".join(f"{name}: {count}" for name, count in blank_required.items())
        raise FEAResultImportError(f"Blank required text values were found ({detail}).")

    invalid_loc = sorted(set(data.loc[~data["LocType"].isin(["Before", "After"]), "LocType"]))
    if invalid_loc:
        raise FEAResultImportError("Unsupported LocType values: " + ", ".join(invalid_loc) + ".")

    invalid_steps = sorted(set(data.loc[~data["StepType"].isin(["", "Max", "Min"]), "StepType"]))
    if invalid_steps:
        raise FEAResultImportError("Unsupported StepType values: " + ", ".join(invalid_steps) + ".")

    key_columns = ["BridgeObj", "SectCutNum", "Distance", "LocType", "OutputCase", "StepType"]
    duplicates = data.duplicated(key_columns, keep=False)
    if duplicates.any():
        raise FEAResultImportError(
            f"Found {int(duplicates.sum())} duplicated result rows using the source identity "
            "BridgeObj/SectCutNum/Distance/LocType/OutputCase/StepType."
        )

    data["SourceState"] = data["StepType"].map(
        lambda value: SOURCE_STATE_SINGLE if value == "" else SOURCE_STATE_COMPONENT_ENVELOPE
    )
    return data.sort_values(["SectCutNum", "OutputCase", "StepType", "SourceRow"]).reset_index(drop=True), units


def _validate_transfer_single_state(frame: pd.DataFrame) -> None:
    """Enforce the transfer-stage contract instead of merely describing it in the UI."""
    output_cases = sorted(set(frame["OutputCase"]))
    if len(output_cases) != 1:
        raise FEAResultImportError(
            "Transfer Stage must contain exactly one OutputCase and one simultaneous force vector per SectCutNum. "
            f"Found {len(output_cases)} OutputCase values: {', '.join(output_cases) or '-'}.")
    nonblank_steps = frame.loc[frame["StepType"] != "", "StepType"]
    if not nonblank_steps.empty:
        raise FEAResultImportError(
            "Transfer Stage must not contain Max/Min StepType rows. Export one single-state result row per SectCutNum."
        )
    rows_per_cut = frame.groupby("SectCutNum").size()
    bad = rows_per_cut[rows_per_cut != 1]
    if not bad.empty:
        preview = ", ".join(f"{int(cut)}:{int(count)}" for cut, count in bad.head(12).items())
        raise FEAResultImportError(
            "Transfer Stage requires exactly one row per SectCutNum. "
            f"Nonconforming cut row counts: {preview}."
        )
    if not (frame["SourceState"] == SOURCE_STATE_SINGLE).all():
        raise FEAResultImportError("Transfer Stage source semantics must be SINGLE STATE for every row.")


def _program_control(raw: pd.DataFrame | None) -> dict[str, str]:
    """Return engineering-use metadata only; never persist license or machine details."""
    if raw is None or raw.empty:
        return {}
    try:
        header_row = next(
            idx
            for idx in range(min(len(raw), 20))
            if "ProgramName" in {_clean_text(v) for v in raw.iloc[idx].tolist()}
        )
    except StopIteration:
        return {}
    headers = [_clean_text(value) for value in raw.iloc[header_row].tolist()]
    data_row = header_row + 2
    if data_row >= len(raw):
        return {}
    values = raw.iloc[data_row].tolist()
    by_name = {
        name: _clean_text(values[index])
        for index, name in enumerate(headers)
        if name and index < len(values) and _clean_text(values[index])
    }
    return {name: by_name[name] for name in PROGRAM_CONTROL_ALLOWLIST if by_name.get(name)}


def _row_source(row: pd.Series) -> dict[str, Any]:
    return {
        "OutputCase": _clean_text(row["OutputCase"]),
        "StepType": _clean_text(row["StepType"]),
        "SourceState": _clean_text(row["SourceState"]),
        "SourceRow": int(row["SourceRow"]),
    }


def build_scalar_envelopes(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Build one scalar-extrema record per physical SectCutNum.

    Each force component keeps its own OutputCase/StepType source. The resulting
    row is deliberately not described as a simultaneous force vector.
    """
    keys = ["BridgeObj", "SectCutNum", "Distance", "LocType"]
    envelopes: list[dict[str, Any]] = []
    for key, group in frame.groupby(keys, sort=True, dropna=False):
        row: dict[str, Any] = {
            "BridgeObj": str(key[0]),
            "SectCutNum": int(key[1]),
            "Distance": float(key[2]),
            "LocType": str(key[3]),
            "CandidateRows": int(len(group)),
        }
        for component in FORCE_COMPONENTS:
            min_row = group.loc[group[component].idxmin()]
            max_row = group.loc[group[component].idxmax()]
            row[f"{component}_min"] = float(min_row[component])
            row[f"{component}_min_source"] = _row_source(min_row)
            row[f"{component}_max"] = float(max_row[component])
            row[f"{component}_max_source"] = _row_source(max_row)
        envelopes.append(row)
    return envelopes


def _case_summary(frame: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for output_case, group in frame.groupby("OutputCase", sort=True):
        steps = [step for step in ("Max", "Min") if step in set(group["StepType"])]
        if "" in set(group["StepType"]):
            steps.append("Single")
        states = sorted(set(group["SourceState"]))
        rows.append(
            {
                "OutputCase": str(output_case),
                "StepTypes": " / ".join(steps),
                "Source semantics": " / ".join(states),
                "Rows": int(len(group)),
                "SectCuts": int(group["SectCutNum"].nunique()),
            }
        )
    return rows


def _record_dicts(frame: pd.DataFrame) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item in frame.to_dict("records"):
        record: dict[str, Any] = {}
        for key, value in item.items():
            if key in {"SourceRow", "SectCutNum"}:
                record[key] = int(value)
            elif key in {"Distance", *FORCE_COMPONENTS}:
                record[key] = float(value)
            else:
                record[key] = _clean_text(value)
        records.append(record)
    return records


def source_semantics_summary(frame: pd.DataFrame) -> dict[str, Any]:
    single_rows = int((frame["SourceState"] == SOURCE_STATE_SINGLE).sum())
    envelope_rows = int((frame["SourceState"] == SOURCE_STATE_COMPONENT_ENVELOPE).sum())
    if envelope_rows and single_rows:
        overall = "MIXED"
    elif envelope_rows:
        overall = SOURCE_STATE_COMPONENT_ENVELOPE
    else:
        overall = SOURCE_STATE_SINGLE
    return {
        "overall": overall,
        "single_state_rows": single_rows,
        "component_envelope_rows": envelope_rows,
        "simultaneous_pairing_allowed": envelope_rows == 0,
    }


def read_csibridge_force_workbook(
    source: bytes | bytearray | BinaryIO | Any,
    *,
    filename: str,
    stage: str,
) -> dict[str, Any]:
    """Read, validate, and normalize a CSiBridge Bridge Object Forces workbook."""
    if stage not in STAGE_LABELS:
        raise FEAResultImportError(f"Unsupported FEA stage: {stage}.")
    raw_bytes = _read_source_bytes(source)
    if not raw_bytes:
        raise FEAResultImportError("The selected FEA workbook is empty.")
    try:
        sheets = pd.read_excel(BytesIO(raw_bytes), sheet_name=None, header=None)
    except Exception as exc:  # noqa: BLE001 - convert spreadsheet parser errors for the UI.
        raise FEAResultImportError(f"Could not read the Excel workbook: {exc}") from exc
    if "Bridge Object Forces" not in sheets:
        raise FEAResultImportError("The workbook must contain a sheet named 'Bridge Object Forces'.")

    frame, units = _normalise_force_sheet(sheets["Bridge Object Forces"], stage=stage)
    bridge_objects = sorted(set(frame["BridgeObj"]))
    if len(bridge_objects) != 1:
        raise FEAResultImportError(
            "Each imported stage must contain exactly one BridgeObj. "
            f"Found BridgeObj values: {', '.join(bridge_objects) or '-'}.",
        )
    all_cut_ids = set(frame["SectCutNum"])
    incomplete_case_steps: list[str] = []
    for (output_case, step_type), group in frame.groupby(["OutputCase", "StepType"], dropna=False):
        if set(group["SectCutNum"]) != all_cut_ids:
            incomplete_case_steps.append(f"{output_case}/{step_type or 'Single'}")
    if incomplete_case_steps:
        raise FEAResultImportError(
            "Every OutputCase/StepType source must cover the complete SectCutNum map. "
            "Incomplete sources: " + ", ".join(incomplete_case_steps[:12]) + "."
        )
    rows_per_cut = frame.groupby("SectCutNum").size()
    cut_location_counts = frame[["SectCutNum", "Distance", "LocType"]].drop_duplicates().groupby("SectCutNum").size()
    if int(cut_location_counts.max()) != 1:
        raise FEAResultImportError("A SectCutNum maps to more than one Distance/LocType identity.")
    if stage == "transfer":
        _validate_transfer_single_state(frame)

    sha256 = hashlib.sha256(raw_bytes).hexdigest()
    semantics = source_semantics_summary(frame)
    payload = {
        "valid": True,
        "stage": stage,
        "stage_label": STAGE_LABELS[stage],
        "filename": str(filename or f"Bridge Forces_{STAGE_LABELS[stage]}.xlsx"),
        "sha256": sha256,
        "sha256_12": sha256[:12],
        "imported_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "bridge_objects": bridge_objects,
        "units": units,
        "program_control": _program_control(sheets.get("Program Control")),
        "summary": {
            "rows": int(len(frame)),
            "sect_cuts": int(frame["SectCutNum"].nunique()),
            "distance_min_m": float(frame["Distance"].min()),
            "distance_max_m": float(frame["Distance"].max()),
            "unique_distances": int(frame["Distance"].nunique()),
            "output_cases": int(frame["OutputCase"].nunique()),
            "rows_per_cut_min": int(rows_per_cut.min()),
            "rows_per_cut_max": int(rows_per_cut.max()),
            "before_rows": int((frame["LocType"] == "Before").sum()),
            "after_rows": int((frame["LocType"] == "After").sum()),
        },
        "source_semantics": semantics,
        "case_summary": _case_summary(frame),
        "records": _record_dicts(frame),
        "envelopes": build_scalar_envelopes(frame),
        "interpretation": (
            "Rows marked SINGLE STATE preserve one simultaneous P-V2-T-M3 force vector. Rows marked COMPONENT "
            "ENVELOPE contain component-wise Max/Min output and must not be treated as simultaneous P-M3 or V2-T pairs. "
            "Compact envelopes retain separate sources for each scalar extremum and are not one force vector."
        ),
    }
    return payload


def stage_source_status(stage_payload: Any, active_bridge_object: str) -> dict[str, str]:
    if not isinstance(stage_payload, dict) or not stage_payload.get("valid"):
        return {"status": "PENDING", "mode": "warn", "note": "Upload the required CSiBridge force workbook."}
    objects = [str(value) for value in stage_payload.get("bridge_objects", [])]
    if active_bridge_object not in objects:
        return {
            "status": "SPAN SOURCE REVIEW",
            "mode": "warn",
            "note": f"Imported source {', '.join(objects) or '-'} does not match active span {active_bridge_object}.",
        }
    if stage_payload.get("stage") == "transfer":
        summary = stage_payload.get("summary", {})
        semantics = stage_payload.get("source_semantics", {})
        if (
            int(summary.get("output_cases", 0)) != 1
            or int(summary.get("rows_per_cut_min", 0)) != 1
            or int(summary.get("rows_per_cut_max", 0)) != 1
            or semantics.get("overall") != SOURCE_STATE_SINGLE
        ):
            return {
                "status": "SOURCE BLOCKED",
                "mode": "fail",
                "note": "Transfer source does not satisfy the one-case, one-row-per-cut SINGLE STATE contract.",
            }
    return {
        "status": "READY",
        "mode": "pass",
        "note": f"Imported source matches active span {active_bridge_object}.",
    }


def station_identity(records: Iterable[dict[str, Any]]) -> set[tuple[int, float, str]]:
    return {
        (int(row["SectCutNum"]), round(float(row["Distance"]), 9), str(row["LocType"]))
        for row in records
    }


def cross_stage_station_consistency(stage_imports: Any) -> dict[str, Any]:
    imports = stage_imports if isinstance(stage_imports, dict) else {}
    available = [stage for stage in ("uls", "transfer", "service") if isinstance(imports.get(stage), dict) and imports[stage].get("valid")]
    if len(available) < 2:
        return {
            "status": "PENDING",
            "mode": "warn",
            "stages": available,
            "mismatch_count": 0,
            "note": "Import at least two stages to compare SectCutNum/Distance/LocType identities.",
        }
    reference = available[0]
    reference_keys = station_identity(imports[reference].get("records", []))
    details: list[dict[str, Any]] = []
    mismatch_count = 0
    for stage in available[1:]:
        keys = station_identity(imports[stage].get("records", []))
        missing = reference_keys - keys
        extra = keys - reference_keys
        mismatch_count += len(missing) + len(extra)
        details.append(
            {
                "Stage": STAGE_LABELS[stage],
                "Station identities": len(keys),
                "Missing vs reference": len(missing),
                "Extra vs reference": len(extra),
            }
        )
    if mismatch_count:
        return {
            "status": "REVIEW",
            "mode": "warn",
            "stages": available,
            "reference_stage": reference,
            "mismatch_count": mismatch_count,
            "details": details,
            "note": "The imported stages do not share one SectCutNum/Distance/LocType map.",
        }
    return {
        "status": "READY",
        "mode": "pass",
        "stages": available,
        "reference_stage": reference,
        "mismatch_count": 0,
        "details": details,
        "note": f"All imported stages share {len(reference_keys)} section-cut identities.",
    }


def source_package_fingerprint(stage_imports: Any) -> str:
    imports = stage_imports if isinstance(stage_imports, dict) else {}
    tokens = [f"{stage}:{imports.get(stage, {}).get('sha256', '-')}" for stage in ("uls", "transfer", "service")]
    return hashlib.sha256("|".join(tokens).encode("utf-8")).hexdigest()


def source_package_gate(stage_imports: Any, active_bridge_object: str) -> dict[str, Any]:
    imports = stage_imports if isinstance(stage_imports, dict) else {}
    stage_states = {stage: stage_source_status(imports.get(stage), active_bridge_object) for stage in ("uls", "transfer", "service")}
    all_ready = all(item["status"] == "READY" for item in stage_states.values())
    consistency = cross_stage_station_consistency(imports)
    ready = all_ready and consistency["status"] == "READY"
    return {
        "status": "READY" if ready else "REVIEW",
        "mode": "pass" if ready else "warn",
        "ready": ready,
        "stage_states": stage_states,
        "station_consistency": consistency,
        "fingerprint": source_package_fingerprint(imports),
        "note": "Three validated source stages share the active span and section-cut map." if ready else "Complete and reconcile ULS, Transfer, and Final Service SLS sources.",
    }


def global_component_extrema(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    frame = pd.DataFrame(list(records))
    if frame.empty:
        return []
    rows: list[dict[str, Any]] = []
    for component in FORCE_COMPONENTS:
        numeric = pd.to_numeric(frame[component], errors="coerce")
        min_row = frame.loc[numeric.idxmin()]
        max_row = frame.loc[numeric.idxmax()]
        abs_row = frame.loc[numeric.abs().idxmax()]
        source = lambda row: f"{row['OutputCase']} / {row.get('StepType') or 'Single'} / Cut {int(row['SectCutNum'])}"
        rows.append(
            {
                "Component": component,
                "Minimum": float(min_row[component]),
                "Minimum source": source(min_row),
                "Maximum": float(max_row[component]),
                "Maximum source": source(max_row),
                "Maximum absolute": float(abs_row[component]),
                "Absolute source": source(abs_row),
            }
        )
    return rows
