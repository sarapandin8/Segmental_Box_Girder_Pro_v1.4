from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "aashto_lrfd_2014"
OPERATIONAL_CATEGORIES = ["Critical", "Essential", "Other"]
CATEGORY_KEY = {"Critical": "critical", "Essential": "essential", "Other": "other"}
DEFAULT_OPERATIONAL_CATEGORY = "Essential"
DEFAULT_SUBSTRUCTURE_KEY = "single_column_or_pier"
DEFAULT_IMPORTANCE_PRESET = "bg40_default"


def _read_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / name)


def load_substructure_r_table() -> pd.DataFrame:
    return _read_csv("response_modification_factors_substructures_3_10_7_1_1.csv")


def load_connection_r_table() -> pd.DataFrame:
    return _read_csv("response_modification_factors_connections_3_10_7_1_2.csv")


def load_importance_presets() -> pd.DataFrame:
    return _read_csv("bridge_importance_factor_presets.csv")


def substructure_options() -> List[str]:
    return load_substructure_r_table()["substructure_label"].tolist()


def substructure_key_from_label(label: str) -> str:
    df = load_substructure_r_table()
    hit = df[df["substructure_label"] == label]
    if hit.empty:
        raise ValueError(f"Unknown AASHTO substructure type: {label}")
    return str(hit.iloc[0]["substructure_key"])


def substructure_label_from_key(key: str) -> str:
    df = load_substructure_r_table()
    hit = df[df["substructure_key"] == key]
    if hit.empty:
        return substructure_label_from_key(DEFAULT_SUBSTRUCTURE_KEY)
    return str(hit.iloc[0]["substructure_label"])


def recommended_substructure_r(substructure_key: str, operational_category: str) -> Dict[str, object]:
    category = operational_category if operational_category in CATEGORY_KEY else DEFAULT_OPERATIONAL_CATEGORY
    col = CATEGORY_KEY[category]
    df = load_substructure_r_table()
    hit = df[df["substructure_key"] == substructure_key]
    if hit.empty:
        hit = df[df["substructure_key"] == DEFAULT_SUBSTRUCTURE_KEY]
    row = hit.iloc[0].to_dict()
    return {
        "R": float(row[col]),
        "operational_category": category,
        "substructure_key": str(row["substructure_key"]),
        "substructure_label": str(row["substructure_label"]),
        "source_reference": str(row["source_reference"]),
        "note": str(row.get("note", "")),
    }


def importance_preset_options() -> List[str]:
    return load_importance_presets()["preset_label"].tolist()


def importance_preset_key_from_label(label: str) -> str:
    df = load_importance_presets()
    hit = df[df["preset_label"] == label]
    if hit.empty:
        raise ValueError(f"Unknown importance preset: {label}")
    return str(hit.iloc[0]["preset_key"])


def importance_preset_label_from_key(key: str) -> str:
    df = load_importance_presets()
    hit = df[df["preset_key"] == key]
    if hit.empty:
        hit = df[df["preset_key"] == DEFAULT_IMPORTANCE_PRESET]
    return str(hit.iloc[0]["preset_label"])


def importance_value_from_preset(key: str, manual_value: float | None = None) -> Dict[str, object]:
    df = load_importance_presets()
    hit = df[df["preset_key"] == key]
    if hit.empty:
        hit = df[df["preset_key"] == DEFAULT_IMPORTANCE_PRESET]
    row = hit.iloc[0].to_dict()
    if str(row["preset_key"]) == "manual":
        if manual_value is None:
            raise ValueError("Manual importance preset requires a manual_value.")
        return {
            "I": float(manual_value),
            "preset_key": "manual",
            "preset_label": str(row["preset_label"]),
            "source_reference": str(row["source_reference"]),
            "note": str(row.get("note", "")),
        }
    return {
        "I": float(row["I_value"]),
        "preset_key": str(row["preset_key"]),
        "preset_label": str(row["preset_label"]),
        "source_reference": str(row["source_reference"]),
        "note": str(row.get("note", "")),
    }
