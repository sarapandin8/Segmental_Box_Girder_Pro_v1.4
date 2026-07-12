from __future__ import annotations

import hashlib
import json
from typing import Any, Dict

from core.validation import PROJECT_SCHEMA_VERSION, ensure_project_schema, project_schema_is_current

MAX_PROJECT_JSON_BYTES = 20 * 1024 * 1024  # 20 MB guard; project JSON should normally be much smaller.



def section_persistence_summary(project: Dict[str, Any]) -> Dict[str, Any]:
    """Return a compact save/load health summary for section geometry data."""
    section = project.get("section", {}) if isinstance(project, dict) else {}
    rows = section.get("coordinate_rows") or [] if isinstance(section, dict) else []
    row_count = len(rows) if isinstance(rows, list) else 0
    has_adopted = all(
        section.get(key) not in (None, "", 0, 0.0)
        for key in ("Ac_m2", "I33_m4", "I22_m4", "J_m4", "S_top_m3", "S_bottom_m3")
    ) if isinstance(section, dict) else False
    computed = section.get("computed_from_coordinates") if isinstance(section, dict) else {}
    return {
        "coordinate_rows": row_count,
        "computed_section_available": bool(computed),
        "adopted_properties_available": bool(has_adopted),
    }


def serialize_project_json_bytes(project: Dict[str, Any]) -> bytes:
    """Return a current-schema JSON payload without re-migrating live state.

    The active Streamlit project is mutable and may be several megabytes after FEA
    source import.  A fully migrated project therefore takes a shallow metadata
    snapshot only; nested engineering records are serialized directly and are not
    deep-copied.  Legacy/non-current dictionaries still use the safe copy-on-
    migrate path before serialization.
    """
    if not isinstance(project, dict):
        raise TypeError("Project must be a dictionary before it can be saved as JSON.")

    if project_schema_is_current(project):
        data = dict(project)
        meta = dict(project.get("meta", {}))
        data["meta"] = meta
    else:
        data = ensure_project_schema(project, copy_project=True)
        meta = data.setdefault("meta", {})

    meta["last_save_section_persistence"] = section_persistence_summary(data)
    meta["saved_with_schema_version"] = PROJECT_SCHEMA_VERSION
    # Compact JSON materially reduces peak string/bytes size for large FEA source
    # packages while remaining standard UTF-8 JSON.
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


class ProjectJsonLoadError(ValueError):
    """Raised when a saved project JSON cannot be loaded safely."""


def project_json_fingerprint(raw: bytes, filename: str = "") -> str:
    """Return a stable fingerprint for an uploaded JSON file."""
    h = hashlib.sha256()
    h.update(filename.encode("utf-8", errors="ignore"))
    h.update(b"\0")
    h.update(raw)
    return h.hexdigest()


def load_project_json_bytes(raw: bytes, filename: str = "") -> Dict[str, Any]:
    """Decode, validate, and migrate a saved project JSON payload.

    The function is intentionally side-effect free so the Streamlit UI can call it
    only from an explicit Apply/Load button. This prevents file_uploader rerun loops
    when an uploaded file remains present across Streamlit reruns.
    """
    if not raw:
        raise ProjectJsonLoadError("The uploaded project JSON is empty.")
    if len(raw) > MAX_PROJECT_JSON_BYTES:
        raise ProjectJsonLoadError(
            f"The uploaded project JSON is too large ({len(raw) / (1024 * 1024):.1f} MB). "
            "Check that this is a saved project JSON, not an input spreadsheet or image."
        )
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ProjectJsonLoadError("The uploaded file is not valid UTF-8 JSON.") from exc
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ProjectJsonLoadError(f"Invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise ProjectJsonLoadError("The project JSON root must be an object/dictionary.")
    meta = data.get("meta", {}) if isinstance(data, dict) else {}
    source_schema = str(meta.get("schema_version") or "-") if isinstance(meta, dict) else "-"
    try:
        loaded = ensure_project_schema(
            data,
            copy_project=False,
            source_schema_version=source_schema,
        )
        # A file saved by the current app declares the current schema even when it
        # carries older provenance fields from an earlier migration.  Normalize the
        # *file* schema trace here without discarding historical origin metadata.
        if source_schema == PROJECT_SCHEMA_VERSION:
            loaded_meta = loaded.setdefault("meta", {})
            loaded_meta["source_file_schema_version"] = source_schema
            loaded_meta["loaded_schema_version"] = source_schema
            loaded_meta["schema_migration_status"] = "Current"
            loaded_meta["migration_path"] = [PROJECT_SCHEMA_VERSION]
            loaded_meta["migration_target_schema_version"] = PROJECT_SCHEMA_VERSION
            loaded_meta["migration_complete"] = True
        return loaded
    except Exception as exc:  # noqa: BLE001 - convert migration errors to a user-facing load error.
        raise ProjectJsonLoadError(f"Project JSON schema migration failed: {exc}") from exc


def project_load_summary(project: Dict[str, Any]) -> Dict[str, str]:
    """Compact user-facing summary for a migrated project dict."""
    meta = project.get("meta", {}) if isinstance(project, dict) else {}
    p = project.get("project", {}) if isinstance(project, dict) else {}
    return {
        "project": str(p.get("name", "-")),
        "bridge_object": str(p.get("bridge_object", "-")),
        "schema_version": str(meta.get("schema_version", "-")),
        "loaded_schema_version": str(meta.get("source_file_schema_version", meta.get("loaded_schema_version", meta.get("schema_version", "-")))),
        "source_file_schema_version": str(meta.get("source_file_schema_version", meta.get("loaded_schema_version", meta.get("schema_version", "-")))),
        "historical_origin_schema_version": str(meta.get("historical_origin_schema_version", "-")),
        "schema_migration_status": str(meta.get("schema_migration_status", "Current")),
        "migration_complete": "yes" if meta.get("migration_complete") is True else "no",
        "baseline_report": str(meta.get("baseline_report", "-")),
    }
