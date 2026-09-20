"""Open interpolating Catmull–Rom curves; controls remain distinct from samples."""
import math
import numpy as np
from qt_dicom_viewer.model.image_geometry import ImagePoint


def sample_curve(points, subdivisions=128):
    """Uniform cubic spline through clicks, with reflected endpoint tangents.

    The same sampled path is used for display, hit testing, arc length and SR.
    Samples are never persisted as editable control points.
    """
    if len(points) < 3:
        return tuple(points)
    p = np.asarray([(v.column, v.row) for v in points], dtype=float)
    extended = np.vstack((2 * p[0] - p[1], p, 2 * p[-1] - p[-2]))
    t = np.arange(subdivisions, dtype=float)[:, None] / subdivisions
    samples = []
    for i in range(len(p) - 1):
        a, b, c, d = extended[i:i + 4]
        v = 0.5 * (2*b + (-a+c)*t + (2*a-5*b+4*c-d)*t*t + (-a+3*b-3*c+d)*t*t*t)
        samples.extend(ImagePoint(float(x), float(y)) for x, y in v)
    samples.append(points[-1])
    return tuple(samples)


def curve_length_mm(points, row_spacing, column_spacing):
    if not all(math.isfinite(v) and v > 0 for v in (row_spacing, column_spacing)):
        return 0.0
    samples = sample_curve(points)
    return sum(math.hypot((b.column-a.column)*column_spacing, (b.row-a.row)*row_spacing)
               for a, b in zip(samples, samples[1:]))


def sample_closed_curve(points, tolerance=0.001):
    """Flatten a periodic interpolating cubic to within 0.001 image pixels.

    Each Catmull–Rom span is converted to a cubic Bezier and subdivided until
    both inner controls are within tolerance of its chord. The closing endpoint
    is omitted so downstream polygon routines close exactly once. Pathological
    contours are bounded and rejected, never silently simplified.
    """
    if not 3 <= len(points) <= 4096:
        return ()
    p = np.asarray([(v.column, v.row) for v in points], dtype=float)
    if not np.isfinite(p).all():
        return ()
    output = []

    def distance_squared(point, a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = dx*dx + dy*dy
        t = max(0.0, min(1.0, ((point[0]-a[0])*dx + (point[1]-a[1])*dy)/length)) if length else 0.0
        return (point[0]-a[0]-t*dx)**2 + (point[1]-a[1]-t*dy)**2

    def midpoint(a, b):
        return ((a[0]+b[0])/2, (a[1]+b[1])/2)

    for i in range(len(p)):
        a, b, c, d = (p[(i+j) % len(p)] for j in (-1, 0, 1, 2))
        stack = [(tuple(b), tuple(b+(c-a)/6), tuple(c-(d-b)/6), tuple(c), 0)]
        while stack:
            a, b, c, d, depth = stack.pop()
            error = max(distance_squared(b, a, d), distance_squared(c, a, d))
            if error <= tolerance*tolerance:
                output.append(ImagePoint(float(a[0]), float(a[1])))
                if len(output) > 16384:
                    return ()
            elif depth >= 16:
                return ()
            else:
                ab, bc, cd = midpoint(a, b), midpoint(b, c), midpoint(c, d)
                abc, bcd = midpoint(ab, bc), midpoint(bc, cd)
                mid = midpoint(abc, bcd)
                stack.append((mid, bcd, cd, d, depth+1))
                stack.append((a, ab, abc, mid, depth+1))
    return tuple(output)
