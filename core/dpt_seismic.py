from __future__ import annotations

from dataclasses import dataclass
from math import inf
from pathlib import Path
from typing import Dict, List

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "dpt_1301_1302_61"

FA_TABLE = {
    "A": [0.8, 0.8, 0.8, 0.8, 0.8],
    "B": [1.0, 1.0, 1.0, 1.0, 1.0],
    "C": [1.2, 1.2, 1.1, 1.0, 1.0],
    "D": [1.6, 1.4, 1.2, 1.1, 1.0],
    "E": [2.5, 1.7, 1.2, 0.9, 0.9],
}
FV_TABLE = {
    "A": [0.8, 0.8, 0.8, 0.8, 0.8],
    "B": [1.0, 1.0, 1.0, 1.0, 1.0],
    "C": [1.7, 1.6, 1.5, 1.4, 1.3],
    "D": [2.4, 2.0, 1.8, 1.6, 1.5],
    "E": [3.5, 3.2, 2.8, 2.4, 2.4],
}
FA_X = [0.25, 0.50, 0.75, 1.00, 1.25]
FV_X = [0.10, 0.20, 0.30, 0.40, 0.50]
CATEGORY_RANK = {"ก": 0, "ข": 1, "ค": 2, "ง": 3}
CATEGORY_BY_RANK = {v: k for k, v in CATEGORY_RANK.items()}


def normalize_thai_location(value: object) -> str:
    """Normalize Thai location labels from user input and PDF extraction.

    The DPT PDF often extracts the Thai sara-am as a separated pattern such as
    ``ค า`` instead of ``คำ``.  This normalizer also strips common prefixes used
    by engineers when typing locations, e.g. ``จ.``, ``จังหวัด``, ``อ.``, and
    ``อำเภอ``.
    """
    s = str(value or "").strip()
    s = s.replace("\uf028", "").replace("\uf029", "").replace("\uf03d", "").replace("\uf0a3", "")
    s = s.replace("จังหวัด", "").replace("จ.", "")
    s = s.replace("อำเภอ", "").replace("อ.", "")
    s = s.replace("เขต", "") if s.startswith("เขต") else s
    s = s.replace(" า", "ำ")
    return " ".join(s.split()).strip()


def _interp(x: float, xs: List[float], ys: List[float]) -> float:
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    for i in range(1, len(xs)):
        if x <= xs[i]:
            x0, x1 = xs[i - 1], xs[i]
            y0, y1 = ys[i - 1], ys[i]
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return ys[-1]


def _read_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / name)


def site_coefficient_fa(soil_class: str, Ss: float) -> float:
    cls = soil_class.upper()
    if cls == "F":
        raise ValueError("Soil class F requires site-specific response analysis per DPT 1301/1302-61.")
    if cls not in FA_TABLE:
        raise ValueError(f"Unknown soil class: {soil_class}")
    return _interp(float(Ss), FA_X, FA_TABLE[cls])


def site_coefficient_fv(soil_class: str, S1: float) -> float:
    cls = soil_class.upper()
    if cls == "F":
        raise ValueError("Soil class F requires site-specific response analysis per DPT 1301/1302-61.")
    if cls not in FV_TABLE:
        raise ValueError(f"Unknown soil class: {soil_class}")
    return _interp(float(S1), FV_X, FV_TABLE[cls])


def load_general_location_database() -> pd.DataFrame:
    path = DATA_DIR / "general_ss_s1_by_district.csv"
    if path.exists():
        return pd.read_csv(path)
    return pd.read_csv(DATA_DIR / "general_ss_s1_seed.csv")


def load_bangkok_zone_map() -> pd.DataFrame:
    return _read_csv("bangkok_basin_zone_map.csv")


def load_bangkok_equiv_static_table(damping_percent: float = 5.0) -> pd.DataFrame:
    name = "bangkok_equiv_static_5p0_table_1_4_5.csv" if abs(float(damping_percent) - 5.0) < 1e-9 else "bangkok_equiv_static_2p5_table_1_4_4.csv"
    return _read_csv(name)


def list_general_provinces() -> list[str]:
    df = load_general_location_database()
    return sorted(df["province_th"].dropna().unique().tolist())


def list_general_districts(province: str) -> list[str]:
    df = load_general_location_database()
    key = normalize_thai_location(province)
    if "province_key" not in df.columns:
        df["province_key"] = df["province_th"].map(normalize_thai_location)
    return sorted(df.loc[df["province_key"] == key, "district_th"].dropna().unique().tolist())


def lookup_general_ss_s1(province: str, district: str) -> Dict[str, object]:
    df = load_general_location_database()
    province_key = normalize_thai_location(province)
    district_key = normalize_thai_location(district)
    if "province_key" not in df.columns:
        df["province_key"] = df["province_th"].map(normalize_thai_location)
    if "district_key" not in df.columns:
        df["district_key"] = df["district_th"].map(normalize_thai_location)
    mask = (df["province_key"].str.strip() == province_key) & (df["district_key"].str.strip() == district_key)
    if not mask.any():
        return {"found": False, "province_th": province_key, "district_th": district_key, "region": "General Thailand"}
    row = df[mask].iloc[0].to_dict()
    row["found"] = True
    row["lookup_source"] = "DPT general district database"
    return row


def lookup_bangkok_basin_zone(province: str, district: str) -> Dict[str, object]:
    df = load_bangkok_zone_map()
    province_key = normalize_thai_location(province)
    district_key = normalize_thai_location(district)
    if "province_key" not in df.columns:
        df["province_key"] = df["province_th"].map(normalize_thai_location)
    if "district_key" not in df.columns:
        df["district_key"] = df["district_th"].map(normalize_thai_location)
    province_rows = df[df["province_key"] == province_key]
    if province_rows.empty:
        return {"found": False, "province_th": province_key, "district_th": district_key, "region": "General Thailand"}
    whole = province_rows[province_rows["district_key"] == "*"]
    if not whole.empty:
        row = whole.iloc[0].to_dict()
        row["found"] = True
        row["region"] = "Bangkok Basin"
        return row
    district_rows = province_rows[province_rows["district_key"] == district_key]
    if not district_rows.empty:
        row = district_rows.iloc[0].to_dict()
        row["found"] = True
        row["region"] = "Bangkok Basin"
        return row
    return {"found": False, "province_th": province_key, "district_th": district_key, "region": "General Thailand"}


def resolve_location_region(province: str, district: str) -> Dict[str, object]:
    """Return Bangkok Basin route first, otherwise general Thailand lookup."""
    bkk = lookup_bangkok_basin_zone(province, district)
    if bkk.get("found"):
        return bkk
    gen = lookup_general_ss_s1(province, district)
    if gen.get("found"):
        gen["region"] = "General Thailand"
    return gen


def _importance_group(I: float) -> str:
    if I >= 1.5:
        return "IV"
    if I >= 1.25:
        return "III"
    return "I_or_II"


def seismic_design_category_from_sds(SDS: float, importance_factor: float) -> str:
    group = _importance_group(importance_factor)
    if SDS < 0.167:
        return "ก"
    if SDS < 0.33:
        return "ค" if group == "IV" else "ข"
    if SDS < 0.50:
        return "ง" if group == "IV" else "ค"
    return "ง"


def seismic_design_category_from_sd1(SD1: float, importance_factor: float) -> str:
    group = _importance_group(importance_factor)
    if SD1 < 0.067:
        return "ก"
    if SD1 < 0.133:
        return "ค" if group == "IV" else "ข"
    if SD1 < 0.20:
        return "ง" if group == "IV" else "ค"
    return "ง"


def governing_seismic_design_category(SDS: float, SD1: float, I: float, T: float | None = None, Ts: float | None = None, region: str = "General Thailand") -> Dict[str, str]:
    """Determine DPT seismic design category with period-based route notes.

    General Thailand: normally use the more stringent result from Tables 1.6-1
    and 1.6-2; DPT allows using only Table 1.6-1 when T < 0.8Ts.
    Bangkok Basin: DPT directs Table 1.6-1 only for T <= 0.5 s and Table 1.6-2
    only for T > 0.5 s.
    """
    cat_sds = seismic_design_category_from_sds(SDS, I)
    cat_sd1 = seismic_design_category_from_sd1(SD1, I)
    region_norm = (region or "").lower()
    if "bangkok" in region_norm:
        if T is not None and float(T) <= 0.5:
            return {"category_sds": cat_sds, "category_sd1": cat_sd1, "category_governing": cat_sds, "category_basis": "Bangkok Basin: T ≤ 0.5 s, DPT allows Table 1.6-1 only"}
        return {"category_sds": cat_sds, "category_sd1": cat_sd1, "category_governing": cat_sd1, "category_basis": "Bangkok Basin: T > 0.5 s, DPT uses Table 1.6-2 only"}
    if T is not None and Ts not in (None, 0) and float(T) < 0.8 * float(Ts):
        return {"category_sds": cat_sds, "category_sd1": cat_sd1, "category_governing": cat_sds, "category_basis": "General Thailand: T < 0.8Ts, DPT allows Table 1.6-1 only"}
    governing = CATEGORY_BY_RANK[max(CATEGORY_RANK[cat_sds], CATEGORY_RANK[cat_sd1])]
    return {"category_sds": cat_sds, "category_sd1": cat_sd1, "category_governing": governing, "category_basis": "General Thailand: more stringent of Tables 1.6-1 and 1.6-2"}


def equivalent_static_sa_general(SDS: float, SD1: float, T_s: float) -> Dict[str, float | str]:
    """Return Sa(T) for DPT general Thailand equivalent-static spectra.

    DPT 1301/1302-61 Section 1.4.5.1 directs equivalent static design
    to use Fig. 1.4-1 when ``SD1 <= SDS`` and Fig. 1.4-2 when
    ``SD1 > SDS``.  These figures are intentionally different from the
    dynamic spectra in Fig. 1.4-3 / Fig. 1.4-4, which start from
    ``0.4SDS`` and ramp to ``SDS``.
    """
    SDS = float(SDS)
    SD1 = float(SD1)
    T = float(T_s)
    if T < 0:
        return {"Sa": 0.0, "T0": 0.0, "Ts": 0.0, "spectrum_branch": "invalid T", "spectrum_figure": "DPT Fig. 1.4-1 / 1.4-2"}

    if SD1 <= SDS:
        Ts = SD1 / SDS if SDS else inf
        T0 = 0.0
        if T <= Ts:
            Sa = SDS
            branch = "Fig. 1.4-1: T ≤ Ts, Sa = SDS"
        else:
            Sa = SD1 / T
            branch = "Fig. 1.4-1: T > Ts, Sa = SD1/T"
        figure = "DPT Fig. 1.4-1 (SD1 ≤ SDS)"
    else:
        # DPT Fig. 1.4-2: Sa = SDS for T <= 0.2 s; linear increase
        # from SDS at 0.2 s to SD1 at 1.0 s; Sa = SD1/T for T > 1.0 s.
        T0 = 0.2
        Ts = 1.0
        if T <= T0:
            Sa = SDS
            branch = "Fig. 1.4-2: T ≤ 0.2 s, Sa = SDS"
        elif T <= Ts:
            Sa = SDS + (SD1 - SDS) * (T - T0) / (Ts - T0)
            branch = "Fig. 1.4-2: 0.2 s < T ≤ 1.0 s, linear SDS→SD1"
        else:
            Sa = SD1 / T
            branch = "Fig. 1.4-2: T > 1.0 s, Sa = SD1/T"
        figure = "DPT Fig. 1.4-2 (SD1 > SDS)"

    return {"Sa": Sa, "T0": T0, "Ts": Ts, "spectrum_branch": branch, "spectrum_figure": figure}


def dpt_general_spectrum(Ss: float, S1: float, soil_class: str, T_s: float, I: float, R: float) -> Dict[str, float | str]:
    Fa = site_coefficient_fa(soil_class, Ss)
    Fv = site_coefficient_fv(soil_class, S1)
    SMS = Fa * Ss
    SM1 = Fv * S1
    SDS = 2.0 / 3.0 * SMS
    SD1 = 2.0 / 3.0 * SM1
    T = float(T_s)
    sa_out = equivalent_static_sa_general(SDS, SD1, T)
    Sa = float(sa_out["Sa"])
    T0 = float(sa_out["T0"])
    Ts = float(sa_out["Ts"])
    Cs_raw = Sa * I / R if R else inf
    Cs = max(Cs_raw, 0.01)
    cats = governing_seismic_design_category(SDS, SD1, I, T, Ts, "General Thailand")
    return {
        "region": "General Thailand",
        "method": "Equivalent Static",
        "Fa": Fa,
        "Fv": Fv,
        "SMS": SMS,
        "SM1": SM1,
        "SDS": SDS,
        "SD1": SD1,
        "T0": T0,
        "Ts": Ts,
        "Sa": Sa,
        "spectrum_branch": sa_out["spectrum_branch"],
        "spectrum_figure": sa_out["spectrum_figure"],
        "Cs_raw": Cs_raw,
        "Cs": Cs,
        **cats,
    }


def _linear_interp(x: float, xs: list[float], ys: list[float]) -> float:
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    for i in range(1, len(xs)):
        if x <= xs[i]:
            x0, x1 = xs[i-1], xs[i]
            y0, y1 = ys[i-1], ys[i]
            return y0 + (y1-y0)*(x-x0)/(x1-x0)
    return ys[-1]


def dpt_bangkok_basin_spectrum(zone: int, T_s: float, I: float, R: float, damping_percent: float = 5.0) -> Dict[str, float | str]:
    df = load_bangkok_equiv_static_table(damping_percent)
    zdf = df[df["zone"].astype(int) == int(zone)].sort_values("T_s")
    if zdf.empty:
        raise ValueError(f"Bangkok Basin zone {zone} not found in equivalent-static spectrum table.")
    periods = zdf["T_s"].astype(float).tolist()
    values = zdf["Sa_g"].astype(float).tolist()
    T = float(T_s)
    Sa = _linear_interp(T, periods, values)
    SDS = float(zdf.loc[(zdf["T_s"].astype(float) - 0.2).abs().idxmin(), "Sa_g"])
    SD1 = float(zdf.loc[(zdf["T_s"].astype(float) - 1.0).abs().idxmin(), "Sa_g"])
    Cs_raw = Sa * I / R if R else inf
    Cs = max(Cs_raw, 0.01)
    cats = governing_seismic_design_category(SDS, SD1, I, T, None, "Bangkok Basin")
    return {"region": "Bangkok Basin", "zone": int(zone), "damping_percent": float(damping_percent), "SDS": SDS, "SD1": SD1, "T0": 0.0, "Ts": 0.0, "Sa": Sa, "spectrum_branch": "Table 1.4-5 interpolation" if float(damping_percent) == 5.0 else "Table 1.4-4 interpolation", "Cs_raw": Cs_raw, "Cs": Cs, **cats}


def response_spectrum_points(SDS: float, SD1: float, t_max: float = 3.0, n: int = 90) -> pd.DataFrame:
    """Generate DPT general Thailand equivalent-static spectrum points.

    This is the plotting companion to :func:`equivalent_static_sa_general` and
    must not use the dynamic Fig. 1.4-3 / 1.4-4 ``0.4SDS`` branch.
    """
    xs = [i * t_max / (n - 1) for i in range(n)]
    ys = [float(equivalent_static_sa_general(SDS, SD1, T)["Sa"]) for T in xs]
    return pd.DataFrame({"T (s)": xs, "Sa (g)": ys})


def bangkok_response_spectrum_points(zone: int, damping_percent: float = 5.0) -> pd.DataFrame:
    df = load_bangkok_equiv_static_table(damping_percent)
    zdf = df[df["zone"].astype(int) == int(zone)].sort_values("T_s")
    return pd.DataFrame({"T (s)": zdf["T_s"].astype(float), "Sa (g)": zdf["Sa_g"].astype(float)})


def list_dpt_provinces() -> list[str]:
    """List provinces available in either general table or Bangkok Basin zone map."""
    parts = []
    try:
        parts.extend(load_general_location_database()["province_th"].dropna().unique().tolist())
    except Exception:
        pass
    try:
        parts.extend(load_bangkok_zone_map()["province_th"].dropna().unique().tolist())
    except Exception:
        pass
    return sorted(set(parts))


def list_dpt_districts(province: str) -> list[str]:
    """List districts for a province from both DPT general and Bangkok Basin datasets."""
    key = normalize_thai_location(province)
    districts: list[str] = []
    try:
        g = load_general_location_database()
        if "province_key" not in g.columns:
            g["province_key"] = g["province_th"].map(normalize_thai_location)
        districts.extend(g.loc[g["province_key"] == key, "district_th"].dropna().unique().tolist())
    except Exception:
        pass
    try:
        b = load_bangkok_zone_map()
        if "province_key" not in b.columns:
            b["province_key"] = b["province_th"].map(normalize_thai_location)
        bb = b[b["province_key"] == key]
        if not bb.empty:
            if (bb["district_th"] == "*").any():
                districts.append("ทั้งจังหวัด")
            districts.extend(bb.loc[bb["district_th"] != "*", "district_th"].dropna().unique().tolist())
    except Exception:
        pass
    return sorted(set(districts))
