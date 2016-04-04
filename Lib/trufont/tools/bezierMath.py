from fontTools.misc import bezierTools
from math import sqrt

# TODO: curve distance


def distance(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    return sqrt(dx * dx + dy * dy)


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


def lineDistance(x1, y1, x2, y2, x, y):
    projX, projY, _ = lineProjection(x1, y1, x2, y2, x, y)
    return distance(x, y, projX, projY)

# intersections


def curveIntersections(p1, p2, p3, p4, x1, y1, x2, y2):
    """
    Computes intersection between a cubic spline and a line segment.
    Adapted from: https://www.particleincell.com/2013/cubic-line-intersection/

    Takes four defcon points describing curve and four scalars describing line
    parameters.
    """

    bx, by = x1 - x2, y2 - y1
    m = x1 * (y1 - y2) + y1 * (x2 - x1)
    a, b, c, d = bezierTools.calcCubicParameters(
        (p1.x, p1.y), (p2.x, p2.y), (p3.x, p3.y), (p4.x, p4.y))

    pc0 = by * a[0] + bx * a[1]
    pc1 = by * b[0] + bx * b[1]
    pc2 = by * c[0] + bx * c[1]
    pc3 = by * d[0] + bx * d[1] + m
    r = bezierTools.solveCubic(pc0, pc1, pc2, pc3)

    sol = []
    for t in r:
        s0 = a[0] * t ** 3 + b[0] * t ** 2 + c[0] * t + d[0]
        s1 = a[1] * t ** 3 + b[1] * t ** 2 + c[1] * t + d[1]
        if (x2 - x1) != 0:
            s = (s0 - x1) / (x2 - x1)
        else:
            s = (s1 - y1) / (y2 - y1)
        if not (t < 0 or t > 1 or s < 0 or s > 1):
            sol.append((s0, s1, t))
    return sol


def lineIntersection(x1, y1, x2, y2, x3, y3, x4, y4):
    """
    Computes intersection point of two lines if any.
    Adapted from Andre LaMothe, "Tricks of the Windows Game Programming Gurus".
    G. Bach, http://stackoverflow.com/a/1968345

    Takes four scalars describing line and four scalars describing otherLine.
    """

    Bx_Ax = x2 - x1
    By_Ay = y2 - y1
    Dx_Cx = x4 - x3
    Dy_Cy = y4 - y3
    determinant = (-Dx_Cx * By_Ay + Bx_Ax * Dy_Cy)
    if abs(determinant) < 1e-20:
        return None
    s = (-By_Ay * (x1 - x3) + Bx_Ax * (y1 - y3)) / determinant
    t = (Dx_Cx * (y1 - y3) - Dy_Cy * (x1 - x3)) / determinant
    if s >= 0 and s <= 1 and t >= 0 and t <= 1:
        return (x1 + (t * Bx_Ax), y1 + (t * By_Ay), t)
    return None
