from __future__ import annotations

from io import StringIO
from typing import Iterable, Mapping, Sequence

import pandas as pd

_TRUE_VALUES = {"1", "true", "yes", "y", "on"}
_FALSE_VALUES = {"0", "false", "no", "n", "off"}


def dataframe_to_csv_text(
    df: pd.DataFrame,
    columns: Sequence[str] | None = None,
    *,
    float_format: str | None = None,
) -> str:
    """Serialize a small editable engineering table without invoking PyArrow."""
    use = df.copy()
    if columns is not None:
        missing = [c for c in columns if c not in use.columns]
        for col in missing:
            use[col] = ""
        use = use[list(columns)]
    return use.to_csv(index=False, lineterminator="\n", float_format=float_format)


def _parse_bool(value: object) -> bool:
    text = str(value).strip().lower()
    if text in _TRUE_VALUES:
        return True
    if text in _FALSE_VALUES:
        return False
    raise ValueError(f"Invalid boolean value {value!r}; use true/false, yes/no, or 1/0.")


def parse_csv_editor_text(
    text: str,
    *,
    columns: Sequence[str],
    numeric_columns: Iterable[str] = (),
    integer_columns: Iterable[str] = (),
    boolean_columns: Iterable[str] = (),
    allowed_values: Mapping[str, Iterable[str]] | None = None,
) -> pd.DataFrame:
    """Parse a text-area CSV editor payload using pandas only.

    This deliberately avoids Streamlit ``st.data_editor`` because that widget
    serializes through PyArrow.  The Streamlit Cloud Python 3.14 / PyArrow 25
    runtime produced a native segmentation fault in that conversion path.
    """
    if not str(text or "").strip():
        return pd.DataFrame(columns=list(columns))
    try:
        df = pd.read_csv(StringIO(text), dtype=object, keep_default_na=False)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Could not parse CSV text: {exc}") from exc

    expected = list(columns)
    missing = [c for c in expected if c not in df.columns]
    extra = [c for c in df.columns if c not in expected]
    if missing or extra:
        details = []
        if missing:
            details.append("missing: " + ", ".join(missing))
        if extra:
            details.append("unexpected: " + ", ".join(extra))
        raise ValueError("CSV columns do not match the required template (" + "; ".join(details) + ").")

    df = df[expected].copy()
    blank_mask = df.apply(lambda row: all(str(v).strip() == "" for v in row), axis=1)
    df = df.loc[~blank_mask].reset_index(drop=True)

    for col in numeric_columns:
        if col not in df.columns:
            continue
        values = pd.to_numeric(df[col], errors="coerce")
        bad = values.isna() & df[col].astype(str).str.strip().ne("")
        if bool(bad.any()):
            row_no = int(bad[bad].index[0]) + 2
            raise ValueError(f"Column {col!r} contains a non-numeric value at CSV row {row_no}.")
        df[col] = values.astype(float)

    for col in integer_columns:
        if col not in df.columns:
            continue
        values = pd.to_numeric(df[col], errors="coerce")
        bad = values.isna() | ((values % 1).abs() > 1e-12)
        if bool(bad.any()):
            row_no = int(bad[bad].index[0]) + 2
            raise ValueError(f"Column {col!r} requires an integer at CSV row {row_no}.")
        df[col] = values.astype(int)

    for col in boolean_columns:
        if col in df.columns:
            try:
                df[col] = df[col].map(_parse_bool).astype(bool)
            except ValueError as exc:
                raise ValueError(f"Column {col!r}: {exc}") from exc

    for col, values in (allowed_values or {}).items():
        if col not in df.columns:
            continue
        allowed = {str(v) for v in values}
        invalid = ~df[col].astype(str).isin(allowed)
        if bool(invalid.any()):
            row_no = int(invalid[invalid].index[0]) + 2
            value = df.loc[invalid, col].iloc[0]
            raise ValueError(f"Column {col!r} has unsupported value {value!r} at CSV row {row_no}.")

    return df
