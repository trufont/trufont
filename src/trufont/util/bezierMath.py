from collections import namedtuple
from fontTools.misc import bezierTools
from fontTools.misc.arrayTools import Vector
from fontTools.pens.basePen import decomposeQuadraticSegment
from math import log2, sqrt

_interval = namedtuple(
    "SturmInterval", ("min", "max", "sign_min", "sign_max", "id", "exp_roots")
)


def distance(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    return sqrt(dx * dx + dy * dy)


def _buildSturmSequence(poly):
    n = len(poly)  # degree+1
    sturm = []
    sturm.append(poly)  # f_0 = f
    fp = [0]
    for i in range(n - 1):
        fp.append((n - 1 - i) * poly[i])
    sturm.append(fp)  # f_1 = f'

    for i in range(2, n):
        # slice to elide the null coeffs
        polm1 = sturm[-1][i - 1 :]  # f_n-1
        polm2 = sturm[-2][i - 2 :]  # f_n-2

        # long polyn division
        rem_coeff = polm2[0] / polm1[0]
        rem_sum = (polm2[1] - rem_coeff * polm1[1]) / polm1[0]
        fn = [0] * i
        for j in range(n - i):
            coeff = rem_sum * polm1[j + 1] - polm2[j + 2]
            if j != n - 1 - i:
                coeff += rem_coeff * polm1[j + 2]
            fn.append(coeff)
        sturm.append(fn)
    return sturm


def _countSturmSignChanges(sturm, t):
    switches = 0
    previous = None

    for poly in sturm:
        sign = _evalPoly(poly, t) >= 0
        if previous is not None:
            switches += sign != previous
        previous = sign

    return switches


def _evalPoly(poly, t):
    n = len(poly)
    result = 0
    for i in range(n - 1):
        result += poly[i]
        result *= t
    result += poly[-1]

    return result


def _solveBisection(poly, imin, imax, eps):
    if _evalPoly(poly, imin) > 0:
        return None
    if _evalPoly(poly, imax) < 0:
        return None

    max_iterations = 1 + int(log2(1 / eps))
    bisect_min = imin
    bisect_max = imax
    for i in range(max_iterations):
        mid = (bisect_max + bisect_min) / 2

        r = _evalPoly(poly, mid)
        if r < 0:
            if r >= -eps:
                return mid
            bisect_min = mid
        else:
            if r <= eps:
                return mid
            bisect_max = mid

    return bisect_min


def curveProjection(p1, p2, p3, p4, x, y, eps=1e-5):
    """
    Returns projection of point p on 3rd order Bézier curve p1 p2 p3 p4.
    Adapted from "Improved Algebraic Algorithm On Point Projection For Bézier
    Curves" by Xiao-Diao Chen, Yin Zhou, Zhenyu Shu, Hua Su and Jean-Claude
    Paul.

    g = (
        -3a.a,
        -(3a.b + 2b.a),
        -(3a.b + 2b.b + a.c),
        -(3a.a + 2b.c + b.c) + p.3a,
        -(2b.a + c.c) + p.2b,
        -a.c + p.c
    )
    """

    poly = bezierTools.calcCubicParameters(
        (p1.x, p1.y), (p2.x, p2.y), (p3.x, p3.y), (p4.x, p4.y)
    )
    vpoly = list(Vector(p) for p in poly)
    a, b, c, d = vpoly
    p = Vector((x, y), True)
    # for the sturm sequence, we need a leading coefficient of 1
    # calculate the inverse
    ilead = -1 / a.dot(3 * a)
    g = [
        1,
        -(b.dot(3 * a) + a.dot(2 * b)) * ilead,
        -(b.dot(3 * a) + b.dot(2 * b) + a.dot(c)) * ilead,
        -(a.dot(3 * a) + c.dot(2 * b) + b.dot(c)) * ilead + p.dot(3 * a) * ilead,
        -(a.dot(2 * b) + c.dot(c)) * ilead + p.dot(2 * b) * ilead,
        -a.dot(c) * ilead + p.dot(c) * ilead,
    ]
    # approx. roots using the sturm theorem
    sturm = _buildSturmSequence(g)
    intervals = []
    lo = _countSturmSignChanges(sturm, eps)
    hi = _countSturmSignChanges(sturm, 1 - eps)
    total_roots = lo - hi
    id_ = 0
    intervals.append(_interval(eps, 1 - eps, lo, hi, id_, total_roots))
    id_ += 1

    root_intervals = []
    while intervals and total_roots > len(root_intervals):
        i = intervals.pop(-1)

        nroots = i.sign_min - i.sign_max

        if nroots <= 0:
            if intervals and intervals[-1].id == i.id:
                i = intervals.pop(-1)
                nroots = i.exp_roots
            else:
                continue

        if nroots == i.exp_roots and intervals and intervals[-1].id == i.id:
            del intervals[-1]
        elif nroots == i.exp_roots - 1 and intervals and intervals[-1].id == i.id:
            root_intervals.append(intervals.pop(-1))

        if nroots == 1:
            root_intervals.append(i)
        else:
            mid = (i.min + i.max) / 2
            if mid - i.min <= eps:
                root_intervals.append(i)
            else:
                # we need to go deeper
                sign_mid = _countSturmSignChanges(sturm, mid)
                intervals.append(
                    _interval(i.min, mid, i.sign_min, sign_mid, id_, nroots)
                )
                intervals.append(
                    _interval(mid, i.max, sign_mid, i.sign_max, id_, nroots)
                )
                id_ += 1

    roots = []
    for i in root_intervals:
        root = _solveBisection(g, i.min, i.max, eps)
        if root is not None:
            roots.append(root)

    # first cp
    min_loc = (p1.x, p1.y, 0)
    min_dist = distance(p1.x, p1.y, x, y)
    # roots
    for t in roots:
        p = _evalPoly(vpoly, t)
        dist = distance(*p.values, x, y)
        if dist < min_dist:
            min_loc = (p[0], p[1], t)
            min_dist = dist
    # last cp
    dist = distance(p4.x, p4.y, x, y)
    if dist < min_dist:
        min_loc = (p4.x, p4.y, 0)
        min_dist = dist
        # dist is useless at this point
    return min_loc


def curveDistance(p1, p2, p3, p4, x, y):
    """
    Returns minimum distance between 3rd order Bézier curve p1 p2 p3 p4 and
    point p.

    TODO: is this really useful without the corresponding point?
    """
    projX, projY, _ = lineProjection(p1, p2, p3, p4, x, y)
    return distance(projX, projY, x, y)


def lineProjection(x1, y1, x2, y2, x, y, ditchOutOfSegment=True):
    """
    Returns minimum distance between line p1, p2 and point p.
    Adapted from Grumdrig, http://stackoverflow.com/a/1501725/2037879.

    If *ditchOutOfSegment* is set, this function will return None if point p
    cannot be projected on the segment, i.e. if there's no line perpendicular
    to p1 p2 that intersects both p and a point of p1 p2.
    This is useful for certain GUI usages. Set by default.
    """
    l2 = (x2 - x1) ** 2 + (y2 - y1) ** 2
    if l2 == 0:
        return (x1, y1, 0.0)
    aX = x - x1
    aY = y - y1
    bX = x2 - x1
    bY = y2 - y1
    t = (aX * bX + aY * bY) / l2
    if ditchOutOfSegment:
        if t < 0:
            return (x1, y1, t)
        elif t > 1:
            return (x2, y2, t)
    projX = x1 + t * bX
    projY = y1 + t * bY
    return (projX, projY, t)


def lineDistance(x, y, p1, p2):
    """
    Returns minimum distance between line p1 p2 and point p.
    """
    projX, projY, _ = lineProjection(p1.x, p1.y, p2.x, p2.y, x, y)
    return distance(x, y, projX, projY)


# intersections


def curveIntersections(x1, y1, x2, y2, p1, p2, p3, p4):
    """
    Computes intersection between a cubic spline and a line segment.
    Adapted from: https://www.particleincell.com/2013/cubic-line-intersection/

    Takes four points describing curve and four scalars describing line
    parameters.
    """

    bx, by = x1 - x2, y2 - y1
    m = x1 * (y1 - y2) + y1 * (x2 - x1)
    a, b, c, d = bezierTools.calcCubicParameters(
        (p1.x, p1.y), (p2.x, p2.y), (p3.x, p3.y), (p4.x, p4.y)
    )

    pc0 = by * a[0] + bx * a[1]
    pc1 = by * b[0] + bx * b[1]
    pc2 = by * c[0] + bx * c[1]
    pc3 = by * d[0] + bx * d[1] + m
    r = bezierTools.solveCubic(pc0, pc1, pc2, pc3)

    sol = []
    for t in r:
        if t < 0 or t > 1:
            continue
        s0 = ((a[0] * t + b[0]) * t + c[0]) * t + d[0]
        s1 = ((a[1] * t + b[1]) * t + c[1]) * t + d[1]
        if (x2 - x1) != 0:
            s = (s0 - x1) / (x2 - x1)
        else:
            s = (s1 - y1) / (y2 - y1)
        if s < 0 or s > 1:
            continue
        sol.append((s0, s1, t))
    return sol


def qcurveIntersections(x1, y1, x2, y2, *pts):
    """
    Computes intersection between a cubic spline and a line segment.
    Adapted from: https://www.particleincell.com/2013/cubic-line-intersection/

    Takes four points describing curve and four scalars describing line
    parameters.
    """

    sol = []

    # PACK for fontTools
    points = []
    for pt in pts:
        points.append((pt.x, pt.y))

    p1 = (pts[0].x, pts[0].y)
    for p2, p3 in decomposeQuadraticSegment(points[1:]):
        bx, by = (y1 - y2), (x2 - x1)
        m = x1 * y2 - x2 * y1
        a, b, c = bezierTools.calcQuadraticParameters(p1, p2, p3)

        # prepare for next turn
        p1 = p3

        pc0 = bx * a[0] - by * a[1]
        pc1 = (bx * b[0] + by * b[1]) / pc0
        pc2 = (bx * c[0] + by * c[1] + m) / pc0
        r = bezierTools.solveQuadratic(pc0, pc1, pc2)

        for t in r:
            if t < 0 or t > 1:
                continue
            s0 = a[0] * (1 - t) ** 2 + b[0] * 2 * t * (1 - t) + c[0] * t ** 2
            s1 = a[1] * (1 - t) ** 2 + b[1] * 2 * t * (1 - t) + c[1] * t ** 2
            if (x2 - x1) != 0:
                s = (s0 - x1) / (x2 - x1)
            else:
                s = (s1 - y1) / (y2 - y1)
            if s < 0 or s > 1:
                continue
            sol.append((s0, s1, t))
    return sol


def lineIntersection(x1, y1, x2, y2, x3, y3, x4, y4):
    """
    Computes intersection point of two lines if any, and the t value on p1p2
    (attn: if you want to use the t value order your segments accordingly!)
    Adapted from Andre LaMothe, "Tricks of the Windows Game Programming Gurus".
    G. Bach, http://stackoverflow.com/a/1968345

    Takes four scalars describing line and four scalars describing otherLine.
    """

    Bx_Ax = x2 - x1
    By_Ay = y2 - y1
    Dx_Cx = x4 - x3
    Dy_Cy = y4 - y3
    determinant = -Dx_Cx * By_Ay + Bx_Ax * Dy_Cy
    if abs(determinant) < 1e-20:
        return None
    s = (-By_Ay * (x1 - x3) + Bx_Ax * (y1 - y3)) / determinant
    t = (Dx_Cx * (y1 - y3) - Dy_Cy * (x1 - x3)) / determinant
    if s >= 0 and s <= 1 and t >= 0 and t <= 1:
        return (x1 + (t * Bx_Ax), y1 + (t * By_Ay), t)
    return None
