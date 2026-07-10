from __future__ import annotations

from math import isfinite
from typing import Any

import pandas as pd

DASH = "—"


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        v = float(value)
        return v if isfinite(v) else None
    try:
        text = str(value).strip().replace(",", "")
        if text in {"", DASH, "-", "N.A.", "N/A", "Auto", "parameters"}:
            return None
        return float(text)
    except Exception:
        return None


def _is_integer_like(value: float) -> bool:
    return abs(value - round(value)) < 1e-9


def format_engineering_value(value: Any, unit: str | None = None, *, quantity: str | None = None) -> str:
    """Format engineering values consistently for UI/report tables.

    Global display rules requested by the project owner:
    - Force/load and moment/torque: no decimals.
    - Equivalent line/distributed load in kN/m: 2 decimals for report/FEA summaries.
    - Stress in MPa: 2 decimals.
    - Length in mm: no decimals; length in m: 3 decimals.
    - Areas in mm²: no decimals; m²/m³/m⁴: 3 decimals.
    - Coefficients, ratios, g, DCR/utilization: 3 decimals.
    - Counts: no decimals.
    """
    if isinstance(value, str):
        # Preserve mixed expressions such as "U20 × 1.20" or "1000 / 25.0".
        return value
    v = _to_float(value)
    if v is None:
        return str(value) if value is not None else DASH

    unit_norm = (unit or "").strip().replace(" ", "")
    q = (quantity or "").strip().lower()

    # Counts / discrete quantities.
    if q in {"count", "integer", "number", "tendon", "strand", "track", "zone"}:
        return f"{v:,.0f}"

    # Force / load.
    if unit_norm in {"kN", "N", "kips", "ton", "tf"} or q in {"force", "load", "reaction"}:
        return f"{v:,.0f}"

    # Moment / torque.
    if unit_norm in {"kN·m", "kN-m", "kNm", "N·mm", "N-mm", "Nmm"} or q in {"moment", "torque"}:
        return f"{v:,.0f}"

    # Distributed/line loads are usually reported with two decimals in BG40 report tables.
    if unit_norm in {"kN/m", "N/mm", "kN/m²", "kPa"} or q in {"line_load", "distributed_load"}:
        return f"{v:,.2f}"

    # Stress.
    if unit_norm in {"MPa", "N/mm²", "N/mm2"} or q == "stress":
        return f"{v:,.2f}"

    # Length.
    if unit_norm == "mm":
        return f"{v:,.0f}"
    if unit_norm == "m":
        return f"{v:,.3f}"

    # Geometry / section properties.
    if unit_norm in {"mm²", "mm2"}:
        return f"{v:,.0f}"
    if unit_norm in {"m²", "m2", "m³", "m3", "m⁴", "m4"}:
        return f"{v:,.3f}"
    if unit_norm in {"mm²/mm", "mm2/mm"}:
        return f"{v:,.3f}"

    # Seismic / factors / dimensionless.
    if unit_norm in {"-", "g", "%LL", "ratio", "factor"} or q in {"coefficient", "factor", "dcr", "utilization", "ratio"}:
        return f"{v:,.3f}"

    if unit_norm == "%":
        return f"{v:,.1f}"

    # Conservative generic fallback for table values.
    if _is_integer_like(v):
        return f"{v:,.0f}"
    return f"{v:,.3f}"


def format_engineering_table(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with numeric cells formatted for display only.

    It recognizes common column layouts used in this app:
    - Value + Unit
    - Value + Unit / source
    - Stress + Unit
    - Mu / φMn / DCR
    """
    out = df.copy()

    unit_col = None
    for cand in ["Unit", "Unit / source", "unit", "Units", "Unit/source"]:
        if cand in out.columns:
            unit_col = cand
            break

    value_like_cols = [c for c in out.columns if c.lower() in {"value", "stress", "mu", "φmn", "dcr", "utilization"}]
    if unit_col and "Value" in out.columns:
        out["Value"] = [format_engineering_value(v, u) for v, u in zip(out["Value"], out[unit_col])]
    if unit_col and "Stress" in out.columns:
        out["Stress"] = [format_engineering_value(v, u, quantity="stress") for v, u in zip(out["Stress"], out[unit_col])]

    for col in value_like_cols:
        if col in {"Value", "Stress"}:
            continue
        q = "dcr" if col.lower() in {"dcr", "utilization"} else None
        unit = "kN·m" if col in {"Mu", "φMn"} else "-"
        out[col] = [format_engineering_value(v, unit, quantity=q) for v in out[col]]

    # Common FEA summary table uses mixed units and a text Value column.
    if "Unit" in out.columns and "Value" in out.columns:
        out["Value"] = [format_engineering_value(v, u) for v, u in zip(out["Value"], out["Unit"])]

    return out
