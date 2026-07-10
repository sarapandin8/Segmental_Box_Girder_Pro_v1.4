from __future__ import annotations

"""Governing design-code basis and trace helpers."""

from copy import deepcopy
from typing import Any

AASHTO_2020_SECTION5_LABEL = "AASHTO LRFD Bridge Design Specifications, 9th Edition, 2020"
AASHTO_2020_SECTION5_TITLE = "Section 5 — Concrete Structures"
AASHTO_2020_SECTION5_SOURCE = "SECTION 5 CONCRETE STRUCTURES(1).pdf"
APP_INTERNAL_UNITS = "kN, m, MPa, mm"

DEFAULT_CODE_BASIS: dict[str, Any] = {
    "concrete_design_standard": AASHTO_2020_SECTION5_LABEL,
    "concrete_design_section": AASHTO_2020_SECTION5_TITLE,
    "governing_status": "GOVERNING",
    "reference_file": AASHTO_2020_SECTION5_SOURCE,
    "internal_units": APP_INTERNAL_UNITS,
    "unit_policy": "Store/display SI only; wrap AASHTO kip/ksi/in/ft equations with explicit internal conversion.",
    "legacy_note": "AASHTO LRFD 9th Edition (2020) is the active governing bridge design-code basis unless a project-specific legacy reference is explicitly documented.",
}

AASHTO_SECTION5_ARTICLE_MAP: list[dict[str, str]] = [
    {"App module": "Materials", "Article / section": "5.4", "Use in app": "Concrete, reinforcing steel, prestressing steel material properties"},
    {"App module": "Limit states / resistance", "Article / section": "5.5", "Use in app": "Service/strength states and resistance factors"},
    {"App module": "ULS Flexure", "Article / section": "5.6", "Use in app": "Flexural and axial force effects in B-regions"},
    {"App module": "ULS Shear / Torsion", "Article / section": "5.7 and 5.12.5.3.8", "Use in app": "Sectional shear/torsion and segmental-bridge alternative provisions"},
    {"App module": "Prestress Losses", "Article / section": "5.9.3", "Use in app": "Instantaneous and time-dependent prestress losses"},
    {"App module": "Post-tensioning details", "Article / section": "5.9.5", "Use in app": "PT duct/tendon/anchorage detailing references"},
    {"App module": "Segmental bridge requirements", "Article / section": "5.12.5", "Use in app": "Segmental bridge analysis, design, losses, and detailing provisions"},
]


def default_code_basis() -> dict[str, Any]:
    return deepcopy(DEFAULT_CODE_BASIS)


def code_basis_summary_rows(project: dict[str, Any]) -> list[dict[str, str]]:
    cb = project.get("code_basis", {}) if isinstance(project, dict) else {}
    return [
        {"Item": "Concrete / PT design standard", "Value": str(cb.get("concrete_design_standard", AASHTO_2020_SECTION5_LABEL)), "Status": str(cb.get("governing_status", "GOVERNING"))},
        {"Item": "Governing section", "Value": str(cb.get("concrete_design_section", AASHTO_2020_SECTION5_TITLE)), "Status": "Section 5"},
        {"Item": "App internal units", "Value": str(cb.get("internal_units", APP_INTERNAL_UNITS)), "Status": "SI only"},
        {"Item": "Unit policy", "Value": str(cb.get("unit_policy", DEFAULT_CODE_BASIS["unit_policy"])), "Status": "Unit-safe wrapper required"},
        {"Item": "Reference file", "Value": str(cb.get("reference_file", AASHTO_2020_SECTION5_SOURCE)), "Status": "Uploaded by user"},
    ]


def migrate_project_code_basis(project: dict[str, Any]) -> dict[str, Any]:
    """Promote project metadata to the AASHTO 2020 Section 5 governing basis.

    This is intentionally limited to the concrete/prestressed-concrete basis.
    Existing EN load-action and DPT seismic basis fields are preserved.
    """
    cb = project.setdefault("code_basis", {})
    for key, value in DEFAULT_CODE_BASIS.items():
        cb.setdefault(key, deepcopy(value))
    cb["concrete_design_standard"] = AASHTO_2020_SECTION5_LABEL
    cb["concrete_design_section"] = AASHTO_2020_SECTION5_TITLE
    cb["governing_status"] = "GOVERNING"
    cb["reference_file"] = AASHTO_2020_SECTION5_SOURCE
    cb["internal_units"] = APP_INTERNAL_UNITS
    cb["unit_policy"] = DEFAULT_CODE_BASIS["unit_policy"]

    proj = project.setdefault("project", {})
    old_design_code = str(proj.get("design_code", ""))
    if "AASHTO" in old_design_code or not old_design_code:
        proj["design_code"] = "AASHTO LRFD 2020 Section 5 + EN Actions"

    criteria = project.setdefault("criteria", {})
    standards = criteria.get("standards", [])
    if isinstance(standards, list):
        updated = False
        for row in standards:
            if isinstance(row, dict) and "AASHTO LRFD" in str(row.get("Code / Standard", "")):
                row["Code / Standard"] = AASHTO_2020_SECTION5_LABEL
                row["Description"] = "Primary concrete / prestressed-concrete bridge design standard — Section 5 governs this app"
                updated = True
        if not updated:
            standards.insert(1, {"Code / Standard": AASHTO_2020_SECTION5_LABEL, "Description": "Primary concrete / prestressed-concrete bridge design standard — Section 5 governs this app"})
        criteria["standards"] = standards
    criteria["units_statement"] = "SI units are used throughout this app and report workflow (kN, kN·m, MPa, m, mm). AASHTO LRFD Section 5 equations written in kip/ksi/in/ft are evaluated through explicit unit-safe conversion wrappers."
    criteria.setdefault("aashto_unit_policy_note", DEFAULT_CODE_BASIS["unit_policy"])
    return project
