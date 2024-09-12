from math import comb
from fontTools.misc import bezierTools


def getArcLength(p_list):
    return bezierTools.calcCubicArcLength(p_list[0], p_list[1], p_list[2], p_list[3])


def getBezierCoeffs(px, b_order):
    """
    Computes the bezier coefficients
    """
    # TODO: simplify for quadratic and cubic to improve performance

    coeffs = []

    for i in range(b_order + 1):
        cc = 0
        sig = 1 if (i % 2 == 0) else -1
        for j in range(i + 1):
            cc = cc + px[j] * sig * comb(i, j)
            sig = -sig
        coeffs.append(cc)
    return coeffs


def getCurvature(px, py, t):
    """
    Computes the curvature at parameter t, where t is in [0, 1].

    Returns the x, y values for parameter r, the tangent vectors dx, dy and the
    curvature value c
    """

    b_order = len(px) - 1

    # Calculate coefficients
    ax = getBezierCoeffs(px, b_order)
    ay = getBezierCoeffs(py, b_order)

    # Calculate curve points
    tn = []
    for i in range(b_order + 1):
        tn.append(t ** i)

    coeffs = [comb(b_order, i) for i in range(b_order + 1)]

    x_t = 0
    y_t = 0
    for i in range(b_order + 1):
        x_t = x_t + coeffs[i] * ax[i] * tn[i]
        y_t = y_t + coeffs[i] * ay[i] * tn[i]

    # Calculate curvature
    # Derivatives
    coeffs1 = [comb(b_order - 1, i) * b_order for i in range(b_order)]

    x_dot = 0
    y_dot = 0
    for i in range(b_order):
        x_dot = x_dot + coeffs1[i] * ax[i + 1] * tn[i]
        y_dot = y_dot + coeffs1[i] * ay[i + 1] * tn[i]

    # Tangent vectors
    d_dot = (x_dot ** 2 + y_dot ** 2) ** 0.5
    if d_dot == 0:
        return {"x": x_t, "y": y_t, "dx": 0, "dy": 0, "c": 0}
    ex = x_dot / d_dot
    ey = y_dot / d_dot

    # 2nd derivatives
    coeffs2 = [
        comb(b_order - 2, i) * (b_order) * (b_order - 1) for i in range(b_order - 1)
    ]

    x_2dot = 0
    y_2dot = 0
    for i in range(b_order - 1):
        x_2dot = x_2dot + coeffs2[i] * ax[i + 2] * tn[i]
        y_2dot = y_2dot + coeffs2[i] * ay[i + 2] * tn[i]

    cvt = (x_2dot * y_dot - y_2dot * x_dot) / abs(x_dot ** 2 + y_dot ** 2) ** (3 / 2)

    return {"x": x_t, "y": y_t, "dx": ex, "dy": ey, "c": cvt}
