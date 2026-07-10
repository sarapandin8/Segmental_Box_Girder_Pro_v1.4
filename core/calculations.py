from __future__ import annotations

from dataclasses import dataclass
from math import exp, sqrt, tan, radians
from typing import Dict, List, Tuple

import pandas as pd

from core.aashto_units import MPA_TO_KSI


def bar_area_mm2(diameter_mm: float) -> float:
    return 3.141592653589793 * diameter_mm**2 / 4.0


def pass_fail(dcr: float) -> str:
    return "PASS" if dcr <= 1.0 else "FAIL"


def fmt(x: float, nd: int = 3) -> str:
    return f"{x:,.{nd}f}"


# -----------------------------------------------------------------------------
# EN rail load helpers
# -----------------------------------------------------------------------------

def en_centrifugal_reduction_factor(speed_kmh: float, Lf_m: float) -> float:
    """EN 1991-2 centrifugal force reduction factor f.

    For V <= 120 km/h or Lf <= 2.88 m, f = 1.0.
    For 120 < V <= 300 km/h and Lf > 2.88 m:
    f = 1 - [(V-120)/1000] [814/V + 1.75] [1 - sqrt(2.88/Lf)], not less than 0.35.
    """
    if speed_kmh <= 120.0 or Lf_m <= 2.88:
        return 1.0
    raw = 1.0 - ((speed_kmh - 120.0) / 1000.0) * ((814.0 / speed_kmh) + 1.75) * (1.0 - sqrt(2.88 / Lf_m))
    return max(raw, 0.35)


def en_centrifugal_percentage(speed_kmh: float, radius_m: float, Lf_m: float) -> Dict[str, float]:
    """Return EN centrifugal force factor as fraction of vertical live load."""
    f = en_centrifugal_reduction_factor(speed_kmh, Lf_m)
    C_basic = speed_kmh**2 / (127.0 * radius_m)
    C_reduced = C_basic * f
    return {"f": f, "C_basic": C_basic, "C_reduced": C_reduced, "C_percent": 100.0 * C_reduced}


# -----------------------------------------------------------------------------
# Prestress losses
# -----------------------------------------------------------------------------

def friction_loss_table(groups: List[Dict], fpi_mpa: float, mu: float) -> Tuple[pd.DataFrame, float, float]:
    rows = []
    total_weight = 0.0
    weighted_loss = 0.0
    for g in groups:
        alpha_total = sqrt(g["alpha_vert_rad"] ** 2 + g["alpha_horiz_rad"] ** 2)
        delta = fpi_mpa * (1.0 - exp(-mu * alpha_total))
        pct = 100.0 * delta / fpi_mpa
        n = float(g.get("n", 1))
        total_weight += n
        weighted_loss += n * delta
        rows.append(
            {
                "Tendon group": g["group"],
                "n": int(n),
                "α_vert (rad)": g["alpha_vert_rad"],
                "α_horiz (rad)": g["alpha_horiz_rad"],
                "α_total (rad)": alpha_total,
                "ΔfpF,eq (MPa)": delta,
                "Loss (%)": pct,
            }
        )
    df = pd.DataFrame(rows)
    avg = weighted_loss / total_weight if total_weight else 0.0
    return df, avg, 100.0 * avg / fpi_mpa


def aashto_creep_coefficient(RH_percent: float, V_over_S_in: float, fc_mpa: float, ti_days: float, delta_ktd: float = 0.482) -> Dict[str, float]:
    """AASHTO-style creep coefficient used by the BG40 report.

    IMPORTANT: AASHTO empirical factors use V/S in inches and concrete strength in ksi. SI app inputs must be converted by the shared AASHTO unit layer before use.
    """
    fc_ksi = fc_mpa * MPA_TO_KSI
    ks = max(1.45 - 0.13 * V_over_S_in, 1.0)
    khc = 1.56 - 0.008 * RH_percent
    kf = 5.0 / (1.0 + fc_ksi)
    ti_factor = ti_days ** (-0.118)
    psi = 1.9 * ks * khc * kf * delta_ktd * ti_factor
    return {"fc_ksi": fc_ksi, "ks": ks, "khc": khc, "kf": kf, "delta_ktd": delta_ktd, "ti_factor": ti_factor, "psi": psi}


def creep_loss_mpa(Ep_mpa: float, Ec_mpa: float, fcgp_mpa: float, psi: float) -> float:
    n = Ep_mpa / Ec_mpa
    return n * fcgp_mpa * psi


def aashto_shrinkage_strain(RH_percent: float, V_over_S_in: float, fc_mpa: float, delta_ktd: float = 0.482) -> Dict[str, float]:
    fc_ksi = fc_mpa * MPA_TO_KSI
    ks = max(1.45 - 0.13 * V_over_S_in, 1.0)
    khs = 2.00 - 0.014 * RH_percent
    kf = 5.0 / (1.0 + fc_ksi)
    eps = ks * khs * kf * delta_ktd * (0.48e-3)
    return {"fc_ksi": fc_ksi, "ks": ks, "khs": khs, "kf": kf, "delta_ktd": delta_ktd, "eps_sh": eps, "microstrain": eps * 1e6}


def shrinkage_loss_mpa(Ep_mpa: float, eps_sh: float) -> float:
    return eps_sh * Ep_mpa


def elastic_shortening_loss_mpa(num_tendons: int, Ep_mpa: float, Eci_mpa: float, fcgp_mpa: float) -> float:
    N = float(num_tendons)
    if N <= 0:
        return 0.0
    return ((N - 1.0) / (2.0 * N)) * (Ep_mpa / Eci_mpa) * fcgp_mpa


def prestress_loss_summary(inputs: Dict) -> Dict[str, float]:
    df, friction, _ = friction_loss_table(inputs["groups"], inputs["fpi_mpa"], inputs["mu"])
    creep = aashto_creep_coefficient(inputs["RH_percent"], inputs["V_over_S_in"], inputs["fc_mpa"], inputs["ti_days"])
    d_creep = creep_loss_mpa(inputs["Ep_mpa"], inputs["Ec_mpa"], inputs["fcgp_mpa"], creep["psi"])
    shrink = aashto_shrinkage_strain(inputs["RH_percent"], inputs["V_over_S_in"], inputs["fc_mpa"])
    d_shrink = shrinkage_loss_mpa(inputs["Ep_mpa"], shrink["eps_sh"])
    d_es = elastic_shortening_loss_mpa(inputs["num_tendons"], inputs["Ep_mpa"], inputs["Ec_mpa"], inputs["fcgp_mpa"])
    anchor = inputs.get("anchor_set_loss_mpa", 0.0)
    relax = inputs.get("relaxation_loss_mpa", 0.0)
    total = friction + anchor + d_es + d_creep + d_shrink + relax
    fpe = inputs["fpi_mpa"] - total
    peff_kn = fpe * inputs["Aps_total_mm2"] / 1000.0
    return {
        "friction_mpa": friction,
        "anchor_set_mpa": anchor,
        "elastic_shortening_mpa": d_es,
        "creep_mpa": d_creep,
        "shrinkage_mpa": d_shrink,
        "relaxation_mpa": relax,
        "total_loss_mpa": total,
        "fpe_mpa": fpe,
        "Peff_kn": peff_kn,
        "creep_psi": creep["psi"],
        "shrinkage_microstrain": shrink["microstrain"],
    }


# -----------------------------------------------------------------------------
# AASHTO 5.8.6 segmental box girder torsion
# -----------------------------------------------------------------------------

def torsion_aashto_586(Tu_knm: float, Aoh_mm2: float, ph_mm: float, fy_mpa: float, phi_v: float) -> Dict[str, float]:
    Tu_nmm = Tu_knm * 1e6
    At_over_s = Tu_nmm / (2.0 * phi_v * Aoh_mm2 * fy_mpa)
    Al = Tu_nmm * ph_mm / (2.0 * phi_v * Aoh_mm2 * fy_mpa)
    q = Tu_nmm / (2.0 * Aoh_mm2)
    return {"At_over_s_mm2_per_mm": At_over_s, "Al_mm2": Al, "q_N_per_mm": q}


def shear_torsion_web_components(Vu_kn: float, Tu_knm: float, Aoh_mm2: float, dweb_mm: float) -> Dict[str, float]:
    q = Tu_knm * 1e6 / (2.0 * Aoh_mm2)
    Vg_web = Vu_kn / 2.0
    Vt_web = q * dweb_mm / 1000.0
    Vu_web = Vg_web + Vt_web
    return {"q_N_per_mm": q, "Vg_web_kn": Vg_web, "Vt_web_kn": Vt_web, "Vu_web_kn": Vu_web}


def shear_reinforcement_required(Vu_web_kn: float, Vc_kn: float, phi_v: float, fy_mpa: float, dv_mm: float, theta_deg: float) -> Dict[str, float]:
    cot_theta = 1.0 / tan(radians(theta_deg))
    Vs_req_kn = max(Vu_web_kn / phi_v - Vc_kn, 0.0)
    Av_over_s = Vs_req_kn * 1000.0 / (fy_mpa * dv_mm * cot_theta) if cot_theta > 0 else float("inf")
    return {"cot_theta": cot_theta, "Vs_req_kn": Vs_req_kn, "Av_over_s_mm2_per_mm": Av_over_s}


def provided_stirrups(diameter_mm: float, spacing_mm: float, legs_per_web: int) -> Dict[str, float]:
    area_one = bar_area_mm2(diameter_mm)
    Avs = legs_per_web * area_one / spacing_mm
    Ats_per_leg = area_one / spacing_mm
    return {"bar_area_mm2": area_one, "Av_over_s_mm2_per_mm": Avs, "At_over_s_per_leg_mm2_per_mm": Ats_per_leg}


def combined_transverse_check(Avs_req: float, Ats_req: float, Avs_prov: float, Ats_per_leg_prov: float) -> Dict[str, float | str]:
    dcr_shear = Avs_req / Avs_prov if Avs_prov > 0 else float("inf")
    dcr_torsion = Ats_req / Ats_per_leg_prov if Ats_per_leg_prov > 0 else float("inf")
    return {
        "DCR_shear": dcr_shear,
        "Status_shear": pass_fail(dcr_shear),
        "DCR_torsion": dcr_torsion,
        "Status_torsion": pass_fail(dcr_torsion),
        "DCR_governing": max(dcr_shear, dcr_torsion),
        "Status_governing": pass_fail(max(dcr_shear, dcr_torsion)),
    }
