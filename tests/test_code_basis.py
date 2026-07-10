from __future__ import annotations

import json

from core.bg40_defaults import BG40_DEFAULT
from core.code_basis import AASHTO_2020_SECTION5_LABEL, AASHTO_2020_SECTION5_TITLE, migrate_project_code_basis
from core.project_io import load_project_json_bytes
from core.validation import PROJECT_SCHEMA_VERSION


def test_default_project_uses_aashto_2020_section5_as_governing_concrete_basis() -> None:
    assert BG40_DEFAULT["project"]["design_code"] == "AASHTO LRFD 2020 Section 5 + EN Actions"
    assert BG40_DEFAULT["code_basis"]["concrete_design_standard"] == AASHTO_2020_SECTION5_LABEL
    assert BG40_DEFAULT["code_basis"]["concrete_design_section"] == AASHTO_2020_SECTION5_TITLE
    assert "SI" in BG40_DEFAULT["code_basis"]["unit_policy"]


def test_legacy_aashto_2014_project_is_promoted_to_2020_section5_on_load() -> None:
    legacy = json.loads(json.dumps(BG40_DEFAULT))
    legacy["meta"]["schema_version"] = "0.4.20-old"
    legacy["project"]["design_code"] = "AASHTO LRFD 2014 + EN Actions"
    legacy["criteria"]["standards"] = [
        {"Code / Standard": "AASHTO LRFD Bridge Design Specifications, 2014", "Description": "Primary bridge design standard"}
    ]
    loaded = load_project_json_bytes(json.dumps(legacy).encode("utf-8"), "legacy.json")
    assert loaded["meta"]["schema_version"] == PROJECT_SCHEMA_VERSION
    assert loaded["project"]["design_code"] == "AASHTO LRFD 2020 Section 5 + EN Actions"
    assert loaded["code_basis"]["concrete_design_standard"] == AASHTO_2020_SECTION5_LABEL
    assert loaded["criteria"]["standards"][0]["Code / Standard"] == AASHTO_2020_SECTION5_LABEL


def test_code_basis_migration_preserves_non_aashto_custom_project_code() -> None:
    project = {"project": {"design_code": "Project-specific EN action basis"}, "criteria": {"standards": []}}
    migrated = migrate_project_code_basis(project)
    assert migrated["project"]["design_code"] == "Project-specific EN action basis"
    assert migrated["code_basis"]["concrete_design_standard"] == AASHTO_2020_SECTION5_LABEL
