from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, sqrt, pi
from typing import Iterable, Any, BinaryIO

import pandas as pd


OUTER_ALIASES = {"outer", "structural", "structural polygon", "structural polygon 1", "concrete", "boundary"}
HOLE_ALIASES = {"hole", "opening", "void", "opening polygon", "opening polygon 1", "inner"}


@dataclass(frozen=True)
class LoopProperties:
    loop_type: str
    name: str
    n_points: int
    area_mm2: float
    cx_mm: float
    cy_mm: float
    ixx_o_mm4: float
    iyy_o_mm4: float
    ixy_o_mm4: float
    perimeter_mm: float


def _as_float(value: Any) -> float:
    if value is None:
        raise ValueError("empty numeric value")
    if isinstance(value, (int, float)):
        v = float(value)
    else:
        v = float(str(value).strip().replace(",", ""))
    if not isfinite(v):
        raise ValueError("non-finite numeric value")
    return v


def canonical_loop_type(loop_name: str) -> str:
    name = str(loop_name or "").strip().lower()
    if name in OUTER_ALIASES or name.startswith("structural"):
        return "outer"
    if name in HOLE_ALIASES or name.startswith("opening"):
        return "hole"
    # Sensible fallback: first/unknown loops are treated as outer only by UI after QA warning.
    return "unknown"


def _detect_coordinate_unit(out: pd.DataFrame, source_columns: dict[str, str], coordinate_unit: str = "auto") -> str:
    unit = str(coordinate_unit or "auto").strip().lower()
    if unit in {"mm", "millimetre", "millimeter", "millimetres", "millimeters"}:
        return "mm"
    if unit in {"m", "metre", "meter", "metres", "meters"}:
        return "m"

    x_col = str(source_columns.get("x_mm", "")).strip().lower()
    y_col = str(source_columns.get("y_mm", "")).strip().lower()
    joined = f"{x_col} {y_col}"
    if "mm" in joined:
        return "mm"
    if "(m)" in joined or joined.endswith("_m") or " metre" in joined or " meter" in joined:
        return "m"

    # CSiBridge section-coordinate exports often use generic X/Y columns in metres
    # (e.g. 0..11.2 m and 0..2.5 m).  App editor/template rows use x_mm/y_mm.
    try:
        xs = pd.to_numeric(out["x_mm"], errors="coerce").dropna()
        ys = pd.to_numeric(out["y_mm"], errors="coerce").dropna()
        span = max(float(xs.max() - xs.min()) if len(xs) else 0.0, float(ys.max() - ys.min()) if len(ys) else 0.0)
        max_abs = max(float(xs.abs().max()) if len(xs) else 0.0, float(ys.abs().max()) if len(ys) else 0.0)
    except Exception:
        return "mm"
    if 0.1 <= span <= 100.0 and max_abs <= 500.0:
        return "m"
    return "mm"


def normalize_coordinate_rows(rows: Iterable[dict[str, Any]] | pd.DataFrame, coordinate_unit: str = "auto") -> pd.DataFrame:
    """Normalize CSiBridge-style section coordinate rows.

    Supported aliases include Shape/loop_name, Point/point_no, X/x_mm, Y/y_mm.
    CSiBridge Excel exports commonly use X/Y in metres, whereas the app editor
    stores x_mm/y_mm.  ``coordinate_unit='auto'`` converts likely metre inputs
    to millimetres and leaves explicit x_mm/y_mm data unchanged.
    """
    df = rows.copy() if isinstance(rows, pd.DataFrame) else pd.DataFrame(list(rows))
    if df.empty:
        return pd.DataFrame(columns=["loop_name", "loop_type", "point_no", "x_mm", "y_mm"])

    colmap: dict[str, str] = {}
    normalized_names = {str(c).strip().lower(): c for c in df.columns}
    for target, aliases in {
        "loop_name": ["loop_name", "loop", "shape", "polygon", "polygon_name", "loop id", "loop_id"],
        "point_no": ["point_no", "point", "point_id", "point no", "point_no.", "point number"],
        "x_mm": ["x_mm", "x", "x coordinate", "x-coordinate", "x (mm)", "x_mm.", "xcoord"],
        "y_mm": ["y_mm", "y", "y coordinate", "y-coordinate", "y (mm)", "y_mm.", "ycoord"],
    }.items():
        for alias in aliases:
            if alias in normalized_names:
                colmap[target] = normalized_names[alias]
                break
    missing = [c for c in ["loop_name", "point_no", "x_mm", "y_mm"] if c not in colmap]
    if missing:
        raise ValueError(f"Missing required coordinate column(s): {', '.join(missing)}")

    out = pd.DataFrame(
        {
            "loop_name": df[colmap["loop_name"]].ffill().astype(str).str.strip(),
            "point_no": df[colmap["point_no"]],
            "x_mm": df[colmap["x_mm"]],
            "y_mm": df[colmap["y_mm"]],
        }
    )
    # Drop CSiBridge reference/insertion rows and blank separator rows before integer conversion.
    out = out.dropna(subset=["point_no", "x_mm", "y_mm"], how="any")
    out = out[out["point_no"].astype(str).str.strip().ne("")]
    out = out[out["x_mm"].astype(str).str.strip().ne("") & out["y_mm"].astype(str).str.strip().ne("")]
    out = out[out["point_no"].astype(str).str.lower().ne("nan")]
    out = out[out["x_mm"].astype(str).str.lower().ne("nan") & out["y_mm"].astype(str).str.lower().ne("nan")]

    source_unit = _detect_coordinate_unit(out, colmap, coordinate_unit)
    out["point_no"] = out["point_no"].apply(lambda v: int(float(str(v).strip())))
    out["x_mm"] = out["x_mm"].apply(_as_float)
    out["y_mm"] = out["y_mm"].apply(_as_float)
    if source_unit == "m":
        out["x_mm"] = out["x_mm"] * 1000.0
        out["y_mm"] = out["y_mm"] * 1000.0

    out["loop_type"] = out["loop_name"].apply(canonical_loop_type)
    type_order = {"outer": 0, "hole": 1, "unknown": 2}
    out["_loop_order"] = out["loop_type"].map(type_order).fillna(9)
    out = out.sort_values(["_loop_order", "loop_name", "point_no"], kind="stable").drop(columns=["_loop_order"]).reset_index(drop=True)
    return out[["loop_name", "loop_type", "point_no", "x_mm", "y_mm"]]


def read_coordinate_table(uploaded: BinaryIO | Any, filename: str | None = None, coordinate_unit: str = "auto") -> pd.DataFrame:
    """Read a CSiBridge coordinate table from CSV or Excel and normalize to mm.

    Excel support is required because CSiBridge commonly exports section coordinates
    as .xlsx with columns Shape, Point, Material, X, Y and generic X/Y in metres.
    """
    name = str(filename or getattr(uploaded, "name", "")).lower()
    if name.endswith((".xlsx", ".xls")):
        try:
            raw = pd.read_excel(uploaded, sheet_name=0)
        except ImportError as exc:
            raise ImportError("Excel import requires openpyxl. Install project requirements and retry.") from exc
    else:
        raw = pd.read_csv(uploaded)
    return normalize_coordinate_rows(raw, coordinate_unit=coordinate_unit)


def _signed_area(points: list[tuple[float, float]]) -> float:
    total = 0.0
    n = len(points)
    for i in range(n):
        x0, y0 = points[i]
        x1, y1 = points[(i + 1) % n]
        total += x0 * y1 - x1 * y0
    return 0.5 * total


def _remove_consecutive_duplicate_points(points: list[tuple[float, float]], tol: float = 1e-9) -> list[tuple[float, float]]:
    cleaned: list[tuple[float, float]] = []
    for pt in points:
        if not cleaned or abs(pt[0] - cleaned[-1][0]) > tol or abs(pt[1] - cleaned[-1][1]) > tol:
            cleaned.append(pt)
    if len(cleaned) > 1 and abs(cleaned[0][0] - cleaned[-1][0]) <= tol and abs(cleaned[0][1] - cleaned[-1][1]) <= tol:
        cleaned.pop()
    return cleaned


def _loop_properties(points: list[tuple[float, float]], loop_type: str, name: str) -> LoopProperties:
    if len(points) < 3:
        raise ValueError(f"Loop {name!r} has fewer than 3 points")
    # Normalize to counter-clockwise for positive geometric properties.
    if _signed_area(points) < 0:
        points = list(reversed(points))

    a2 = 0.0
    cx_num = 0.0
    cy_num = 0.0
    ixx_num = 0.0
    iyy_num = 0.0
    ixy_num = 0.0
    perimeter = 0.0
    n = len(points)
    for i in range(n):
        x0, y0 = points[i]
        x1, y1 = points[(i + 1) % n]
        cross = x0 * y1 - x1 * y0
        a2 += cross
        cx_num += (x0 + x1) * cross
        cy_num += (y0 + y1) * cross
        ixx_num += (y0 * y0 + y0 * y1 + y1 * y1) * cross
        iyy_num += (x0 * x0 + x0 * x1 + x1 * x1) * cross
        ixy_num += (2 * x0 * y0 + x0 * y1 + x1 * y0 + 2 * x1 * y1) * cross
        perimeter += sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)

    area = 0.5 * a2
    if abs(area) < 1e-9:
        raise ValueError(f"Loop {name!r} has near-zero area")
    cx = cx_num / (6.0 * area)
    cy = cy_num / (6.0 * area)
    ixx = ixx_num / 12.0
    iyy = iyy_num / 12.0
    ixy = ixy_num / 24.0
    return LoopProperties(loop_type, name, n, area, cx, cy, ixx, iyy, ixy, perimeter)


def _segment_intersection(p1, p2, p3, p4) -> bool:
    def orient(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    def on_segment(a, b, c):
        return min(a[0], b[0]) - 1e-9 <= c[0] <= max(a[0], b[0]) + 1e-9 and min(a[1], b[1]) - 1e-9 <= c[1] <= max(a[1], b[1]) + 1e-9

    o1 = orient(p1, p2, p3)
    o2 = orient(p1, p2, p4)
    o3 = orient(p3, p4, p1)
    o4 = orient(p3, p4, p2)
    if o1 * o2 < -1e-9 and o3 * o4 < -1e-9:
        return True
    if abs(o1) <= 1e-9 and on_segment(p1, p2, p3):
        return True
    if abs(o2) <= 1e-9 and on_segment(p1, p2, p4):
        return True
    if abs(o3) <= 1e-9 and on_segment(p3, p4, p1):
        return True
    if abs(o4) <= 1e-9 and on_segment(p3, p4, p2):
        return True
    return False


def loop_self_intersects(points: list[tuple[float, float]]) -> bool:
    n = len(points)
    if n < 4:
        return False
    for i in range(n):
        a1 = points[i]
        a2 = points[(i + 1) % n]
        for j in range(i + 1, n):
            # Adjacent segments share endpoints and should not count.
            if j in {i, (i - 1) % n, (i + 1) % n}:
                continue
            if i == 0 and j == n - 1:
                continue
            b1 = points[j]
            b2 = points[(j + 1) % n]
            if _segment_intersection(a1, a2, b1, b2):
                return True
    return False


def point_in_polygon(point: tuple[float, float], polygon: list[tuple[float, float]]) -> bool:
    x, y = point
    inside = False
    j = len(polygon) - 1
    for i in range(len(polygon)):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-12) + xi):
            inside = not inside
        j = i
    return inside


def _distance_point_to_segment(point: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> float:
    """Shortest distance from a point to a line segment, in the same units as input."""
    px, py = point
    ax, ay = a
    bx, by = b
    dx = bx - ax
    dy = by - ay
    denom = dx * dx + dy * dy
    if denom <= 1e-18:
        return sqrt((px - ax) ** 2 + (py - ay) ** 2)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / denom))
    qx = ax + t * dx
    qy = ay + t * dy
    return sqrt((px - qx) ** 2 + (py - qy) ** 2)


def _minimum_distance_to_polygon_boundary(point: tuple[float, float], polygon: list[tuple[float, float]]) -> float | None:
    if not polygon:
        return None
    distances = [
        _distance_point_to_segment(point, polygon[i], polygon[(i + 1) % len(polygon)])
        for i in range(len(polygon))
    ]
    return min(distances) if distances else None


def section_loop_polygons(df: pd.DataFrame) -> dict[str, list[list[tuple[float, float]]]]:
    """Return normalized outer and hole polygons from section coordinates in mm."""
    coords = normalize_coordinate_rows(df)
    loops: dict[str, list[list[tuple[float, float]]]] = {"outer": [], "hole": [], "unknown": []}
    if coords.empty:
        return loops
    for _, g in coords.groupby("loop_name", sort=False):
        loop_type = str(g["loop_type"].iloc[0]) if "loop_type" in g else "unknown"
        pts = _remove_consecutive_duplicate_points(list(zip(g["x_mm"].astype(float), g["y_mm"].astype(float))))
        if len(pts) >= 3:
            loops.setdefault(loop_type, []).append(pts)
    return loops


def classify_point_in_section_void(point_mm: tuple[float, float], df: pd.DataFrame) -> dict[str, Any]:
    """Classify a point relative to the concrete section and voids.

    Returns a QA dictionary suitable for external tendon checks.  For an external
    tendon inside a hollow box, the desired status is ``INSIDE VOID``.
    """
    loops = section_loop_polygons(df)
    outer_polys = loops.get("outer", [])
    hole_polys = loops.get("hole", [])
    inside_outer = any(point_in_polygon(point_mm, poly) for poly in outer_polys) if outer_polys else False
    inside_hole = any(point_in_polygon(point_mm, poly) for poly in hole_polys) if hole_polys else False

    distances = []
    for poly in hole_polys:
        d = _minimum_distance_to_polygon_boundary(point_mm, poly)
        if d is not None:
            distances.append(d)
    min_clearance = min(distances) if distances else None

    if inside_hole:
        status = "PASS"
        location = "INSIDE VOID"
        note = "External tendon point is inside the box-girder void."
    elif inside_outer:
        status = "FAIL"
        location = "INSIDE CONCRETE"
        note = "External tendon point is inside the concrete polygon; review dp/HorizOff convention."
    else:
        status = "FAIL"
        location = "OUTSIDE SECTION"
        note = "Tendon point is outside the structural polygon; review coordinates and sign convention."

    return {
        "status": status,
        "location": location,
        "inside_outer": inside_outer,
        "inside_void": inside_hole,
        "min_clearance_to_inner_boundary_mm": min_clearance,
        "note": note,
    }


def calculate_section_properties(df: pd.DataFrame) -> dict[str, Any]:
    """Calculate hollow-section properties from normalized coordinate rows in mm."""
    coords = normalize_coordinate_rows(df)
    if coords.empty:
        return {"valid": False, "errors": ["No coordinate rows available"], "warnings": []}

    errors: list[str] = []
    warnings: list[str] = []
    loop_props: list[LoopProperties] = []
    outer_polygons: list[list[tuple[float, float]]] = []
    hole_polygons: list[list[tuple[float, float]]] = []

    for loop_name, g in coords.groupby("loop_name", sort=False):
        loop_type = str(g["loop_type"].iloc[0])
        points_raw = list(zip(g["x_mm"].astype(float), g["y_mm"].astype(float)))
        points = _remove_consecutive_duplicate_points(points_raw)
        if len(points) < len(points_raw):
            warnings.append(f"Loop {loop_name!r} contains consecutive duplicate CSiBridge points; duplicates are ignored for property calculation.")
        if loop_type == "unknown":
            warnings.append(f"Loop {loop_name!r} has unknown type; use loop name Structural Polygon 1 or Opening Polygon 1.")
            continue
        if loop_self_intersects(points):
            errors.append(f"Loop {loop_name!r} appears to self-intersect.")
        try:
            props = _loop_properties(points, loop_type, str(loop_name))
            loop_props.append(props)
            if loop_type == "outer":
                outer_polygons.append(points)
            elif loop_type == "hole":
                hole_polygons.append(points)
        except ValueError as exc:
            errors.append(str(exc))

    if not any(p.loop_type == "outer" for p in loop_props):
        errors.append("No outer / Structural Polygon loop found.")
    if errors:
        return {"valid": False, "errors": errors, "warnings": warnings, "coordinates": coords}

    # Check hole vertices inside at least one outer polygon.
    for h in hole_polygons:
        if outer_polygons and not all(any(point_in_polygon(pt, outer) for outer in outer_polygons) for pt in h):
            warnings.append("At least one opening polygon point is outside the structural polygon.")

    # Composite properties about origin. Holes are subtracted regardless of loop orientation.
    A = Cx_num = Cy_num = Ixx_o = Iyy_o = Ixy_o = 0.0
    for p in loop_props:
        sign = 1.0 if p.loop_type == "outer" else -1.0
        A += sign * p.area_mm2
        Cx_num += sign * p.area_mm2 * p.cx_mm
        Cy_num += sign * p.area_mm2 * p.cy_mm
        Ixx_o += sign * p.ixx_o_mm4
        Iyy_o += sign * p.iyy_o_mm4
        Ixy_o += sign * p.ixy_o_mm4
    if A <= 0:
        errors.append("Composite section area is not positive after subtracting openings.")
        return {"valid": False, "errors": errors, "warnings": warnings, "coordinates": coords}

    cx = Cx_num / A
    cy = Cy_num / A
    Ixx_c = Ixx_o - A * cy * cy
    Iyy_c = Iyy_o - A * cx * cx
    Ixy_c = Ixy_o - A * cx * cy

    xmin = float(coords["x_mm"].min())
    xmax = float(coords["x_mm"].max())
    ymin = float(coords["y_mm"].min())
    ymax = float(coords["y_mm"].max())
    y_top = ymax - cy
    y_bottom = cy - ymin
    x_left = cx - xmin
    x_right = xmax - cx
    S_top = Ixx_c / y_top if y_top > 0 else 0.0
    S_bottom = Ixx_c / y_bottom if y_bottom > 0 else 0.0
    S_left = Iyy_c / x_left if x_left > 0 else 0.0
    S_right = Iyy_c / x_right if x_right > 0 else 0.0

    return {
        "valid": True,
        "errors": errors,
        "warnings": warnings,
        "coordinates": coords,
        "loops": loop_props,
        "A_mm2": A,
        "A_m2": A / 1e6,
        "cx_mm": cx,
        "cy_mm": cy,
        "Ixx_mm4": Ixx_c,
        "Iyy_mm4": Iyy_c,
        "Ixy_mm4": Ixy_c,
        "I33_m4": Ixx_c / 1e12,
        "I22_m4": Iyy_c / 1e12,
        "Ixy_m4": Ixy_c / 1e12,
        "S_top_m3": S_top / 1e9,
        "S_bottom_m3": S_bottom / 1e9,
        "S_left_m3": S_left / 1e9,
        "S_right_m3": S_right / 1e9,
        "xcg_from_left_m": x_left / 1000.0,
        "xcg_from_right_m": x_right / 1000.0,
        "ycg_from_bottom_m": y_bottom / 1000.0,
        "yt_from_top_m": y_top / 1000.0,
        "width_m": (xmax - xmin) / 1000.0,
        "depth_m": (ymax - ymin) / 1000.0,
        "bounds_mm": {"xmin": xmin, "xmax": xmax, "ymin": ymin, "ymax": ymax},
        "mapping_note": "App x/y coordinates are read from CSiBridge section X/Y. I33 is reported from Ixx about the horizontal centroidal axis and I22 from Iyy about the vertical centroidal axis for BG40 review mapping.",
    }



def estimate_thin_walled_closed_box_j(
    df: pd.DataFrame,
    *,
    t_top_m: float,
    t_bot_m: float,
    t_web_m: float,
    include_corner_correction: bool = True,
) -> dict[str, Any]:
    """Estimate St. Venant torsional constant J for a single-cell closed box.

    This is a thin-walled closed-section estimate intended for QA/preliminary
    comparison only.  It uses the Opening Polygon as the inner void boundary,
    classifies void-boundary segments as top slab / bottom slab / web based on
    their location, and estimates the wall centreline area as:

        A_m ≈ A_inner + 0.5 Σ(l_i t_i) + corner correction

    Then:

        J ≈ 4 A_m² / Σ(l_i/t_i)

    The method is deliberately labelled as an estimate because CSiBridge/J from
    section analysis or FEA remains the preferred design-source value.
    """
    coords = normalize_coordinate_rows(df)
    props = calculate_section_properties(coords)
    if not props.get("valid"):
        return {"valid": False, "errors": props.get("errors", ["Invalid section coordinates"]), "warnings": props.get("warnings", [])}

    t_top = float(t_top_m)
    t_bot = float(t_bot_m)
    t_web = float(t_web_m)
    if min(t_top, t_bot, t_web) <= 0:
        return {"valid": False, "errors": ["Wall thicknesses must be positive for thin-walled J estimate."], "warnings": []}

    hole_groups = [(name, g) for name, g in coords.groupby("loop_name", sort=False) if str(g["loop_type"].iloc[0]) == "hole"]
    if len(hole_groups) != 1:
        return {"valid": False, "errors": ["Thin-walled closed-box J estimate requires exactly one Opening Polygon / cell."], "warnings": []}

    name, g = hole_groups[0]
    pts_mm = _remove_consecutive_duplicate_points(list(zip(g["x_mm"].astype(float), g["y_mm"].astype(float))))
    if len(pts_mm) < 3:
        return {"valid": False, "errors": ["Opening Polygon has fewer than 3 unique points."], "warnings": []}

    lp = _loop_properties(pts_mm, "hole", str(name))
    inner_area_m2 = abs(lp.area_mm2) / 1e6
    bounds = props["bounds_mm"]
    ymin = float(bounds["ymin"])
    ymax = float(bounds["ymax"])
    depth = max(ymax - ymin, 1e-9)
    cy = float(props["cy_mm"])
    bottom_threshold = ymin + 0.35 * depth

    segment_rows: list[dict[str, Any]] = []
    sum_l_over_t = 0.0
    sum_l_t = 0.0
    for i, (p0, p1) in enumerate(zip(pts_mm, pts_mm[1:] + pts_mm[:1]), start=1):
        x0, y0 = p0
        x1, y1 = p1
        length_m = sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2) / 1000.0
        if length_m <= 1e-9:
            continue
        y_mid = 0.5 * (y0 + y1)
        if y_mid >= cy:
            component = "top slab / upper haunch"
            t = t_top
        elif y_mid <= bottom_threshold:
            component = "bottom slab / lower corner"
            t = t_bot
        else:
            component = "web"
            t = t_web
        sum_l_over_t += length_m / t
        sum_l_t += length_m * t
        segment_rows.append({
            "segment": i,
            "component": component,
            "length_m": length_m,
            "t_m": t,
            "l_over_t": length_m / t,
        })

    if sum_l_over_t <= 0:
        return {"valid": False, "errors": ["Could not compute Σ(l/t) for thin-walled J estimate."], "warnings": []}

    # First-order variable-thickness offset estimate from the inner void boundary.
    centerline_area_m2 = inner_area_m2 + 0.5 * sum_l_t
    if include_corner_correction:
        # Approximate the corner term using the average half-thickness. This improves
        # rectangular/box estimates but remains a QA-level estimate.
        avg_half_thickness = 0.5 * sum_l_t / sum(seg["length_m"] for seg in segment_rows)
        centerline_area_m2 += pi * avg_half_thickness * avg_half_thickness

    j_m4 = 4.0 * centerline_area_m2 * centerline_area_m2 / sum_l_over_t
    warnings = [
        "Thin-walled J is an estimate for QA/preliminary comparison. Use FEA/manual J for design unless the estimate is explicitly reviewed and adopted.",
        "Segment thickness classification is inferred from Opening Polygon location: upper segments use t_top, lower segments use t_bot, and side segments use t_web.",
    ]
    return {
        "valid": True,
        "errors": [],
        "warnings": warnings,
        "J_m4": j_m4,
        "Am_m2": centerline_area_m2,
        "inner_area_m2": inner_area_m2,
        "sum_l_over_t": sum_l_over_t,
        "sum_l_t_m2": sum_l_t,
        "segment_rows": segment_rows,
        "method": "Thin-walled single-cell closed-box estimate: J ≈ 4Am² / Σ(l/t)",
    }


def default_coordinate_template() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"loop_name": "Structural Polygon 1", "point_no": 1, "x_mm": 0.0, "y_mm": 0.0},
            {"loop_name": "Structural Polygon 1", "point_no": 2, "x_mm": 4000.0, "y_mm": 0.0},
            {"loop_name": "Structural Polygon 1", "point_no": 3, "x_mm": 4000.0, "y_mm": 2000.0},
            {"loop_name": "Structural Polygon 1", "point_no": 4, "x_mm": 0.0, "y_mm": 2000.0},
            {"loop_name": "Opening Polygon 1", "point_no": 1, "x_mm": 1000.0, "y_mm": 500.0},
            {"loop_name": "Opening Polygon 1", "point_no": 2, "x_mm": 3000.0, "y_mm": 500.0},
            {"loop_name": "Opening Polygon 1", "point_no": 3, "x_mm": 3000.0, "y_mm": 1500.0},
            {"loop_name": "Opening Polygon 1", "point_no": 4, "x_mm": 1000.0, "y_mm": 1500.0},
        ]
    )
