from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from visualization.figure_system import (
    ENGINEERING_FIGURE_COLORS,
    ENGINEERING_REVIEW_CONFIG,
    apply_engineering_figure_layout,
)

PLOTLY_SECTION_CONFIG = ENGINEERING_REVIEW_CONFIG


def _closed_xy(g: pd.DataFrame, *, x_shift: float = 0.0) -> tuple[list[float], list[float]]:
    xs = (g["x_mm"].astype(float) - x_shift).tolist()
    ys = g["y_mm"].astype(float).tolist()
    if xs and ys and (xs[0] != xs[-1] or ys[0] != ys[-1]):
        xs.append(xs[0])
        ys.append(ys[0])
    return xs, ys


def _major_point_mask(g: pd.DataFrame) -> list[bool]:
    """Return a sparse point-label mask to reduce overlapping labels."""
    if g.empty:
        return []
    xs = g["x_mm"].astype(float)
    ys = g["y_mm"].astype(float)
    extremes = set()
    for series in [xs, ys]:
        extremes.add(series.idxmin())
        extremes.add(series.idxmax())
    mask = []
    for pos, idx in enumerate(g.index):
        mask.append(idx in extremes or pos == 0 or pos == len(g) - 1 or pos % 3 == 0)
    return mask


def _dimension_label(
    fig: go.Figure,
    *,
    x: float,
    y: float,
    text: str,
    textangle: int = 0,
    color: str = "#64748b",
    size: int = 12,
) -> None:
    fig.add_annotation(
        x=x,
        y=y,
        text=text,
        textangle=textangle,
        showarrow=False,
        align="center",
        bgcolor="rgba(255,255,255,0.96)",
        bordercolor="rgba(100,116,139,0.50)",
        borderwidth=1,
        borderpad=4,
        font={"color": color, "size": size},
    )


def _tick_shape(x0: float, y0: float, x1: float, y1: float, color: str) -> dict:
    return {"type": "line", "x0": x0, "y0": y0, "x1": x1, "y1": y1, "line": {"color": color, "width": 1.35}}


def _add_horizontal_dimension(
    fig: go.Figure,
    *,
    x0: float,
    x1: float,
    y: float,
    ext_to_y: float,
    label: str,
    color: str,
) -> None:
    tick = 52.0
    fig.add_shape(type="line", x0=x0, y0=ext_to_y, x1=x0, y1=y, line={"color": color, "width": 1.15})
    fig.add_shape(type="line", x0=x1, y0=ext_to_y, x1=x1, y1=y, line={"color": color, "width": 1.15})
    fig.add_shape(type="line", x0=x0, y0=y, x1=x1, y1=y, line={"color": color, "width": 1.45})
    fig.add_shape(**_tick_shape(x0 - tick, y - tick, x0 + tick, y + tick, color))
    fig.add_shape(**_tick_shape(x1 - tick, y - tick, x1 + tick, y + tick, color))
    _dimension_label(fig, x=0.5 * (x0 + x1), y=y + 88.0, text=label, color=color, size=12)


def _add_vertical_dimension(
    fig: go.Figure,
    *,
    x: float,
    y0: float,
    y1: float,
    ext_to_x: float,
    label: str,
    color: str,
    label_side: str = "left",
) -> None:
    tick = 52.0
    fig.add_shape(type="line", x0=ext_to_x, y0=y0, x1=x, y1=y0, line={"color": color, "width": 1.15})
    fig.add_shape(type="line", x0=ext_to_x, y0=y1, x1=x, y1=y1, line={"color": color, "width": 1.15})
    fig.add_shape(type="line", x0=x, y0=y0, x1=x, y1=y1, line={"color": color, "width": 1.45})
    fig.add_shape(**_tick_shape(x - tick, y0 - tick, x + tick, y0 + tick, color))
    fig.add_shape(**_tick_shape(x - tick, y1 - tick, x + tick, y1 + tick, color))
    dx = -112.0 if label_side == "left" else 112.0
    _dimension_label(fig, x=x + dx, y=0.5 * (y0 + y1), text=label, textangle=-90, color=color, size=12)


def _section_display_bounds(coords: pd.DataFrame, props: dict, origin_mode: str) -> dict[str, float]:
    bounds = props.get("bounds_mm", {}) if props else {}
    xmin = float(bounds.get("xmin", coords["x_mm"].min() if coords is not None and not coords.empty else 0.0))
    xmax = float(bounds.get("xmax", coords["x_mm"].max() if coords is not None and not coords.empty else 0.0))
    ymin = float(bounds.get("ymin", coords["y_mm"].min() if coords is not None and not coords.empty else 0.0))
    ymax = float(bounds.get("ymax", coords["y_mm"].max() if coords is not None and not coords.empty else 0.0))
    x_shift = 0.5 * (xmin + xmax) if str(origin_mode).lower().startswith("center") else 0.0
    return {
        "xmin_raw": xmin,
        "xmax_raw": xmax,
        "xmin": xmin - x_shift,
        "xmax": xmax - x_shift,
        "ymin": ymin,
        "ymax": ymax,
        "x_shift": x_shift,
        "width": xmax - xmin,
        "depth": ymax - ymin,
    }


def _apply_section_preview_viewport(
    fig: go.Figure,
    coords: pd.DataFrame,
    props: dict,
    *,
    origin_mode: str,
    dimension_mode: str,
) -> go.Figure:
    if not props.get("valid"):
        return fig
    b = _section_display_bounds(coords, props, origin_mode)
    width = max(float(b["width"]), 1.0)
    depth = max(float(b["depth"]), 1.0)
    mode = str(dimension_mode or "clean").strip().lower()
    include_dimensions = not mode.startswith("hide")
    full_dimensions = mode.startswith("full")
    left_pad = max(620.0, 0.09 * width) if include_dimensions else max(380.0, 0.05 * width)
    right_pad = max(620.0, 0.09 * width) * (1.38 if full_dimensions else 1.05) if include_dimensions else max(380.0, 0.05 * width)
    top_pad = max(560.0, 0.22 * depth) if include_dimensions else max(300.0, 0.12 * depth)
    bottom_pad = max(230.0, 0.09 * depth) if include_dimensions else max(170.0, 0.07 * depth)
    fig.update_xaxes(range=[b["xmin"] - left_pad, b["xmax"] + right_pad], autorange=False)
    fig.update_yaxes(range=[b["ymin"] - bottom_pad, b["ymax"] + top_pad], autorange=False, scaleanchor=None, scaleratio=None)
    return fig


def _add_section_dimension_layer(
    fig: go.Figure,
    coords: pd.DataFrame,
    props: dict,
    *,
    origin_mode: str,
    dimension_mode: str,
) -> go.Figure:
    """Add the shared engineering dimension grammar to the section preview.

    Modes mirror the tendon overlay figure system:
    - clean: B, D, CL if applicable, and centroid guides only.
    - full dimensions: clean plus y_cg and y_t fiber dimensions.
    - hide dimensions: no dimension guide layer.
    """
    mode = str(dimension_mode or "clean").strip().lower()
    if mode.startswith("hide") or not props.get("valid"):
        return _apply_section_preview_viewport(fig, coords, props, origin_mode=origin_mode, dimension_mode=mode)

    b = _section_display_bounds(coords, props, origin_mode)
    xmin = b["xmin"]
    xmax = b["xmax"]
    ymin = b["ymin"]
    ymax = b["ymax"]
    width = max(float(b["width"]), 1.0)
    depth = max(float(b["depth"]), 1.0)
    cx = float(props.get("cx_mm", 0.5 * (b["xmin_raw"] + b["xmax_raw"]))) - b["x_shift"]
    cy = float(props.get("cy_mm", 0.5 * (ymin + ymax)))

    dim_color = "#66768c"
    cl_color = "#2563eb"
    cg_color = ENGINEERING_FIGURE_COLORS["centroid"]
    cg_line_color = "rgba(190,18,60,0.50)"
    y_dim = ymax + max(360.0, 0.17 * depth)
    x_dim_left = xmin - max(520.0, 0.075 * width)
    x_dim_right = xmax + max(520.0, 0.065 * width)

    _add_horizontal_dimension(fig, x0=xmin, x1=xmax, y=y_dim, ext_to_y=ymax + 0.018 * depth, label=f"B = {width:.0f} mm", color=dim_color)
    _add_vertical_dimension(fig, x=x_dim_left, y0=ymin, y1=ymax, ext_to_x=xmin - 0.018 * width, label=f"D = {depth:.0f} mm", color=dim_color, label_side="left")

    if str(origin_mode).lower().startswith("center"):
        fig.add_shape(type="line", x0=0, y0=ymin - 0.06 * depth, x1=0, y1=ymax + 0.065 * depth, line={"color": "rgba(37,99,235,0.48)", "width": 1.05, "dash": "dash"})
        _dimension_label(fig, x=0, y=ymax + 0.085 * depth, text="CL", color=cl_color, size=11)

    fig.add_shape(type="line", x0=xmin, y0=cy, x1=xmax, y1=cy, line={"color": cg_line_color, "width": 0.95, "dash": "dot"})
    fig.add_shape(type="line", x0=cx, y0=ymin, x1=cx, y1=ymax, line={"color": cg_line_color, "width": 0.95, "dash": "dot"})
    _dimension_label(fig, x=cx + 0.070 * width, y=cy + 0.055 * depth, text="CG", color=cg_color, size=11)

    if mode.startswith("full"):
        ycg_mm = float(props.get("ycg_from_bottom_m", cy / 1000.0)) * 1000.0
        yt_mm = float(props.get("yt_from_top_m", max(ymax - cy, 0.0) / 1000.0)) * 1000.0
        _add_vertical_dimension(fig, x=x_dim_right, y0=ymin, y1=cy, ext_to_x=xmax + 0.018 * width, label=f"y_cg = {ycg_mm:.0f} mm", color=dim_color, label_side="right")
        _add_vertical_dimension(fig, x=x_dim_right + 0.34 * max(520.0, 0.065 * width), y0=cy, y1=ymax, ext_to_x=xmax + 0.018 * width, label=f"y_t = {yt_mm:.0f} mm", color=dim_color, label_side="right")

    return _apply_section_preview_viewport(fig, coords, props, origin_mode=origin_mode, dimension_mode=mode)


def section_polygon_figure(
    coords: pd.DataFrame,
    props: dict,
    *,
    point_label_mode: str = "major",
    show_dimensions: bool = True,
    origin_mode: str = "csibridge",
    dimension_mode: str | None = None,
) -> go.Figure:
    fig = go.Figure()
    if coords is None or coords.empty:
        apply_engineering_figure_layout(fig, title="No section coordinates loaded", height=520, showlegend=False)
        return fig

    bounds = props.get("bounds_mm", {}) if props else {}
    xmin = float(bounds.get("xmin", coords["x_mm"].min()))
    xmax = float(bounds.get("xmax", coords["x_mm"].max()))
    x_shift = 0.0
    x_title = "x (mm)"
    if str(origin_mode).lower().startswith("center"):
        x_shift = 0.5 * (xmin + xmax)
        x_title = "x (mm, CL = 0)"

    # Outer loops first, then holes.
    for loop_name, g in coords.groupby("loop_name", sort=False):
        loop_type = str(g["loop_type"].iloc[0]) if "loop_type" in g else "unknown"
        xs, ys = _closed_xy(g, x_shift=x_shift)
        fillcolor = ENGINEERING_FIGURE_COLORS["concrete_fill"] if loop_type == "outer" else "rgba(255, 255, 255, 0.96)"
        linecolor = ENGINEERING_FIGURE_COLORS["concrete_line"]
        fig.add_trace(
            go.Scatter(
                x=xs,
                y=ys,
                mode="lines+markers" if point_label_mode != "hide" else "lines",
                fill="toself",
                fillcolor=fillcolor,
                line=dict(color=linecolor, width=2.5),
                marker=dict(size=5, color=linecolor),
                name=str(loop_name),
                hovertemplate="x=%{x:.0f} mm<br>y=%{y:.0f} mm<extra>" + str(loop_name) + "</extra>",
            )
        )
        if point_label_mode != "hide":
            label_df = g.copy()
            if point_label_mode == "major":
                mask = _major_point_mask(label_df)
                label_df = label_df.loc[mask]
            fig.add_trace(
                go.Scatter(
                    x=label_df["x_mm"].astype(float) - x_shift,
                    y=label_df["y_mm"],
                    mode="text",
                    text=label_df["point_no"].astype(str),
                    textposition="top center",
                    textfont=dict(size=9, color="#64748b"),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

    if props.get("valid"):
        cx_raw = float(props["cx_mm"])
        cx = cx_raw - x_shift
        cy = props["cy_mm"]
        fig.add_trace(
            go.Scatter(
                x=[cx],
                y=[cy],
                mode="markers",
                marker=dict(size=12, symbol="cross", color=ENGINEERING_FIGURE_COLORS["centroid"]),
                name="Centroid",
                hovertemplate="Centroid<br>x=%{x:.1f} mm<br>y=%{y:.1f} mm<extra></extra>",
            )
        )
        dim_mode = dimension_mode if dimension_mode is not None else ("clean" if show_dimensions else "hide")
        fig = _add_section_dimension_layer(fig, coords, props, origin_mode=origin_mode, dimension_mode=dim_mode)

    apply_engineering_figure_layout(
        fig,
        title="",
        x_title=x_title,
        y_title="y (mm)",
        height=540,
        showlegend=True,
        equal_axis=False,
        margin=dict(l=48, r=18, t=38, b=48),
    )
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.03, xanchor="center", x=0.5))
    fig.update_xaxes(gridcolor="rgba(148,163,184,0.09)")
    fig.update_yaxes(gridcolor="rgba(148,163,184,0.09)")
    return fig
