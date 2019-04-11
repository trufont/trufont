from PyQt5.QtCore import QLineF, QPointF

from trufont.objects.defcon import TContour
from trufont.tools import bezierMath

# ----------------
# Helper functions
# ----------------


def nudgeUICurve(on1, off1, off2, on2, delta):
    if on2.selected != on1.selected:
        sign = -on1.selected or 1
        sdx, sdy = map(float(sign).__mul__, delta)
        # factor
        xFactor = on2.x - on1.x - sdx
        if xFactor:
            xFactor = (on2.x - on1.x) / xFactor
        yFactor = on2.y - on1.y - sdy
        if yFactor:
            yFactor = (on2.y - on1.y) / yFactor
        # apply
        if not off1.selected:
            off1.x = on1.x + xFactor * (off1.x - on1.x)
            off1.y = on1.y + yFactor * (off1.y - on1.y)
        if not off2.selected:
            off2.x = on1.x + xFactor * (off2.x - on1.x - sdx)
            off2.y = on1.y + yFactor * (off2.y - on1.y - sdy)


def projectUIPointOnRefLine(x1, y1, x2, y2, pt):
    x, y, t = bezierMath.lineProjection(x1, y1, x2, y2, pt.x, pt.y, False)
    # TODO: use grid precision ROUND
    pt.x = x  # round(x)
    pt.y = y  # round(y)


def rotateUIPointAroundRefLine(x1, y1, x2, y2, pt):
    """
    Given three points p1, p2, pt this rotates pt around p2 such that p1,p2 and
    p1,pt are collinear.
    """
    line = QLineF(pt.x, pt.y, x2, y2)
    p2p_l = line.length()
    line.setP1(QPointF(x1, y1))
    p1p2_l = line.length()
    if not p1p2_l:
        return
    line.setLength(p1p2_l + p2p_l)
    # TODO: use grid precision ROUND
    pt.x = line.x2()  # round(line.x2())
    pt.y = line.y2()  # round(line.y2())


# ----------
# Main sauce
# ----------


def UIMove(contour, delta, nudgePoints=False, slidePoints=False):
    contour_ = contour
    # start at an onCurve; situations we want to avoid are:
    # - two offCurves at the start of the contour, since all "handles ops"
    #   (like rotation etc.) need a "next" offCurve after reading the parent
    #   onCurve
    # - one offCurve at the start of the contour, nudge needs to read the
    #   previous onCurve followed by offCurves (followed by onCurve)
    if len(contour) > 2 and contour[0].segmentType is None:
        offset = 1 + (contour[1].segmentType is None)
        contour = contour[offset:] + contour[:offset]
    # first pass: move
    didMove = False
    nextOffShouldMove = False
    nudgeStuff = []
    prev = contour[-1]
    for point in contour:
        if len(nudgeStuff) == 1 and point.segmentType is None:
            nudgeStuff.append(point)
        if point.selected or (nextOffShouldMove and point.segmentType is None):
            point.move(delta)
            didMove = True
        nextOffShouldMove = False
        if point.segmentType and not slidePoints:
            if point.selected:
                # move previous point
                if (
                    prev.segmentType is None
                    and not prev.selected
                    and point.segmentType != "move"
                ):
                    prev.move(delta)
                    didMove = True
                # schedule the next point for move
                nextOffShouldMove = True
            if nudgePoints:
                if len(nudgeStuff) == 2 and point.segmentType == "curve":
                    on1, off1 = nudgeStuff
                    nudgeUICurve(on1, off1, prev, point, delta)
                nudgeStuff = [point]
        prev = point
    if len(nudgeStuff) == 2 and contour[0].segmentType == "curve":
        on1, off1 = nudgeStuff
        nudgeUICurve(on1, off1, prev, contour[0], delta)
    if not didMove:
        return
    del nudgeStuff
    # second pass: constrain
    secondPrevForSliding = None
    secondPrevForRotation = None
    prev = contour[-1]
    for point in contour:
        # slide points
        if secondPrevForSliding is not None and (
            point.segmentType is None or secondPrevForSliding.segmentType is None
        ):
            p1, p2, p3 = secondPrevForSliding, prev, point
            if p2.selected and p2.segmentType != "move":
                if p1.selected or p3.selected:
                    if p1.selected:
                        p1, p3 = p3, p1
                    # if p3 is selected, we just let it move freely
                    if not p1.selected and p3.segmentType is None:
                        rotateUIPointAroundRefLine(p1.x, p1.y, p2.x, p2.y, p3)
                else:
                    if p2.smooth:
                        projectUIPointOnRefLine(p1.x, p1.y, p3.x, p3.y, p2)
            elif p1.selected != p3.selected:
                if p1.selected:
                    p1, p3 = p3, p1
                if p3.segmentType is None:
                    if p2.smooth and p2.segmentType != "move":
                        projectUIPointOnRefLine(p1.x, p1.y, p2.x, p2.y, p3)
                    else:
                        dx, dy = delta
                        rx, ry = p3.x - dx, p3.y - dy
                        projectUIPointOnRefLine(p2.x, p2.y, rx, ry, p3)
        secondPrevForSliding = None
        if slidePoints and point.segmentType is not None:
            secondPrevForSliding = prev
        # rotation/projection across smooth onCurve
        if secondPrevForRotation is not None and (
            point.segmentType is None or secondPrevForRotation.segmentType is None
        ):
            p1, p2, p3 = secondPrevForRotation, prev, point
            if p2.selected:
                if p1.segmentType is None:
                    p1, p3 = p3, p1
                if p1.segmentType is not None:
                    rotateUIPointAroundRefLine(p1.x, p1.y, p2.x, p2.y, p3)
            elif p1.selected != p3.selected:
                if p1.selected:
                    p1, p3 = p3, p1
                if p1.segmentType is not None:
                    projectUIPointOnRefLine(p1.x, p1.y, p2.x, p2.y, p3)
                elif not slidePoints:
                    rotateUIPointAroundRefLine(p3.x, p3.y, p2.x, p2.y, p1)
        secondPrevForRotation = None
        if point.smooth and point.segmentType not in ("move", None):
            secondPrevForRotation = prev
        # --
        prev = point
    contour_.dirty = True


# -----
# Tests
# -----


def UIMove_buildContour(data):
    contour = TContour()
    pen = contour
    pen.beginPath()
    for coords, segmentType, smooth, selected in data:
        pen.addPoint(coords, segmentType, smooth, selected=selected)
    pen.endPath()
    return contour


def UIMove_testContour(contour, data):
    assert len(contour) == len(data), "contour has len {}, expected {}".format(
        len(contour), len(data)
    )
    try:
        for point, (coords, segmentType, smooth, selected) in zip(contour, data):
            # HACK: we round here for now
            point.x = round(point.x)
            point.y = round(point.y)
            assert (point.x, point.y) == coords
            assert point.segmentType == segmentType
            assert point.smooth == smooth
            assert point.selected == selected
    except AssertionError:
        # TODO: pprint and make array from contour instead of doing this
        # manually
        print("contour gives:")
        print("[")
        for point in contour:
            print(
                "    (({}, {}), {}, {}, {}),".format(
                    point.x,
                    point.y,
                    repr(point.segmentType),
                    point.smooth,
                    point.selected,
                )
            )
        print("]")
        print("expected:")
        print("[")
        for line in data:
            print(f"    {line},")
        print("]")
        print()


# runner


def UIMove_runTests():
    UIMove_test_move()
    UIMove_test_move_offWithOn()
    UIMove_test_move_offAtStart()
    UIMove_test_constrain_slidePoints()
    UIMove_test_constrain_smoothOffRotation()
    UIMove_test_constrain_smoothOnProjection()


# tests


def UIMove_test_move():
    """
    Simple test moving onCurve points.

    At closed and open contour boundaries.
    """
    contour = UIMove_buildContour(
        [
            ((0, 0), "move", False, False),
            ((3, 2), "line", False, True),
            ((0, 3), "line", False, False),
        ]
    )
    UIMove(contour, (2, 3))
    UIMove_testContour(
        contour,
        [
            ((0, 0), "move", False, False),
            ((5, 5), "line", False, True),
            ((0, 3), "line", False, False),
        ],
    )
    contour[1].selected = False
    contour[2].selected = True
    UIMove(contour, (2, 3))
    UIMove_testContour(
        contour,
        [
            ((0, 0), "move", False, False),
            ((5, 5), "line", False, False),
            ((2, 6), "line", False, True),
        ],
    )


def UIMove_test_move_offWithOn():
    """
    Moving offCurve points along with their onCurve.

    Make sure offCurve points move with the onCurve, whether or not the
    offCurve is selected.

    Make sure an offCurve moves normally when its onCurve is not selected.

    Edge-case: given an open contour with trailing offCurve, make sure the
    first point moving does not move the trailing offCurve.

    TODO: Edge-case: avoid double move for quadratic curve with single
    offCurve.
    """
    contour = UIMove_buildContour(
        [
            ((3, 0), "move", False, True),
            ((3, 2), None, False, False),
            ((2, 3), None, False, False),
            ((0, 3), "curve", False, False),
            ((-2, 3), None, False, False),
        ]
    )
    UIMove(contour, (1, 2))
    UIMove_testContour(
        contour,
        [
            ((4, 2), "move", False, True),
            ((4, 4), None, False, False),
            ((2, 3), None, False, False),
            ((0, 3), "curve", False, False),
            ((-2, 3), None, False, False),
        ],
    )
    contour[0].selected = False
    contour[2].selected = True
    contour[3].selected = True
    UIMove(contour, (1, 2))
    UIMove_testContour(
        contour,
        [
            ((4, 2), "move", False, False),
            ((4, 4), None, False, False),
            ((3, 5), None, False, True),
            ((1, 5), "curve", False, True),
            ((-1, 5), None, False, False),
        ],
    )
    contour[1].selected = True
    contour[3].smooth = True
    UIMove(contour, (1, 2))
    UIMove_testContour(
        contour,
        [
            ((4, 2), "move", False, False),
            ((5, 6), None, False, True),
            ((4, 7), None, False, True),
            ((2, 7), "curve", True, True),
            ((0, 7), None, False, False),
        ],
    )


def UIMove_test_move_offAtStart():
    """
    Make sure everything works in the special case of two offCurves
    at the beginning of a contour.
    """
    contour = UIMove_buildContour(
        [
            ((2, 2), None, False, True),
            ((1, 3), None, False, True),
            ((0, 5), "curve", False, True),
            ((3, 0), "line", False, True),
        ]
    )
    UIMove(contour, (2, 1))
    UIMove_testContour(
        contour,
        [
            ((4, 3), None, False, True),
            ((3, 4), None, False, True),
            ((2, 6), "curve", False, True),
            ((5, 1), "line", False, True),
        ],
    )


def UIMove_test_constrain_slidePoints():
    """
    Slide points along Bézier handles. Disarm other move relationships
    (offWithOn, onCurve moves offCurve across its sibling smooth on)

    Make sure non-smooth onCurve isn't constrained when moving.
    """
    contour = UIMove_buildContour(
        [
            ((3, 0), "move", False, False),
            ((2, 2), None, False, False),
            ((1, 3), None, False, False),
            ((0, 5), "curve", True, True),
            ((-1, 7), None, False, False),
        ]
    )
    UIMove(contour, (2, 2), slidePoints=True)
    UIMove_testContour(
        contour,
        [
            ((3, 0), "move", False, False),
            ((2, 2), None, False, False),
            ((1, 3), None, False, False),
            ((0, 6), "curve", True, True),
            ((-1, 7), None, False, False),
        ],
    )
    contour[4].selected = True
    UIMove(contour, (2, 0), slidePoints=True)
    UIMove_testContour(
        contour,
        [
            ((3, 0), "move", False, False),
            ((2, 2), None, False, False),
            ((1, 3), None, False, False),
            ((2, 6), "curve", True, True),
            ((2, 7), None, False, True),
        ],
    )
    contour[3].selected = False
    contour[4].selected = False
    contour[1].selected = True
    UIMove(contour, (1, 3), slidePoints=True)
    UIMove_testContour(
        contour,
        [
            ((3, 0), "move", False, False),
            ((1, 4), None, False, True),
            ((1, 3), None, False, False),
            ((2, 6), "curve", True, False),
            ((2, 7), None, False, False),
        ],
    )
    contour[4].segmentType = "line"
    contour[1].selected = False
    contour[4].selected = True
    UIMove(contour, (-2, -3), slidePoints=True)
    UIMove_testContour(
        contour,
        [
            ((3, 0), "move", False, False),
            ((1, 4), None, False, False),
            ((1, 3), None, False, False),
            ((2, 6), "curve", True, False),
            ((0, 4), "line", False, True),
        ],
    )
    contour[4].segmentType = None
    contour[2].selected = True
    contour[3].selected = True
    UIMove(contour, (4, 2), slidePoints=True)
    UIMove_testContour(
        contour,
        [
            ((3, 0), "move", False, False),
            ((1, 4), None, False, False),
            ((5, 5), None, False, True),
            ((6, 8), "curve", True, True),
            ((4, 6), None, False, True),
        ],
    )
    contour[2].selected = False
    contour[4].selected = False
    contour[3].smooth = False
    UIMove(contour, (-4, -2), slidePoints=True)
    UIMove_testContour(
        contour,
        [
            ((3, 0), "move", False, False),
            ((1, 4), None, False, False),
            ((5, 5), None, False, False),
            ((2, 6), "curve", False, True),
            ((4, 6), None, False, False),
        ],
    )


def UIMove_test_constrain_smoothOffRotation():
    """
    Rotate offCurve point across smooth onCurve.
    NOTE: we make sure in the first test to make it fail if the function
    projects instead of rotating (by doing a pi/2 rotation, hence making
    old/new vectors orthogonal).

    Edge-case: don't rotate across open contour boundary; given a trailing
    offCurve.

    Make sure that two offCurve on either side of a smooth point can move
    freely if the smooth point is unselected.
    TODO: is this really the ideal behavior? I guess it makes the most sense.
    """
    contour = UIMove_buildContour(
        [
            ((3, 0), "move", True, False),
            ((3, 2), None, False, False),
            ((2, 4), None, False, True),
            ((0, 3), "curve", True, False),
            ((-2, 2), None, False, False),
        ]
    )
    UIMove(contour, (-3, 1))
    UIMove_testContour(
        contour,
        [
            ((3, 0), "move", True, False),
            ((3, 2), None, False, False),
            ((-1, 5), None, False, True),
            ((0, 3), "curve", True, False),
            ((1, 1), None, False, False),
        ],
    )
    contour[2].selected = False
    contour[1].selected = True
    UIMove(contour, (1, 2))
    UIMove_testContour(
        contour,
        [
            ((3, 0), "move", True, False),
            ((4, 4), None, False, True),
            ((-1, 5), None, False, False),
            ((0, 3), "curve", True, False),
            ((1, 1), None, False, False),
        ],
    )
    contour[1].selected = False
    contour[2].selected = True
    contour[3].selected = True
    UIMove(contour, (1, 2))
    UIMove_testContour(
        contour,
        [
            ((3, 0), "move", True, False),
            ((4, 4), None, False, False),
            ((0, 7), None, False, True),
            ((1, 5), "curve", True, True),
            ((2, 3), None, False, False),
        ],
    )
    contour[3].selected = False
    contour[4].selected = True
    UIMove(contour, (1, 2))
    UIMove_testContour(
        contour,
        [
            ((3, 0), "move", True, False),
            ((4, 4), None, False, False),
            ((1, 9), None, False, True),
            ((1, 5), "curve", True, False),
            ((3, 5), None, False, True),
        ],
    )


def UIMove_test_constrain_smoothOnProjection():
    """
    Project offCurve point across smooth onCurve (with another onCurve on the
    other side).

    Edge-case: don't project across open contour boundary; given a trailing
    offCurve, smooth onCurve first point, and selected onCurve second point.

    Make sure moving the smooth point rotates its sibling offCurve.

    Make two onCurves around a smooth onCurve don't get constrained.

    TODO: handle the case where the onCurve and offCurve on each side of the
    smooth point are selected.
    """
    contour = UIMove_buildContour(
        [
            ((3, 0), "move", True, False),
            ((2, 2), "line", True, False),
            ((1, 4), None, False, True),
            ((0, 5), None, False, False),
            ((-2, 5), "curve", True, False),
            ((-4, 5), "line", True, False),
            ((-6, 5), None, False, False),
        ]
    )
    UIMove(contour, (1, 3))
    UIMove_testContour(
        contour,
        [
            ((3, 0), "move", True, False),
            ((2, 2), "line", True, False),
            ((0, 6), None, False, True),
            ((0, 5), None, False, False),
            ((-2, 5), "curve", True, False),
            ((-4, 5), "line", True, False),
            ((-6, 5), None, False, False),
        ],
    )
    UIMove(contour, (5, -4))
    UIMove_testContour(
        contour,
        [
            ((3, 0), "move", True, False),
            ((2, 2), "line", True, False),
            ((1, 3), None, False, True),
            ((0, 5), None, False, False),
            ((-2, 5), "curve", True, False),
            ((-4, 5), "line", True, False),
            ((-6, 5), None, False, False),
        ],
    )
    contour[2].selected = False
    contour[0].selected = True
    UIMove(contour, (-3, 2))
    UIMove_testContour(
        contour,
        [
            ((0, 2), "move", True, True),
            ((2, 2), "line", True, False),
            ((3, 2), None, False, False),
            ((0, 5), None, False, False),
            ((-2, 5), "curve", True, False),
            ((-4, 5), "line", True, False),
            ((-6, 5), None, False, False),
        ],
    )
    contour[1].selected = True
    UIMove(contour, (1, 2))
    UIMove_testContour(
        contour,
        [
            ((1, 4), "move", True, True),
            ((3, 4), "line", True, True),
            ((4, 4), None, False, False),
            ((0, 5), None, False, False),
            ((-2, 5), "curve", True, False),
            ((-4, 5), "line", True, False),
            ((-6, 5), None, False, False),
        ],
    )
    contour[0].selected = False
    contour[1].selected = False
    contour[5].selected = True
    UIMove(contour, (0, 2))
    UIMove_testContour(
        contour,
        [
            ((1, 4), "move", True, False),
            ((3, 4), "line", True, False),
            ((4, 4), None, False, False),
            ((-1, 4), None, False, False),
            ((-2, 5), "curve", True, False),
            ((-4, 7), "line", True, True),
            ((-5, 8), None, False, False),
        ],
    )
    contour[4].smooth = False
    contour[6].segmentType = "line"
    UIMove(contour, (1, 2))
    UIMove_testContour(
        contour,
        [
            ((1, 4), "move", True, False),
            ((3, 4), "line", True, False),
            ((4, 4), None, False, False),
            ((-1, 4), None, False, False),
            ((-2, 5), "curve", False, False),
            ((-3, 9), "line", True, True),
            ((-5, 8), "line", False, False),
        ],
    )
    contour[5].selected = False
    contour[6].selected = True
    UIMove(contour, (1, 2))
    UIMove_testContour(
        contour,
        [
            ((1, 4), "move", True, False),
            ((3, 4), "line", True, False),
            ((4, 4), None, False, False),
            ((-1, 4), None, False, False),
            ((-2, 5), "curve", False, False),
            ((-3, 9), "line", True, False),
            ((-4, 10), "line", False, True),
        ],
    )
