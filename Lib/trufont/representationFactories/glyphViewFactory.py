from fontTools.misc.transform import Transform
from fontTools.pens.qtPen import QtPen
from fontTools.ufoLib.pointPen import PointToSegmentPen
from PyQt5.QtCore import Qt

from defconQt.representationFactories.glyphViewFactory import OnlyComponentsQtPen


def _reverseEnumerate(seq):
    n = len(seq)
    for obj in reversed(seq):
        n -= 1
        yield n, obj


# -------------------
# selected components
# -------------------


def SelectedComponentsQPainterPathFactory(glyph):
    pen = OnlyComponentsQtPen(glyph.layer)
    pointPen = PointToSegmentPen(pen)
    selectedPen = OnlyComponentsQtPen(glyph.layer)
    selectedPointPen = PointToSegmentPen(selectedPen)
    originPts = []
    for component in glyph.components:
        if component.selected:
            component.drawPoints(selectedPointPen)
            t = Transform(*component.transformation)
            originPts.append(t.transformPoint((0, 0)))
        else:
            component.drawPoints(pointPen)
    pen.path.setFillRule(Qt.WindingFill)
    selectedPen.path.setFillRule(Qt.WindingFill)
    return (pen.path, selectedPen.path, originPts)


# --------------
# component path
# --------------


def ComponentQPainterPathFactory(component):
    pen = OnlyComponentsQtPen(component.font)
    component.draw(pen)
    pen.path.setFillRule(Qt.WindingFill)
    return pen.path


# ---------------
# selection glyph
# ---------------


def FilterSelectionFactory(glyph):
    copyGlyph = glyph.__class__()
    # points
    pen = copyGlyph.getPointPen()
    for contour in glyph:
        onCurvesSelected = True
        for point in contour:
            if point.segmentType and not point.selected:
                onCurvesSelected = False
                break
        if onCurvesSelected:
            contour.drawPoints(pen)
        else:
            segments = contour.segments
            # put start point at the beginning of a subcontour
            lastSubcontour = None
            for index, segment in reversed(list(enumerate(segments))):
                if segment[-1].selected:
                    lastSubcontour = index
                else:
                    if lastSubcontour is not None:
                        break
            if lastSubcontour is None:
                continue
            segments = segments[lastSubcontour:] + segments[:lastSubcontour]
            # now draw filtered
            shouldMoveTo = True
            for segment in segments:
                on = segment[-1]
                if not on.selected:
                    if not shouldMoveTo:
                        pen.endPath()
                        shouldMoveTo = True
                    continue
                if on.segmentType == "move" and not shouldMoveTo:
                    pen.endPath()
                    shouldMoveTo = True
                if shouldMoveTo:
                    pen.beginPath()
                    pen.addPoint(
                        (on.x, on.y), segmentType="move", smooth=on.smooth, name=on.name
                    )
                    shouldMoveTo = False
                    continue
                for point in segment:
                    pen.addPoint(
                        (point.x, point.y),
                        segmentType=point.segmentType,
                        smooth=point.smooth,
                        name=point.name,
                    )
            if not shouldMoveTo:
                pen.endPath()
    # other stuff
    for component in glyph.components:
        if component.selected:
            component.drawPoints(pen)
    for anchor in glyph.anchors:
        if anchor.selected:
            copyGlyph.appendAnchor(dict(anchor))
    for guideline in glyph.guidelines:
        if guideline.selected:
            copyGlyph.appendGuideline(dict(guideline))
    if glyph.image is not None:
        if glyph.image.selected:
            copyGlyph.image = dict(glyph.image)
    return copyGlyph


def SelectedContoursQPainterPathFactory(glyph):
    copyGlyph = glyph.getRepresentation("TruFont.FilterSelection")
    path = copyGlyph.getRepresentation("defconQt.NoComponentsQPainterPath")
    return path


# --------------------
# curve path and lines
# --------------------


def SplitLinesQPainterPathFactory(glyph):
    pen = SplitLinesFromPathQtPen(glyph.layer)
    for contour in glyph:
        contour.draw(pen)
    pen.path.setFillRule(Qt.WindingFill)
    return (pen.path, pen.lines)


class SplitLinesFromPathQtPen(QtPen):
    def __init__(self, glyphSet, path=None):
        super().__init__(glyphSet, path)
        self.lines = []
        self._curPos = (0, 0)
        self._initPos = None

    def _registerPoint(self, p):
        self._curPos = (p[0], p[1])
        if self._initPos is None:
            self._initPos = self._curPos

    def _moveTo(self, p):
        super()._moveTo(p)
        self._registerPoint(p)

    def _lineTo(self, p):
        self.lines.append((self._curPos[0], self._curPos[1], p[0], p[1]))
        self._moveTo(p)

    def _curveToOne(self, p1, p2, p3):
        super()._curveToOne(p1, p2, p3)
        self._registerPoint(p3)

    def _qCurveToOne(self, p1, p2):
        super()._qCurveToOne(p1, p2)
        self._registerPoint(p2)

    def _closePath(self):
        if self._initPos is not None and self._curPos != self._initPos:
            self.lines.append(
                (self._curPos[0], self._curPos[1], self._initPos[0], self._initPos[1])
            )
        self._initPos = None

    def _endPath(self):
        self._initPos = None
