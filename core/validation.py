from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Dict, Iterable, Literal

PROJECT_SCHEMA_VERSION = "0.5.11-commercial-fea5d1c-pandas-arrow-string-crash-hotfix"

IssueLevel = Literal["ERROR", "WARNING", "INFO"]


@dataclass(frozen=True)
class ValidationIssue:
    level: IssueLevel
    category: str
    message: str
    code_basis: str = ""
    recommendation: str = ""
    issue_code: str = ""



_SECTION_COORDINATE_LEGACY_KEYS = (
    "coordinate_rows",
    "coordinates",
    "section_coordinates",
    "section_coordinate_rows",
    "csibridge_coordinate_rows",
    "coordinate_table",
)


def _normalize_section_coordinate_records(value) -> list[dict] | None:
    """Return canonical coordinate records from legacy saved-project shapes.

    The project JSON schema must be non-destructive: if a user saved imported
    CSiBridge section coordinates in an older key, migration should preserve the
    geometry instead of replacing it with the BG40 default empty table.
    """
    if not value:
        return None
    try:
        from core.section_geometry import normalize_coordinate_rows

        rows = normalize_coordinate_rows(value)
    except Exception:
        return None
    if rows.empty:
        return None
    return rows[["loop_name", "point_no", "x_mm", "y_mm"]].to_dict("records")


def _migrate_section_coordinate_rows(data: Dict) -> None:
    """Migrate section coordinate rows before default schema fill.

    Old project files and intermediate development builds may store section
    coordinates under a different key.  This function searches known legacy
    locations and writes only the canonical ``section.coordinate_rows`` key.
    Existing non-empty canonical rows always win.
    """
    if not isinstance(data, dict):
        return
    section = data.setdefault("section", {})
    if not isinstance(section, dict):
        data["section"] = {}
        section = data["section"]

    current = _normalize_section_coordinate_records(section.get("coordinate_rows"))
    if current:
        section["coordinate_rows"] = current
        return

    for key in _SECTION_COORDINATE_LEGACY_KEYS:
        if key == "coordinate_rows":
            continue
        migrated = _normalize_section_coordinate_records(section.get(key))
        if migrated:
            section["coordinate_rows"] = migrated
            section.setdefault("coordinate_source", f"Migrated from legacy section.{key} during project JSON load.")
            return

    for key in ("section_coordinate_rows", "section_coordinates", "csibridge_section_coordinates"):
        migrated = _normalize_section_coordinate_records(data.get(key))
        if migrated:
            section["coordinate_rows"] = migrated
            section.setdefault("coordinate_source", f"Migrated from legacy project.{key} during project JSON load.")
            return



def _migrate_fea_result_sources(data: Dict) -> None:
    """Sanitize legacy FEA payloads and add explicit source semantics."""
    if not isinstance(data, dict):
        return
    from core.fea_results import (
        PROGRAM_CONTROL_ALLOWLIST,
        SOURCE_STATE_COMPONENT_ENVELOPE,
        SOURCE_STATE_SINGLE,
    )

    fea = data.setdefault("fea_results", {})
    if not isinstance(fea, dict):
        data["fea_results"] = {}
        fea = data["fea_results"]
    imports = fea.setdefault("stage_imports", {})
    if not isinstance(imports, dict):
        fea["stage_imports"] = {}
        imports = fea["stage_imports"]
    for stage in ("uls", "transfer", "service"):
        payload = imports.get(stage)
        if not isinstance(payload, dict):
            imports[stage] = {}
            continue
        program = payload.get("program_control", {})
        if isinstance(program, dict):
            payload["program_control"] = {
                key: str(program[key])
                for key in PROGRAM_CONTROL_ALLOWLIST
                if program.get(key) not in (None, "")
            }
        records = payload.get("records", [])
        if isinstance(records, list):
            single_rows = 0
            envelope_rows = 0
            for row in records:
                if not isinstance(row, dict):
                    continue
                state = SOURCE_STATE_SINGLE if not str(row.get("StepType", "")).strip() else SOURCE_STATE_COMPONENT_ENVELOPE
                row["SourceState"] = state
                if state == SOURCE_STATE_SINGLE:
                    single_rows += 1
                else:
                    envelope_rows += 1
            if records:
                overall = "MIXED" if single_rows and envelope_rows else (SOURCE_STATE_COMPONENT_ENVELOPE if envelope_rows else SOURCE_STATE_SINGLE)
                payload["source_semantics"] = {
                    "overall": overall,
                    "single_state_rows": single_rows,
                    "component_envelope_rows": envelope_rows,
                    "simultaneous_pairing_allowed": envelope_rows == 0,
                }
        envelopes = payload.get("envelopes", [])
        if isinstance(envelopes, list):
            for envelope in envelopes:
                if not isinstance(envelope, dict):
                    continue
                for component in ("P", "V2", "T", "M3"):
                    for bound in ("min", "max"):
                        source = envelope.get(f"{component}_{bound}_source")
                        if isinstance(source, dict):
                            source["SourceState"] = SOURCE_STATE_SINGLE if not str(source.get("StepType", "")).strip() else SOURCE_STATE_COMPONENT_ENVELOPE
    attempts = fea.setdefault("import_attempts", {})
    if not isinstance(attempts, dict):
        fea["import_attempts"] = {}
        attempts = fea["import_attempts"]
    for stage in ("uls", "transfer", "service"):
        attempts.setdefault(stage, {})
    downstream = fea.setdefault("downstream_connection", {})
    if not isinstance(downstream, dict):
        fea["downstream_connection"] = {}
        downstream = fea["downstream_connection"]
    downstream.setdefault("status", "NOT YET CONNECTED")
    downstream.setdefault("connected_modules", [])
    downstream.setdefault("source_package_fingerprint", "")
    downstream.setdefault("note", "Sections 6–9 continue to use existing BG40/keyed demands until a separately reviewed connection milestone is implemented.")

def _deep_fill_missing(target: Dict, defaults: Dict) -> Dict:
    for key, default_value in defaults.items():
        if key not in target:
            target[key] = deepcopy(default_value)
        elif isinstance(target[key], dict) and isinstance(default_value, dict):
            _deep_fill_missing(target[key], default_value)
    return target

def project_schema_is_current(project: Dict) -> bool:
    """Return True when a session project is already migrated to this app schema.

    The explicit completion marker prevents a partially migrated dictionary from
    taking the fast path merely because its schema string was edited.
    """
    if not isinstance(project, dict):
        return False
    meta = project.get("meta", {})
    return bool(
        isinstance(meta, dict)
        and str(meta.get("schema_version", "")) == PROJECT_SCHEMA_VERSION
        and meta.get("migration_complete") is True
        and str(meta.get("migration_target_schema_version", "")) == PROJECT_SCHEMA_VERSION
    )


def _migrate_project_schema_in_place(
    data: Dict,
    *,
    source_schema_version: str | None = None,
) -> Dict:
    """Migrate a newly decoded project dictionary exactly once, in place.

    ``json.loads`` already returns a private object, so copying that entire object
    again only increases peak memory.  This function is therefore used by the
    Project JSON loader after it has captured the source-file schema.
    """
    if not isinstance(data, dict):
        raise TypeError("Project must be a dictionary before schema migration.")

    from core.bg40_defaults import BG40_DEFAULT

    meta = data.setdefault("meta", {})
    if not isinstance(meta, dict):
        data["meta"] = {}
        meta = data["meta"]

    source_schema = str(
        source_schema_version
        or meta.get("schema_version")
        or meta.get("source_file_schema_version")
        or "-"
    )
    historical_origin = str(meta.get("loaded_schema_version") or "").strip()

    _migrate_section_coordinate_rows(data)
    _migrate_fea_result_sources(data)
    data = _deep_fill_missing(data, BG40_DEFAULT)
    _migrate_section_coordinate_rows(data)
    _migrate_fea_result_sources(data)

    from core.code_basis import migrate_project_code_basis

    data = migrate_project_code_basis(data)

    tendon_layout = data.get("tendon_layout", {}) if isinstance(data, dict) else {}
    adopted_model = tendon_layout.get("adopted_model", {}) if isinstance(tendon_layout, dict) else {}
    if isinstance(adopted_model, dict) and adopted_model.get("valid"):
        from core.tendon_adoption import build_tendon_source_trace

        tendon_layout["adopted_source_trace"] = build_tendon_source_trace(tendon_layout, adopted_model)

    meta = data.setdefault("meta", {})
    meta["source_file_schema_version"] = source_schema
    # Compatibility field retained for existing report/UI code.  It now means the
    # schema declared by the file being loaded, not the oldest historical origin.
    meta["loaded_schema_version"] = source_schema
    if historical_origin and historical_origin not in {"-", source_schema}:
        meta["historical_origin_schema_version"] = historical_origin

    if source_schema == PROJECT_SCHEMA_VERSION:
        meta["schema_migration_status"] = "Current"
        meta["migration_path"] = [PROJECT_SCHEMA_VERSION]
    else:
        meta["schema_migration_status"] = f"Migrated from {source_schema}"
        meta["migration_path"] = [source_schema, PROJECT_SCHEMA_VERSION]

    meta["schema_version"] = PROJECT_SCHEMA_VERSION
    meta["migration_target_schema_version"] = PROJECT_SCHEMA_VERSION
    meta["migration_complete"] = True
    meta.setdefault("app_name", "Segmental Box Girder Pro")
    meta.setdefault("dataset_status", "BG40 R10 report-driven baseline loaded")
    meta.setdefault("schema_note", "Report-driven chapter/subsection schema for commercial-grade QA, traceability, and future report export.")
    return data


def ensure_project_schema(
    project: Dict,
    *,
    copy_project: bool = True,
    source_schema_version: str | None = None,
) -> Dict:
    """Return a project dictionary migrated to the active commercial schema.

    Existing callers retain copy-on-migrate behavior by default.  The JSON loader
    passes ``copy_project=False`` because its decoded object is already private,
    avoiding a second full-project deepcopy.  A fully migrated session project is
    returned immediately when no copy was requested.
    """
    if not isinstance(project, dict):
        raise TypeError("Project must be a dictionary before schema migration.")
    if project_schema_is_current(project) and not copy_project:
        return project

    data = deepcopy(project) if copy_project else project
    return _migrate_project_schema_in_place(
        data,
        source_schema_version=source_schema_version,
    )


def issue_counts(issues: Iterable[ValidationIssue]) -> Dict[str, int]:
    counts = {"ERROR": 0, "WARNING": 0, "INFO": 0}
    for issue in issues:
        counts[issue.level] += 1
    return counts


def _is_external_tendon(project: Dict) -> bool:
    tendon = project.get("project", {}).get("tendon_system", "")
    return "External" in tendon or "Unbonded" in tendon


def validate_project(project: Dict) -> list[ValidationIssue]:
    """Engineering QA validation for the active project inputs.

    The checks are intentionally conservative. They are not a substitute for code
    review, but they catch common unit and workflow errors before calculations are
    trusted.
    """
    issues: list[ValidationIssue] = []
    p = project.get("project", {})
    m = project.get("materials", {})
    s = project.get("section", {})
    ps = project.get("prestress", {})
    loads = project.get("loads", {})
    rail = project.get("rail_loads", {})

    def require_positive(value: float, label: str, category: str, unit: str = "") -> None:
        suffix = f" {unit}" if unit else ""
        if value <= 0:
            issues.append(
                ValidationIssue(
                    "ERROR",
                    category,
                    f"{label} must be greater than zero. Current value = {value:g}{suffix}.",
                    recommendation="Correct the input before using any design result.",
                )
            )

    span = float(p.get("span_m", 0.0))
    depth = float(p.get("depth_m", 0.0))
    width = float(p.get("width_m", 0.0))
    require_positive(span, "Span length L", "Geometry", "m")
    require_positive(depth, "Section depth D", "Geometry", "m")
    require_positive(width, "Total width B", "Geometry", "m")
    if span > 0 and depth > 0:
        slenderness = span / depth
        if slenderness < 10 or slenderness > 30:
            issues.append(
                ValidationIssue(
                    "WARNING",
                    "Geometry",
                    f"Span/depth ratio L/D = {slenderness:.1f}. Verify this is intentional for a PT segmental box girder.",
                    recommendation="Check geometry definition and whether D is the structural depth at the critical section.",
                )
            )
    if width > 0 and depth > 0 and width < depth:
        issues.append(
            ValidationIssue(
                "WARNING",
                "Geometry",
                "Total bridge width is less than section depth. This is unusual for a box girder cross-section.",
                recommendation="Confirm that B and D have not been swapped.",
            )
        )

    for key, label in [
        ("fc_mpa", "Concrete strength f′c"),
        ("Ec_mpa", "Concrete modulus Ec"),
        ("fy_mpa", "Rebar yield strength fy"),
        ("Ep_mpa", "Prestressing steel modulus Ep"),
        ("fpi_mpa", "Initial prestress fpi"),
    ]:
        require_positive(float(m.get(key, 0.0)), label, "Materials", "MPa")
    fpi = float(m.get("fpi_mpa", 0.0))
    fpu = float(m.get("fpu_mpa", 0.0))
    if fpi > 0 and fpu > 0:
        if fpi >= fpu:
            issues.append(
                ValidationIssue(
                    "ERROR",
                    "Materials",
                    "Initial prestress fpi is greater than or equal to fpu.",
                    recommendation="Check strand grade and jacking stress.",
                )
            )
        elif fpi / fpu > 0.80:
            issues.append(
                ValidationIssue(
                    "WARNING",
                    "Materials",
                    f"fpi/fpu = {fpi / fpu:.3f}. Confirm that this complies with the project jacking-stress limit.",
                    code_basis="AASHTO LRFD prestressing limits / project criteria",
                )
            )

    for key, label, unit in [
        ("Ac_m2", "Gross area Ac", "m²"),
        ("I33_m4", "Moment of inertia I33", "m⁴"),
        ("Aoh_mm2", "Closed torsion area Aoh", "mm²"),
        ("ph_mm", "Closed torsion perimeter ph", "mm"),
        ("dv_mm", "Effective shear depth dv", "mm"),
        ("dweb_mm", "Web lever arm / web depth dweb", "mm"),
        ("tcr_knm", "Torsional cracking resistance Tcr", "kN·m"),
    ]:
        require_positive(float(s.get(key, 0.0)), label, "Section", unit)

    require_positive(float(ps.get("Aps_total_mm2", 0.0)), "Total prestressing area Aps,total", "Prestress", "mm²")
    require_positive(float(ps.get("num_tendons", 0.0)), "Number of tendons", "Prestress")
    vs_in = float(ps.get("V_over_S_in", 0.0))
    require_positive(vs_in, "V/S for AASHTO creep/shrinkage factors", "Prestress losses", "in")
    if vs_in > 20.0:
        issues.append(
            ValidationIssue(
                "WARNING",
                "Prestress losses",
                f"V/S = {vs_in:.2f} in is high. This may indicate that V/S was entered in mm instead of inches.",
                code_basis="AASHTO empirical creep/shrinkage factors",
                recommendation="Convert V/S from mm to inches before evaluating ks.",
            )
        )
    rh = float(ps.get("RH_percent", 0.0))
    if rh <= 0 or rh > 100:
        issues.append(
            ValidationIssue(
                "ERROR",
                "Prestress losses",
                f"Relative humidity RH must be between 0 and 100 percent. Current RH = {rh:g}%.",
                recommendation="Enter RH as a percent, e.g. 75 for 75%.",
            )
        )

    for key, label, unit in [
        ("Vu_kn", "ULS shear demand Vu", "kN"),
        ("Tu_knm", "ULS torsion demand Tu", "kN·m"),
        ("Vc_per_web_kn", "Concrete shear resistance Vc per web", "kN"),
        ("stirrup_bar_dia_mm", "Closed stirrup bar diameter", "mm"),
        ("stirrup_spacing_mm", "Closed stirrup spacing", "mm"),
        ("stirrup_legs_per_web", "Closed stirrup legs per web", ""),
    ]:
        require_positive(float(loads.get(key, 0.0)), label, "ULS demand / reinforcement", unit)

    speed = float(rail.get("speed_kmh", 0.0))
    radius = float(rail.get("radius_m", 0.0))
    lf = float(rail.get("Lf_m", 0.0))
    require_positive(speed, "Train speed V", "Rail actions", "km/h")
    require_positive(radius, "Curve radius R", "Rail actions", "m")
    require_positive(lf, "Loaded influence length Lf", "Rail actions", "m")
    if speed > 300:
        issues.append(
            ValidationIssue(
                "WARNING",
                "Rail actions",
                "EN 1991-2 centrifugal reduction formula shown in the app is limited to the stated speed range up to 300 km/h.",
                code_basis="EN 1991-2 Art. 6.5.1",
                recommendation="Confirm project-specific treatment for higher speeds.",
            )
        )

    # Section 5 FEA source-package validation. These checks validate imported
    # source records only; they do not imply that Sections 6–9 consume them yet.
    from core.fea_results import (
        STAGE_LABELS,
        cross_stage_station_consistency,
        source_package_fingerprint,
        stage_source_status,
    )

    fea = project.get("fea_results", {}) if isinstance(project, dict) else {}
    stage_imports = fea.get("stage_imports", {}) if isinstance(fea, dict) else {}
    active_span = str(p.get("bridge_object", ""))
    missing_codes = {
        "uls": "FEA_ULS_SOURCE_MISSING",
        "transfer": "FEA_TRANSFER_SOURCE_MISSING",
        "service": "FEA_SERVICE_SOURCE_MISSING",
    }
    ready_stages = 0
    for stage in ("uls", "transfer", "service"):
        payload = stage_imports.get(stage, {}) if isinstance(stage_imports, dict) else {}
        status = stage_source_status(payload, active_span)
        if status["status"] == "PENDING":
            issues.append(
                ValidationIssue(
                    "WARNING",
                    "FEA Results",
                    f"{STAGE_LABELS[stage]} source is missing.",
                    recommendation="Upload and validate the required CSiBridge Bridge Object Forces workbook in Section 5.",
                    issue_code=missing_codes[stage],
                )
            )
        elif status["status"] in {"SPAN SOURCE REVIEW", "SOURCE BLOCKED"}:
            issues.append(
                ValidationIssue(
                    "ERROR",
                    "FEA Results",
                    f"{STAGE_LABELS[stage]}: {status['note']}",
                    recommendation="Correct the source workbook or active span before downstream design use.",
                    issue_code="FEA_SPAN_SOURCE_MISMATCH" if status["status"] == "SPAN SOURCE REVIEW" else "FEA_TRANSFER_SOURCE_INVALID",
                )
            )
        else:
            ready_stages += 1

    consistency = cross_stage_station_consistency(stage_imports)
    if consistency["status"] == "REVIEW":
        issues.append(
            ValidationIssue(
                "ERROR",
                "FEA Results",
                consistency["note"],
                recommendation="Use one consistent SectCutNum/Distance/LocType map for ULS, Transfer, and Final Service SLS.",
                issue_code="FEA_STATION_MAP_MISMATCH",
            )
        )

    downstream = fea.get("downstream_connection", {}) if isinstance(fea, dict) else {}
    downstream_status = str(downstream.get("status", "NOT YET CONNECTED")).upper()
    current_package_fingerprint = source_package_fingerprint(stage_imports)
    if ready_stages == 3 and consistency["status"] == "READY":
        if downstream_status != "CONNECTED":
            issues.append(
                ValidationIssue(
                    "WARNING",
                    "FEA Results",
                    "The three-stage FEA source package is ready, but Sections 6–9 are not yet connected to these imported demands.",
                    recommendation="Do not interpret existing Section 6–8 results as calculated from the imported Section 5 sources until a separate connection milestone is completed.",
                    issue_code="FEA_DOWNSTREAM_NOT_CONNECTED",
                )
            )
        else:
            adopted_fingerprint = str(downstream.get("source_package_fingerprint", ""))
            if adopted_fingerprint and adopted_fingerprint != current_package_fingerprint:
                issues.append(
                    ValidationIssue(
                        "ERROR",
                        "FEA Results",
                        "Downstream design results are stale because the active FEA source package changed.",
                        recommendation="Re-run the connected downstream checks from the current source package.",
                        issue_code="FEA_RESULTS_STALE",
                    )
                )

    if _is_external_tendon(project):
        issues.append(
            ValidationIssue(
                "INFO",
                "AASHTO 5.8.6",
                "External / unbonded tendon system detected; φv = 0.85 is used for segmental shear/torsion checks.",
                code_basis="AASHTO LRFD 2020 Section 5, Art. 5.5.4.2",
            )
        )

    return issues


def workflow_status(project: Dict, issues: list[ValidationIssue] | None = None) -> list[Dict[str, str]]:
    issues = issues if issues is not None else validate_project(project)
    error_categories = {i.category for i in issues if i.level == "ERROR"}
    warning_categories = {i.category for i in issues if i.level == "WARNING"}

    rows = [
        ("Geometry", {"Section"}, "Project and closed-cell torsion geometry"),
        ("Materials", {"Materials"}, "Concrete, rebar, and prestressing properties"),
        ("Prestress Losses", {"Prestress losses"}, "Friction, elastic shortening, creep, shrinkage, relaxation"),
        ("FEA Demand", {"ULS demand / reinforcement", "FEA Results"}, "Three-stage imported force sources and downstream connection state"),
        ("Rail Actions", {"Rail actions"}, "EN centrifugal-force inputs"),
        ("ULS Shear/Torsion", {"AASHTO 5.8.6"}, "Segmental box-girder shear/torsion design basis"),
        ("Report / QA", {"Report"}, "Calculation trace and issue summary"),
    ]
    out = []
    for item, categories, note in rows:
        if categories & error_categories:
            status = "BLOCKED"
        elif categories & warning_categories:
            status = "REVIEW"
        else:
            status = "READY"
        out.append({"Workflow item": item, "Status": status, "QA note": note})
    return out
