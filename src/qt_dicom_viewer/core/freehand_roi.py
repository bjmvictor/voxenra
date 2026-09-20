"""Closed freehand polygons in image pixel-center coordinates."""

import math
from functools import lru_cache
import numpy as np


def polygon_area(points):
    p = np.asarray([(v.column, v.row) for v in points], dtype=float)
    if len(p) < 3:
        return 0.0
    return (
        abs(
            float(
                np.sum(p[:, 0] * np.roll(p[:, 1], -1) - p[:, 1] * np.roll(p[:, 0], -1))
            )
        )
        / 2
    )


def simple_polygon(points):
    """Reject crossings/touches between nonadjacent edges; area stays unambiguous."""
    p = np.asarray([(v.column, v.row) for v in points], dtype=float)
    n = len(p)
    if n < 3 or n > 16384 or not np.isfinite(p).all() or polygon_area(points) <= 1e-6:
        return False
    q = np.roll(p, -1, axis=0)
    cross = lambda a, b: a[..., 0] * b[..., 1] - a[..., 1] * b[..., 0]
    for i in range(n - 2):
        js = np.arange(i + 2, n - (1 if i == 0 else 0))
        if not len(js):
            continue
        a, b, c, d = p[i], q[i], p[js], q[js]
        overlap = np.all(
            np.maximum(np.minimum(a, b), np.minimum(c, d))
            <= np.minimum(np.maximum(a, b), np.maximum(c, d)) + 1e-9,
            axis=1,
        )
        hit = (
            (cross(b - a, c - a) * cross(b - a, d - a) <= 1e-12)
            & (cross(d - c, a - c) * cross(d - c, b - c) <= 1e-12)
            & overlap
        )
        if np.any(hit):
            return False
    return True


def contains_point(points, x, y):
    if len(points) < 3:
        return False
    inside = False
    for a, b in zip(points, (*points[1:], points[0])):
        if (a.row > y) != (b.row > y):
            crossing = a.column + (y - a.row) * (b.column - a.column) / (b.row - a.row)
            if x < crossing:
                inside = not inside
    return inside


def polygon_mask(points, x0, x1, y0, y1):
    """Scanline fill including boundary pixel centers, bounded by the image crop."""
    mask = np.zeros((y1 - y0 + 1, x1 - x0 + 1), dtype=bool)
    p = np.asarray([(v.column, v.row) for v in points], dtype=float)
    q = np.roll(p, -1, axis=0)
    for row, y in enumerate(range(y0, y1 + 1)):
        crossing = (p[:, 1] > y) != (q[:, 1] > y)
        a, b = p[crossing], q[crossing]
        xs = np.sort(
            a[:, 0] + (y - a[:, 1]) * (b[:, 0] - a[:, 0]) / (b[:, 1] - a[:, 1])
        )
        for left, right in zip(xs[::2], xs[1::2]):
            lo, hi = max(x0, math.ceil(left - 1e-9)), min(x1, math.floor(right + 1e-9))
            if lo <= hi:
                mask[row, lo - x0 : hi - x0 + 1] = True
        # Horizontal edges (including upper/lower bounds) belong to the ROI.
        horizontal = (abs(p[:, 1] - y) < 1e-9) & (abs(q[:, 1] - y) < 1e-9)
        for a, b in zip(p[horizontal], q[horizontal]):
            lo, hi = (
                max(x0, math.ceil(min(a[0], b[0]))),
                min(x1, math.floor(max(a[0], b[0]))),
            )
            if lo <= hi:
                mask[row, lo - x0 : hi - x0 + 1] = True
        for a in p[abs(p[:, 1] - y) < 1e-9]:
            x = round(float(a[0]))
            if x0 <= x <= x1 and abs(x - a[0]) < 1e-9:
                mask[row, x - x0] = True
    return mask


def roi_outline(points, smooth=False):
    """One boundary for display, statistics, picking, reports and segmentation."""
    return _roi_outline(tuple(points), smooth)


@lru_cache(maxsize=16)
def _roi_outline(points, smooth):
    if not smooth:
        return points
    from qt_dicom_viewer.core.curve_geometry import sample_closed_curve
    return sample_closed_curve(points)
