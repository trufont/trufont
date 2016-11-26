"""
UI-constrained point management methods.
"""
from trufont.tools import bezierMath
from PyQt5.QtCore import QLineF, QPointF
import itertools


def _getOffCurveSiblingPoints(contour, point):
    index = contour.index(point)
    pts = []
    # edge-cases: open contour boundaries and 3 offCurves+ qCurve segment
    shouldMoveAnyway = False
    onlyOffCurves = True
    for d in (-1, 1):
        sibling = contour.getPoint(index + d)
        if sibling.segmentType is not None:
            onlyOffCurves = False
        if sibling.selected:
            continue
        if sibling.segmentType is not None:
            sSibling = contour.getPoint(index + 2 * d)
            curPts = (sibling, sSibling)
            if contour.open and any(pt == contour[0] for pt in curPts):
                shouldMoveAnyway = True
                continue
            pts.append(curPts)
    if onlyOffCurves:
        shouldMoveAnyway = True
    return pts, shouldMoveAnyway


def maybeProjectUISmoothPointOffcurve(contour, onCurve, delta=None):
    if not onCurve.smooth:
        return
    index = contour.index(onCurve)
    if contour.open and index in (0, len(contour) - 1):
        return
    offCurve, otherPoint = None, None
    for d in (-1, 1):
        pt = contour.getPoint(index + d)
        if pt.segmentType is None:
            if offCurve is not None:
                return
            offCurve = pt
        else:
            if otherPoint is not None:
                return
            if pt.selected and onCurve.selected:
                return
            px, py = pt.x, pt.y
            if d == 1 and delta is not None:
                # this point hasn't been moved yet. add the delta
                dx, dy = delta
                px += dx
                py += dy
            otherPoint = (px, py)
    if None not in (offCurve, otherPoint):
        px, py = otherPoint
        rotateUIPointAroundRefLine(px, py, onCurve.x, onCurve.y, offCurve)


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
    pt.x = line.x2()
    pt.y = line.y2()


def moveUIPoint(contour, point, delta):
    if point.segmentType is None:
        # point is an offCurve. Get its sibling onCurve and the other
        # offCurve.
        siblings, shouldMoveAnyway = _getOffCurveSiblingPoints(contour, point)
        # if an onCurve is selected, the offCurve will move along with it
        if not (siblings or shouldMoveAnyway):
            return
        point.move(delta)
        for onCurve, otherPoint in siblings:
            if not onCurve.smooth or otherPoint.selected:
                continue
            # if the onCurve is smooth, we need to either...
            if otherPoint.segmentType is None:
                # keep the other offCurve inline
                rotateUIPointAroundRefLine(
                    point.x, point.y, onCurve.x, onCurve.y, otherPoint)
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
                maybeProjectUISmoothPointOffcurve(contour, point, delta)
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
            if onCurve.segmentType == "line":
                preserveShape = False
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
                    onCurve = segment[2]
                    otherOnCurve = contour.getPoint(contour.index(onCurve) - 3)
                    for i in range(2):
                        contour.removePoint(segment[i])
                    onCurve.segmentType = "line"
                    onCurve.smooth = otherOnCurve.smooth = False
                    break


def UIGlyphGuidelines(glyph):
    guidelines = glyph.guidelines
    font = glyph.font
    if font is not None:
        guidelines = itertools.chain(guidelines, font.guidelines)
    return guidelines


def moveUIGlyphElements(glyph, dx, dy):
    for anchor in glyph.anchors:
        if anchor.selected:
            anchor.move((dx, dy))
    for contour in glyph:
        moveUISelection(contour, (dx, dy))
    for component in glyph.components:
        if component.selected:
            component.move((dx, dy))
    for guideline in UIGlyphGuidelines(glyph):
        if guideline.selected:
            guideline.x += dx
            guideline.y += dy
    image = glyph.image
    if image.selected:
        image.move((dx, dy))


def removeUIGlyphElements(glyph, preserveShape):
    for anchor in glyph.anchors:
        if anchor.selected:
            glyph.removeAnchor(anchor)
    for contour in reversed(glyph):
        removeUISelection(contour, preserveShape)
    for component in glyph.components:
        if component.selected:
            glyph.removeComponent(component)
    for guideline in UIGlyphGuidelines(glyph):
        if guideline.selected:
            parent = guideline.getParent()
            parent.removeGuideline(guideline)
    if glyph.image.selected:
        glyph.image = None


def unselectUIGlyphElements(glyph):
    for anchor in glyph.anchors:
        anchor.selected = False
    for component in glyph.components:
        component.selected = False
    glyph.selected = False
    for guideline in UIGlyphGuidelines(glyph):
        guideline.selected = False
    glyph.image.selected = False
