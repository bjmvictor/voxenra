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
