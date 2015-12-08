"""
UI-constrained point management methods.
"""
from PyQt5.QtCore import QLineF, QPointF


def _getOffCurveSiblingPoints(contour, point):
    index = contour.index(point)
    for d in (-1, 1):
        sibling = contour.getPoint(index + d)
        if sibling.segmentType is not None:
            sSibling = contour.getPoint(index + 2 * d)
            return sibling, sSibling
    raise IndexError


def moveUIPoint(contour, point, delta):
    if point.segmentType is None:
        # point is an offCurve. Get its sibling onCurve and the other
        # offCurve.
        onCurve, otherPoint = _getOffCurveSiblingPoints(contour, point)
        # if the onCurve is selected, the offCurve will move along with it
        if onCurve.selected:
            return
        point.move(delta)
        if not onCurve.smooth:
            contour.dirty = True
            return
        # if the onCurve is smooth, we need to either...
        if otherPoint.segmentType is None and not otherPoint.selected:
            # keep the other offCurve inline
            line = QLineF(point.x, point.y, onCurve.x, onCurve.y)
            otherLine = QLineF(
                onCurve.x, onCurve.y, otherPoint.x, otherPoint.y)
            line.setLength(line.length() + otherLine.length())
            otherPoint.x = line.x2()
            otherPoint.y = line.y2()
        else:
            # keep point in tangency with onCurve -> otherPoint segment,
            # ie. do an orthogonal projection
            line = QLineF(otherPoint.x, otherPoint.y, onCurve.x, onCurve.y)
            n = line.normalVector()
            n.translate(QPointF(point.x, point.y) - n.p1())
            targetPoint = QPointF()
            n.intersect(line, targetPoint)
            # check that targetPoint is beyond its neighbor onCurve
            # we do this by calculating position of the offCurve and second
            # onCurve relative to the first onCurve. If there is no symmetry
            # in at least one of the axis, then we need to clamp
            onCurvePoint = line.p2()
            onDistance = line.p1() - onCurvePoint
            newDistance = targetPoint - onCurvePoint
            if (onDistance.x() >= 0) != (newDistance.x() <= 0) or \
                    (onDistance.y() >= 0) != (newDistance.y() <= 0):
                targetPoint = onCurvePoint
            # ok, now set pos
            point.x, point.y = targetPoint.x(), targetPoint.y()
    else:
        # point is an onCurve. Move its offCurves along with it.
        index = contour.index(point)
        point.move(delta)
        for d in (-1, 1):
            pt = contour.getPoint(index + d)
            if pt.segmentType is None:
                pt.move(delta)
    contour.dirty = True


def moveUISelection(contour, delta):
    for point in contour.selection:
        moveUIPoint(contour, point, delta)


def removeUISelection(contour, preserveShape=True):
    segments = contour.segments
    # the last segments contains the first point, make sure to process it last
    # so as to not offset indexes
    toFirstPoint = segments[-1]
    toIter = list(enumerate(segments))
    toIter.insert(0, toIter.pop())
    # moonwalk through segments
    for index, segment in reversed(toIter):
        if segment == toFirstPoint:
            index = len(segments) - 1
        onCurve = segment[-1]
        # if the onCurve is selected, wipe it
        if onCurve.selected:
            # remove the contour if we have exhausted segments
            if len(segments) < 2:
                glyph = contour.glyph
                glyph.removeContour(contour)
                return
            # using preserveShape at the edge of an open contour will traceback
            if contour.open and contour.index(onCurve) == len(contour):
                preserveShape = False
            contour.removeSegment(index, preserveShape)
            # remove segment so we can keep track of how many remain
            del segments[index]
        elif len(segment) == 3:
            # if offCurve selected, wipe them
            for i in (0, 1):
                if segment[i].selected:
                    contour.removePoint(segment[0])
                    contour.removePoint(segment[1])
                    segment[2].segmentType = "line"
                    break
