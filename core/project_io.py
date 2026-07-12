from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any, Dict

from core.validation import ensure_project_schema

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
    """Return a schema-migrated JSON payload for Project Save.

    This is the only project-save serialization path. It protects section
    coordinate rows from accidental loss by running the same schema/migration
    pass used by project load before emitting JSON.
    """
    if not isinstance(project, dict):
        raise TypeError("Project must be a dictionary before it can be saved as JSON.")
    data = ensure_project_schema(deepcopy(project))
    meta = data.setdefault("meta", {})
    meta["last_save_section_persistence"] = section_persistence_summary(data)
    return json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")


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
    try:
        return ensure_project_schema(data)
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
        "loaded_schema_version": str(meta.get("loaded_schema_version", meta.get("schema_version", "-"))),
        "schema_migration_status": str(meta.get("schema_migration_status", "Current")),
        "baseline_report": str(meta.get("baseline_report", "-")),
    }
