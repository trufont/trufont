from fontTools.misc import bezierTools
from math import sqrt
from sympy import poly, sturm, Symbol

# distance


def distance(x1, y1, x2, y2):
    """
    Returns distance between two points x1 y1 and x2 y2.
    """
    dx = x2 - x1
    dy = y2 - y1
    return sqrt(dx * dx + dy * dy)


def _sturmApprox(sturm, a, b):
    """
    Discriminate real roots onto distinct intervals using Sturm theorem, given
    sturm chain and search interval.

    http://math.ucsb.edu/~padraic/mathcamp_2013/root_find_alg/
    Mathcamp_2013_Root-Finding_Algorithms_Day_2.pdf
    """

    def isRoot(c):
        for polyn in sturm:
            if abs(polyn.eval(c)) < 1e-6:
                return True
        return False

    # sigma(a) - sigma(b), we're looking at [a, b] interval
    sigma = []
    for e in (a, b):
        count = 0
        isPositive = None
        for polyn in sturm:
            value = polyn.eval(e) >= 0
            if isPositive is not None and isPositive != value:
                count += 1
            isPositive = value
        sigma.append(count)
    res = sigma[0] - sigma[1]
    if res == 0:
        # no roots in this interval
        return []
    elif res == 1:
        return [a, b]
    else:
        c = (a + b) / 2
        while isRoot(c):
            c += 1e-3
        assert(c < a)
        return _sturmApprox(sturm, a, c) + _sturmApprox(sturm, c, b)


def curveProjection(p1, p2, p3, p4, x, y):
    """
    Returns projection of point p on 3rd order Bézier curve p1 p2 p3 p4.
    Adapted from "Improved Algebraic Algorithm On Point Projection For Bézier
    Curves" by Xiao-Diao Chen, Yin Zhou, Zhenyu Shu, Hua Su and Jean-Claude
    Paul.
    """

    a, b, c, d = bezierTools.calcCubicParameters(
        (p1.x, p1.y), (p2.x, p2.y), (p3.x, p3.y), (p4.x, p4.y))
    # eqn formulation and first solving pass
    lo = None
    p = (x, y)
    t = Symbol('t')
    Vs = []
    for i in (0, 1):
        # explicit curve eqn
        V = a[i] * t**3 + b[i] * t**2 + c[i] * t + d[i]
        # first derivative
        Vp = 3 * a[i] * t**2 + 2 * b[i] * t + c[i]
        # distance eqn
        g = Vp * (p[i] - V)
        if g == 0:
            # collinear CPs... the curve is a li(n)e!
            # XXX: fill in w lineDistance here
            continue
        g = poly(g)
        Vs.append(poly(V))
        # approx. roots using the sturm theorem
        intervals = _sturmApprox(sturm(g), 0, 1)
        # pruning: roots are valid iff g(ai) < 0 and g(bi) > 0
        psol = []
        print(intervals)
        for ai, bi in zip(intervals[::2], intervals[1::2]):
            print("here--", g.eval(ai), g.eval(bi))
            if g.eval(ai) < 0 and g.eval(bi) > 0:
                print("pruned")
            psol.append((ai, bi))
        # bisection
        roots = []
        for ai, bi in psol:
            while True:
                mi = (ai + bi) / 2
                if bi - ai < 1e-6:
                    roots.append((mi, i))
                    break
                gmi = g.eval(mi)
                if gmi == 0:
                    roots.append((mi, i))
                    break
                elif gmi < 0:
                    ai = mi
                else:
                    bi = mi
        # picking: choose the root that minimizes the distance
        for ri, i in roots:
            gri = g.eval(ri)
            if lo is None:
                lo = (ri, gri)
            else:
                if gri < lo[1]:
                    lo = (ri, gri)
    if lo is not None:
        root = lo[0]
        rx = Vs[0].eval(root)
        ry = Vs[1].eval(root)
        return (rx, ry)
    return None


def curveDistance(p1, p2, p3, p4, x, y):
    """
    Returns minimum distance between 3rd order Bézier curve p1 p2 p3 p4 and
    point p.
    """
    rx, ry = curveProjection(p1, p2, p3, p4, x, y)
    return distance(rx, ry, x, y)


def lineProjection(x1, y1, x2, y2, x, y, ditchOutOfSegment=True):
    """
    Returns minimum distance between line p1, p2 and point p.
    Adapted from Grumdrig, http://stackoverflow.com/a/1501725/2037879.

    If *ditchOutOfSegment* is set, this function will return None if point p
    cannot be projected on the segment, ie. if there's no line perpendicular to
    p1 p2 that intersects both p and a point of p1 p2.
    This is useful for certain GUI usages. Set by default.
    """

    l2 = (x2 - x1) ** 2 + (y2 - y1) ** 2
    if l2 == 0:
        return (x1, y1)
    aX = x - x1
    aY = y - y1
    bX = x2 - x1
    bY = y2 - y1
    t = (aX * bX + aY * bY) / l2
    if t < 0:
        if ditchOutOfSegment:
            return None
        return (x1, y1)
    elif t > 1:
        if ditchOutOfSegment:
            return None
        return (x2, y2)
    projX = x1 + t * bX
    projY = y1 + t * bY
    return (projX, projY)


def lineDistance(x1, y1, x2, y2, x, y):
    rx, ry = lineProjection(x1, y1, x2, y2, x, y)
    return distance(rx, ry, x, y)

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
