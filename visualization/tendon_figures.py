"""Plotly figures for CSiBridge tendon-layout imports."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from visualization.figure_system import (
    ENGINEERING_REPORT_CONFIG,
    ENGINEERING_REVIEW_CONFIG,
    apply_engineering_figure_layout,
)


FAMILY_COLORS = [
    "#2563eb", "#16a34a", "#d97706", "#7c3aed",
    "#0891b2", "#db2777", "#65a30d", "#dc2626",
]


def _family_index(family: str) -> int:
    import re
    m = re.search(r"(\d+)", str(family or ""))
    return (int(m.group(1)) - 1) if m else 0


def _family_color(family: str) -> str:
    return FAMILY_COLORS[_family_index(family) % len(FAMILY_COLORS)]


def _label_for_mode(row: dict, label_mode: str) -> str:
    mode = str(label_mode or "hide").lower()
    if mode.startswith("all"):
        return str(row.get("Tendon", row.get("tendon", "")))
    if mode.startswith("family"):
        return str(row.get("Family", row.get("family", "")))
    return ""

PLOTLY_TENDON_CONFIG = ENGINEERING_REVIEW_CONFIG

# Global figure system aliases retained for existing app imports/tests.
# Interactive review keeps the Plotly modebar for zoom/pan/reset/camera checks.
# Report preview hides the modebar so exported/report figures stay clean.
# Legacy explicit settings retained in comments for regression trace: "displayModeBar": True / "displayModeBar": False
PLOTLY_TENDON_REVIEW_CONFIG = ENGINEERING_REVIEW_CONFIG
PLOTLY_TENDON_REPORT_CONFIG = ENGINEERING_REPORT_CONFIG
PLOTLY_TENDON_CANVAS_CONFIG = PLOTLY_TENDON_REPORT_CONFIG



def _style_layout(fig: go.Figure, title: str, x_title: str, y_title: str, *, showlegend: bool = True) -> go.Figure:
    return apply_engineering_figure_layout(
        fig,
        title=title,
        x_title=x_title,
        y_title=y_title,
        height=520,
        showlegend=showlegend,
        margin=dict(l=56, r=26, t=56 if title else 34, b=54),
    )


def _tendon_passes_filter(
    tendon: dict,
    *,
    family_filter: str | None = None,
    side_filter: str | None = None,
    tendon_filter: str | None = None,
) -> bool:
    fam = str(tendon.get("family") or tendon.get("Family") or "")
    side = str(tendon.get("side") or tendon.get("Side") or "")
    tendon_name = str(tendon.get("tendon") or tendon.get("Tendon") or "")
    family_text = str(family_filter or "All families")
    side_text = str(side_filter or "Both sides")
    tendon_text = str(tendon_filter or "All tendons")
    if family_text != "All families" and fam != family_text:
        return False
    if side_text in {"Left only", "L"} and side != "L":
        return False
    if side_text in {"Right only", "R"} and side != "R":
        return False
    if tendon_text not in {"All tendons", "", "None"} and tendon_name != tendon_text:
        return False
    return True


def _side_line_dash(side: str) -> str:
    return "solid" if str(side).upper() != "R" else "dot"


def tendon_elevation_figure(
    model: dict,
    *,
    show_labels: bool = False,
    family_filter: str | None = None,
    side_filter: str | None = None,
    showlegend: bool = False,
) -> go.Figure:
    fig = go.Figure()
    for t in model.get("tendons", []):
        if not _tendon_passes_filter(t, family_filter=family_filter, side_filter=side_filter):
            continue
        prof = pd.DataFrame(t.get("vertical_profile", []))
        if prof.empty:
            continue
        text = [t.get("tendon", "") if show_labels else "" for _ in range(len(prof))]
        family = str(t.get("family", ""))
        side = str(t.get("side", ""))
        fig.add_trace(
            go.Scatter(
                x=prof["x_m"],
                y=prof["dp_top_m"],
                mode="lines+markers+text" if show_labels else "lines+markers",
                name=t.get("tendon", ""),
                legendgroup=family,
                text=text,
                textposition="top center",
                hovertemplate="%{fullData.name}<br>x = %{x:.3f} m<br>dp = %{y:.3f} m<extra></extra>",
                line=dict(width=2.2, color=_family_color(family), dash=_side_line_dash(side)),
                marker=dict(size=6, color=_family_color(family), line=dict(width=0.8, color="#0f172a")),
            )
        )
    span = float(model.get("span_m") or 0.0)
    mid = float(model.get("midspan_m") or span / 2.0)
    if span:
        fig.add_vline(x=0, line_dash="dot", line_color="#64748b", annotation_text="Start")
        fig.add_vline(x=mid, line_dash="dash", line_color="#dc2626", annotation_text="Midspan")
        fig.add_vline(x=span, line_dash="dot", line_color="#64748b", annotation_text="End")
        fig.update_xaxes(range=[-0.02 * span, span * 1.02], autorange=False)
    _style_layout(fig, "", "Station x (m)", "dp from top (m)", showlegend=showlegend)
    fig.update_yaxes(autorange="reversed", gridcolor="rgba(148,163,184,0.09)")
    fig.update_xaxes(gridcolor="rgba(148,163,184,0.09)")
    return fig


def tendon_plan_figure(
    model: dict,
    *,
    show_labels: bool = False,
    family_filter: str | None = None,
    side_filter: str | None = None,
    showlegend: bool = False,
) -> go.Figure:
    fig = go.Figure()
    for t in model.get("tendons", []):
        if not _tendon_passes_filter(t, family_filter=family_filter, side_filter=side_filter):
            continue
        prof = pd.DataFrame(t.get("horizontal_profile", []))
        if prof.empty:
            continue
        text = [t.get("tendon", "") if show_labels else "" for _ in range(len(prof))]
        family = str(t.get("family", ""))
        side = str(t.get("side", ""))
        fig.add_trace(
            go.Scatter(
                x=prof["x_m"],
                y=prof["horiz_off_m"],
                mode="lines+markers+text" if show_labels else "lines+markers",
                name=t.get("tendon", ""),
                legendgroup=family,
                text=text,
                textposition="top center",
                hovertemplate="%{fullData.name}<br>x = %{x:.3f} m<br>HorizOff = %{y:.3f} m<extra></extra>",
                line=dict(width=2.2, color=_family_color(family), dash=_side_line_dash(side)),
                marker=dict(size=6, color=_family_color(family), line=dict(width=0.8, color="#0f172a")),
            )
        )
    span = float(model.get("span_m") or 0.0)
    mid = float(model.get("midspan_m") or span / 2.0)
    if span:
        fig.add_vline(x=0, line_dash="dot", line_color="#64748b", annotation_text="Start")
        fig.add_vline(x=mid, line_dash="dash", line_color="#dc2626", annotation_text="Midspan")
        fig.add_vline(x=span, line_dash="dot", line_color="#64748b", annotation_text="End")
        fig.update_xaxes(range=[-0.02 * span, span * 1.02], autorange=False)
    fig.add_hline(y=0, line_dash="dash", line_color="#475569", annotation_text="CL")
    _style_layout(fig, "", "Station x (m)", "HorizOff from CL (m)", showlegend=showlegend)
    fig.update_xaxes(gridcolor="rgba(148,163,184,0.09)")
    fig.update_yaxes(gridcolor="rgba(148,163,184,0.09)")
    return fig




def _loop_groups(section_coords: pd.DataFrame) -> list[tuple[str, str, pd.DataFrame]]:
    """Return ordered section coordinate loops for figure generation."""
    if section_coords is None or section_coords.empty:
        return []
    df = section_coords.copy()
    if "point_no" in df.columns:
        df = df.sort_values(["loop_type", "loop_name", "point_no"])
    groups: list[tuple[str, str, pd.DataFrame]] = []
    for (loop_type, loop_name), g in df.groupby(["loop_type", "loop_name"], sort=False):
        gg = g[["x_mm", "y_mm"]].dropna().copy()
        if len(gg) >= 2:
            groups.append((str(loop_type), str(loop_name), gg))
    return groups


def _section_loop_to_yz_m(loop_df: pd.DataFrame, section_props: dict) -> tuple[list[float], list[float]]:
    """Map section x/y coordinates in mm into 3D local Y/Z coordinates in m.

    3D convention:
    - X = station along span (m)
    - Y = transverse coordinate from section centerline (m)
    - Z = vertical coordinate from section bottom (m)
    """
    bounds = section_props.get("bounds_mm", {}) if section_props else {}
    xmin = float(bounds.get("xmin", loop_df["x_mm"].min()))
    xmax = float(bounds.get("xmax", loop_df["x_mm"].max()))
    x_shift = 0.5 * (xmin + xmax)
    y_m = ((loop_df["x_mm"].astype(float) - x_shift) / 1000.0).tolist()
    z_m = (loop_df["y_mm"].astype(float) / 1000.0).tolist()
    return y_m, z_m



def _clip_yz_polygon_to_half_plane(
    y: list[float],
    z: list[float],
    *,
    keep: str,
) -> tuple[list[float], list[float]]:
    """Clip a closed Y/Z section loop to one side of the centerline.

    keep = "left" keeps Y >= 0.0; keep = "right" keeps Y <= 0.0.
    The helper is used only for the 3D review viewport half-shell display. It
    does not modify stored section coordinates or any engineering calculation.
    """
    mode = str(keep or "full").lower()
    if mode not in {"left", "right"} or len(y) < 3:
        return y, z

    points = list(zip([float(v) for v in y], [float(v) for v in z]))
    eps = 1e-9

    def inside(pt: tuple[float, float]) -> bool:
        yy, _ = pt
        return yy >= -eps if mode == "left" else yy <= eps

    def intersect(p1: tuple[float, float], p2: tuple[float, float]) -> tuple[float, float]:
        y1, z1 = p1
        y2, z2 = p2
        denom = y2 - y1
        if abs(denom) < eps:
            return (0.0, z1)
        t = (0.0 - y1) / denom
        return (0.0, z1 + t * (z2 - z1))

    clipped: list[tuple[float, float]] = []
    prev = points[-1]
    prev_inside = inside(prev)
    for curr in points:
        curr_inside = inside(curr)
        if curr_inside:
            if not prev_inside:
                clipped.append(intersect(prev, curr))
            clipped.append(curr)
        elif prev_inside:
            clipped.append(intersect(prev, curr))
        prev, prev_inside = curr, curr_inside

    # Remove near-duplicate consecutive points introduced by clipping.
    cleaned: list[tuple[float, float]] = []
    for pt in clipped:
        if not cleaned or abs(pt[0] - cleaned[-1][0]) > 1e-8 or abs(pt[1] - cleaned[-1][1]) > 1e-8:
            cleaned.append(pt)
    if len(cleaned) > 1 and abs(cleaned[0][0] - cleaned[-1][0]) < 1e-8 and abs(cleaned[0][1] - cleaned[-1][1]) < 1e-8:
        cleaned.pop()
    if len(cleaned) < 3:
        return [], []
    return [pt[0] for pt in cleaned], [pt[1] for pt in cleaned]


def _shell_clip_side(shell_display_mode: str | None) -> str | None:
    """Return clipping side for 3D shell display mode."""
    text = str(shell_display_mode or "Full shell").strip().lower()
    if text.startswith("left"):
        return "left"
    if text.startswith("right"):
        return "right"
    return None


def _shell_visibility(shell_display_mode: str | None) -> tuple[bool, bool]:
    """Return outer/inner visibility for 3D shell display mode."""
    text = str(shell_display_mode or "Full shell").strip().lower()
    if text.startswith("no shell"):
        return False, False
    if text.startswith("inner void"):
        return False, True
    return True, True

def _add_section_loop_surface_3d(
    fig: go.Figure,
    loop_df: pd.DataFrame,
    section_props: dict,
    *,
    span_m: float,
    name: str,
    color: str,
    opacity: float,
    legendgroup: str,
    showlegend: bool,
    clip_side: str | None = None,
) -> None:
    """Add translucent extruded boundary surfaces for a section loop."""
    y, z = _section_loop_to_yz_m(loop_df, section_props)
    if clip_side:
        y, z = _clip_yz_polygon_to_half_plane(y, z, keep=clip_side)
    if len(y) < 2 or span_m <= 0:
        return
    xs: list[float] = []
    ys: list[float] = []
    zs: list[float] = []
    i: list[int] = []
    j: list[int] = []
    k: list[int] = []
    n = len(y)
    for idx in range(n):
        idx2 = (idx + 1) % n
        base = len(xs)
        xs.extend([0.0, 0.0, span_m, span_m])
        ys.extend([y[idx], y[idx2], y[idx2], y[idx]])
        zs.extend([z[idx], z[idx2], z[idx2], z[idx]])
        i.extend([base, base, base + 2])
        j.extend([base + 1, base + 2, base + 3])
        k.extend([base + 2, base + 3, base])
    fig.add_trace(
        go.Mesh3d(
            x=xs,
            y=ys,
            z=zs,
            i=i,
            j=j,
            k=k,
            name=name,
            legendgroup=legendgroup,
            showlegend=showlegend,
            color=color,
            opacity=opacity,
            hoverinfo="skip",
            flatshading=True,
        )
    )


def _add_section_loop_wireframe_3d(
    fig: go.Figure,
    loop_df: pd.DataFrame,
    section_props: dict,
    *,
    span_m: float,
    name: str,
    color: str,
    dash: str = "solid",
    legendgroup: str = "section",
    showlegend: bool = False,
    clip_side: str | None = None,
) -> None:
    """Add start/end section frames and longitudinal edge lines."""
    y, z = _section_loop_to_yz_m(loop_df, section_props)
    if clip_side:
        y, z = _clip_yz_polygon_to_half_plane(y, z, keep=clip_side)
    if len(y) < 2:
        return
    y_closed = y + [y[0]]
    z_closed = z + [z[0]]
    for xval, frame_name, legend in [(0.0, f"{name} start", showlegend), (span_m, f"{name} end", False)]:
        fig.add_trace(
            go.Scatter3d(
                x=[xval] * len(y_closed),
                y=y_closed,
                z=z_closed,
                mode="lines",
                name=frame_name,
                legendgroup=legendgroup,
                showlegend=legend,
                line=dict(color=color, width=5, dash=dash),
                hoverinfo="skip",
            )
        )
    for yy, zz in zip(y, z):
        fig.add_trace(
            go.Scatter3d(
                x=[0.0, span_m],
                y=[yy, yy],
                z=[zz, zz],
                mode="lines",
                name=f"{name} longitudinal edge",
                legendgroup=legendgroup,
                showlegend=False,
                line=dict(color=color, width=2.6, dash=dash),
                hoverinfo="skip",
            )
        )


def _profile_xyz_for_tendon(tendon: dict, depth_m: float) -> tuple[list[float], list[float], list[float]]:
    """Return station/transverse/vertical 3D arrays from one tendon model."""
    vprof = pd.DataFrame(tendon.get("vertical_profile", []))
    hprof = pd.DataFrame(tendon.get("horizontal_profile", []))
    if vprof.empty or hprof.empty or "x_m" not in vprof.columns or "x_m" not in hprof.columns:
        return [], [], []
    stations = sorted(set(vprof["x_m"].astype(float).tolist()) | set(hprof["x_m"].astype(float).tolist()))
    if not stations:
        return [], [], []
    vprof = vprof.sort_values("x_m")
    hprof = hprof.sort_values("x_m")
    xs = [float(x) for x in stations]
    dp = pd.Series(np.interp(xs, vprof["x_m"].astype(float), vprof["dp_top_m"].astype(float)))
    off = pd.Series(np.interp(xs, hprof["x_m"].astype(float), hprof["horiz_off_m"].astype(float)))
    ys = off.astype(float).tolist()
    zs = (depth_m - dp.astype(float)).tolist()
    return xs, ys, zs


def _camera_for_preset(preset: str) -> dict:
    """Return stable CAD-style 3D camera presets for tendon review.

    Plotly's default perspective camera is useful while exploring the model, but
    report figures need an orthographic projection so the image reads more like
    an engineering/CAD isometric view.  This helper is presentation only; it
    does not change the tendon geometry.
    """
    text = str(preset or "Isometric · Orthographic").strip().lower()
    projection_type = "orthographic" if any(key in text for key in ("orthographic", "report", "top", "side", "end")) else "perspective"

    if text.startswith("top"):
        camera = dict(eye=dict(x=0.02, y=0.02, z=2.45), up=dict(x=0, y=1, z=0))
    elif text.startswith("side"):
        camera = dict(eye=dict(x=1.90, y=-2.35, z=0.02), up=dict(x=0, y=0, z=1))
    elif text.startswith("end"):
        camera = dict(eye=dict(x=-2.45, y=0.02, z=0.58), up=dict(x=0, y=0, z=1))
    elif text.startswith("tendon"):
        camera = dict(eye=dict(x=1.48, y=-1.22, z=0.78), up=dict(x=0, y=0, z=1))
    elif text.startswith("report"):
        camera = dict(eye=dict(x=1.35, y=-1.35, z=0.82), up=dict(x=0, y=0, z=1))
    elif "perspective" in text:
        camera = dict(eye=dict(x=1.45, y=-1.55, z=0.92), up=dict(x=0, y=0, z=1))
    else:
        # Default to orthographic isometric for a drawing-like first view.
        camera = dict(eye=dict(x=1.35, y=-1.35, z=0.82), up=dict(x=0, y=0, z=1))

    camera["projection"] = dict(type=projection_type)
    return camera


def _aspectratio_for_3d(span_m: float, width_m: float, depth_m: float, aspect_mode: str | None = None) -> dict:
    """Return aspect ratio for true-scale or presentation-scale 3D review.

    True scale preserves the geometric proportion between span, width, and
    depth. Presentation scale mildly compresses the long span and lifts the
    vertical scale so tendon paths remain readable in a report-ready viewport.
    """
    span = max(float(span_m or 0.0), 1.0)
    width = max(float(width_m or 0.0), 1.0)
    depth = max(float(depth_m or 0.0), 0.1)
    x_true = span / width
    z_true = depth / width
    text = str(aspect_mode or "Presentation scale").strip().lower()
    if text.startswith("true"):
        return dict(x=max(x_true, 1.0), y=1.0, z=max(z_true, 0.08))
    return dict(x=min(max(x_true, 2.2), 3.2), y=1.0, z=min(max(z_true * 1.75, 0.38), 0.62))


def tendon_3d_review_figure(
    model: dict,
    section_coords: pd.DataFrame,
    section_props: dict,
    *,
    family_filter: str | None = None,
    side_filter: str | None = None,
    tendon_filter: str | None = None,
    show_outer_shell: bool | None = None,
    show_inner_void: bool | None = None,
    show_station_markers: bool = True,
    show_tendon_labels: bool = False,
    view_preset: str = "Isometric · Orthographic",
    aspect_mode: str = "Presentation scale",
    shell_display_mode: str = "Full shell",
    outer_shell_opacity: float = 0.18,
    inner_void_opacity: float = 0.16,
    focus_tendon: str | None = None,
    fade_unfocused_tendons: bool = False,
    tendon_line_width: float = 6.0,
    station_marker_mode: str | None = None,
) -> go.Figure:
    """Build an interactive 3D tendon review viewport.

    The view is intentionally a review model, not a full bridge solid model:
    translucent section boundary envelopes + tendon polylines from the adopted
    merged vertical/horizontal profile data.  No calculation logic is changed.
    """
    fig = go.Figure()
    span_m = float(model.get("span_m") or 0.0)
    if not span_m:
        # Fall back to max tendon station for partially populated models.
        for t in model.get("tendons", []):
            for prof_key in ("vertical_profile", "horizontal_profile"):
                for p in t.get(prof_key, []) or []:
                    span_m = max(span_m, float(p.get("x_m") or 0.0))
    depth_m = float(section_props.get("depth_m") or section_props.get("D_m") or 0.0)
    bounds = section_props.get("bounds_mm", {}) if section_props else {}
    width_m = float(section_props.get("width_m") or section_props.get("B_m") or ((float(bounds.get("xmax", 0.0)) - float(bounds.get("xmin", 0.0))) / 1000.0) or 0.0)
    if show_outer_shell is None and show_inner_void is None:
        show_outer_shell, show_inner_void = _shell_visibility(shell_display_mode)
    elif show_outer_shell is None:
        show_outer_shell = _shell_visibility(shell_display_mode)[0]
    elif show_inner_void is None:
        show_inner_void = _shell_visibility(shell_display_mode)[1]
    clip_side = _shell_clip_side(shell_display_mode)
    outer_opacity = min(max(float(outer_shell_opacity or 0.0), 0.0), 0.8)
    inner_opacity = min(max(float(inner_void_opacity or 0.0), 0.0), 0.8)
    loops = _loop_groups(section_coords)
    outer_index = 0
    void_index = 0
    for loop_type, loop_name, loop in loops:
        is_hole = str(loop_type).lower() in {"hole", "opening", "inner", "void"} or "opening" in str(loop_name).lower()
        if is_hole:
            void_index += 1
            if show_inner_void:
                _add_section_loop_surface_3d(
                    fig,
                    loop,
                    section_props,
                    span_m=span_m,
                    name="Inner void envelope" if void_index == 1 else f"Inner void {void_index}",
                    color="rgba(37,99,235,0.38)",
                    opacity=inner_opacity,
                    legendgroup="inner_void",
                    showlegend=void_index == 1,
                    clip_side=clip_side,
                )
                _add_section_loop_wireframe_3d(
                    fig,
                    loop,
                    section_props,
                    span_m=span_m,
                    name="Inner void frame" if void_index == 1 else f"Inner void frame {void_index}",
                    color="#2563eb",
                    dash="dash",
                    legendgroup="inner_void",
                    showlegend=False,
                    clip_side=clip_side,
                )
        else:
            outer_index += 1
            if show_outer_shell:
                _add_section_loop_surface_3d(
                    fig,
                    loop,
                    section_props,
                    span_m=span_m,
                    name="Outer shell envelope" if outer_index == 1 else f"Outer shell {outer_index}",
                    color="rgba(41,72,96,0.42)",
                    opacity=outer_opacity,
                    legendgroup="outer_shell",
                    showlegend=outer_index == 1,
                    clip_side=clip_side,
                )
                _add_section_loop_wireframe_3d(
                    fig,
                    loop,
                    section_props,
                    span_m=span_m,
                    name="Outer shell frame" if outer_index == 1 else f"Outer shell frame {outer_index}",
                    color="#294860",
                    dash="solid",
                    legendgroup="outer_shell",
                    showlegend=False,
                    clip_side=clip_side,
                )

    base_line_width = min(max(float(tendon_line_width or 6.0), 2.0), 14.0)
    focus_name = str(focus_tendon or "").strip()
    if focus_name in {"None", "No focus", "All tendons"}:
        focus_name = ""
    tendon_count = 0
    for t in model.get("tendons", []):
        if not _tendon_passes_filter(t, family_filter=family_filter, side_filter=side_filter, tendon_filter=tendon_filter):
            continue
        xs, ys, zs = _profile_xyz_for_tendon(t, depth_m)
        if not xs:
            continue
        family = str(t.get("family", ""))
        side = str(t.get("side", ""))
        tendon_name = str(t.get("tendon", ""))
        is_focused = bool(focus_name) and tendon_name == focus_name
        is_unfocused = bool(focus_name) and not is_focused
        color = _family_color(family)
        opacity = 0.18 if (fade_unfocused_tendons and is_unfocused) else 1.0
        line_width = max(base_line_width * 0.45, 2.0) if (fade_unfocused_tendons and is_unfocused) else (base_line_width * 1.35 if is_focused else base_line_width)
        marker_size = 2.5 if (fade_unfocused_tendons and is_unfocused) else (6 if is_focused else 4)
        text = [tendon_name if show_tendon_labels and (idx in {0, len(xs)-1}) and not (fade_unfocused_tendons and is_unfocused) else "" for idx in range(len(xs))]
        tendon_count += 1
        fig.add_trace(
            go.Scatter3d(
                x=xs,
                y=ys,
                z=zs,
                mode="lines+markers+text" if show_tendon_labels else "lines+markers",
                name=tendon_name,
                legendgroup=family,
                showlegend=False,
                text=text,
                textposition="top center",
                opacity=opacity,
                line=dict(width=line_width, color=color, dash=_side_line_dash(side)),
                marker=dict(size=marker_size, color=color, line=dict(width=1.2 if is_focused else 0.8, color="#0f172a")),
                hovertemplate=(
                    "%{fullData.name}<br>Station x = %{x:.3f} m"
                    "<br>HorizOff = %{y:.3f} m<br>z from bottom = %{z:.3f} m<extra></extra>"
                ),
            )
        )

    marker_mode = str(station_marker_mode or ("Key only" if show_station_markers else "Off")).strip().lower()
    if not show_station_markers:
        marker_mode = "off"
    if marker_mode not in {"off", "none"} and span_m:
        y_half = max(width_m / 2.0, 0.5)
        if marker_mode.startswith("all"):
            station_items = [
                (0.0, "Start", "solid"),
                (0.25 * span_m, "0.25L", "dot"),
                (0.50 * span_m, "Midspan", "dash"),
                (0.75 * span_m, "0.75L", "dot"),
                (span_m, "End", "solid"),
            ]
        else:
            station_items = [(0.0, "Start", "solid"), (0.5 * span_m, "Midspan", "dash"), (span_m, "End", "solid")]
        for station, label, dash in station_items:
            fig.add_trace(
                go.Scatter3d(
                    x=[station, station],
                    y=[-y_half, y_half],
                    z=[0.0, 0.0],
                    mode="lines+text",
                    name=label,
                    showlegend=False,
                    text=["", label],
                    textposition="top center",
                    line=dict(color="#64748b", width=3, dash=dash),
                    hovertemplate=f"{label}<br>x = {station:.3f} m<extra></extra>",
                )
            )

    # Add family legend placeholders for the custom/Plotly legend without dense tendon names.
    families = list(dict.fromkeys([str(t.get("family", "")) for t in model.get("tendons", []) if _tendon_passes_filter(t, family_filter=family_filter, side_filter=side_filter, tendon_filter=tendon_filter) and str(t.get("family", "")).strip()]))
    for fam in families:
        fig.add_trace(
            go.Scatter3d(
                x=[None], y=[None], z=[None],
                mode="markers",
                name=fam,
                marker=dict(size=7, color=_family_color(fam)),
                showlegend=True,
                legendgroup=fam,
                hoverinfo="skip",
            )
        )

    fig.update_layout(
        height=650,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        margin=dict(l=0, r=0, t=12, b=0),
        font=dict(color="#0f172a", size=12, family="Arial, sans-serif"),
        showlegend=False,
        scene=dict(
            xaxis=dict(title="Station x (m)", backgroundcolor="#ffffff", gridcolor="rgba(148,163,184,0.16)", showbackground=True, zerolinecolor="rgba(37,99,235,0.24)"),
            yaxis=dict(title="HorizOff / section Y (m)", backgroundcolor="#ffffff", gridcolor="rgba(148,163,184,0.14)", showbackground=True, zerolinecolor="rgba(37,99,235,0.24)"),
            zaxis=dict(title="z from bottom (m)", backgroundcolor="#ffffff", gridcolor="rgba(148,163,184,0.14)", showbackground=True, zerolinecolor="rgba(37,99,235,0.24)"),
            aspectmode="manual",
            aspectratio=_aspectratio_for_3d(span_m, width_m, depth_m, aspect_mode),
            camera=_camera_for_preset(view_preset),
        ),
        uirevision="tendon_3d_review",
    )
    return fig



def _section_bounds_for_display(section_coords: pd.DataFrame, section_props: dict, origin_mode: str) -> dict[str, float]:
    """Return section bounds in the same display coordinates used by the overlay figure."""
    bounds = section_props.get("bounds_mm", {}) if section_props else {}
    xmin = float(bounds.get("xmin", section_coords["x_mm"].min() if section_coords is not None and not section_coords.empty else 0.0))
    xmax = float(bounds.get("xmax", section_coords["x_mm"].max() if section_coords is not None and not section_coords.empty else 0.0))
    ymin = float(bounds.get("ymin", section_coords["y_mm"].min() if section_coords is not None and not section_coords.empty else 0.0))
    ymax = float(bounds.get("ymax", section_coords["y_mm"].max() if section_coords is not None and not section_coords.empty else 0.0))
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


def _tick_shape(x0: float, y0: float, x1: float, y1: float, color: str) -> dict:
    return {"type": "line", "x0": x0, "y0": y0, "x1": x1, "y1": y1, "line": {"color": color, "width": 1.35}}


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


def _apply_tendon_overlay_viewport(
    fig: go.Figure,
    section_coords: pd.DataFrame,
    section_props: dict,
    *,
    origin_mode: str,
    include_dimensions: bool,
    full_dimensions: bool = False,
) -> go.Figure:
    """Apply a compact default viewport so the section opens large enough for review.

    The base section figure uses equal-axis scaling for geometric drawings.  In a
    very wide Streamlit canvas that can make the box girder look small.  The
    tendon overlay is a review/report viewport, so it uses an explicit compact
    range with fixed autorange disabled while preserving an approximately true
    engineering proportion.
    """
    if not section_props.get("valid"):
        return fig
    b = _section_bounds_for_display(section_coords, section_props, origin_mode)
    xmin = b["xmin"]
    xmax = b["xmax"]
    ymin = b["ymin"]
    ymax = b["ymax"]
    width = max(float(b["width"]), 1.0)
    depth = max(float(b["depth"]), 1.0)

    if include_dimensions:
        left_pad = max(620.0, 0.090 * width)
        right_pad = max(620.0, 0.090 * width) * (1.34 if full_dimensions else 1.08)
        top_pad = max(580.0, 0.245 * depth)
        bottom_pad = max(230.0, 0.090 * depth)
    else:
        left_pad = max(360.0, 0.050 * width)
        right_pad = max(360.0, 0.050 * width)
        top_pad = max(300.0, 0.130 * depth)
        bottom_pad = max(170.0, 0.070 * depth)

    fig.update_xaxes(range=[xmin - left_pad, xmax + right_pad], autorange=False)
    fig.update_yaxes(range=[ymin - bottom_pad, ymax + top_pad], autorange=False, scaleanchor=None, scaleratio=None)
    return fig


def _add_tendon_overlay_dimension_layer(
    fig: go.Figure,
    section_coords: pd.DataFrame,
    section_props: dict,
    *,
    origin_mode: str,
    dimension_mode: str = "clean",
) -> go.Figure:
    """Add report-style dimension guides for the tendon section overlay.

    Modes:
    - clean: B, D, CL, and centroid guides only.
    - full dimensions: clean plus y_cg and y_t fiber dimensions.
    - hide dimensions: no dimension guide layer.
    """
    mode = str(dimension_mode or "clean").strip().lower()
    if mode.startswith("hide") or not section_props.get("valid"):
        return _apply_tendon_overlay_viewport(
            fig,
            section_coords,
            section_props,
            origin_mode=origin_mode,
            include_dimensions=False,
        )

    b = _section_bounds_for_display(section_coords, section_props, origin_mode)
    xmin = b["xmin"]
    xmax = b["xmax"]
    ymin = b["ymin"]
    ymax = b["ymax"]
    width = max(float(b["width"]), 1.0)
    depth = max(float(b["depth"]), 1.0)
    cx = float(section_props.get("cx_mm", 0.5 * (b["xmin_raw"] + b["xmax_raw"]))) - b["x_shift"]
    cy = float(section_props.get("cy_mm", 0.5 * (ymin + ymax)))

    dim_color = "#66768c"
    cl_color = "#2563eb"
    cg_color = "#be123c"
    cg_line_color = "rgba(190,18,60,0.50)"
    top_offset = max(360.0, 0.17 * depth)
    left_offset = max(520.0, 0.075 * width)
    right_offset = max(520.0, 0.065 * width)
    y_dim = ymax + top_offset
    x_dim_left = xmin - left_offset
    x_dim_right = xmax + right_offset

    _add_horizontal_dimension(
        fig,
        x0=xmin,
        x1=xmax,
        y=y_dim,
        ext_to_y=ymax + 0.018 * depth,
        label=f"B = {width:.0f} mm",
        color=dim_color,
    )
    _add_vertical_dimension(
        fig,
        x=x_dim_left,
        y0=ymin,
        y1=ymax,
        ext_to_x=xmin - 0.018 * width,
        label=f"D = {depth:.0f} mm",
        color=dim_color,
        label_side="left",
    )

    # Centerline guide is part of the Clean view because the overlay is reviewed by horizontal offset from CL.
    if str(origin_mode).lower().startswith("center"):
        fig.add_shape(
            type="line",
            x0=0,
            y0=ymin - 0.06 * depth,
            x1=0,
            y1=ymax + 0.065 * depth,
            line={"color": "rgba(37,99,235,0.48)", "width": 1.05, "dash": "dash"},
        )
        _dimension_label(fig, x=0, y=ymax + 0.085 * depth, text="CL", color=cl_color, size=11)

    # Centroid guides are deliberately lighter than the tendon points to avoid visual competition.
    fig.add_shape(type="line", x0=xmin, y0=cy, x1=xmax, y1=cy, line={"color": cg_line_color, "width": 0.95, "dash": "dot"})
    fig.add_shape(type="line", x0=cx, y0=ymin, x1=cx, y1=ymax, line={"color": cg_line_color, "width": 0.95, "dash": "dot"})
    _dimension_label(fig, x=cx + 0.070 * width, y=cy + 0.055 * depth, text="CG", color=cg_color, size=11)

    if mode.startswith("full"):
        ycg_mm = float(section_props.get("ycg_from_bottom_m", cy / 1000.0)) * 1000.0
        yt_mm = float(section_props.get("yt_from_top_m", max(ymax - cy, 0.0) / 1000.0)) * 1000.0
        x_fiber = x_dim_right
        _add_vertical_dimension(
            fig,
            x=x_fiber,
            y0=ymin,
            y1=cy,
            ext_to_x=xmax + 0.018 * width,
            label=f"y_cg = {ycg_mm:.0f} mm",
            color=dim_color,
            label_side="right",
        )
        _add_vertical_dimension(
            fig,
            x=x_fiber + 0.34 * right_offset,
            y0=cy,
            y1=ymax,
            ext_to_x=xmax + 0.018 * width,
            label=f"y_t = {yt_mm:.0f} mm",
            color=dim_color,
            label_side="right",
        )

    # Give the external dimension layer breathing room, but keep the section large
    # enough for review when the canvas first opens.
    return _apply_tendon_overlay_viewport(
        fig,
        section_coords,
        section_props,
        origin_mode=origin_mode,
        include_dimensions=True,
        full_dimensions=mode.startswith("full"),
    )


def tendon_section_overlay_figure(
    section_coords: pd.DataFrame,
    section_props: dict,
    tendon_points: pd.DataFrame,
    *,
    positive_offset_direction: str = "left",
    point_label_mode: str = "family",
    show_point_numbers: bool = True,
    origin_mode: str = "csibridge",
    dimension_mode: str = "clean",
    station_label: str | None = None,
    station_m: float | None = None,
) -> go.Figure:
    from visualization.section_figures import section_polygon_figure

    fig = section_polygon_figure(
        section_coords,
        section_props,
        point_label_mode="major" if show_point_numbers else "hide",
        show_dimensions=False,
        origin_mode=origin_mode,
    )
    # Clean CSiBridge loop names into report-ready legend labels.
    hide_dimensions = str(dimension_mode or "clean").strip().lower().startswith("hide")
    for tr in fig.data:
        name = str(getattr(tr, "name", ""))
        if name.startswith("Structural Polygon"):
            tr.name = "Concrete"
            tr.legendgroup = "section"
        elif name.startswith("Opening Polygon"):
            tr.name = "Inner void"
            tr.legendgroup = "section"
        elif name == "Centroid":
            tr.legendgroup = "section"
            tr.mode = "markers"
            tr.text = [""]
    if hide_dimensions:
        fig.data = tuple(tr for tr in fig.data if str(getattr(tr, "name", "")) != "Centroid")

    if tendon_points is not None and not tendon_points.empty:
        width_m = float(section_props.get("width_m") or section_props.get("B_m") or 0.0)
        depth_m = float(section_props.get("depth_m") or section_props.get("D_m") or 0.0)
        bounds = section_props.get("bounds_mm", {}) if section_props else {}
        xmin = float(bounds.get("xmin", 0.0))
        xmax = float(bounds.get("xmax", width_m * 1000.0))
        x_shift = 0.0
        if str(origin_mode).lower().startswith("center"):
            x_shift = 0.5 * (xmin + xmax)

        for family, g in tendon_points.groupby("Family", sort=False):
            xs = []
            ys = []
            text = []
            hover = []
            for _, r in g.iterrows():
                off = float(r["HorizOff (m)"])
                dp = float(r["dp from top (m)"])
                if positive_offset_direction == "left":
                    x_m = width_m / 2.0 - off
                else:
                    x_m = width_m / 2.0 + off
                y_m = depth_m - dp
                x_mm = x_m * 1000.0 - x_shift
                y_mm = y_m * 1000.0
                xs.append(x_mm)
                ys.append(y_mm)
                label = _label_for_mode(r.to_dict(), point_label_mode)
                text.append(label)
                hover.append(
                    f"{r['Tendon']}<br>Family = {r['Family']}<br>Station = {float(r['Station (m)']):.3f} m"
                    f"<br>dp = {dp:.3f} m<br>HorizOff = {off:.3f} m"
                    f"<br>x(section) = {x_mm:.0f} mm<br>y(section) = {y_mm:.0f} mm"
                )
            show_text = any(str(t) for t in text)
            fig.add_trace(
                go.Scatter(
                    x=xs,
                    y=ys,
                    mode="markers+text" if show_text else "markers",
                    name=str(family),
                    text=text,
                    textposition="top center",
                    marker=dict(symbol="circle", size=10, color=_family_color(str(family)), line=dict(width=1.2, color="#0f172a")),
                    hovertemplate="%{customdata}<extra></extra>",
                    customdata=hover,
                )
            )
    # M3H.9: Station = ... is intentionally not drawn inside the Plotly body.
    # The app renders the selected station as a clear badge above the drawing viewport.
    fig = _add_tendon_overlay_dimension_layer(
        fig,
        section_coords,
        section_props,
        origin_mode=origin_mode,
        dimension_mode=dimension_mode,
    )

    apply_engineering_figure_layout(
        fig,
        title="",
        x_title="x (mm, CL = 0)" if str(origin_mode).lower().startswith("center") else "x (mm)",
        y_title="y (mm)",
        height=520,
        showlegend=True,
        margin=dict(l=50, r=18, t=44, b=52),
    )
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.055, xanchor="center", x=0.5, font=dict(size=11)),
    )
    return fig
