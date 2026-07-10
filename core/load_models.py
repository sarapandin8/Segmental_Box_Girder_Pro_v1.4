from __future__ import annotations

from math import sqrt
from typing import Any, Dict, Iterable, List

import pandas as pd


def sdl_totals(components: Iterable[Dict[str, Any]]) -> Dict[str, float]:
    df = pd.DataFrame(list(components))
    if df.empty:
        return {"single_total": 0.0, "double_total": 0.0}
    include = df["Include"] if "Include" in df.columns else True
    df = df[include.astype(bool)] if not isinstance(include, bool) else df
    return {
        "single_total": float(df["Single Track (kN/m)"].sum()),
        "double_total": float(df["Double Track (kN/m)"].sum()),
    }


def en_dynamic_factor_standard_maintenance(L_left_m: float, L_right_m: float) -> Dict[str, float]:
    """EN 1991-2 dynamic factor used by the BG40 report for standard maintenance.

    Report form: phi = 2.16/(sqrt(L_phi) - 0.2) + 0.73, with
    L_phi = min(L_left, L_right). This reproduces BG40 value 1.1079 for L_phi = 35 m.
    """
    Lphi = min(float(L_left_m), float(L_right_m))
    if Lphi <= 0.04:
        phi = float("inf")
    else:
        phi = 2.16 / (sqrt(Lphi) - 0.20) + 0.73
    return {"Lphi_m": Lphi, "phi": phi}


def longitudinal_force_en1991(length_m: float, span_m: float, traction_rate_kn_m: float = 33.0, braking_rate_kn_m: float = 20.0, traction_cap_kn: float = 1000.0, braking_cap_kn: float = 6000.0) -> Dict[str, float]:
    q_lak_raw = traction_rate_kn_m * length_m
    q_lbk_raw = braking_rate_kn_m * length_m
    q_lak = min(q_lak_raw, traction_cap_kn)
    q_lbk = min(q_lbk_raw, braking_cap_kn)
    design = max(q_lak, q_lbk)
    return {
        "Qlak_raw_kn": q_lak_raw,
        "Qlak_kn": q_lak,
        "Qlbk_raw_kn": q_lbk_raw,
        "Qlbk_kn": q_lbk,
        "LF_design_kn": design,
        "LF_design_kn_m": design / span_m if span_m else 0.0,
    }


def hunting_force_en1991(qsk_kn: float = 100.0, alpha: float = 0.8, reduce_when_alpha_lt_1: bool = False) -> Dict[str, float | str]:
    """EN 1991-2 nosing/hunting force decision logic.

    Qsk is not reduced for alpha < 1 unless a project requirement explicitly permits it.
    """
    if alpha >= 1.0:
        adopted = alpha * qsk_kn
        basis = "α ≥ 1, Qsk amplified by α"
    elif reduce_when_alpha_lt_1:
        adopted = alpha * qsk_kn
        basis = "User override: α < 1 reduction allowed by project setting"
    else:
        adopted = qsk_kn
        basis = "α < 1 shown for vertical U20 load classification; Qsk is not reduced by default"
    return {"Qsk_kn": qsk_kn, "alpha": alpha, "HF_adopted_kn": adopted, "decision_basis": basis}



WIND_REFERENCE_GROUPS = {
    "Group 1": {"V50_m_s": 25.0, "TF": 1.00, "note": "DPT 1311-50 Group 1"},
    "Group 2": {"V50_m_s": 27.0, "TF": 1.00, "note": "DPT 1311-50 Group 2"},
    "Group 3": {"V50_m_s": 29.0, "TF": 1.00, "note": "DPT 1311-50 Group 3"},
    "Group 4A": {"V50_m_s": 25.0, "TF": 1.20, "note": "DPT 1311-50 Group 4A"},
    "Group 4B": {"V50_m_s": 25.0, "TF": 1.08, "note": "DPT 1311-50 Group 4B"},
}


def wind_reference_group_options() -> list[str]:
    return list(WIND_REFERENCE_GROUPS.keys())


def wind_vb0_recommended_from_group(group: str) -> dict[str, float | str]:
    data = WIND_REFERENCE_GROUPS.get(group, WIND_REFERENCE_GROUPS["Group 1"])
    v50 = float(data["V50_m_s"])
    tf = float(data["TF"])
    return {"group": group if group in WIND_REFERENCE_GROUPS else "Group 1", "V50_m_s": v50, "TF": tf, "vb0_m_s": v50 * tf, "note": str(data["note"])}


def wind_load_factor_c_bridge(b_over_d: float, ze_m: float) -> dict[str, float | str]:
    """EN 1991-1-4 bridge wind load factor C by b/dtot and ze.

    Uses the BG40 report's Table 2.5 (data taken from EN 1991-1-4, Table 8.2):
    b/dtot <= 0.5: C = 6.7 at ze <= 20 m; C = 8.3 at ze = 50 m.
    b/dtot >= 4.0: C = 3.6 at ze <= 20 m; C = 4.5 at ze = 50 m.
    If 0.5 < b/dtot < 4.0, linear interpolation may be used.
    """
    ratio = float(b_over_d)
    ze = float(ze_m)

    def by_ratio(c_at_05: float, c_at_4: float) -> tuple[float, str]:
        if ratio <= 0.5:
            return c_at_05, "b/dtot <= 0.5; upper table row used"
        if ratio >= 4.0:
            return c_at_4, "b/dtot >= 4.0; lower table row used"
        t = (ratio - 0.5) / (4.0 - 0.5)
        return c_at_05 + t * (c_at_4 - c_at_05), "0.5 < b/dtot < 4.0; linear interpolation in b/dtot"

    c20, ratio_note = by_ratio(6.7, 3.6)
    c50, _ = by_ratio(8.3, 4.5)
    if ze <= 20.0:
        c = c20
        ze_note = "ze <= 20 m; ze=20 m column used"
    elif ze >= 50.0:
        c = c50
        ze_note = "ze >= 50 m; ze=50 m column used"
    else:
        t = (ze - 20.0) / 30.0
        c = c20 + t * (c50 - c20)
        ze_note = "20 m < ze < 50 m; linear interpolation between ze columns"
    return {"C": c, "b_over_d": ratio, "ze_m": ze, "ratio_note": ratio_note, "ze_note": ze_note, "source": "EN 1991-1-4 Table 8.2 / BG40 R10 Table 2.5"}


def wind_load_en1991_dpt_auto(
    rho_air_kg_m3: float,
    vb0_m_s: float,
    cdir: float,
    cseason: float,
    b_m: float,
    dtot_ws_m: float,
    dtot_ws_wl_m: float,
    ze_m: float,
    span_m: float,
) -> Dict[str, float | str]:
    vb = float(cdir) * float(cseason) * float(vb0_m_s)
    ratio_ws = float(b_m) / float(dtot_ws_m) if float(dtot_ws_m) else 0.0
    ratio_wl = float(b_m) / float(dtot_ws_wl_m) if float(dtot_ws_wl_m) else 0.0
    c_ws = wind_load_factor_c_bridge(ratio_ws, ze_m)
    c_wl = wind_load_factor_c_bridge(ratio_wl, ze_m)
    out = wind_load_en1991_dpt(float(rho_air_kg_m3), vb, float(c_ws["C"]), float(c_wl["C"]), float(dtot_ws_m), float(dtot_ws_wl_m), float(span_m))
    out.update({
        "vb_m_s": vb,
        "b_m": float(b_m),
        "dtot_ws_m": float(dtot_ws_m),
        "dtot_ws_wl_m": float(dtot_ws_wl_m),
        "ze_m": float(ze_m),
        "b_over_d_ws": ratio_ws,
        "b_over_d_ws_wl": ratio_wl,
        "C_ws": float(c_ws["C"]),
        "C_ws_wl": float(c_wl["C"]),
        "C_ws_note": f"{c_ws['ratio_note']}; {c_ws['ze_note']}",
        "C_ws_wl_note": f"{c_wl['ratio_note']}; {c_wl['ze_note']}",
        "C_source": "EN 1991-1-4 Table 8.2 / BG40 R10 Table 2.5",
    })
    return out

def wind_load_en1991_dpt(rho_air_kg_m3: float, vb_m_s: float, C_ws: float, C_ws_wl: float, dtot_ws_m: float, dtot_ws_wl_m: float, span_m: float) -> Dict[str, float]:
    q_pa = 0.5 * rho_air_kg_m3 * vb_m_s**2
    aref_ws = dtot_ws_m * span_m
    aref_wl = dtot_ws_wl_m * span_m
    ws_kn = q_pa * C_ws * aref_ws / 1000.0
    ws_wl_kn = q_pa * C_ws_wl * aref_wl / 1000.0
    return {
        "q_pa": q_pa,
        "Aref_ws_m2": aref_ws,
        "Aref_ws_wl_m2": aref_wl,
        "WSsuper_kn": ws_kn,
        "WSsuper_WL_kn": ws_wl_kn,
        "WSsuper_kn_m": ws_kn / span_m if span_m else 0.0,
        "WSsuper_WL_kn_m": ws_wl_kn / span_m if span_m else 0.0,
    }
