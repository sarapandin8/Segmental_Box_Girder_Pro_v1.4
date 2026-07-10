"""Shared engineering Plotly figure system for Segmental Box Girder Pro.

All app figures should use this module for layout, axes, margins, and Plotly
modebar behavior so drawings, load diagrams, spectra, and result plots feel like
one commercial report-driven application rather than isolated Plotly defaults.
"""

from __future__ import annotations

from typing import Literal

import plotly.graph_objects as go

FigureViewMode = Literal["interactive", "report"]

ENGINEERING_FIGURE_COLORS = {
    "ink": "#0f172a",
    "muted": "#64748b",
    "axis": "#475569",
    "grid": "rgba(148,163,184,0.12)",
    "grid_report": "rgba(148,163,184,0.08)",
    "zeroline": "rgba(37,99,235,0.24)",
    "concrete_line": "#294860",
    "concrete_fill": "rgba(90,124,155,0.28)",
    "void_line": "#294860",
    "centroid": "#be123c",
    "brand": "#175cd3",
    "paper": "#ffffff",
    "plot": "#ffffff",
}

ENGINEERING_MODEBAR_BUTTONS_TO_REMOVE = [
    "lasso2d",
    "select2d",
    "autoScale2d",
    "toggleSpikelines",
]

ENGINEERING_MODEBAR_BUTTONS_TO_ADD = ["drawline", "drawrect", "eraseshape"]

ENGINEERING_REVIEW_CONFIG = {
    "displaylogo": False,
    "displayModeBar": True,
    "responsive": True,
    "scrollZoom": True,
    "modeBarButtonsToRemove": ENGINEERING_MODEBAR_BUTTONS_TO_REMOVE,
    "modeBarButtonsToAdd": ENGINEERING_MODEBAR_BUTTONS_TO_ADD,
    "toImageButtonOptions": {
        "format": "png",
        "filename": "segmental_box_girder_pro_figure",
        "height": 900,
        "width": 1500,
        "scale": 2,
    },
}

ENGINEERING_REPORT_CONFIG = {
    **ENGINEERING_REVIEW_CONFIG,
    "displayModeBar": False,
    "scrollZoom": False,
}

# Backward-compatible alias used by older modules/tests. New code should call
# plotly_config_for_view_mode() so all charts follow one global figure mode.
PLOTLY_CONFIG = ENGINEERING_REVIEW_CONFIG


def normalize_figure_view_mode(view_mode: str | None) -> FigureViewMode:
    """Return a stable internal figure view mode from user-facing labels."""
    text = str(view_mode or "interactive").strip().lower()
    if text.startswith("report"):
        return "report"
    return "interactive"


def plotly_config_for_view_mode(view_mode: str | None) -> dict:
    """Return the shared Plotly config for Interactive review or Report preview."""
    return ENGINEERING_REPORT_CONFIG if normalize_figure_view_mode(view_mode) == "report" else ENGINEERING_REVIEW_CONFIG


def figure_view_badge_text(view_mode: str | None) -> str:
    """Human-readable badge text used consistently in canvas headers."""
    if normalize_figure_view_mode(view_mode) == "report":
        return "Report preview · toolbar hidden"
    return "Interactive review · toolbar on"


def apply_engineering_figure_layout(
    fig: go.Figure,
    *,
    title: str = "",
    x_title: str = "",
    y_title: str = "",
    height: int = 520,
    showlegend: bool = True,
    legend_y: float = 1.02,
    equal_axis: bool = False,
    subtle_grid: bool = True,
    report_ready_title: bool = True,
    margin: dict | None = None,
) -> go.Figure:
    """Apply the global Segmental Box Girder Pro engineering figure theme.

    This intentionally avoids calculation changes. It only standardizes the
    presentation layer: font, axes, grid, margins, legend, background, and hover.
    """
    colors = ENGINEERING_FIGURE_COLORS
    fig.update_layout(
        title={"text": title, "x": 0.01, "xanchor": "left"} if report_ready_title else title,
        height=height,
        paper_bgcolor=colors["paper"],
        plot_bgcolor=colors["plot"],
        margin=margin or dict(l=56, r=26, t=62 if title else 38, b=54),
        font=dict(color=colors["ink"], size=12, family="Arial, sans-serif"),
        hovermode="closest",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=legend_y,
            xanchor="center",
            x=0.5,
            font=dict(size=11, color=colors["ink"]),
            bgcolor="rgba(255,255,255,0.72)",
        ),
        showlegend=showlegend,
    )
    grid_color = colors["grid_report"] if subtle_grid else colors["grid"]
    fig.update_xaxes(
        title_text=x_title,
        showgrid=True,
        gridcolor=grid_color,
        zeroline=True,
        zerolinecolor=colors["zeroline"],
        linecolor="rgba(100,116,139,0.30)",
        tickfont=dict(color=colors["muted"], size=10),
        title_font=dict(color=colors["axis"], size=11),
        showline=True,
        mirror=False,
    )
    yaxis_update = dict(
        title_text=y_title,
        showgrid=True,
        gridcolor=grid_color,
        zeroline=True,
        zerolinecolor="rgba(148,163,184,0.20)",
        linecolor="rgba(100,116,139,0.30)",
        tickfont=dict(color=colors["muted"], size=10),
        title_font=dict(color=colors["axis"], size=11),
        showline=True,
        mirror=False,
    )
    if equal_axis:
        yaxis_update.update(scaleanchor="x", scaleratio=1)
    fig.update_yaxes(**yaxis_update)
    return fig


__all__ = [
    "ENGINEERING_FIGURE_COLORS",
    "ENGINEERING_REVIEW_CONFIG",
    "ENGINEERING_REPORT_CONFIG",
    "PLOTLY_CONFIG",
    "apply_engineering_figure_layout",
    "figure_view_badge_text",
    "normalize_figure_view_mode",
    "plotly_config_for_view_mode",
]
