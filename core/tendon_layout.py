"""CSiBridge tendon-layout import and QA utilities.

The CSiBridge export used by BG40 is split into three tables:
General, Vertical Layout, and Horizontal Layout.  This module reads those
spreadsheet/CSV tables into a one-source tendon model that can drive report
figures, prestress-loss summaries, and QA checks.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO, StringIO
import re
from typing import Any, Iterable

import numpy as np
import pandas as pd

REQUIRED_GENERAL_COLUMNS = {"BridgeObj", "Tendon", "Material", "TendonArea", "Force"}
FPU_MPA = 1860.0
JACKING_STRESS_RATIO = 0.75
JACKING_STRESS_MPA = FPU_MPA * JACKING_STRESS_RATIO
STRAND_NOMINAL_AREA_MM2 = 140.0
STRAND_SIZE_LABEL = "T15.2"
REQUIRED_VERTICAL_COLUMNS = {"BridgeObj", "Tendon", "TendonDist", "VertOff"}
REQUIRED_HORIZONTAL_COLUMNS = {"BridgeObj", "Tendon", "TendonDist", "HorizOff"}


@dataclass(frozen=True)
class TendonImportResult:
    general: list[dict[str, Any]]
    vertical: list[dict[str, Any]]
    horizontal: list[dict[str, Any]]
    model: dict[str, Any]


def _read_bytes(source: Any) -> bytes:
    if source is None:
        return b""
    if isinstance(source, bytes):
        return source
    if isinstance(source, (str, bytes)):
        with open(source, "rb") as f:
            return f.read()
    if hasattr(source, "getvalue"):
        return source.getvalue()
    if hasattr(source, "read"):
        pos = None
        try:
            pos = source.tell()
        except Exception:  # pragma: no cover - file-like may not support tell
            pos = None
        data = source.read()
        if pos is not None:
            try:
                source.seek(pos)
            except Exception:  # pragma: no cover
                pass
        return data
    raise TypeError(f"Unsupported tendon source type: {type(source)!r}")


def _read_raw_table(source: Any, filename: str | None = None) -> pd.DataFrame:
    """Read a CSiBridge export, preserving the title/header/unit rows."""
    data = _read_bytes(source)
    name = (filename or getattr(source, "name", "") or "").lower()
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(BytesIO(data), sheet_name=0, header=None)
    if name.endswith(".csv"):
        text = data.decode("utf-8-sig")
        return pd.read_csv(StringIO(text), header=None)
    # Fallback: try Excel first, then CSV.
    try:
        return pd.read_excel(BytesIO(data), sheet_name=0, header=None)
    except Exception:
        text = data.decode("utf-8-sig")
        return pd.read_csv(StringIO(text), header=None)


def _table_from_csibridge_raw(raw: pd.DataFrame, required: set[str]) -> pd.DataFrame:
    """Find the CSiBridge header row and return a clean data table."""
    header_idx: int | None = None
    for i, row in raw.iterrows():
        values = {str(v).strip() for v in row.dropna().tolist()}
        if required.issubset(values):
            header_idx = int(i)
            break
    if header_idx is None:
        raise ValueError(f"Could not find required CSiBridge columns: {sorted(required)}")

    headers = [str(v).strip() if pd.notna(v) else f"Unnamed_{j}" for j, v in enumerate(raw.iloc[header_idx].tolist())]
    data = raw.iloc[header_idx + 1 :].copy()
    data.columns = headers
    # Drop CSiBridge unit row and fully empty rows.
    data = data.dropna(how="all")
    if "Tendon" in data.columns:
        data = data[~data["Tendon"].astype(str).str.strip().str.lower().isin({"text", "", "nan"})]
    return data.reset_index(drop=True)


def _natural_tendon_sort_key(name: str) -> tuple[int, str, str]:
    match = re.search(r"T\s*(\d+)", str(name), re.I)
    n = int(match.group(1)) if match else 9999
    side = "0"
    if re.search(r"[-_]?L\b", str(name), re.I):
        side = "L"
    elif re.search(r"[-_]?R\b", str(name), re.I):
        side = "R"
    return (n, side, str(name))


def parse_tendon_family(name: str) -> tuple[str, str]:
    text = str(name).strip()
    family_match = re.search(r"(T\s*\d+)", text, re.I)
    family = family_match.group(1).replace(" ", "").upper() if family_match else text
    side = ""
    if re.search(r"[-_]?L\b", text, re.I):
        side = "L"
    elif re.search(r"[-_]?R\b", text, re.I):
        side = "R"
    return family, side


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def normalize_general_tendon_rows(raw: pd.DataFrame | Any, filename: str | None = None) -> pd.DataFrame:
    df = _table_from_csibridge_raw(_read_raw_table(raw, filename) if not isinstance(raw, pd.DataFrame) else raw, REQUIRED_GENERAL_COLUMNS)
    keep = [c for c in ["BridgeObj", "Tendon", "LoadName", "StartSpan", "StartType", "EndSpan", "EndType", "PreType", "JackFrom", "Material", "TendonArea", "LoadType", "Force"] if c in df.columns]
    out = df[keep].copy()
    out["BridgeObj"] = out["BridgeObj"].astype(str).str.strip()
    out["Tendon"] = out["Tendon"].astype(str).str.strip()
    out["family"] = out["Tendon"].map(lambda x: parse_tendon_family(x)[0])
    out["side"] = out["Tendon"].map(lambda x: parse_tendon_family(x)[1])
    out["TendonArea"] = pd.to_numeric(out.get("TendonArea", 0.0), errors="coerce")
    out["Force"] = pd.to_numeric(out.get("Force", 0.0), errors="coerce")
    out["Aps_mm2"] = out["TendonArea"] * 1_000_000.0
    # CSiBridge area for BG40 is 0.00336 m² = 3360 mm² = 24 x 140 mm².
    out["strand_count_140mm2"] = out["Aps_mm2"] / STRAND_NOMINAL_AREA_MM2
    out["strand_count"] = out["strand_count_140mm2"].round().astype("Int64")
    out["strand_size"] = STRAND_SIZE_LABEL
    out["strand_label"] = out["strand_count"].astype(str) + "-" + STRAND_SIZE_LABEL
    out["fpu_mpa"] = FPU_MPA
    out["jacking_stress_mpa"] = JACKING_STRESS_MPA
    out["force_imported_kN"] = out["Force"]
    out["force_075fpu_kN"] = out["Aps_mm2"] * JACKING_STRESS_MPA / 1000.0
    return out.sort_values("Tendon", key=lambda s: s.map(_natural_tendon_sort_key)).reset_index(drop=True)


def normalize_tendon_profile_rows(raw: pd.DataFrame | Any, filename: str | None = None, profile: str = "vertical") -> pd.DataFrame:
    required = REQUIRED_VERTICAL_COLUMNS if profile == "vertical" else REQUIRED_HORIZONTAL_COLUMNS
    value_col = "VertOff" if profile == "vertical" else "HorizOff"
    df = _table_from_csibridge_raw(_read_raw_table(raw, filename) if not isinstance(raw, pd.DataFrame) else raw, required)
    keep = [c for c in ["BridgeObj", "Tendon", "SegType", "TendonDist", value_col] if c in df.columns]
    out = df[keep].copy()
    out["BridgeObj"] = out["BridgeObj"].astype(str).str.strip()
    out["Tendon"] = out["Tendon"].astype(str).str.strip()
    out["SegType"] = out.get("SegType", "").astype(str).str.strip()
    out["TendonDist"] = pd.to_numeric(out["TendonDist"], errors="coerce")
    out[value_col] = pd.to_numeric(out[value_col], errors="coerce")
    out = out.dropna(subset=["Tendon", "TendonDist", value_col])
    out["family"] = out["Tendon"].map(lambda x: parse_tendon_family(x)[0])
    out["side"] = out["Tendon"].map(lambda x: parse_tendon_family(x)[1])
    if profile == "vertical":
        out["x_m"] = out["TendonDist"].astype(float)
        out["dp_top_m"] = out["VertOff"].astype(float).abs()
    else:
        out["x_m"] = out["TendonDist"].astype(float)
        out["horiz_off_m"] = out["HorizOff"].astype(float)
    return out.sort_values(["Tendon", "TendonDist"], key=lambda s: s.map(_natural_tendon_sort_key) if s.name == "Tendon" else s).reset_index(drop=True)


def read_tendon_general_table(source: Any, filename: str | None = None) -> pd.DataFrame:
    return normalize_general_tendon_rows(source, filename)


def read_tendon_vertical_table(source: Any, filename: str | None = None) -> pd.DataFrame:
    return normalize_tendon_profile_rows(source, filename, profile="vertical")


def read_tendon_horizontal_table(source: Any, filename: str | None = None) -> pd.DataFrame:
    return normalize_tendon_profile_rows(source, filename, profile="horizontal")


def _interp_profile(df: pd.DataFrame, tendon: str, value_col: str, x_m: float) -> float | None:
    td = df[df["Tendon"] == tendon].sort_values("x_m")
    if td.empty:
        return None
    xs = td["x_m"].to_numpy(dtype=float)
    ys = td[value_col].to_numpy(dtype=float)
    if len(xs) == 1:
        return float(ys[0])
    x = float(np.clip(x_m, xs.min(), xs.max()))
    return float(np.interp(x, xs, ys))


def _profile_list(df: pd.DataFrame, tendon: str, value_col: str) -> list[dict[str, Any]]:
    rows = []
    for _, r in df[df["Tendon"] == tendon].sort_values("x_m").iterrows():
        rows.append({"x_m": float(r["x_m"]), value_col: float(r[value_col]), "seg_type": str(r.get("SegType", ""))})
    return rows




def _seg_type_at_station(df: pd.DataFrame, tendon: str, x_m: float) -> str:
    """Return the profile segment type at an exact exported station when available."""
    if df is None or df.empty or "x_m" not in df.columns:
        return ""
    td = df[df["Tendon"] == tendon].copy()
    if td.empty:
        return ""
    exact = td[(td["x_m"].astype(float) - float(x_m)).abs() < 1e-9]
    if not exact.empty:
        return str(exact.iloc[0].get("SegType", ""))
    return "Interpolated"


def _profile_stations(df: pd.DataFrame, tendon: str) -> list[float]:
    if df is None or df.empty or "x_m" not in df.columns:
        return []
    vals = df[df["Tendon"] == tendon]["x_m"].dropna().astype(float).tolist()
    return sorted(set(round(float(v), 9) for v in vals))


def _bridge_objects(*dfs: pd.DataFrame) -> list[str]:
    out: list[str] = []
    for df in dfs:
        if df is not None and not df.empty and "BridgeObj" in df.columns:
            for obj in df["BridgeObj"].dropna().astype(str).str.strip().unique().tolist():
                if obj and obj not in out:
                    out.append(obj)
    return out


def _most_common_bridge_object(df: pd.DataFrame) -> str:
    if df is None or df.empty or "BridgeObj" not in df.columns:
        return ""
    vc = df["BridgeObj"].astype(str).str.strip().value_counts()
    return str(vc.index[0]) if len(vc) else ""


def build_tendon_layout_model(
    general_df: pd.DataFrame,
    vertical_df: pd.DataFrame,
    horizontal_df: pd.DataFrame,
    *,
    active_bridge_object: str | None = None,
    map_to_active_bridge_object: bool = False,
    y_t_from_top_m: float = 0.0,
) -> dict[str, Any]:
    """Merge CSiBridge General/Vertical/Horizontal tables into one tendon model."""
    general = general_df.copy() if general_df is not None else pd.DataFrame()
    vertical = vertical_df.copy() if vertical_df is not None else pd.DataFrame()
    horizontal = horizontal_df.copy() if horizontal_df is not None else pd.DataFrame()

    default_obj = _most_common_bridge_object(general) or _most_common_bridge_object(vertical) or _most_common_bridge_object(horizontal)
    active_obj = (active_bridge_object or default_obj or "").strip()
    imported_objs = _bridge_objects(general, vertical, horizontal)
    warnings: list[str] = []
    errors: list[str] = []
    if len(imported_objs) > 1:
        warnings.append("BridgeObj mismatch detected across General / Vertical / Horizontal tendon tables.")
    if map_to_active_bridge_object and active_obj:
        for df in (general, vertical, horizontal):
            if not df.empty and "BridgeObj" in df.columns:
                df["BridgeObj_original"] = df["BridgeObj"]
                df["BridgeObj"] = active_obj

    tendon_names = sorted(set(general.get("Tendon", [])) | set(vertical.get("Tendon", [])) | set(horizontal.get("Tendon", [])), key=_natural_tendon_sort_key)
    if not tendon_names:
        errors.append("No tendon names found in imported tables.")

    span_m = 0.0
    if not vertical.empty:
        span_m = max(span_m, float(vertical["x_m"].max()))
    if not horizontal.empty:
        span_m = max(span_m, float(horizontal["x_m"].max()))
    mid_m = span_m / 2.0 if span_m else 0.0

    general_by_tendon = {str(r["Tendon"]): r.to_dict() for _, r in general.iterrows()}
    tendons: list[dict[str, Any]] = []
    for name in tendon_names:
        fam, side = parse_tendon_family(name)
        g = general_by_tendon.get(name, {})
        end_dp = _interp_profile(vertical, name, "dp_top_m", 0.0)
        mid_dp = _interp_profile(vertical, name, "dp_top_m", mid_m) if mid_m else None
        end_h = _interp_profile(horizontal, name, "horiz_off_m", 0.0)
        mid_h = _interp_profile(horizontal, name, "horiz_off_m", mid_m) if mid_m else None
        aps_mm2 = _to_float(g.get("Aps_mm2", 0.0), 0.0)
        force_imported_kn = _to_float(g.get("force_imported_kN", g.get("Force", 0.0)), 0.0)
        force_075fpu_kn = _to_float(g.get("force_075fpu_kN", aps_mm2 * JACKING_STRESS_MPA / 1000.0 if aps_mm2 else 0.0), 0.0)
        force_kn = force_075fpu_kn
        tendons.append(
            {
                "tendon": name,
                "family": fam,
                "side": side,
                "bridge_obj": str(g.get("BridgeObj", active_obj or "")),
                "material": str(g.get("Material", "")),
                "load_name": str(g.get("LoadName", "")),
                "pre_type": str(g.get("PreType", "")),
                "jack_from": str(g.get("JackFrom", "")),
                "area_m2": _to_float(g.get("TendonArea", aps_mm2 / 1_000_000.0 if aps_mm2 else 0.0)),
                "area_mm2": aps_mm2,
                "strand_count_140mm2": _to_float(g.get("strand_count_140mm2", 0.0)),
                "strand_count": int(round(_to_float(g.get("strand_count_140mm2", 0.0)))) if _to_float(g.get("strand_count_140mm2", 0.0)) else 0,
                "strand_size": STRAND_SIZE_LABEL,
                "strand_label": f"{int(round(_to_float(g.get('strand_count_140mm2', 0.0))))}-{STRAND_SIZE_LABEL}" if _to_float(g.get("strand_count_140mm2", 0.0)) else "-",
                "fpu_mpa": FPU_MPA,
                "jacking_stress_mpa": JACKING_STRESS_MPA,
                "force_imported_kN": force_imported_kn,
                "force_kN": force_kn,
                "force_basis": "0.75 fpu × Aps",
                "end_dp_m": end_dp,
                "midspan_dp_m": mid_dp,
                "end_horiz_off_m": end_h,
                "midspan_horiz_off_m": mid_h,
                "vertical_profile": _profile_list(vertical, name, "dp_top_m"),
                "horizontal_profile": _profile_list(horizontal, name, "horiz_off_m"),
            }
        )

    # Merge vertical and horizontal control-point rows into a complete tendon profile table.
    # This is the user-facing adopted profile table; raw vertical/horizontal imports remain QA-only.
    profile_rows: list[dict[str, Any]] = []
    station_match_rows: list[dict[str, Any]] = []
    for t in tendons:
        name = str(t.get("tendon", ""))
        v_stations = _profile_stations(vertical, name)
        h_stations = _profile_stations(horizontal, name)
        station_union = sorted(set(v_stations + h_stations))
        station_status = "MATCH" if v_stations == h_stations and v_stations else "REVIEW"
        if not v_stations:
            station_status = "MISSING VERTICAL"
        if not h_stations:
            station_status = "MISSING HORIZONTAL"
        station_match_rows.append(
            {
                "Tendon": name,
                "Vertical points": len(v_stations),
                "Horizontal points": len(h_stations),
                "Merged profile points": len(station_union),
                "Station match status": station_status,
            }
        )
        for idx, x in enumerate(station_union, start=1):
            dp = _interp_profile(vertical, name, "dp_top_m", x)
            off = _interp_profile(horizontal, name, "horiz_off_m", x)
            v_seg = _seg_type_at_station(vertical, name, x)
            h_seg = _seg_type_at_station(horizontal, name, x)
            seg_type = v_seg if v_seg and v_seg == h_seg else (v_seg or h_seg or "Interpolated")
            if v_seg and h_seg and v_seg != h_seg:
                seg_type = f"V:{v_seg} / H:{h_seg}"
            profile_rows.append(
                {
                    "Tendon": name,
                    "Family": t.get("family", ""),
                    "Side": t.get("side", ""),
                    "BridgeObj": t.get("bridge_obj", active_obj),
                    "Point No.": idx,
                    "SegType": seg_type,
                    "x_m": float(x),
                    "dp_top_m": dp,
                    "horiz_off_m": off,
                    "Status": "OK" if dp is not None and off is not None else "REVIEW",
                }
            )
        t["vertical_point_count"] = len(v_stations)
        t["horizontal_point_count"] = len(h_stations)
        t["profile_point_count"] = len(station_union)
        t["profile_status"] = station_status if station_status != "MATCH" else "OK"

    # Symmetry check by family: L/R should have identical vertical profile and opposite horizontal offsets.
    symmetry_rows: list[dict[str, Any]] = []
    for fam in sorted({t["family"] for t in tendons}, key=_natural_tendon_sort_key):
        left = next((t for t in tendons if t["family"] == fam and t["side"] == "L"), None)
        right = next((t for t in tendons if t["family"] == fam and t["side"] == "R"), None)
        if left and right:
            stations = sorted(set([p["x_m"] for p in left["vertical_profile"]] + [p["x_m"] for p in right["vertical_profile"]]))
            vdiffs = []
            hdiffs = []
            for x in stations:
                lv = _interp_profile(vertical, left["tendon"], "dp_top_m", x)
                rv = _interp_profile(vertical, right["tendon"], "dp_top_m", x)
                lh = _interp_profile(horizontal, left["tendon"], "horiz_off_m", x)
                rh = _interp_profile(horizontal, right["tendon"], "horiz_off_m", x)
                if lv is not None and rv is not None:
                    vdiffs.append(abs(lv - rv))
                if lh is not None and rh is not None:
                    hdiffs.append(abs(lh + rh))
            symmetry_rows.append({"Family": fam, "Vertical max diff (m)": max(vdiffs) if vdiffs else None, "Horizontal sign-sym diff (m)": max(hdiffs) if hdiffs else None, "Status": "MATCH" if (max(vdiffs or [0]) < 1e-6 and max(hdiffs or [0]) < 1e-6) else "REVIEW"})

    # Summary in report-style groups: T1–T2, T3–T4, T5–T6, T7–T8.
    family_numbers = sorted({int(re.search(r"\d+", t["family"]).group(0)) for t in tendons if re.search(r"\d+", t["family"])})
    group_rows: list[dict[str, Any]] = []
    total_weight = 0.0
    weighted_end = 0.0
    weighted_mid = 0.0
    for i in range(0, len(family_numbers), 2):
        pair_nums = family_numbers[i : i + 2]
        pair_fams = {f"T{n}" for n in pair_nums}
        group_tendons = [t for t in tendons if t["family"] in pair_fams]
        if not group_tendons:
            continue
        weights = [t["area_mm2"] if t["area_mm2"] else 1.0 for t in group_tendons]
        end_vals = [t["end_dp_m"] for t in group_tendons if t["end_dp_m"] is not None]
        mid_vals = [t["midspan_dp_m"] for t in group_tendons if t["midspan_dp_m"] is not None]
        w_end_vals = [(t["end_dp_m"], t["area_mm2"] if t["area_mm2"] else 1.0) for t in group_tendons if t["end_dp_m"] is not None]
        w_mid_vals = [(t["midspan_dp_m"], t["area_mm2"] if t["area_mm2"] else 1.0) for t in group_tendons if t["midspan_dp_m"] is not None]
        group_weight = sum(weights)
        end_avg = sum(v * w for v, w in w_end_vals) / sum(w for _, w in w_end_vals) if w_end_vals else None
        mid_avg = sum(v * w for v, w in w_mid_vals) / sum(w for _, w in w_mid_vals) if w_mid_vals else None
        group_name = f"T{pair_nums[0]}–T{pair_nums[-1]}" if len(pair_nums) > 1 else f"T{pair_nums[0]}"
        group_rows.append({"Group": group_name, "Count": len(group_tendons), "End dp (m)": end_avg, "Midspan dp (m)": mid_avg, "Aps total (mm²)": sum(t["area_mm2"] for t in group_tendons), "Force total (kN)": sum(t["force_kN"] for t in group_tendons)})
        if end_avg is not None and mid_avg is not None:
            total_weight += group_weight
            weighted_end += end_avg * group_weight
            weighted_mid += mid_avg * group_weight

    dp_avg_end = weighted_end / total_weight if total_weight else None
    dp_avg_mid = weighted_mid / total_weight if total_weight else None
    eccentricity_mid = dp_avg_mid - y_t_from_top_m if dp_avg_mid is not None else None

    station_match_status = "MATCH" if station_match_rows and all(r.get("Station match status") == "MATCH" for r in station_match_rows) else "REVIEW"
    qa_rows = [
        {"Check": "Tendon count", "Value": len(tendons), "Status": "MATCH" if len(tendons) == 16 else "REVIEW"},
        {"Check": "General rows", "Value": len(general), "Status": "READY" if len(general) else "MISSING"},
        {"Check": "Vertical profile rows", "Value": len(vertical), "Status": "READY" if len(vertical) else "MISSING"},
        {"Check": "Horizontal profile rows", "Value": len(horizontal), "Status": "READY" if len(horizontal) else "MISSING"},
        {"Check": "Merged profile rows", "Value": len(profile_rows), "Status": "READY" if len(profile_rows) else "MISSING"},
        {"Check": "Vertical/Horizontal station match", "Value": station_match_status, "Status": station_match_status},
        {"Check": "BridgeObj imported", "Value": ", ".join(imported_objs), "Status": "REVIEW" if len(imported_objs) > 1 else "MATCH"},
        {"Check": "BridgeObj adopted", "Value": active_obj, "Status": "MAPPED" if map_to_active_bridge_object and len(imported_objs) > 1 else "MATCH"},
    ]

    return {
        "valid": len(errors) == 0 and len(tendons) > 0,
        "errors": errors,
        "warnings": warnings,
        "active_bridge_object": active_obj,
        "imported_bridge_objects": imported_objs,
        "mapped_to_active_bridge_object": bool(map_to_active_bridge_object),
        "span_m": span_m,
        "midspan_m": mid_m,
        "tendons": tendons,
        "profile_rows": profile_rows,
        "station_match_rows": station_match_rows,
        "group_summary": group_rows,
        "symmetry_rows": symmetry_rows,
        "qa_rows": qa_rows,
        "dp_avg_end_m": dp_avg_end,
        "dp_avg_midspan_m": dp_avg_mid,
        "eccentricity_midspan_m": eccentricity_mid,
        "material": next((t.get("material") for t in tendons if t.get("material")), ""),
        "strand_label": next((t.get("strand_label") for t in tendons if t.get("strand_label") and t.get("strand_label") != "-"), "-"),
        "strand_count": int(round(float(np.mean([t.get("strand_count", 0) for t in tendons if t.get("strand_count", 0)])))) if any(t.get("strand_count", 0) for t in tendons) else 0,
        "strand_size": STRAND_SIZE_LABEL,
        "fpu_mpa": FPU_MPA,
        "jacking_stress_ratio": JACKING_STRESS_RATIO,
        "jacking_stress_mpa": JACKING_STRESS_MPA,
        "Aps_per_tendon_mm2": float(np.mean([t["area_mm2"] for t in tendons if t["area_mm2"]])) if any(t["area_mm2"] for t in tendons) else 0.0,
        "force_per_tendon_kN": float(np.mean([t["force_kN"] for t in tendons if t["force_kN"]])) if any(t["force_kN"] for t in tendons) else 0.0,
        "total_area_mm2": sum(t["area_mm2"] for t in tendons),
        "total_force_kN": sum(t["force_kN"] for t in tendons),
    }


def tendon_model_to_frames(model: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    tendons = pd.DataFrame(model.get("tendons", []))
    groups = pd.DataFrame(model.get("group_summary", []))
    symmetry = pd.DataFrame(model.get("symmetry_rows", []))
    qa = pd.DataFrame(model.get("qa_rows", []))
    return tendons, groups, symmetry, qa


def tendon_model_to_profile_frame(model: dict[str, Any]) -> pd.DataFrame:
    """Return merged vertical + horizontal tendon control-point rows for user-facing review."""
    return pd.DataFrame(model.get("profile_rows", []))


def tendon_model_to_station_match_frame(model: dict[str, Any]) -> pd.DataFrame:
    """Return per-tendon vertical/horizontal station consistency checks."""
    return pd.DataFrame(model.get("station_match_rows", []))


def tendon_points_at_station(model: dict[str, Any], station_m: float) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    tendons = model.get("tendons", [])
    # Build small dataframes for interpolation from the profile lists.
    for t in tendons:
        vprof = pd.DataFrame(t.get("vertical_profile", []))
        hprof = pd.DataFrame(t.get("horizontal_profile", []))
        if vprof.empty or hprof.empty:
            continue
        vprof = vprof.rename(columns={"dp_top_m": "value"})
        hprof = hprof.rename(columns={"horiz_off_m": "value"})
        dp = float(np.interp(station_m, vprof["x_m"].astype(float), vprof["value"].astype(float)))
        off = float(np.interp(station_m, hprof["x_m"].astype(float), hprof["value"].astype(float)))
        rows.append({"Tendon": t.get("tendon"), "Family": t.get("family"), "Side": t.get("side"), "Station (m)": station_m, "dp from top (m)": dp, "HorizOff (m)": off})
    return pd.DataFrame(rows)
