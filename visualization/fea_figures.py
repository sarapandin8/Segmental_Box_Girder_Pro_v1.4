"""Commercial FEA result-review figures for Segmental Box Girder Pro.

The figures in this module are review-only. They visualize source-traced scalar
component envelopes imported from CSiBridge; they do not create simultaneous
force vectors and they do not feed the downstream design checks.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

import pandas as pd
import plotly.graph_objects as go

from visualization.figure_system import (
    ENGINEERING_FIGURE_COLORS,
    apply_engineering_figure_layout,
)

FORCE_COMPONENT_META: dict[str, dict[str, str]] = {
    "P": {
        "title": "P (Axial)",
        "section": "5.2.1",
        "unit": "kN",
        "axis": "Axial force, P (kN)",
        "mapping": "P → Axial",
        "upper": "P max",
        "lower": "P min",
        "governing": "Governing |P| (Axial)",
        "metric": "GOVERNING |P| (AXIAL)",
    },
    "V2": {
        "title": "V2 (Vy)",
        "section": "5.2.2",
        "unit": "kN",
        "axis": "Vertical shear, V2 = Vy (kN)",
        "mapping": "V2 → Vy",
        "upper": "V2 max",
        "lower": "V2 min",
        "governing": "Governing |V2| (Vy)",
        "metric": "GOVERNING |V2| (Vy)",
    },
    "T": {
        "title": "T (Torsion)",
        "section": "5.2.3",
        "unit": "kN·m",
        "axis": "Torsion, T (kN·m)",
        "mapping": "T → Torsion",
        "upper": "T max",
        "lower": "T min",
        "governing": "Governing |T| (Torsion)",
        "metric": "GOVERNING |T| (TORSION)",
    },
    "M3": {
        "title": "M3 (Mx)",
        "section": "5.2.4",
        "unit": "kN·m",
        "axis": "Bending moment, M3 = Mx (kN·m)",
        "mapping": "M3 → Mx",
        "upper": "M3 max",
        "lower": "M3 min",
        "governing": "Governing |M3| (Mx)",
        "metric": "GOVERNING |M3| (Mx)",
    },
}



def _source_text(source: Any) -> str:
    if not isinstance(source, dict):
        return "-"
    case = str(source.get("OutputCase") or "-")
    step = str(source.get("StepType") or "Single")
    state = str(source.get("SourceState") or "-")
    row = source.get("SourceRow")
    row_text = f" · row {int(row)}" if row not in (None, "") else ""
    return f"{case} / {step} · {state}{row_text}"


def component_envelope_frame(payload: dict[str, Any], component: str) -> pd.DataFrame:
    """Return one source-traced upper/lower scalar envelope row per SectCutNum."""
    if component not in FORCE_COMPONENT_META:
        raise ValueError(f"Unsupported FEA force component: {component}")
    rows: list[dict[str, Any]] = []
    for envelope in payload.get("envelopes", []):
        lower = float(envelope[f"{component}_min"])
        upper = float(envelope[f"{component}_max"])
        governing_side = "MAX" if abs(upper) >= abs(lower) else "MIN"
        governing_value = upper if governing_side == "MAX" else lower
        governing_source = envelope.get(f"{component}_{governing_side.lower()}_source")
        rows.append(
            {
                "SectCutNum": int(envelope["SectCutNum"]),
                "Distance": float(envelope["Distance"]),
                "LocType": str(envelope["LocType"]),
                "CandidateRows": int(envelope.get("CandidateRows", 0)),
                "Lower": lower,
                "LowerSource": _source_text(envelope.get(f"{component}_min_source")),
                "Upper": upper,
                "UpperSource": _source_text(envelope.get(f"{component}_max_source")),
                "GoverningAbs": abs(governing_value),
                "GoverningValue": governing_value,
                "GoverningSide": governing_side,
                "GoverningSource": _source_text(governing_source),
            }
        )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("SectCutNum").reset_index(drop=True)


def governing_component_envelope(payload: dict[str, Any], component: str) -> dict[str, Any]:
    """Return the global maximum-absolute scalar envelope point for a component."""
    frame = component_envelope_frame(payload, component)
    if frame.empty:
        return {}
    row = frame.loc[frame["GoverningAbs"].idxmax()]
    return {
        "component": component,
        "value": float(row["GoverningValue"]),
        "absolute": float(row["GoverningAbs"]),
        "side": str(row["GoverningSide"]),
        "sect_cut_num": int(row["SectCutNum"]),
        "distance_m": float(row["Distance"]),
        "loc_type": str(row["LocType"]),
        "source": str(row["GoverningSource"]),
    }


def _source_case_label(source: Any) -> str:
    """Return a row-independent source label for dominance counts."""
    if not isinstance(source, dict):
        return "-"
    case = str(source.get("OutputCase") or "-")
    step = str(source.get("StepType") or "Single")
    state = str(source.get("SourceState") or "-")
    return f"{case} / {step} · {state}"


def dominant_component_sources(payload: dict[str, Any], component: str) -> dict[str, dict[str, Any]]:
    """Return the most frequent upper/lower source across section cuts.

    Source-row numbers are intentionally excluded so repeated governing output
    cases can be recognized across the full span.
    """
    if component not in FORCE_COMPONENT_META:
        raise ValueError(f"Unsupported FEA force component: {component}")
    envelopes = payload.get("envelopes", []) if isinstance(payload, dict) else []
    result: dict[str, dict[str, Any]] = {}
    for side, suffix in (("max", "max_source"), ("min", "min_source")):
        labels = [
            _source_case_label(row.get(f"{component}_{suffix}"))
            for row in envelopes
            if isinstance(row, dict)
        ]
        labels = [label for label in labels if label != "-"]
        if not labels:
            result[side] = {"label": "-", "count": 0, "total": 0, "percentage": 0.0}
            continue
        label, count = Counter(labels).most_common(1)[0]
        total = len(labels)
        result[side] = {
            "label": label,
            "count": int(count),
            "total": int(total),
            "percentage": 100.0 * float(count) / float(total),
        }
    return result


def uls_component_envelope_figure(
    payload: dict[str, Any],
    component: str,
    *,
    bridge_object: str = "",
) -> go.Figure:
    """Build a commercial ULS scalar-envelope review chart.

    The upper and lower traces are independent scalar extrema. The function does
    not pair P-M3 or V2-T and therefore preserves the source-semantics guard.
    """
    meta = FORCE_COMPONENT_META.get(component)
    if meta is None:
        raise ValueError(f"Unsupported FEA force component: {component}")
    frame = component_envelope_frame(payload, component)
    fig = go.Figure()
    if frame.empty:
        return apply_engineering_figure_layout(
            fig,
            title=f"ULS {meta['title']} Envelope — no source data",
            x_title="Distance from left end of span (m)",
            y_title=meta["axis"],
            height=560,
            showlegend=False,
        )

    common_custom = frame[["SectCutNum", "LocType"]].to_numpy()
    upper_custom = [
        [int(cut), str(loc), str(source)]
        for cut, loc, source in zip(frame["SectCutNum"], frame["LocType"], frame["UpperSource"])
    ]
    lower_custom = [
        [int(cut), str(loc), str(source)]
        for cut, loc, source in zip(frame["SectCutNum"], frame["LocType"], frame["LowerSource"])
    ]

    fig.add_trace(
        go.Scatter(
            x=frame["Distance"],
            y=frame["Upper"],
            mode="lines+markers",
            name=meta["upper"],
            line=dict(color="#1f77b4", width=2.5),
            marker=dict(size=5, color="#1f77b4"),
            customdata=upper_custom,
            hovertemplate=(
                f"<b>{meta['upper']} · {meta['title']}</b><br>"
                "x = %{x:.3f} m<br>"
                "SectCutNum = %{customdata[0]} · %{customdata[1]}<br>"
                f"Value = %{{y:,.3f}} {meta['unit']}<br>"
                "Source = %{customdata[2]}<extra></extra>"
            ),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=frame["Distance"],
            y=frame["Lower"],
            mode="lines+markers",
            name=meta["lower"],
            line=dict(color="#ff2b2b", width=2.5, dash="dash"),
            marker=dict(size=5, color="#ff2b2b", symbol="circle-open"),
            customdata=lower_custom,
            hovertemplate=(
                f"<b>{meta['lower']} · {meta['title']}</b><br>"
                "x = %{x:.3f} m<br>"
                "SectCutNum = %{customdata[0]} · %{customdata[1]}<br>"
                f"Value = %{{y:,.3f}} {meta['unit']}<br>"
                "Source = %{customdata[2]}<extra></extra>"
            ),
        )
    )

    governing = governing_component_envelope(payload, component)
    if governing:
        fig.add_trace(
            go.Scatter(
                x=[governing["distance_m"]],
                y=[governing["value"]],
                mode="markers",
                name=meta["governing"],
                marker=dict(size=10, color="#111111", symbol="circle"),
                customdata=[[
                    governing["sect_cut_num"],
                    governing["loc_type"],
                    governing["source"],
                ]],
                hovertemplate=(
                    f"<b>{meta['governing']}</b><br>"
                    "x = %{x:.3f} m<br>"
                    "SectCutNum = %{customdata[0]} · %{customdata[1]}<br>"
                    f"Value = %{{y:,.3f}} {meta['unit']}<br>"
                    "Source = %{customdata[2]}<extra></extra>"
                ),
            )
        )
        fig.add_annotation(
            x=governing["distance_m"],
            y=governing["value"],
            text=meta["governing"],
            showarrow=True,
            arrowhead=2,
            ax=0,
            ay=-34 if governing["value"] >= 0 else 34,
            font=dict(size=11, color=ENGINEERING_FIGURE_COLORS["axis"]),
            bgcolor="rgba(255,255,255,0.86)",
            bordercolor="rgba(148,163,184,0.45)",
            borderwidth=1,
            borderpad=4,
        )

    span_text = bridge_object or ", ".join(payload.get("bridge_objects", [])) or "Active span"
    title = (
        f"<b>ULS {meta['title']} Envelope</b>"
        f"<br><span style='font-size:12px'>CSiBridge scalar component envelope · {meta['mapping']} · {span_text}</span>"
    )
    apply_engineering_figure_layout(
        fig,
        title=title,
        x_title="Distance from left end of span (m)",
        y_title=meta["axis"],
        height=560,
        showlegend=True,
        subtle_grid=False,
        margin=dict(l=72, r=34, t=84, b=112),
    )
    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor="center", y=0.97, yanchor="top"),
        hovermode="closest",
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.20,
            xanchor="center",
            x=0.5,
            font=dict(size=11),
            bgcolor="rgba(255,255,255,0.92)",
            bordercolor="rgba(148,163,184,0.35)",
            borderwidth=1,
        ),
    )
    fig.update_xaxes(
        range=[float(frame["Distance"].min()), float(frame["Distance"].max())],
        tickformat=".3~f",
    )
    return fig


__all__ = [
    "FORCE_COMPONENT_META",
    "dominant_component_sources",
    "component_envelope_frame",
    "governing_component_envelope",
    "uls_component_envelope_figure",
]
