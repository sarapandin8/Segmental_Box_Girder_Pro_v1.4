"""Explicit tendon source-of-truth adoption helpers.

The tendon layout workflow has two distinct states:

1. imported/working model parsed from CSiBridge General + Vertical + Horizontal exports;
2. adopted design-source snapshot used by downstream prestress/report checks.

This separation prevents silent changes to design inputs when a user uploads or edits
raw import data.  Downstream modules should read the adopted snapshot/summary, not
raw imported rows.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from typing import Any


def tendon_model_fingerprint(model: dict[str, Any] | None) -> str:
    """Return a deterministic short fingerprint for a tendon model."""
    if not isinstance(model, dict) or not model:
        return ""
    payload = {
        "active_bridge_object": model.get("active_bridge_object"),
        "imported_bridge_objects": model.get("imported_bridge_objects", []),
        "mapped_to_active_bridge_object": model.get("mapped_to_active_bridge_object"),
        "span_m": model.get("span_m"),
        "tendons": model.get("tendons", []),
        "profile_rows": model.get("profile_rows", []),
        "group_summary": model.get("group_summary", []),
        "qa_rows": model.get("qa_rows", []),
    }
    raw = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def tendon_model_status(model: dict[str, Any] | None, tendon_layout: dict[str, Any] | None = None) -> dict[str, str]:
    """Compact status used by cards and QA gates."""
    tl = tendon_layout or {}
    model = model or {}
    valid = bool(model.get("valid"))
    adopted = tl.get("adopted_model") if isinstance(tl.get("adopted_model"), dict) else {}
    working_fp = tendon_model_fingerprint(model)
    adopted_fp = str(tl.get("adopted_model_fingerprint") or tendon_model_fingerprint(adopted))
    if not valid:
        return {"status": "PENDING", "mode": "warn", "message": "Import General / Vertical / Horizontal tendon tables."}
    if not adopted_fp:
        return {"status": "NOT ADOPTED", "mode": "warn", "message": "Working model is valid but not locked as design source."}
    if working_fp and adopted_fp and working_fp != adopted_fp:
        return {"status": "RE-ADOPT REQUIRED", "mode": "warn", "message": "Imported working model differs from the adopted design-source snapshot."}
    return {"status": "LOCKED", "mode": "pass", "message": "Adopted tendon model is the current downstream source of truth."}


def _source_metadata_text(value: Any) -> str:
    """Return a clean source-metadata value, treating UI placeholders as missing."""
    text = str(value or "").strip()
    if text in {"", "-", "—", "None", "null"}:
        return ""
    return text


def build_tendon_source_trace(tendon_layout: dict[str, Any] | None, model: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Build report-ready source trace rows for tendon import/adoption.

    Engineering payload completeness and original-file provenance are deliberately
    separated. A saved project may contain complete adopted tendon rows while the
    original upload filename/SHA metadata is unavailable. Such rows are labelled
    ``RESTORED FROM PROJECT SNAPSHOT`` rather than being over-certified as READY.
    """
    tl = tendon_layout or {}
    model = model or {}
    source_meta = tl.get("source_meta", {}) if isinstance(tl.get("source_meta"), dict) else {}

    prior_rows: list[dict[str, Any]] = []
    for candidate in (tl.get("adopted_source_trace"), model.get("source_trace_rows")):
        if isinstance(candidate, list):
            prior_rows.extend(row for row in candidate if isinstance(row, dict))
    prior_by_label = {str(row.get("Source table", "")): row for row in prior_rows}

    row_specs = [
        ("General", "general_rows", "general", "Tendon, area, material, jack-from, force trace"),
        ("Vertical", "vertical_rows", "vertical", "Station x and dp from top surface"),
        ("Horizontal", "horizontal_rows", "horizontal", "Station x and horizontal offset from CL"),
    ]
    rows: list[dict[str, Any]] = []
    for label, rows_key, meta_key, role in row_specs:
        records = tl.get(rows_key, []) if isinstance(tl.get(rows_key, []), list) else []
        meta = source_meta.get(meta_key, {}) if isinstance(source_meta.get(meta_key), dict) else {}
        prior = prior_by_label.get(label, {})

        fallback_count = 0
        if label == "General":
            fallback_count = len(model.get("tendons", []) or [])
        elif label in {"Vertical", "Horizontal"}:
            fallback_count = len(model.get("profile_rows", []) or [])
        try:
            prior_count = int(prior.get("Imported rows") or 0)
        except (TypeError, ValueError):
            prior_count = 0
        row_count = len(records) or prior_count or fallback_count

        filename = _source_metadata_text(meta.get("filename")) or _source_metadata_text(prior.get("Filename"))
        sha12 = _source_metadata_text(meta.get("sha256_12")) or _source_metadata_text(prior.get("File SHA-256 (12)"))

        if row_count <= 0:
            status = "MISSING"
        elif filename and sha12:
            status = "READY"
        elif filename or sha12:
            status = "SOURCE METADATA PARTIAL"
        else:
            status = "RESTORED FROM PROJECT SNAPSHOT"

        rows.append(
            {
                "Source table": label,
                "Imported rows": row_count,
                "Filename": filename or "-",
                "File SHA-256 (12)": sha12 or "-",
                "Role": role,
                "Status": status,
            }
        )

    imported_objs = model.get("imported_bridge_objects", []) or []
    rows.append(
        {
            "Source table": "BridgeObj mapping",
            "Imported rows": len(imported_objs),
            "Filename": ", ".join(imported_objs) if imported_objs else "-",
            "File SHA-256 (12)": "-",
            "Role": f"Mapped to active BridgeObj = {model.get('active_bridge_object', tl.get('active_bridge_object', '-'))}",
            "Status": "MAPPED" if model.get("mapped_to_active_bridge_object") and len(imported_objs) > 1 else ("MATCH" if imported_objs else "PENDING"),
        }
    )
    return rows


def summarize_tendon_source_provenance(source_trace: list[dict[str, Any]] | None) -> dict[str, Any]:
    """Summarize original-file provenance without blocking a complete design snapshot."""
    rows = [
        row
        for row in (source_trace or [])
        if isinstance(row, dict) and str(row.get("Source table", "")) in {"General", "Vertical", "Horizontal"}
    ]
    statuses = [str(row.get("Status", "")).upper() for row in rows]
    ready_count = sum(status == "READY" for status in statuses)
    snapshot_count = sum(status == "RESTORED FROM PROJECT SNAPSHOT" for status in statuses)
    partial_count = sum(status == "SOURCE METADATA PARTIAL" for status in statuses)
    missing_count = sum(status in {"", "MISSING", "REVIEW"} for status in statuses)

    if len(rows) == 3 and ready_count == 3:
        status = "READY"
        message = "Original filename and SHA-256 metadata are available for all three tendon source tables."
    elif len(rows) == 3 and missing_count == 0:
        status = "PARTIAL"
        message = "The adopted calculation snapshot is complete, but original filename/SHA metadata is unavailable for one or more source tables."
    else:
        status = "REVIEW"
        message = "One or more required tendon source tables or provenance records are missing."

    return {
        "status": status,
        "ready_count": ready_count,
        "snapshot_count": snapshot_count,
        "partial_count": partial_count,
        "missing_count": missing_count,
        "source_count": len(rows),
        "message": message,
    }



def normalise_jack_from(value: Any) -> str:
    """Return a compact JackFrom / stressing-end label from CSiBridge or project text."""
    raw = str(value or "").strip()
    if not raw:
        return ""
    key = raw.lower().replace("_", " ").replace("-", " ")
    if any(token in key for token in ("both", "two end", "two ends", "both ends")):
        return "Both ends"
    if key.startswith("start") or key in {"s", "left", "begin", "beginning"}:
        return "Start"
    if key.startswith("end") or key in {"e", "right"}:
        return "End"
    return raw


def build_tendon_stressing_basis_summary(model: dict[str, Any] | None) -> dict[str, Any]:
    """Summarize JackFrom / stressing mode from a tendon model without creating new input.

    This is an engineering source gate: the app should auto-detect the stressing
    basis from the CSiBridge General tendon table, then ask for review or a
    traced override only when the source is missing, mixed, or project-specific.
    Two-end stressing affects loss distribution only; it never doubles Aps,total
    or total tendon axial jacking force.
    """
    model = model or {}
    tendons = model.get("tendons", []) if isinstance(model.get("tendons", []), list) else []
    raw_values = [str(t.get("jack_from", "")).strip() for t in tendons if isinstance(t, dict)]
    normalised = [normalise_jack_from(v) for v in raw_values]
    missing_count = sum(1 for v in normalised if not v)
    present = [v for v in normalised if v]
    order = {"Start": 0, "End": 1, "Both ends": 2}
    unique = sorted(set(present), key=lambda v: order.get(v, 9))
    jack_display = ", ".join(unique) if unique else "—"

    if not model.get("valid") or not tendons:
        status = "PENDING"
        mode = "warn"
        detected_mode = "Build/import tendon model first"
        adoption_status = "BLOCKED"
        message = "Import General / Vertical / Horizontal tendon tables before stressing-basis review."
        ready = False
    elif not unique:
        status = "MISSING"
        mode = "warn"
        detected_mode = "JackFrom not found"
        adoption_status = "REVIEW REQUIRED"
        message = "General tendon table does not provide JackFrom / stressing-end metadata."
        ready = False
    elif unique == ["Both ends"] and missing_count == 0:
        status = "READY"
        mode = "pass"
        detected_mode = "Two-end stressing"
        adoption_status = "READY FOR ADOPTION"
        message = "Two-end stressing is explicit; use it for loss distribution only, not force doubling."
        ready = True
    elif len(unique) == 1 and unique[0] in {"Start", "End"} and missing_count == 0:
        status = "READY"
        mode = "pass"
        detected_mode = f"One-end stressing from {unique[0]}"
        adoption_status = "READY FOR ADOPTION"
        message = "One-end stressing basis is explicit from the General tendon table."
        ready = True
    elif set(unique).issubset({"Start", "End"}) and missing_count == 0:
        status = "REVIEW"
        mode = "warn"
        detected_mode = "Mixed one-end stressing by tendon"
        adoption_status = "REVIEW BEFORE ADOPTION"
        message = "Start/End stressing is tendon-specific; detailed loss routing must use each tendon row."
        ready = True
    else:
        status = "REVIEW"
        mode = "warn"
        detected_mode = "Mixed / project-specific JackFrom"
        adoption_status = "REVIEW BEFORE ADOPTION"
        message = "JackFrom values include missing or project-specific entries; confirm before adoption."
        ready = False if missing_count else True

    return {
        "status": status,
        "mode": mode,
        "ready": ready,
        "adoption_status": adoption_status,
        "detected_mode": detected_mode,
        "jack_from_values": unique,
        "jack_from_display": jack_display,
        "raw_jack_from_values": raw_values,
        "tendon_count": len(tendons),
        "missing_count": missing_count,
        "message": message,
        "source": "General tendon table · JackFrom field",
        "affects": "Friction loss and anchor-set distribution",
        "force_policy": "Pj/tendon is axial force; two-end stressing does not double Aps,total or total Pj.",
    }

def build_tendon_downstream_summary(model: dict[str, Any] | None, *, y_t_from_top_m: float = 0.0) -> dict[str, Any]:
    """Return the exact tendon summary intended for downstream design modules."""
    model = model or {}
    stressing = build_tendon_stressing_basis_summary(model)
    return {
        "source": "Adopted CSiBridge tendon layout model",
        "active_bridge_object": model.get("active_bridge_object", "-"),
        "tendon_count": int(len(model.get("tendons", []) or [])),
        "family_count": int(len({str(t.get("family", "")) for t in model.get("tendons", []) if str(t.get("family", "")).strip()})),
        "Aps_per_tendon_mm2": float(model.get("Aps_per_tendon_mm2") or 0.0),
        "Aps_total_mm2": float(model.get("total_area_mm2") or 0.0),
        "jacking_stress_mpa": float(model.get("jacking_stress_mpa") or 0.0),
        "jacking_force_per_tendon_kN": float(model.get("force_per_tendon_kN") or 0.0),
        "jacking_force_total_kN": float(model.get("total_force_kN") or 0.0),
        "dp_avg_end_m": float(model.get("dp_avg_end_m") or 0.0),
        "dp_avg_midspan_m": float(model.get("dp_avg_midspan_m") or 0.0),
        "y_t_from_top_m": float(y_t_from_top_m or 0.0),
        "eccentricity_midspan_m": float(model.get("eccentricity_midspan_m") or ((model.get("dp_avg_midspan_m") or 0.0) - (y_t_from_top_m or 0.0))),
        "jack_from_display": stressing.get("jack_from_display", "—"),
        "stressing_mode": stressing.get("detected_mode", "—"),
        "stressing_status": stressing.get("status", "PENDING"),
        "stressing_source": stressing.get("source", "General tendon table · JackFrom field"),
        "stressing_force_policy": stressing.get("force_policy", "Pj/tendon is axial force; two-end stressing does not double total Pj."),
        "model_fingerprint": tendon_model_fingerprint(model),
    }


def build_tendon_detailed_qa_integrity(
    model: dict[str, Any] | None,
    tendon_layout: dict[str, Any] | None = None,
    downstream_summary: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Return readiness checks for payload integrity and source provenance.

    A complete saved-project snapshot can remain usable even when the original
    upload filename/SHA metadata is unavailable. The register therefore reports
    calculation-payload readiness separately from source-metadata provenance.
    """
    model = model or {}
    tl = tendon_layout or {}
    tendons = model.get("tendons", []) if isinstance(model.get("tendons", []), list) else []
    profile_rows = model.get("profile_rows", []) if isinstance(model.get("profile_rows", []), list) else []
    group_rows = model.get("group_summary", []) if isinstance(model.get("group_summary", []), list) else []
    expected_profile_rows = sum(max(int(t.get("profile_point_count") or 0), 0) for t in tendons if isinstance(t, dict))
    source_trace = build_tendon_source_trace(tl, model)
    provenance = summarize_tendon_source_provenance(source_trace)
    summary = downstream_summary if isinstance(downstream_summary, dict) else build_tendon_downstream_summary(model)

    tendon_count = len(tendons)
    summary_tendon_count = int(summary.get("tendon_count") or 0)
    summary_area = float(summary.get("Aps_total_mm2") or 0.0)
    model_area = float(model.get("total_area_mm2") or 0.0)
    trace_labels = {str(row.get("Source table", "")) for row in source_trace if isinstance(row, dict)}
    required_trace_labels = {"General", "Vertical", "Horizontal", "BridgeObj mapping"}

    checks = [
        {
            "Item": "Tendon-by-tendon table",
            "Available": tendon_count,
            "Expected / basis": int(model.get("tendon_count") or tendon_count),
            "Status": "READY" if tendon_count > 0 else "MISSING",
        },
        {
            "Item": "Merged profile table",
            "Available": len(profile_rows),
            "Expected / basis": expected_profile_rows,
            "Status": "READY" if len(profile_rows) > 0 and len(profile_rows) == expected_profile_rows else "REVIEW",
        },
        {
            "Item": "Tendon group summary",
            "Available": len(group_rows),
            "Expected / basis": "At least 1 group",
            "Status": "READY" if len(group_rows) > 0 else "MISSING",
        },
        {
            "Item": "Downstream summary",
            "Available": f"{summary_tendon_count} tendons / {summary_area:,.0f} mm²",
            "Expected / basis": f"{tendon_count} tendons / {model_area:,.0f} mm²",
            "Status": "READY" if summary_tendon_count == tendon_count and tendon_count > 0 and abs(summary_area - model_area) <= 1e-6 else "REVIEW",
        },
        {
            "Item": "Source trace rows",
            "Available": len(source_trace),
            "Expected / basis": "General + Vertical + Horizontal + BridgeObj",
            "Status": "READY" if required_trace_labels.issubset(trace_labels) else "REVIEW",
        },
        {
            "Item": "Source metadata provenance",
            "Available": f"{provenance['ready_count']} ready / {provenance['snapshot_count']} snapshot / {provenance['partial_count']} partial",
            "Expected / basis": "Filename + SHA-256 for General / Vertical / Horizontal",
            "Status": provenance["status"],
        },
    ]
    return checks


def adopt_tendon_model(
    tendon_layout: dict[str, Any],
    prestress: dict[str, Any],
    model: dict[str, Any],
    *,
    y_t_from_top_m: float = 0.0,
) -> dict[str, Any]:
    """Lock the current imported tendon model as downstream design source.

    This intentionally updates the prestress summary fields from the adopted
    snapshot, not from raw imports.  Physical bend/deviator geometry from this
    locked source is consumed by the prestress-loss module for cumulative 3D
    friction α.
    """
    if not model or not model.get("valid"):
        raise ValueError("Cannot adopt an invalid tendon model.")
    snapshot = deepcopy(model)
    fp = tendon_model_fingerprint(snapshot)
    summary = build_tendon_downstream_summary(snapshot, y_t_from_top_m=y_t_from_top_m)
    tendon_layout["adopted_model"] = snapshot
    tendon_layout["adopted_model_fingerprint"] = fp
    tendon_layout["adopted_downstream_summary"] = summary
    tendon_layout["adopted_source_trace"] = build_tendon_source_trace(tendon_layout, snapshot)
    tendon_layout["adopted_status"] = "LOCKED: imported CSiBridge tendon layout adopted as downstream design source"
    tendon_layout["adopted_at_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    prestress["num_tendons"] = int(summary["tendon_count"])
    prestress["Aps_per_tendon_mm2"] = float(summary["Aps_per_tendon_mm2"])
    prestress["Aps_total_mm2"] = float(summary["Aps_total_mm2"])
    prestress["dp_avg_end_m"] = float(summary["dp_avg_end_m"])
    prestress["dp_avg_midspan_m"] = float(summary["dp_avg_midspan_m"])
    prestress["eccentricity_midspan_m"] = float(summary["eccentricity_midspan_m"])

    group_map = {g.get("Group"): g for g in snapshot.get("group_summary", [])}
    for g in prestress.get("tendon_friction_groups", []):
        row = group_map.get(g.get("group"))
        if row:
            if row.get("End dp (m)") is not None:
                g["end_dp_m"] = float(row["End dp (m)"])
            if row.get("Midspan dp (m)") is not None:
                g["midspan_dp_m"] = float(row["Midspan dp (m)"])
    return summary


def clear_adopted_tendon_model(tendon_layout: dict[str, Any]) -> None:
    """Clear only the adopted design-source snapshot; raw imports remain for review."""
    for key in [
        "adopted_model",
        "adopted_model_fingerprint",
        "adopted_downstream_summary",
        "adopted_source_trace",
        "adopted_at_utc",
    ]:
        tendon_layout.pop(key, None)
    tendon_layout["adopted_status"] = "NOT ADOPTED: imported tendon model is available for review only"
