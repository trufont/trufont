"""
UI-constrained point management methods.
"""
from trufont.tools import bezierMath
from PyQt5.QtCore import QLineF
import math


def _getOffCurveSiblingPoints(contour, point):
    index = contour.index(point)
    pts = []
    for d in (-1, 1):
        sibling = contour.getPoint(index + d)
        if sibling.selected:
            continue
        if sibling.segmentType is not None:
            sSibling = contour.getPoint(index + 2 * d)
            curPts = (sibling, sSibling)
            if contour.open and any(pt == contour[0] for pt in curPts):
                continue
            pts.append(curPts)
    return pts


def maybeProjectUISmoothPointOffcurve(contour, onCurve):
    if not onCurve.smooth:
        return
    index = contour.index(onCurve)
    if contour.open and index in (0, len(contour) - 1):
        return
    offCurve, otherPoint = None, None
    for delta in (-1, 1):
        pt = contour.getPoint(index + delta)
        if pt.segmentType is None:
            if offCurve is not None:
                return
            offCurve = pt
        else:
            if otherPoint is not None:
                return
            otherPoint = pt
    if None not in (offCurve, otherPoint):
        # target angle: take the other onCurve's angle and add pi
        dy, dx = otherPoint.y - onCurve.y, otherPoint.x - onCurve.x
        angle = math.atan2(dy, dx) + math.pi
        # subtract the offCurve's angle
        dy, dx = offCurve.y - onCurve.y, offCurve.x - onCurve.x
        angle -= math.atan2(dy, dx)
        c, s = math.cos(angle), math.sin(angle)
        # rotate by our newly found angle
        # http://stackoverflow.com/a/2259502
        offCurve.x -= onCurve.x
        offCurve.y -= onCurve.y
        nx = offCurve.x * c - offCurve.y * s
        ny = offCurve.x * s + offCurve.y * c
        offCurve.x = nx + onCurve.x
        offCurve.y = ny + onCurve.y
        contour.dirty = True


def moveUIPoint(contour, point, delta):
    if point.segmentType is None:
        # point is an offCurve. Get its sibling onCurve and the other
        # offCurve.
        siblings = _getOffCurveSiblingPoints(contour, point)
        # if an onCurve is selected, the offCurve will move along with it
        if not siblings:
            return
        point.move(delta)
        for onCurve, otherPoint in siblings:
            if not onCurve.smooth:
                continue
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
                # i.e. do an orthogonal projection
                point.x, point.y, _ = bezierMath.lineProjection(
                    onCurve.x, onCurve.y, otherPoint.x, otherPoint.y,
                    point.x, point.y, False)
    else:
        # point is an onCurve. Move its offCurves along with it.
        index = contour.index(point)
        point.move(delta)
        for d in (-1, 1):
            # edge-case: contour open, trailing offCurve and moving first
            # onCurve in contour
            if contour.open and index == 0 and d == -1:
                continue
            pt = contour.getPoint(index + d)
            if pt.segmentType is None:
                # avoid double move for qCurve with single offCurve
                if d > 0:
                    otherPt = contour.getPoint(index + 2 * d)
                    if otherPt.segmentType is not None and \
                            otherPt.segmentType != "move" and otherPt.selected:
                        continue
                pt.move(delta)
                maybeProjectUISmoothPointOffcurve(contour, point)
    contour.dirty = True


def moveUISelection(contour, delta):
    for point in contour.selection:
        moveUIPoint(contour, point, delta)


def deleteUISelection(glyph):
    for anchor in glyph.anchors:
        anchor.selected = not anchor.selected
    for component in glyph.components:
        component.selected = not component.selected
    for contour in glyph:
        for point in contour:
            point.selected = not point.selected
        contour.postNotification("Contour.SelectionChanged")
    cutGlyph = glyph.getRepresentation("TruFont.FilterSelection")
    glyph.prepareUndo()
    glyph.holdNotifications()
    glyph.clear()
    pen = glyph.getPointPen()
    cutGlyph.drawPoints(pen)
    # HACK: defcon won't let us transfer anchors in bulk otherwise
    for anchor in cutGlyph.anchors:
        anchor._glyph = None
    glyph.anchors = cutGlyph.anchors
    glyph.releaseHeldNotifications()


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
            if preserveShape and contour.open:
                if index in (0, len(segments) - 1):
                    preserveShape = False
            contour.removeSegment(index, preserveShape)
            # remove segment so we can keep track of how many remain
            del segments[index]
        elif len(segment) == 2:
            # move with trailing offCurve
            offCurve = segment[0]
            if offCurve.selected:
                assert offCurve.segmentType is None
                contour.removePoint(offCurve)
        elif len(segment) == 3:
            # if offCurve selected, wipe them
            for i in (0, 1):
                if segment[i].selected:
                    contour.removePoint(segment[0])
                    contour.removePoint(segment[1])
                    segment[2].segmentType = "line"
                    break
