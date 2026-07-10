from core.bg40_defaults import BG40_DEFAULT
from core.calculations import (
    en_centrifugal_percentage,
    friction_loss_table,
    prestress_loss_summary,
    shear_torsion_web_components,
    torsion_aashto_586,
)


def test_centrifugal_bg40():
    cf = en_centrifugal_percentage(160.0, 10000.0, 40.0)
    assert abs(cf["f"] - 0.7999) < 0.005
    assert abs(cf["C_percent"] - 1.613) < 0.02


def test_torsion_bg40():
    d = BG40_DEFAULT
    out = torsion_aashto_586(
        d["loads"]["Tu_knm"],
        d["section"]["Aoh_mm2"],
        d["section"]["ph_mm"],
        d["materials"]["fy_mpa"],
        0.85,
    )
    assert abs(out["At_over_s_mm2_per_mm"] - 0.573) < 0.002
    assert abs(out["Al_mm2"] - 14949) < 30


def test_web_components_bg40():
    d = BG40_DEFAULT
    out = shear_torsion_web_components(
        d["loads"]["Vu_kn"],
        d["loads"]["Tu_knm"],
        d["section"]["Aoh_mm2"],
        d["section"]["dweb_mm"],
    )
    assert abs(out["q_N_per_mm"] - 189.9) < 0.5
    assert abs(out["Vt_web_kn"] - 426.3) < 2.0
    assert abs(out["Vu_web_kn"] - 6502.8) < 3.0


def test_prestress_summary_bg40():
    d = BG40_DEFAULT
    p = d["prestress"]
    m = d["materials"]
    inputs = {
        "groups": p["tendon_friction_groups"],
        "fpi_mpa": m["fpi_mpa"],
        "mu": p["mu_external"],
        "RH_percent": p["RH_percent"],
        "V_over_S_in": p["V_over_S_in"],
        "fc_mpa": m["fc_mpa"],
        "ti_days": p["ti_days"],
        "Ep_mpa": m["Ep_mpa"],
        "Ec_mpa": m["Ec_mpa"],
        "fcgp_mpa": p["fcgp_mpa"],
        "num_tendons": p["num_tendons"],
        "anchor_set_loss_mpa": p["anchor_set_loss_mpa"],
        "relaxation_loss_mpa": p["relaxation_loss_mpa"],
        "Aps_total_mm2": p["Aps_total_mm2"],
    }
    out = prestress_loss_summary(inputs)
    assert abs(out["friction_mpa"] - 21.5) < 0.2
    assert abs(out["creep_mpa"] - 59.5) < 0.5
    assert abs(out["shrinkage_mpa"] - 22.3) < 0.3


def test_default_project_has_no_blocking_validation_errors():
    from core.validation import ensure_project_schema, issue_counts, validate_project, workflow_status

    d = ensure_project_schema(BG40_DEFAULT)
    issues = validate_project(d)
    counts = issue_counts(issues)
    assert counts["ERROR"] == 0
    workflow = workflow_status(d, issues)
    assert all(row["Status"] in {"READY", "REVIEW"} for row in workflow)


def test_schema_is_added_to_legacy_project():
    from copy import deepcopy
    from core.validation import PROJECT_SCHEMA_VERSION, ensure_project_schema

    legacy = deepcopy(BG40_DEFAULT)
    legacy.pop("meta", None)
    out = ensure_project_schema(legacy)
    assert out["meta"]["schema_version"] == PROJECT_SCHEMA_VERSION
