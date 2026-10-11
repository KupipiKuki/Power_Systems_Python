"""minicad_dxf.py - Headless R12 (AC1009) DXF generation and editing.

Produces and reads DXF files whose conventions match the MiniCAD interactive
editor (../assets/minicad.html), so files round-trip between the two and also
open in AutoCAD, LibreCAD, QCAD, DraftSight, etc.

Units are dimensionless. Angles in the public API are DEGREES, CCW positive.
Colors use the AutoCAD Color Index (ACI); entities are BYLAYER unless a color
or linetype is set on the entity. Supported linetypes: CONTINUOUS, DASHED,
DOTTED, DASHDOT, HIDDEN, CENTER.

Typical use:

    from minicad_dxf import Drawing
    d = Drawing()
    d.add_layer("WALLS", color=5, linetype="CONTINUOUS")
    d.add_line((0, 0), (100, 0), layer="WALLS")
    d.add_arc((100, 0), radius=50, start_deg=0, end_deg=90, layer="WALLS")
    d.add_circle((50, 50), 10)
    d.add_rect((10, 10), (90, 90))
    d.add_text((10, 20), "NOTE 1", height=5, align="left")
    d.save_dxf("out.dxf")     # R12 DXF (portable)
    d.save_json("out.json")   # native MiniCAD format (opens in the editor)

Editing an existing file:

    d = Drawing.load("existing.dxf")   # or .json
    d.entities = [e for e in d.entities if e["type"] != "text"]  # drop labels
    d.translate(10, 0)
    d.rotate(45, center=(50, 50))
    d.save_dxf("existing.dxf")

Run `python minicad_dxf.py --selftest` to verify a round-trip.
"""
import copy
import json
import math

# --- Standards shared with the editor -------------------------------------
ACI_NAME = {7: "White/Black", 1: "Red", 30: "Orange", 2: "Yellow", 3: "Green",
            4: "Cyan", 5: "Blue", 6: "Magenta", 8: "Gray", 9: "Lt Gray"}
PALETTE = [7, 1, 30, 2, 3, 4, 5, 6, 8, 9]
LTYPES = ["CONTINUOUS", "DASHED", "DOTTED", "DASHDOT", "HIDDEN", "CENTER"]
LTDEF = {
    "CONTINUOUS": {"d": "Solid line", "e": []},
    "DASHED":     {"d": "Dashed __ __ __", "e": [0.5, -0.25]},
    "DOTTED":     {"d": "Dotted . . .", "e": [0, -0.25]},
    "DASHDOT":    {"d": "Dash dot _._._", "e": [0.5, -0.25, 0, -0.25]},
    "HIDDEN":     {"d": "Hidden _ _ _", "e": [0.25, -0.125]},
    "CENTER":     {"d": "Center ____ _", "e": [1.0, -0.25, 0.25, -0.25]},
}
TWO_PI = 2 * math.pi
TRANSFORM_EPS = 1e-9


def _norm_deg(d):
    d = d % 360.0
    return d + 360.0 if d < 0 else d


def _norm_rad(r):
    r = r % TWO_PI
    return r + TWO_PI if r < 0 else r


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _fmt(v):
    """Format a number like the editor: integers without a trailing .0."""
    f = float(v)
    if f == int(f):
        return str(int(f))
    return repr(round(f, 6)).rstrip('0').rstrip('.') if '.' in repr(round(f, 6)) else repr(round(f, 6))


# --- Geometry & Decomposition Utilities -----------------------------------

def rect_corners(e):
    """Returns 4 corners of a rectangle in CCW order: [TL, TR, BR, BL]."""
    ax, ay = e["a"]["x"], e["a"]["y"]
    bx, by = e["b"]["x"], e["b"]["y"]
    return [
        {"x": ax, "y": ay},
        {"x": bx, "y": ay},
        {"x": bx, "y": by},
        {"x": ax, "y": by}
    ]


def dim_geom(e):
    """Computes dimension line, witness endpoints, measurement, and angle."""
    p1 = e["p1"]
    p2 = e["p2"]
    dp = e["dp"]
    dtype = e.get("dtype", "aligned")

    if dtype == "horizontal":
        d1 = {"x": p1["x"], "y": dp["y"]}
        d2 = {"x": p2["x"], "y": dp["y"]}
        measure = abs(p2["x"] - p1["x"])
    elif dtype == "vertical":
        d1 = {"x": dp["x"], "y": p1["y"]}
        d2 = {"x": dp["x"], "y": p2["y"]}
        measure = abs(p2["y"] - p1["y"])
    else:
        dx = p2["x"] - p1["x"]
        dy = p2["y"] - p1["y"]
        length = math.hypot(dx, dy)
        if length < 1e-9:
            dx, dy, length = 1.0, 0.0, 1.0
        ux = dx / length
        uy = dy / length
        nx = -uy
        ny = ux
        off = (dp["x"] - p1["x"]) * nx + (dp["y"] - p1["y"]) * ny
        d1 = {"x": p1["x"] + nx * off, "y": p1["y"] + ny * off}
        d2 = {"x": p2["x"] + nx * off, "y": p2["y"] + ny * off}
        measure = length

    ang = math.atan2(d2["y"] - d1["y"], d2["x"] - d1["x"])
    return {"p1": p1, "p2": p2, "d1": d1, "d2": d2, "measure": measure, "ang": ang}


def dim_text(e, g):
    if e.get("text"):
        return str(e["text"])
    return _fmt(round(g["measure"], 2))


def callout_geom(e, default_text_height=5):
    h = e.get("h") or default_text_height
    pad = h * 0.6
    txt = e.get("text") or ""
    tw = max(len(txt) * h * 0.58, h)
    w = tw + 2 * pad
    hgt = h + 2 * pad
    bx, by = e["box"]["x"], e["box"]["y"]
    tl = {"x": bx, "y": by}
    tr = {"x": bx + w, "y": by}
    br = {"x": bx + w, "y": by - hgt}
    bl = {"x": bx, "y": by - hgt}
    return {
        "w": w, "hgt": hgt, "pad": pad,
        "corners": [tl, tr, br, bl],
        "center": {"x": bx + w / 2, "y": by - hgt / 2},
        "textAt": {"x": bx + pad, "y": by - pad - h * 0.82}
    }


def seg_seg_param(a, b, c, d):
    d1x = b["x"] - a["x"]
    d1y = b["y"] - a["y"]
    d2x = d["x"] - c["x"]
    d2y = d["y"] - c["y"]
    den = d1x * d2y - d1y * d2x
    if abs(den) < 1e-12:
        return None
    t = ((c["x"] - a["x"]) * d2y - (c["y"] - a["y"]) * d2x) / den
    u = ((c["x"] - a["x"]) * d1y - (c["y"] - a["y"]) * d1x) / den
    if -1e-9 <= u <= 1 + 1e-9 and -1e-9 <= t <= 1 + 1e-9:
        return t
    return None


def callout_attach(g, target):
    c = g["center"]
    cor = g["corners"]
    for i in range(4):
        r = seg_seg_param(c, target, cor[i], cor[(i + 1) % 4])
        if r is not None and r > 1e-6:
            return {"x": c["x"] + (target["x"] - c["x"]) * r, "y": c["y"] + (target["y"] - c["y"]) * r}
    return c


def hatch_lines(boundary, spacing, angle_deg):
    if not boundary or len(boundary) < 3 or spacing <= 0:
        return []
    ang = math.radians(angle_deg)
    dx, dy = math.cos(ang), math.sin(ang)
    nx, ny = -dy, dx
    mn = 1e18
    mx = -1e18
    tmn = 1e18
    tmx = -1e18
    for p in boundary:
        dd = p["x"] * nx + p["y"] * ny
        tt = p["x"] * dx + p["y"] * dy
        if dd < mn: mn = dd
        if dd > mx: mx = dd
        if tt < tmn: tmn = tt
        if tt > tmx: tmx = tt

    segs = []
    start = math.ceil(mn / spacing) * spacing
    pad = 1.0
    d = start
    while d <= mx + 1e-9:
        bx = nx * d
        by = ny * d
        a = {"x": bx + dx * (tmn - pad), "y": by + dy * (tmn - pad)}
        b = {"x": bx + dx * (tmx + pad), "y": by + dy * (tmx + pad)}
        ts = []
        n = len(boundary)
        for i in range(n):
            r = seg_seg_param(a, b, boundary[i], boundary[(i + 1) % n])
            if r is not None:
                ts.append(r)
        ts.sort()
        for i in range(0, len(ts) - 1, 2):
            t1, t2 = ts[i], ts[i + 1]
            if t2 - t1 < 1e-9:
                continue
            segs.append([
                {"x": a["x"] + (b["x"] - a["x"]) * t1, "y": a["y"] + (b["y"] - a["y"]) * t1},
                {"x": a["x"] + (b["x"] - a["x"]) * t2, "y": a["y"] + (b["y"] - a["y"]) * t2}
            ])
        d += spacing
    return segs


def hatch_segs(e):
    b = e.get("boundary", [])
    sp = e.get("spacing", 4)
    ang = e.get("angle", 45)
    out = hatch_lines(b, sp, ang)
    if e.get("pattern") == "cross":
        out.extend(hatch_lines(b, sp, ang + 90))
    return out


def cloud_arcs(e):
    pts = e.get("pts", [])
    if not pts or len(pts) < 2:
        return []
    arcs = []
    bump = e.get("bump", 6)
    cx = sum(p["x"] for p in pts) / len(pts)
    cy = sum(p["y"] for p in pts) / len(pts)
    seg_list = []
    for i in range(len(pts) - 1):
        seg_list.append((pts[i], pts[i + 1]))
    if e.get("closed") and len(pts) > 2:
        seg_list.append((pts[-1], pts[0]))
    for A, B in seg_list:
        L = math.hypot(B["x"] - A["x"], B["y"] - A["y"])
        if L < 1e-9:
            continue
        n = max(1, round(L / bump))
        ux = (B["x"] - A["x"]) / L
        uy = (B["y"] - A["y"]) / L
        step = L / n
        for k in range(n):
            sx = A["x"] + ux * step * k
            sy = A["y"] + uy * step * k
            ex = A["x"] + ux * step * (k + 1)
            ey = A["y"] + uy * step * (k + 1)
            mx = (sx + ex) / 2
            my = (sy + ey) / 2
            nnx, nny = -uy, ux
            if e.get("closed"):
                if (mx - cx) * nnx + (my - cy) * nny < 0:
                    nnx, nny = -nnx, -nny
            a0 = math.atan2(sy - my, sx - mx)
            sweep = math.pi
            mid_a = a0 + sweep / 2
            if math.cos(mid_a) * nnx + math.sin(mid_a) * nny < 0:
                sweep = -math.pi
            arcs.append({"c": {"x": mx, "y": my}, "r": step / 2, "a0": a0, "sweep": sweep})
    return arcs


rectCorners = rect_corners
dimGeom = dim_geom
dimText = dim_text
calloutGeom = callout_geom
calloutAttach = callout_attach
hatchLines = hatch_lines
hatchSegs = hatch_segs
cloudArcs = cloud_arcs


def bbox(e):
    """Calculates axis-aligned bounding box {"minx", "miny", "maxx", "maxy"} for an entity."""
    t = e.get("type")
    if t in ("arc", "circle"):
        c, r = e["c"], e["r"]
        return {"minx": c["x"] - r, "miny": c["y"] - r, "maxx": c["x"] + r, "maxy": c["y"] + r}
    if t == "ellipse":
        c, rx, ry, rot = e["c"], e["rx"], e["ry"], e.get("rot", 0)
        hw = math.hypot(rx * math.cos(rot), -ry * math.sin(rot))
        hh = math.hypot(rx * math.sin(rot), ry * math.cos(rot))
        return {"minx": c["x"] - hw, "miny": c["y"] - hh, "maxx": c["x"] + hw, "maxy": c["y"] + hh}
    if t == "line":
        return {
            "minx": min(e["a"]["x"], e["b"]["x"]), "miny": min(e["a"]["y"], e["b"]["y"]),
            "maxx": max(e["a"]["x"], e["b"]["x"]), "maxy": max(e["a"]["y"], e["b"]["y"])
        }
    if t == "rect":
        if "a" in e and "b" in e:
            return {
                "minx": min(e["a"]["x"], e["b"]["x"]), "miny": min(e["a"]["y"], e["b"]["y"]),
                "maxx": max(e["a"]["x"], e["b"]["x"]), "maxy": max(e["a"]["y"], e["b"]["y"])
            }
        elif "pts" in e:
            xs = [p["x"] for p in e["pts"]]
            ys = [p["y"] for p in e["pts"]]
            return {"minx": min(xs), "miny": min(ys), "maxx": max(xs), "maxy": max(ys)}
    if t in ("poly", "cloud"):
        xs = [p["x"] for p in e.get("pts", [])]
        ys = [p["y"] for p in e.get("pts", [])]
        pad = e.get("bump", 6) if t == "cloud" else 0
        return {"minx": min(xs) - pad, "miny": min(ys) - pad, "maxx": max(xs) + pad, "maxy": max(ys) + pad}
    if t == "hatch":
        xs = [p["x"] for p in e.get("boundary", [])]
        ys = [p["y"] for p in e.get("boundary", [])]
        return {"minx": min(xs), "miny": min(ys), "maxx": max(xs), "maxy": max(ys)}
    if t == "dim":
        xs = [e["p1"]["x"], e["p2"]["x"], e["dp"]["x"]]
        ys = [e["p1"]["y"], e["p2"]["y"], e["dp"]["y"]]
        return {"minx": min(xs), "miny": min(ys), "maxx": max(xs), "maxy": max(ys)}
    if t == "callout":
        g = calloutGeom(e)
        xs = [p["x"] for p in g["corners"]] + [p["x"] for p in e.get("leaders", [])]
        ys = [p["y"] for p in g["corners"]] + [p["y"] for p in e.get("leaders", [])]
        return {"minx": min(xs), "miny": min(ys), "maxx": max(xs), "maxy": max(ys)}
    if t == "point":
        return {"minx": e["p"]["x"], "miny": e["p"]["y"], "maxx": e["p"]["x"], "maxy": e["p"]["y"]}
    if t == "text":
        h = e.get("h", 5)
        txt = e.get("text", "")
        w = len(txt) * h * 0.6
        return {"minx": e["p"]["x"], "miny": e["p"]["y"], "maxx": e["p"]["x"] + w, "maxy": e["p"]["y"] + h}
    return {"minx": 0.0, "miny": 0.0, "maxx": 0.0, "maxy": 0.0}


# --- Transformations ------------------------------------------------------

def _transform_point(p, m):
    x, y = p["x"], p["y"]
    return {
        "x": m["a"] * x + m["c"] * y + m["e"],
        "y": m["b"] * x + m["d"] * y + m["f"]
    }


def _transform_entity(e, m):
    t = e["type"]
    T = lambda pt: _transform_point(pt, m)

    if t == "line":
        e["a"] = T(e["a"])
        e["b"] = T(e["b"])
    elif t == "circle":
        e["c"] = T(e["c"])
        scale = math.hypot(m["a"], m["b"])
        e["r"] *= scale
    elif t == "arc":
        e["c"] = T(e["c"])
        scale = math.hypot(m["a"], m["b"])
        e["r"] *= scale
        rot = math.atan2(m["b"], m["a"])
        det = m["a"] * m["d"] - m["b"] * m["c"]
        if det < 0:
            # Reflection
            e["a0"] = _norm_rad(rot - e["a0"])
            e["sweep"] = -e["sweep"]
        else:
            e["a0"] = _norm_rad(e["a0"] + rot)
    elif t == "ellipse":
        ang = e.get("rot", 0)
        maj = {"x": e["c"]["x"] + e["rx"] * math.cos(ang), "y": e["c"]["y"] + e["rx"] * math.sin(ang)}
        tc = T(e["c"])
        tm = T(maj)
        e["c"] = tc
        scale = math.hypot(m["a"], m["b"])
        e["rx"] *= scale
        e["ry"] *= scale
        e["rot"] = math.atan2(tm["y"] - tc["y"], tm["x"] - tc["x"])
    elif t == "point":
        e["p"] = T(e["p"])
    elif t == "text":
        e["p"] = T(e["p"])
        rot = math.degrees(math.atan2(m["b"], m["a"]))
        e["rot"] = _norm_deg(e.get("rot", 0) + rot)
        scale = math.hypot(m["a"], m["b"])
        e["h"] = (e.get("h", 5)) * scale
    elif t == "rect":
        if "a" in e and "b" in e:
            corners = rect_corners(e)
            t_corners = [T(p) for p in corners]
            # Check if still axis-aligned
            is_axis = all(
                abs(t_corners[i]["x"] - t_corners[(i + 1) % 4]["x"]) <= TRANSFORM_EPS or
                abs(t_corners[i]["y"] - t_corners[(i + 1) % 4]["y"]) <= TRANSFORM_EPS
                for i in range(4)
            )
            if is_axis:
                xs = [p["x"] for p in t_corners]
                ys = [p["y"] for p in t_corners]
                e["a"] = {"x": min(xs), "y": min(ys)}
                e["b"] = {"x": max(xs), "y": max(ys)}
            else:
                e["type"] = "poly"
                e["pts"] = t_corners
                e["closed"] = True
                del e["a"]
                del e["b"]
        elif "pts" in e:
            e["pts"] = [T(p) for p in e["pts"]]
    elif t == "poly":
        e["pts"] = [T(p) for p in e.get("pts", [])]
    elif t == "dim":
        e["p1"] = T(e["p1"])
        e["p2"] = T(e["p2"])
        e["dp"] = T(e["dp"])
        scale = math.hypot(m["a"], m["b"])
        if e.get("h"):
            e["h"] *= scale
    elif t == "hatch":
        e["boundary"] = [T(p) for p in e.get("boundary", [])]
        rot = math.degrees(math.atan2(m["b"], m["a"]))
        e["angle"] = _norm_deg(e.get("angle", 45) + rot)
        scale = math.hypot(m["a"], m["b"])
        e["spacing"] = e.get("spacing", 4) * scale
    elif t == "cloud":
        e["pts"] = [T(p) for p in e.get("pts", [])]
        scale = math.hypot(m["a"], m["b"])
        e["bump"] = e.get("bump", 6) * scale
    elif t == "callout":
        e["box"] = T(e["box"])
        e["leaders"] = [T(p) for p in e.get("leaders", [])]
        scale = math.hypot(m["a"], m["b"])
        if e.get("h"):
            e["h"] *= scale
    return e


# --- Explode Engine -------------------------------------------------------

def explode_entity(e, default_text_height=5):
    """Decomposes compound entities into primitive lines, arcs, and text."""
    if not e:
        return None
    t = e.get("type")

    if t == "rect":
        c = rect_corners(e) if ("a" in e and "b" in e) else e.get("pts", [])
        if len(c) < 4:
            return None
        lines = []
        for i in range(4):
            lines.append({
                "type": "line",
                "a": {"x": c[i]["x"], "y": c[i]["y"]},
                "b": {"x": c[(i + 1) % 4]["x"], "y": c[(i + 1) % 4]["y"]},
                "layer": e.get("layer", "0"),
                "color": e.get("color"),
                "linetype": e.get("linetype")
            })
        return lines

    if t == "poly":
        pts = e.get("pts", [])
        if len(pts) < 2:
            return None
        lines = []
        for i in range(len(pts) - 1):
            lines.append({
                "type": "line",
                "a": {"x": pts[i]["x"], "y": pts[i]["y"]},
                "b": {"x": pts[i + 1]["x"], "y": pts[i + 1]["y"]},
                "layer": e.get("layer", "0"),
                "color": e.get("color"),
                "linetype": e.get("linetype")
            })
        if e.get("closed") and len(pts) > 2:
            lines.append({
                "type": "line",
                "a": {"x": pts[-1]["x"], "y": pts[-1]["y"]},
                "b": {"x": pts[0]["x"], "y": pts[0]["y"]},
                "layer": e.get("layer", "0"),
                "color": e.get("color"),
                "linetype": e.get("linetype")
            })
        return lines

    if t == "callout":
        g = calloutGeom(e, default_text_height)
        parts = []
        # Box polyline
        parts.append({
            "type": "poly",
            "pts": [{"x": p["x"], "y": p["y"]} for p in g["corners"]],
            "closed": True,
            "layer": e.get("layer", "0"),
            "color": e.get("color"),
            "linetype": e.get("linetype")
        })
        # Text label
        parts.append({
            "type": "text",
            "p": {"x": g["textAt"]["x"], "y": g["textAt"]["y"]},
            "h": e.get("h") or default_text_height,
            "text": e.get("text", ""),
            "rot": 0,
            "align": "left",
            "layer": e.get("layer", "0"),
            "color": e.get("color")
        })
        # Leaders
        for tgt in e.get("leaders", []):
            at = callout_attach(g, tgt)
            parts.append({
                "type": "line",
                "a": {"x": at["x"], "y": at["y"]},
                "b": {"x": tgt["x"], "y": tgt["y"]},
                "layer": e.get("layer", "0"),
                "color": e.get("color"),
                "linetype": e.get("linetype")
            })
        return parts

    if t == "hatch":
        parts = []
        # Boundary polyline
        parts.append({
            "type": "poly",
            "pts": [{"x": p["x"], "y": p["y"]} for p in e.get("boundary", [])],
            "closed": True,
            "layer": e.get("layer", "0"),
            "color": e.get("color"),
            "linetype": e.get("linetype")
        })
        # Hatch lines
        for s in hatch_segs(e):
            parts.append({
                "type": "line",
                "a": {"x": s[0]["x"], "y": s[0]["y"]},
                "b": {"x": s[1]["x"], "y": s[1]["y"]},
                "layer": e.get("layer", "0"),
                "color": e.get("color"),
                "linetype": e.get("linetype")
            })
        return parts

    if t == "dim":
        g = dim_geom(e)
        parts = []
        # 2 extension lines
        parts.append({
            "type": "line", "a": {"x": e["p1"]["x"], "y": e["p1"]["y"]}, "b": {"x": g["d1"]["x"], "y": g["d1"]["y"]},
            "layer": e.get("layer", "0"), "color": e.get("color"), "linetype": e.get("linetype")
        })
        parts.append({
            "type": "line", "a": {"x": e["p2"]["x"], "y": e["p2"]["y"]}, "b": {"x": g["d2"]["x"], "y": g["d2"]["y"]},
            "layer": e.get("layer", "0"), "color": e.get("color"), "linetype": e.get("linetype")
        })
        # Dimension line
        parts.append({
            "type": "line", "a": {"x": g["d1"]["x"], "y": g["d1"]["y"]}, "b": {"x": g["d2"]["x"], "y": g["d2"]["y"]},
            "layer": e.get("layer", "0"), "color": e.get("color"), "linetype": e.get("linetype")
        })
        # Text
        mx = (g["d1"]["x"] + g["d2"]["x"]) / 2
        my = (g["d1"]["y"] + g["d2"]["y"]) / 2
        parts.append({
            "type": "text", "p": {"x": mx, "y": my},
            "h": e.get("h") or default_text_height,
            "text": dim_text(e, g),
            "rot": math.degrees(g["ang"]),
            "align": "center",
            "layer": e.get("layer", "0"), "color": e.get("color")
        })
        return parts

    return None


# --- Join Engine ----------------------------------------------------------

def _pts_collinear(p1, p2, p3, tol=1e-4):
    dx1, dy1 = p2["x"] - p1["x"], p2["y"] - p1["y"]
    dx2, p3x, p3y = p3["x"] - p2["x"], p3["x"], p3["y"]
    dy2 = p3y - p2["y"]
    cross = dx1 * dy2 - dy1 * dx2
    dot = dx1 * dx2 + dy1 * dy2
    return abs(cross) < tol and dot >= 0


def _simplify_chain(pts, tol=1e-4):
    if len(pts) <= 2:
        return pts
    res = [pts[0]]
    for i in range(1, len(pts) - 1):
        prev, curr, nxt = res[-1], pts[i], pts[i + 1]
        if _pts_collinear(prev, curr, nxt, tol):
            continue
        res.append(curr)
    res.append(pts[-1])
    return res


def join_chains(chains, tol=0.5):
    """Joins chain dicts {"pts", "closed", "layer", "color", "linetype", "wasLineOnly"}."""
    working = [dict(c, pts=list(c["pts"])) for c in chains]
    merged_any = True

    while merged_any:
        merged_any = False
        found_merge = False
        for i in range(len(working)):
            if found_merge:
                break
            for j in range(i + 1, len(working)):
                c1, c2 = working[i], working[j]
                if c1.get("closed") or c2.get("closed"):
                    continue
                c1_s, c1_e = c1["pts"][0], c1["pts"][-1]
                c2_s, c2_e = c2["pts"][0], c2["pts"][-1]

                if math.hypot(c1_e["x"] - c2_s["x"], c1_e["y"] - c2_s["y"]) <= tol:
                    c1["pts"].extend(c2["pts"][1:])
                    c1["wasLineOnly"] = c1["wasLineOnly"] and c2["wasLineOnly"]
                    working.pop(j)
                    merged_any = True
                    found_merge = True
                    break
                if math.hypot(c1_e["x"] - c2_e["x"], c1_e["y"] - c2_e["y"]) <= tol:
                    c1["pts"].extend(list(reversed(c2["pts"]))[1:])
                    c1["wasLineOnly"] = c1["wasLineOnly"] and c2["wasLineOnly"]
                    working.pop(j)
                    merged_any = True
                    found_merge = True
                    break
                if math.hypot(c1_s["x"] - c2_e["x"], c1_s["y"] - c2_e["y"]) <= tol:
                    c1["pts"] = c2["pts"] + c1["pts"][1:]
                    c1["wasLineOnly"] = c1["wasLineOnly"] and c2["wasLineOnly"]
                    working.pop(j)
                    merged_any = True
                    found_merge = True
                    break
                if math.hypot(c1_s["x"] - c2_s["x"], c1_s["y"] - c2_s["y"]) <= tol:
                    c1["pts"] = list(reversed(c1["pts"])) + c2["pts"][1:]
                    c1["wasLineOnly"] = c1["wasLineOnly"] and c2["wasLineOnly"]
                    working.pop(j)
                    merged_any = True
                    found_merge = True
                    break

    output = []
    for c in working:
        pts = _simplify_chain(c["pts"])
        is_closed = bool(c.get("closed"))
        if not is_closed and len(pts) > 2:
            p0, pend = pts[0], pts[-1]
            if math.hypot(p0["x"] - pend["x"], p0["y"] - pend["y"]) <= tol:
                is_closed = True
                pts.pop()
        if not is_closed and len(pts) == 2 and c.get("wasLineOnly"):
            output.append({
                "type": "line", "a": pts[0], "b": pts[1],
                "layer": c.get("layer", "0"), "color": c.get("color"), "linetype": c.get("linetype")
            })
        else:
            output.append({
                "type": "poly", "pts": pts, "closed": is_closed,
                "layer": c.get("layer", "0"), "color": c.get("color"), "linetype": c.get("linetype")
            })
    return output


# --- Main Drawing Class ---------------------------------------------------

class Drawing:
    """An in-memory MiniCAD drawing: layers + entities.

    Entities are plain dicts matching the editor's internal shape so the JSON
    format is byte-compatible with the interactive tool. Use the add_* helpers
    rather than building dicts by hand.
    """

    def __init__(self):
        self.layers = [{"name": "0", "color": 7, "linetype": "CONTINUOUS", "visible": True}]
        self.entities = []
        self.grid_spacing = 10
        self.text_height = 5
        self.active_layer = "0"

    # -- layers -------------------------------------------------------------
    def add_layer(self, name, color=7, linetype="CONTINUOUS", visible=True):
        name = str(name)
        lt = linetype.upper()
        if lt not in LTYPES:
            lt = "CONTINUOUS"
        for l in self.layers:
            if l["name"] == name:
                l.update(color=color, linetype=lt, visible=visible)
                return l
        l = {"name": name, "color": color, "linetype": lt, "visible": visible}
        self.layers.append(l)
        return l

    def _lt(self, linetype):
        if linetype is None:
            return None
        lt = str(linetype).upper()
        return lt if lt in LTYPES and lt != "BYLAYER" else None

    def _base(self, layer, color, linetype):
        return {"layer": str(layer) if layer else "0",
                "color": (int(color) if color is not None else None),
                "linetype": self._lt(linetype)}

    # -- entity constructors ------------------------------------------------
    def add_line(self, a, b, layer="0", color=None, linetype=None):
        e = {"type": "line", "a": {"x": a[0], "y": a[1]}, "b": {"x": b[0], "y": b[1]}}
        e.update(self._base(layer, color, linetype))
        self.entities.append(e)
        return e

    def add_arc(self, center, radius, start_deg, end_deg, layer="0", color=None, linetype=None):
        """Arc from start_deg to end_deg, sweeping CCW (positive)."""
        a0 = math.radians(start_deg)
        sweep = math.radians(_norm_deg(end_deg - start_deg)) or TWO_PI
        e = {"type": "arc", "c": {"x": center[0], "y": center[1]}, "r": radius,
             "a0": a0, "sweep": sweep}
        e.update(self._base(layer, color, linetype))
        self.entities.append(e)
        return e

    def add_arc_scE(self, start, center, end, cw=False, layer="0", color=None, linetype=None):
        """Arc by start / center / end points (matches the editor's arc tool)."""
        cx, cy = center
        r = math.hypot(start[0] - cx, start[1] - cy)
        a0 = math.atan2(start[1] - cy, start[0] - cx)
        a1 = math.atan2(end[1] - cy, end[0] - cx)
        sweep = a1 - a0
        while sweep <= 0:
            sweep += TWO_PI
        if cw:
            sweep -= TWO_PI
        e = {"type": "arc", "c": {"x": cx, "y": cy}, "r": r, "a0": a0, "sweep": sweep}
        e.update(self._base(layer, color, linetype))
        self.entities.append(e)
        return e

    def add_circle(self, center, radius, layer="0", color=None, linetype=None):
        e = {"type": "circle", "c": {"x": center[0], "y": center[1]}, "r": radius}
        e.update(self._base(layer, color, linetype))
        self.entities.append(e)
        return e

    def add_ellipse(self, center, rx, ry, rot_deg=0, layer="0", color=None, linetype=None):
        e = {"type": "ellipse", "c": {"x": center[0], "y": center[1]},
             "rx": rx, "ry": ry, "rot": math.radians(rot_deg)}
        e.update(self._base(layer, color, linetype))
        self.entities.append(e)
        return e

    def add_point(self, p, layer="0", color=None, linetype=None):
        e = {"type": "point", "p": {"x": p[0], "y": p[1]}}
        e.update(self._base(layer, color, linetype))
        self.entities.append(e)
        return e

    def add_text(self, p, text, height=None, rot_deg=0, align="left",
                 layer="0", color=None, linetype=None):
        if align not in ("left", "center", "right"):
            align = "left"
        e = {"type": "text", "p": {"x": p[0], "y": p[1]}, "text": str(text),
             "h": height if height is not None else self.text_height,
             "rot": rot_deg, "align": align}
        e.update(self._base(layer, color, linetype))
        self.entities.append(e)
        return e

    def add_polyline(self, pts, closed=False, layer="0", color=None, linetype=None):
        e = {"type": "poly", "pts": [{"x": p[0], "y": p[1]} for p in pts],
             "closed": bool(closed)}
        e.update(self._base(layer, color, linetype))
        self.entities.append(e)
        return e

    def add_rect(self, corner1, corner2, layer="0", color=None, linetype=None):
        """Native MiniCAD rectangle entity."""
        e = {"type": "rect", "a": {"x": corner1[0], "y": corner1[1]}, "b": {"x": corner2[0], "y": corner2[1]}}
        e.update(self._base(layer, color, linetype))
        self.entities.append(e)
        return e

    def add_dim(self, p1, p2, dp, dtype="aligned", text="", height=None,
                layer="0", color=None, linetype=None):
        """Dimension entity (dtype: 'aligned', 'horizontal', 'vertical')."""
        if dtype not in ("aligned", "horizontal", "vertical"):
            dtype = "aligned"
        e = {
            "type": "dim",
            "p1": {"x": p1[0], "y": p1[1]},
            "p2": {"x": p2[0], "y": p2[1]},
            "dp": {"x": dp[0], "y": dp[1]},
            "dtype": dtype,
            "h": height if height is not None else self.text_height,
            "text": str(text)
        }
        e.update(self._base(layer, color, linetype))
        self.entities.append(e)
        return e

    def add_callout(self, box, text, leaders, height=None,
                    layer="0", color=None, linetype=None):
        """Callout entity with text label box and leader lines."""
        e = {
            "type": "callout",
            "box": {"x": box[0], "y": box[1]},
            "text": str(text),
            "h": height if height is not None else self.text_height,
            "leaders": [{"x": p[0], "y": p[1]} for p in leaders]
        }
        e.update(self._base(layer, color, linetype))
        self.entities.append(e)
        return e

    def add_hatch(self, boundary, pattern="hash", spacing=4, angle_deg=45,
                  layer="0", color=None, linetype=None):
        """Hatch entity inside boundary polygon (pattern: 'hash' or 'cross')."""
        e = {
            "type": "hatch",
            "boundary": [{"x": p[0], "y": p[1]} for p in boundary],
            "pattern": "cross" if pattern == "cross" else "hash",
            "spacing": float(spacing),
            "angle": float(angle_deg)
        }
        e.update(self._base(layer, color, linetype))
        self.entities.append(e)
        return e

    def add_cloud(self, pts, closed=True, bump=6,
                  layer="0", color=None, linetype=None):
        """Revision cloud entity."""
        e = {
            "type": "cloud",
            "pts": [{"x": p[0], "y": p[1]} for p in pts],
            "closed": bool(closed),
            "bump": float(bump)
        }
        e.update(self._base(layer, color, linetype))
        self.entities.append(e)
        return e

    # -- bounds & analysis --------------------------------------------------
    def bounds(self, entities=None):
        ents = entities if entities is not None else self.entities
        if not ents:
            return {"minx": 0.0, "miny": 0.0, "maxx": 0.0, "maxy": 0.0}
        boxes = [bbox(e) for e in ents]
        return {
            "minx": min(b["minx"] for b in boxes),
            "miny": min(b["miny"] for b in boxes),
            "maxx": max(b["maxx"] for b in boxes),
            "maxy": max(b["maxy"] for b in boxes)
        }

    # -- transforms ---------------------------------------------------------
    def translate(self, dx, dy, entities=None):
        m = {"a": 1.0, "b": 0.0, "c": 0.0, "d": 1.0, "e": float(dx), "f": float(dy)}
        target = entities if entities is not None else self.entities
        for e in target:
            _transform_entity(e, m)
        return self

    def rotate(self, angle_deg, center=(0, 0), entities=None):
        ang = math.radians(angle_deg)
        c, s = math.cos(ang), math.sin(ang)
        cx, cy = center
        m = {
            "a": c, "b": s, "c": -s, "d": c,
            "e": cx - c * cx + s * cy,
            "f": cy - s * cx - c * cy
        }
        target = entities if entities is not None else self.entities
        for e in target:
            _transform_entity(e, m)
        return self

    def scale(self, factor, center=(0, 0), entities=None):
        k = float(factor)
        cx, cy = center
        m = {
            "a": k, "b": 0.0, "c": 0.0, "d": k,
            "e": cx * (1.0 - k),
            "f": cy * (1.0 - k)
        }
        target = entities if entities is not None else self.entities
        for e in target:
            _transform_entity(e, m)
        return self

    def mirror(self, p1, p2, keep_source=False, entities=None):
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        L = math.hypot(dx, dy)
        if L < 1e-9:
            return self
        u, v = dx / L, dy / L
        # 2D line reflection matrix
        m = {
            "a": 2 * u * u - 1,
            "b": 2 * u * v,
            "c": 2 * u * v,
            "d": 2 * v * v - 1,
            "e": p1[0] - (2 * u * u - 1) * p1[0] - 2 * u * v * p1[1],
            "f": p1[1] - 2 * u * v * p1[0] - (2 * v * v - 1) * p1[1]
        }
        target = entities if entities is not None else self.entities
        if keep_source:
            clones = [copy.deepcopy(e) for e in target]
            for e in clones:
                _transform_entity(e, m)
            self.entities.extend(clones)
        else:
            for e in target:
                _transform_entity(e, m)
        return self

    # -- editing tools ------------------------------------------------------
    def explode(self, entity=None):
        """Decomposes compound entities (rect, poly, dim, callout, hatch) into primitive entities."""
        targets = [entity] if entity is not None else list(self.entities)
        new_ents = []
        for e in targets:
            parts = explode_entity(e, self.text_height)
            if parts is not None:
                idx = self.entities.index(e)
                self.entities[idx:idx + 1] = parts
                new_ents.extend(parts)
        return new_ents

    def join(self, entities=None, tol=0.5):
        """Chains touching lines and polylines into continuous polylines or collinear lines."""
        targets = entities if entities is not None else [e for e in self.entities if e["type"] in ("line", "poly")]
        if not targets:
            return []
        chains = []
        for e in targets:
            if e["type"] == "line":
                chains.append({
                    "pts": [dict(e["a"]), dict(e["b"])],
                    "closed": False,
                    "layer": e.get("layer", "0"),
                    "color": e.get("color"),
                    "linetype": e.get("linetype"),
                    "wasLineOnly": True
                })
            elif e["type"] == "poly":
                chains.append({
                    "pts": [dict(p) for p in e.get("pts", [])],
                    "closed": bool(e.get("closed")),
                    "layer": e.get("layer", "0"),
                    "color": e.get("color"),
                    "linetype": e.get("linetype"),
                    "wasLineOnly": False
                })

        joined = join_chains(chains, tol)
        # Remove original targets from drawing and insert joined entities
        for e in targets:
            if e in self.entities:
                self.entities.remove(e)
        self.entities.extend(joined)
        return joined

    def offset(self, entity, distance, side_point=None):
        """Creates a parallel or concentric offset copy of an entity."""
        if not entity or distance <= 0:
            return None
        e = entity
        t = e["type"]
        pt = {"x": side_point[0], "y": side_point[1]} if side_point is not None else None

        if t == "line":
            dx = e["b"]["x"] - e["a"]["x"]
            dy = e["b"]["y"] - e["a"]["y"]
            length = math.hypot(dx, dy)
            if length < 1e-12:
                return None
            nx, ny = -dy / length, dx / length
            s = 1.0
            if pt:
                dot = (pt["x"] - e["a"]["x"]) * nx + (pt["y"] - e["a"]["y"]) * ny
                s = 1.0 if dot >= 0 else -1.0
            off_x = s * distance * nx
            off_y = s * distance * ny
            clone = copy.deepcopy(e)
            clone["a"]["x"] += off_x
            clone["a"]["y"] += off_y
            clone["b"]["x"] += off_x
            clone["b"]["y"] += off_y
            self.entities.append(clone)
            return clone

        if t in ("circle", "arc"):
            c = e["c"]
            r = e["r"]
            if pt:
                d = math.hypot(pt["x"] - c["x"], pt["y"] - c["y"])
                r_prime = (r + distance) if d >= r else (r - distance)
            else:
                r_prime = r + distance
            if r_prime <= 1e-4:
                raise ValueError(f"Offset distance {distance} is too large for radius {r}")
            clone = copy.deepcopy(e)
            clone["r"] = r_prime
            self.entities.append(clone)
            return clone

        if t == "rect":
            x0 = min(e["a"]["x"], e["b"]["x"])
            x1 = max(e["a"]["x"], e["b"]["x"])
            y0 = min(e["a"]["y"], e["b"]["y"])
            y1 = max(e["a"]["y"], e["b"]["y"])
            w = x1 - x0
            h = y1 - y0
            inside = False
            if pt:
                inside = (x0 <= pt["x"] <= x1 and y0 <= pt["y"] <= y1)
            if inside:
                if w <= 2 * distance or h <= 2 * distance:
                    raise ValueError(f"Offset distance {distance} too large for rectangle ({w}x{h})")
                na = {"x": x0 + distance, "y": y0 + distance}
                nb = {"x": x1 - distance, "y": y1 - distance}
            else:
                na = {"x": x0 - distance, "y": y0 - distance}
                nb = {"x": x1 + distance, "y": y1 + distance}
            clone = copy.deepcopy(e)
            clone["a"], clone["b"] = na, nb
            self.entities.append(clone)
            return clone

        if t == "poly":
            pts = e.get("pts", [])
            n = len(pts)
            if n < 2:
                return None
            is_closed = bool(e.get("closed"))
            seg_count = n if is_closed else (n - 1)
            offset_lines = []
            for i in range(seg_count):
                p1 = pts[i]
                p2 = pts[(i + 1) % n]
                dx, dy = p2["x"] - p1["x"], p2["y"] - p1["y"]
                L = math.hypot(dx, dy)
                if L < 1e-9:
                    continue
                nx, ny = -dy / L, dx / L
                offset_lines.append((
                    {"x": p1["x"] + nx * distance, "y": p1["y"] + ny * distance},
                    {"x": p2["x"] + nx * distance, "y": p2["y"] + ny * distance}
                ))
            # Connect adjacent offset edges
            new_pts = []
            for i in range(len(offset_lines)):
                if not is_closed and i == 0:
                    new_pts.append(offset_lines[0][0])
                if i < len(offset_lines) - 1 or is_closed:
                    l1 = offset_lines[i]
                    l2 = offset_lines[(i + 1) % len(offset_lines)]
                    # Line-line intersection
                    denom = (l1[0]["x"] - l1[1]["x"]) * (l2[0]["y"] - l2[1]["y"]) - (l1[0]["y"] - l1[1]["y"]) * (l2[0]["x"] - l2[1]["x"])
                    if abs(denom) > 1e-6:
                        t_param = ((l1[0]["x"] - l2[0]["x"]) * (l2[0]["y"] - l2[1]["y"]) - (l1[0]["y"] - l2[0]["y"]) * (l2[0]["x"] - l2[1]["x"])) / denom
                        new_pts.append({
                            "x": l1[0]["x"] + t_param * (l1[1]["x"] - l1[0]["x"]),
                            "y": l1[0]["y"] + t_param * (l1[1]["y"] - l1[0]["y"])
                        })
                    else:
                        new_pts.append(l1[1])
                elif not is_closed:
                    new_pts.append(offset_lines[-1][1])
            clone = copy.deepcopy(e)
            clone["pts"] = new_pts
            self.entities.append(clone)
            return clone

        return None

    def break_at_point(self, entity, pt):
        """Splits an entity at coordinate pt into two independent entities."""
        if not entity or not pt:
            return None
        t = entity["type"]
        px, py = pt[0], pt[1]

        if t == "line":
            dx = entity["b"]["x"] - entity["a"]["x"]
            dy = entity["b"]["y"] - entity["a"]["y"]
            len_sq = dx * dx + dy * dy
            if len_sq < 1e-12:
                return None
            param = ((px - entity["a"]["x"]) * dx + (py - entity["a"]["y"]) * dy) / len_sq
            if param <= 0.001 or param >= 0.999:
                raise ValueError("Break point must be between line endpoints")
            split_p = {"x": entity["a"]["x"] + param * dx, "y": entity["a"]["y"] + param * dy}
            l1 = copy.deepcopy(entity)
            l1["b"] = dict(split_p)
            l2 = copy.deepcopy(entity)
            l2["a"] = dict(split_p)
            idx = self.entities.index(entity)
            self.entities[idx:idx + 1] = [l1, l2]
            return [l1, l2]

        if t == "arc":
            phi = math.atan2(py - entity["c"]["y"], px - entity["c"]["x"])
            diff = _norm_rad(phi - entity["a0"]) if entity["sweep"] >= 0 else _norm_rad(entity["a0"] - phi)
            abs_sweep = abs(entity["sweep"])
            if diff <= 0.005 or diff >= abs_sweep - 0.005:
                raise ValueError("Break point must be within arc sweep")
            s1 = diff if entity["sweep"] >= 0 else -diff
            s2 = entity["sweep"] - s1
            arc1 = copy.deepcopy(entity)
            arc1["sweep"] = s1
            arc2 = copy.deepcopy(entity)
            arc2["a0"] = _norm_rad(entity["a0"] + s1)
            arc2["sweep"] = s2
            idx = self.entities.index(entity)
            self.entities[idx:idx + 1] = [arc1, arc2]
            return [arc1, arc2]

        if t == "circle":
            phi = math.atan2(py - entity["c"]["y"], px - entity["c"]["x"])
            arc1 = {
                "type": "arc", "c": dict(entity["c"]), "r": entity["r"],
                "a0": phi, "sweep": math.pi,
                "layer": entity.get("layer", "0"), "color": entity.get("color"), "linetype": entity.get("linetype")
            }
            arc2 = {
                "type": "arc", "c": dict(entity["c"]), "r": entity["r"],
                "a0": _norm_rad(phi + math.pi), "sweep": math.pi,
                "layer": entity.get("layer", "0"), "color": entity.get("color"), "linetype": entity.get("linetype")
            }
            idx = self.entities.index(entity)
            self.entities[idx:idx + 1] = [arc1, arc2]
            return [arc1, arc2]

        if t == "rect":
            # Decompose into 4 lines, split the target line
            parts = explode_entity(entity, self.text_height)
            best_line = None
            best_dist = 1e18
            for l in parts:
                dx = l["b"]["x"] - l["a"]["x"]
                dy = l["b"]["y"] - l["a"]["y"]
                L2 = dx * dx + dy * dy
                tt = max(0.0, min(1.0, ((px - l["a"]["x"]) * dx + (py - l["a"]["y"]) * dy) / L2)) if L2 > 0 else 0
                proj_x, proj_y = l["a"]["x"] + tt * dx, l["a"]["y"] + tt * dy
                d = math.hypot(px - proj_x, py - proj_y)
                if d < best_dist:
                    best_dist = d
                    best_line = l
            if best_line:
                split_parts = self.break_at_point(best_line, pt)
                if split_parts:
                    idx = self.entities.index(entity)
                    remaining = [p for p in parts if p != best_line]
                    self.entities[idx:idx + 1] = remaining + split_parts
                    return remaining + split_parts

        return None

    # -- DXF output ---------------------------------------------------------
    def to_dxf(self):
        L = []
        def P(c, v):
            L.append(str(c)); L.append(_fmt(v) if isinstance(v, (int, float)) else str(v))
        P(0, "SECTION"); P(2, "HEADER"); P(9, "$ACADVER"); P(1, "AC1009"); P(0, "ENDSEC")
        P(0, "SECTION"); P(2, "TABLES")
        P(0, "TABLE"); P(2, "LTYPE"); P(70, len(LTYPES))
        for n in LTYPES:
            d = LTDEF[n]
            P(0, "LTYPE"); P(2, n); P(70, 0); P(3, d["d"]); P(72, 65); P(73, len(d["e"]))
            P(40, sum(abs(x) for x in d["e"]))
            for x in d["e"]:
                P(49, x)
        P(0, "ENDTAB")
        P(0, "TABLE"); P(2, "LAYER"); P(70, len(self.layers))
        for l in self.layers:
            P(0, "LAYER"); P(2, l["name"]); P(70, 0); P(62, l["color"]); P(6, l.get("linetype") or "CONTINUOUS")
        P(0, "ENDTAB"); P(0, "ENDSEC")
        P(0, "SECTION"); P(2, "ENTITIES")

        def com(e):
            P(8, e.get("layer") or "0")
            if e.get("color") is not None:
                P(62, e["color"])
            if e.get("linetype") and e["linetype"] != "BYLAYER":
                P(6, e["linetype"])

        def line_out(a, b, e):
            P(0, "LINE"); com(e); P(10, a["x"]); P(20, a["y"]); P(30, 0)
            P(11, b["x"]); P(21, b["y"]); P(31, 0)

        def solid_out(tip, dir_val, ux, uy, nx, ny, ah, aw, e):
            bx = tip["x"] + dir_val * ux * ah
            by = tip["y"] + dir_val * uy * ah
            q1 = {"x": bx + nx * aw, "y": by + ny * aw}
            q2 = {"x": bx - nx * aw, "y": by - ny * aw}
            P(0, "SOLID"); com(e); P(10, tip["x"]); P(20, tip["y"]); P(30, 0)
            P(11, q1["x"]); P(21, q1["y"]); P(31, 0)
            P(12, q2["x"]); P(22, q2["y"]); P(32, 0)
            P(13, q2["x"]); P(23, q2["y"]); P(33, 0)

        for e in self.entities:
            t = e["type"]
            if t == "line":
                line_out(e["a"], e["b"], e)
            elif t == "arc":
                if e["sweep"] >= 0:
                    sa = e["a0"]; ea = e["a0"] + e["sweep"]
                else:
                    sa = e["a0"] + e["sweep"]; ea = e["a0"]
                P(0, "ARC"); com(e); P(10, e["c"]["x"]); P(20, e["c"]["y"]); P(30, 0)
                P(40, e["r"]); P(50, _norm_deg(math.degrees(sa))); P(51, _norm_deg(math.degrees(ea)))
            elif t == "circle":
                P(0, "CIRCLE"); com(e); P(10, e["c"]["x"]); P(20, e["c"]["y"]); P(30, 0); P(40, e["r"])
            elif t == "ellipse":
                mx = e["rx"] * math.cos(e.get("rot", 0)); my = e["rx"] * math.sin(e.get("rot", 0))
                P(0, "ELLIPSE"); com(e); P(10, e["c"]["x"]); P(20, e["c"]["y"]); P(30, 0)
                P(11, mx); P(21, my); P(31, 0)
                P(40, (e["ry"] / e["rx"]) if e["rx"] > 1e-9 else 1); P(41, 0); P(42, TWO_PI)
            elif t == "point":
                P(0, "POINT"); com(e); P(10, e["p"]["x"]); P(20, e["p"]["y"]); P(30, 0)
            elif t == "text":
                ha = 1 if e.get("align") == "center" else 2 if e.get("align") == "right" else 0
                P(0, "TEXT"); com(e); P(10, e["p"]["x"]); P(20, e["p"]["y"]); P(30, 0)
                P(40, e["h"]); P(1, e.get("text") or ""); P(50, e.get("rot") or 0)
                if ha:
                    P(72, ha); P(11, e["p"]["x"]); P(21, e["p"]["y"]); P(31, 0)
            elif t == "rect":
                pts = rect_corners(e) if ("a" in e and "b" in e) else e.get("pts", [])
                P(0, "POLYLINE"); com(e); P(66, 1); P(70, 1)
                for p in pts:
                    P(0, "VERTEX"); P(8, e.get("layer") or "0"); P(10, p["x"]); P(20, p["y"]); P(30, 0)
                P(0, "SEQEND"); P(8, e.get("layer") or "0")
            elif t == "poly":
                pts = e.get("pts", [])
                closed = 1 if e.get("closed") else 0
                P(0, "POLYLINE"); com(e); P(66, 1); P(70, closed)
                for p in pts:
                    P(0, "VERTEX"); P(8, e.get("layer") or "0"); P(10, p["x"]); P(20, p["y"]); P(30, 0)
                P(0, "SEQEND"); P(8, e.get("layer") or "0")
            elif t == "dim":
                g = dim_geom(e)
                h = e.get("h") or self.text_height
                ah = h * 0.9
                aw = h * 0.32
                ux = math.cos(g["ang"])
                uy = math.sin(g["ang"])
                nx = -uy
                ny = ux
                e1 = math.atan2(g["d1"]["y"] - e["p1"]["y"], g["d1"]["x"] - e["p1"]["x"])
                e2 = math.atan2(g["d2"]["y"] - e["p2"]["y"], g["d2"]["x"] - e["p2"]["x"])
                line_out(e["p1"], {"x": g["d1"]["x"] + aw * math.cos(e1), "y": g["d1"]["y"] + aw * math.sin(e1)}, e)
                line_out(e["p2"], {"x": g["d2"]["x"] + aw * math.cos(e2), "y": g["d2"]["y"] + aw * math.sin(e2)}, e)
                line_out(g["d1"], g["d2"], e)
                solid_out(g["d1"], 1, ux, uy, nx, ny, ah, aw, e)
                solid_out(g["d2"], -1, ux, uy, nx, ny, ah, aw, e)
                mx = (g["d1"]["x"] + g["d2"]["x"]) / 2
                my = (g["d1"]["y"] + g["d2"]["y"]) / 2
                txt = dim_text(e, g)
                ta = math.degrees(g["ang"])
                if ta > 90: ta -= 180
                if ta < -90: ta += 180
                tox = h * 0.4
                tx = mx + nx * tox
                ty = my + ny * tox
                P(0, "TEXT"); com(e); P(10, tx); P(20, ty); P(30, 0)
                P(40, h); P(1, txt); P(50, ta); P(72, 1); P(11, tx); P(21, ty); P(31, 0)
            elif t == "hatch":
                for s in hatch_segs(e):
                    line_out(s[0], s[1], e)
            elif t == "cloud":
                for a in cloud_arcs(e):
                    if a["sweep"] >= 0:
                        sa = a["a0"]; ea = a["a0"] + a["sweep"]
                    else:
                        sa = a["a0"] + a["sweep"]; ea = a["a0"]
                    P(0, "ARC"); com(e); P(10, a["c"]["x"]); P(20, a["c"]["y"]); P(30, 0)
                    P(40, a["r"]); P(50, _norm_deg(math.degrees(sa))); P(51, _norm_deg(math.degrees(ea)))
            elif t == "callout":
                g = calloutGeom(e, self.text_height)
                P(0, "POLYLINE"); com(e); P(66, 1); P(70, 1)
                for p in g["corners"]:
                    P(0, "VERTEX"); P(8, e.get("layer") or "0"); P(10, p["x"]); P(20, p["y"]); P(30, 0)
                P(0, "SEQEND"); P(8, e.get("layer") or "0")
                h = e.get("h") or self.text_height
                P(0, "TEXT"); com(e); P(10, g["textAt"]["x"]); P(20, g["textAt"]["y"]); P(30, 0)
                P(40, h); P(1, e.get("text") or ""); P(50, 0)
                for tgt in e.get("leaders", []):
                    at = callout_attach(g, tgt)
                    line_out(at, tgt, e)
                    ah = h * 0.9; aw = h * 0.32
                    dx = tgt["x"] - at["x"]
                    dy = tgt["y"] - at["y"]
                    L2 = math.hypot(dx, dy) or 1.0
                    ux = dx / L2; uy = dy / L2
                    nx2, ny2 = -uy, ux
                    bx2 = tgt["x"] - ux * ah
                    by2 = tgt["y"] - uy * ah
                    q1 = {"x": bx2 + nx2 * aw, "y": by2 + ny2 * aw}
                    q2 = {"x": bx2 - nx2 * aw, "y": by2 - ny2 * aw}
                    P(0, "SOLID"); com(e); P(10, tgt["x"]); P(20, tgt["y"]); P(30, 0)
                    P(11, q1["x"]); P(21, q1["y"]); P(31, 0)
                    P(12, q2["x"]); P(22, q2["y"]); P(32, 0)
                    P(13, q2["x"]); P(23, q2["y"]); P(33, 0)

        P(0, "ENDSEC"); P(0, "EOF")
        return "\n".join(L)

    def save_dxf(self, path):
        with open(path, "w") as f:
            f.write(self.to_dxf())
        return path

    # -- native JSON (opens directly in the editor) ------------------------
    def to_json(self):
        return json.dumps({
            "format": "minicad", "version": 3, "units": "dimensionless",
            "gridSpacing": self.grid_spacing, "textHeight": self.text_height,
            "activeLayer": self.active_layer, "layers": self.layers,
            "entities": self.entities,
        }, indent=2)

    def save_json(self, path):
        with open(path, "w") as f:
            f.write(self.to_json())
        return path

    # -- loaders ------------------------------------------------------------
    @classmethod
    def load(cls, path):
        with open(path) as f:
            text = f.read()
        if path.lower().endswith(".json") or text.lstrip()[:1] == "{":
            return cls.from_json(text)
        return cls.from_dxf(text)

    @classmethod
    def from_json(cls, text):
        o = json.loads(text)
        if not isinstance(o.get("entities"), list):
            raise ValueError("not a MiniCAD JSON file")
        d = cls()
        if isinstance(o.get("gridSpacing"), (int, float)):
            d.grid_spacing = o["gridSpacing"]
        if isinstance(o.get("textHeight"), (int, float)):
            d.text_height = o["textHeight"]
        if o.get("layers"):
            d.layers = [{"name": str(l["name"]), "color": l.get("color", 7),
                         "linetype": l.get("linetype", "CONTINUOUS"),
                         "visible": l.get("visible", True) is not False} for l in o["layers"]]
        d.entities = o["entities"]
        d.active_layer = o.get("activeLayer") or d.layers[0]["name"]
        return d

    @classmethod
    def from_dxf(cls, text):
        raw = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        pairs = []
        i = 0
        while i + 1 < len(raw):
            try:
                c = int(raw[i].strip())
            except ValueError:
                i += 1
                continue
            pairs.append((c, raw[i + 1]))
            i += 2

        def read_map(idx):
            f = {}
            j = idx + 1
            while j < len(pairs) and pairs[j][0] != 0:
                f[pairs[j][0]] = pairs[j][1]
                j += 1
            return f, j

        # layer table
        layer_defs = {}
        for k in range(len(pairs)):
            if pairs[k][0] == 0 and str(pairs[k][1]).strip() == "LAYER":
                j = k + 1
                name, col, lt = None, 7, "CONTINUOUS"
                while j < len(pairs) and pairs[j][0] != 0:
                    c, v = pairs[j][0], str(pairs[j][1]).strip()
                    if c == 2:
                        name = v
                    elif c == 62:
                        col = abs(int(_num(v))) or 7
                    elif c == 6:
                        lt = v.upper()
                    j += 1
                if name:
                    layer_defs[name] = {"color": col, "linetype": lt if lt in LTYPES else "CONTINUOUS"}

        d = cls()
        ents = []
        used = {}

        def tag(e, f):
            e["layer"] = (str(f[8]).strip() if f.get(8) is not None else "0") or "0"
            e["color"] = abs(int(_num(f[62]))) if f.get(62) is not None else None
            lt = str(f[6]).strip().upper() if f.get(6) is not None else None
            e["linetype"] = lt if (lt and lt != "BYLAYER" and lt in LTYPES) else None
            used[e["layer"]] = True
            return e

        i = 0
        while i < len(pairs):
            code, val = pairs[i]
            if code != 0:
                i += 1
                continue
            t = str(val).strip()
            if t == "LINE":
                f, ni = read_map(i)
                ents.append(tag({"type": "line", "a": {"x": _num(f.get(10)), "y": _num(f.get(20))},
                                 "b": {"x": _num(f.get(11)), "y": _num(f.get(21))}}, f)); i = ni
            elif t == "ARC":
                f, ni = read_map(i)
                c = {"x": _num(f.get(10)), "y": _num(f.get(20))}; r = _num(f.get(40))
                a0 = math.radians(_num(f.get(50)))
                dd = _norm_deg(_num(f.get(51)) - _num(f.get(50))) or 360
                sweep = math.radians(dd)
                ents.append(tag({"type": "arc", "c": c, "r": r, "a0": a0, "sweep": sweep}, f)); i = ni
            elif t == "CIRCLE":
                f, ni = read_map(i)
                ents.append(tag({"type": "circle", "c": {"x": _num(f.get(10)), "y": _num(f.get(20))},
                                 "r": _num(f.get(40))}, f)); i = ni
            elif t == "ELLIPSE":
                f, ni = read_map(i)
                c = {"x": _num(f.get(10)), "y": _num(f.get(20))}
                mx, my = _num(f.get(11)), _num(f.get(21))
                rx = math.hypot(mx, my); rot = math.atan2(my, mx)
                ratio = _num(f.get(40)) if f.get(40) is not None else 1
                ents.append(tag({"type": "ellipse", "c": c, "rx": rx, "ry": rx * ratio, "rot": rot}, f)); i = ni
            elif t == "POINT":
                f, ni = read_map(i)
                ents.append(tag({"type": "point", "p": {"x": _num(f.get(10)), "y": _num(f.get(20))}}, f)); i = ni
            elif t == "TEXT":
                f, ni = read_map(i)
                ha = int(_num(f.get(72)))
                al = "right" if ha == 2 else "center" if ha == 1 else "left"
                ax = _num(f.get(11)) if (ha != 0 and f.get(11) is not None) else _num(f.get(10))
                ay = _num(f.get(21)) if (ha != 0 and f.get(21) is not None) else _num(f.get(20))
                ents.append(tag({"type": "text", "p": {"x": ax, "y": ay},
                                 "h": _num(f.get(40)) or d.text_height,
                                 "text": str(f.get(1)) if f.get(1) is not None else "",
                                 "rot": _num(f.get(50)), "align": al}, f)); i = ni
            elif t == "LWPOLYLINE":
                j = i + 1
                verts = []
                closed = False
                f = {}
                while j < len(pairs) and pairs[j][0] != 0:
                    c, v = pairs[j]
                    if c == 8:
                        f[8] = v
                    elif c == 62:
                        f[62] = v
                    elif c == 6:
                        f[6] = v
                    elif c == 70:
                        closed = (int(_num(v)) & 1) == 1
                    elif c == 10:
                        verts.append({"x": _num(v), "y": 0})
                    elif c == 20 and verts:
                        verts[-1]["y"] = _num(v)
                    j += 1
                if len(verts) >= 2:
                    ents.append(tag({"type": "poly", "pts": verts, "closed": closed}, f))
                i = j
            elif t in ("SOLID", "TRACE"):
                f, ni = read_map(i)
                pv = [{"x": _num(f.get(10)), "y": _num(f.get(20))},
                      {"x": _num(f.get(11)), "y": _num(f.get(21))},
                      {"x": _num(f.get(13)), "y": _num(f.get(23))},
                      {"x": _num(f.get(12)), "y": _num(f.get(22))}]
                uniq = []
                for p in pv:
                    if not any(abs(q["x"] - p["x"]) < 1e-9 and abs(q["y"] - p["y"]) < 1e-9 for q in uniq):
                        uniq.append(p)
                if len(uniq) >= 3:
                    ents.append(tag({"type": "poly", "pts": uniq, "closed": True}, f))
                i = ni
            elif t == "POLYLINE":
                f, ni = read_map(i)
                closed = (int(_num(f.get(70, 0))) & 1) == 1
                j = ni
                verts = []
                while j < len(pairs) and pairs[j][0] == 0 and str(pairs[j][1]).strip() == "VERTEX":
                    vf, nj = read_map(j)
                    verts.append({"x": _num(vf.get(10)), "y": _num(vf.get(20))})
                    j = nj
                if j < len(pairs) and pairs[j][0] == 0 and str(pairs[j][1]).strip() == "SEQEND":
                    _, nj = read_map(j)
                    j = nj
                if len(verts) >= 2:
                    ents.append(tag({"type": "poly", "pts": verts, "closed": closed}, f))
                i = j
            else:
                i += 1

        names = {}
        d.layers = []

        def ensure(nm, df):
            if nm in names:
                return
            names[nm] = True
            d.layers.append({"name": nm, "color": df["color"] if df else 7,
                             "linetype": df["linetype"] if df else "CONTINUOUS", "visible": True})

        ensure("0", layer_defs.get("0"))
        for nm in layer_defs:
            ensure(nm, layer_defs[nm])
        for nm in used:
            ensure(nm, None)
        d.entities = ents
        d.active_layer = d.layers[0]["name"]
        return d

    # -- summary ------------------------------------------------------------
    def summary(self):
        counts = {}
        for e in self.entities:
            counts[e["type"]] = counts.get(e["type"], 0) + 1
        return {"entities": len(self.entities), "by_type": counts,
                "layers": [l["name"] for l in self.layers]}


# --- Self-Test ------------------------------------------------------------

def _selftest():
    print("--- 1. Testing Entity Constructors & JSON Round-Trip ---")
    d = Drawing()
    d.add_layer("WALLS", color=5, linetype="DASHED")
    d.add_layer("DIMS", color=1, linetype="CONTINUOUS")

    d.add_line((0, 0), (100, 0), layer="WALLS")
    d.add_arc((100, 0), 50, 0, 90, layer="WALLS", color=1)
    d.add_circle((50, 50), 10)
    d.add_ellipse((0, 0), 30, 15, rot_deg=30)
    d.add_point((5, 5))
    d.add_text((10, 20), "NOTE 1", height=5, align="right")
    d.add_rect((0, 0), (40, 20))
    d.add_polyline([(0, 0), (10, 5), (20, 0)], closed=False)
    d.add_dim((0, 0), (100, 0), (50, 15), dtype="aligned", layer="DIMS")
    d.add_callout((10, 80), "DETAIL A", [(25, 60), (35, 60)])
    d.add_hatch([(0, 0), (50, 0), (50, 50), (0, 50)], pattern="hash", spacing=10)
    d.add_cloud([(0, 0), (40, 0), (40, 40), (0, 40)], closed=True, bump=8)

    assert len(d.entities) == 12, f"Expected 12 entities, got {len(d.entities)}"
    types = {e["type"] for e in d.entities}
    assert types == {"line", "arc", "circle", "ellipse", "point", "text", "rect", "poly", "dim", "callout", "hatch", "cloud"}
    print("  PASS: All 12 entity types created successfully")

    # Native rect verification
    rect_ent = next(e for e in d.entities if e["type"] == "rect")
    assert "a" in rect_ent and "b" in rect_ent, "Rect must have native 'a' and 'b' points"
    print("  PASS: Native rectangle entity schema verified")

    # JSON Round-Trip
    js_text = d.to_json()
    d_json = Drawing.from_json(js_text)
    assert len(d_json.entities) == 12
    assert d_json.summary() == d.summary()
    print("  PASS: JSON round-trip preserved all 12 entities and layer tables")

    print("\n--- 2. Testing DXF R12 Export & Reload ---")
    dxf_text = d.to_dxf()
    assert "SECTION" in dxf_text and "AC1009" in dxf_text
    d_dxf = Drawing.from_dxf(dxf_text)
    # Compound entities (dim, callout, hatch, cloud, rect) decompose into R12 primitives
    dxf_types = {e["type"] for e in d_dxf.entities}
    assert "line" in dxf_types and "poly" in dxf_types and "arc" in dxf_types and "text" in dxf_types
    print("  PASS: DXF R12 export and reload successful, decomposed into native primitives")

    print("\n--- 3. Testing Transforms (Translate, Rotate, Scale, Mirror) ---")
    # Translate
    d_tr = Drawing()
    d_tr.add_line((0, 0), (10, 10))
    d_tr.add_circle((20, 20), 5)
    d_tr.add_rect((0, 0), (30, 20))
    d_tr.translate(10, 5)
    assert d_tr.entities[0]["a"] == {"x": 10.0, "y": 5.0}
    assert d_tr.entities[1]["c"] == {"x": 30.0, "y": 25.0}
    assert d_tr.entities[2]["a"] == {"x": 10.0, "y": 5.0} and d_tr.entities[2]["b"] == {"x": 40.0, "y": 25.0}
    print("  PASS: translate() verified on line, circle, rect")

    # Rotate
    d_rot = Drawing()
    d_rot.add_line((0, 0), (10, 0))
    d_rot.rotate(90, center=(0, 0))
    assert abs(d_rot.entities[0]["b"]["x"]) < 1e-6 and abs(d_rot.entities[0]["b"]["y"] - 10) < 1e-6
    print("  PASS: rotate() verified")

    # Scale
    d_sc = Drawing()
    d_sc.add_circle((0, 0), 10)
    d_sc.scale(2.5, center=(0, 0))
    assert abs(d_sc.entities[0]["r"] - 25.0) < 1e-6
    print("  PASS: scale() verified")

    # Mirror
    d_mir = Drawing()
    d_mir.add_point((5, 10))
    d_mir.mirror((0, 0), (0, 100), keep_source=True)
    assert len(d_mir.entities) == 2
    assert abs(d_mir.entities[1]["p"]["x"] - (-5.0)) < 1e-6
    print("  PASS: mirror() verified")

    print("\n--- 4. Testing CAD Editing Tools ---")
    # Explode
    d_exp = Drawing()
    d_exp.add_rect((0, 0), (50, 30))
    res_exp = d_exp.explode()
    assert len(res_exp) == 4
    assert all(e["type"] == "line" for e in res_exp)
    assert len(d_exp.entities) == 4
    print("  PASS: explode() decomposed rectangle into 4 lines")

    # Join
    d_join = Drawing()
    d_join.add_line((0, 0), (50, 0))
    d_join.add_line((50, 0), (100, 0))
    res_join = d_join.join(tol=0.5)
    assert len(d_join.entities) == 1
    assert d_join.entities[0]["type"] == "line"
    assert d_join.entities[0]["a"]["x"] == 0 and d_join.entities[0]["b"]["x"] == 100
    print("  PASS: join() merged collinear lines into a single line")

    d_poly_join = Drawing()
    d_poly_join.add_line((0, 0), (10, 0))
    d_poly_join.add_line((10, 0), (10, 10))
    d_poly_join.add_line((10, 10), (0, 10))
    d_poly_join.add_line((0, 10), (0, 0))
    d_poly_join.join(tol=0.5)
    assert len(d_poly_join.entities) == 1
    assert d_poly_join.entities[0]["type"] == "poly"
    assert d_poly_join.entities[0]["closed"] is True
    print("  PASS: join() assembled 4 lines into closed polyline")

    # Offset
    d_off = Drawing()
    l = d_off.add_line((0, 0), (100, 0))
    off_l = d_off.offset(l, 10, side_point=(50, 20))
    assert abs(off_l["a"]["y"] - 10) < 1e-6
    print("  PASS: offset() created parallel line")

    # Break
    d_brk = Drawing()
    l2 = d_brk.add_line((0, 0), (100, 0))
    halves = d_brk.break_at_point(l2, (40, 0))
    assert len(halves) == 2
    assert abs(halves[0]["b"]["x"] - 40) < 1e-6 and abs(halves[1]["a"]["x"] - 40) < 1e-6
    print("  PASS: break_at_point() split line into two at picked coordinate")

    # Bounds
    b = d.bounds()
    assert b["minx"] < b["maxx"] and b["miny"] < b["maxy"]
    print("  PASS: bounds() verified")

    print("\n=== ALL SELFTESTS PASSED (100%) ===")


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        _selftest()
    elif len(sys.argv) >= 3 and sys.argv[1] == "info":
        print(json.dumps(Drawing.load(sys.argv[2]).summary(), indent=2))
    else:
        print(__doc__)
