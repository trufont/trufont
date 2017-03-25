from PyQt5.QtCore import Qt
from defcon.objects.contour import Recorder  # XXX: should be somewhere else
from defconQt.representationFactories.glyphViewFactory import (
    OnlyComponentsQtPen)
from fontTools.misc.transform import Transform
from fontTools.pens.qtPen import QtPen
from ufoLib.pointPen import AbstractPointPen, PointToSegmentPen


class MutRecorder(Recorder):

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)

        def command(*args, **kwds):
            self._data.append([name, list(args), kwds])
        # cache the method, don't use __setattr__
        self.__dict__[name] = command
        return command


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
    pen = FilterSelectionPen(copyGlyph.getPointPen())
    glyph.drawPoints(pen)
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


class FilterSelectionPen(AbstractPointPen):

    def __init__(self, outPen):
        self.recordData = []
        # TODO: use a more direct way of storage, like fontTools RecordingPen
        self.pen = MutRecorder(self.recordData)
        self.outPen = outPen

        self.shouldBeginPath = True
        self.offCurves = []
        self.lastOnCurveSelected = False
        self.onCurveDropped = False
        self.firstOnCurveIsntMove = False

    def beginPath(self, identifier=None, **kwargs):
        self.atContourStart = self.shouldBeginPath = True
        self.firstOnCurveIsntMove = self.lastOnCurveSelected = \
            self.onCurveDropped = False

    def endPath(self):
        # end path
        if not self.shouldBeginPath:
            if self.offCurves:
                for data, kwargs_ in self.offCurves:
                    self.pen.addPoint(*data, **kwargs_)
            self.pen.endPath()
        self.offCurves = []
        # process
        # NSC of non-direct compatibility (by elision-rotation):
        # - first onCurve isn't a move
        # - last onCurve isn't dropped
        # - an onCurve is dropped in the contour
        if self.firstOnCurveIsntMove and self.lastOnCurveSelected and \
                self.onCurveDropped:
            # remove beginPath/endPath at source contour boundary
            del self.recordData[0]
            del self.recordData[-1]
            # rotate source data to put the last beginPath in ident position
            for index, (methodName, *_) in _reverseEnumerate(self.recordData):
                if methodName == "beginPath":
                    self.recordData[:] = self.recordData[
                        index:] + self.recordData[:index]
                    break
        # if the last onCurve is dropped, we need to correct the first poin
        # into a move + remove any preceding offCurves
        elif len(self.recordData) > 3 and not self.lastOnCurveSelected:
            self.recordData[1][1][1] = "move"
            beginIndex = endIndex = None
            for index, (_, args, _) in _reverseEnumerate(self.recordData[:-1]):
                if args[1] is None:
                    beginIndex = index
                    if endIndex is None:
                        endIndex = index
                else:
                    break
            if endIndex is not None:
                del self.recordData[beginIndex:endIndex]
        self.pen(self.outPen)
        self.recordData.clear()

    def addPoint(self, pt, segmentType=None, smooth=False, name=None,
                 identifier=None, **kwargs):
        if segmentType is not None:
            self.lastOnCurveSelected = selected = kwargs.get("selected")
            if selected:
                if self.atContourStart:
                    self.firstOnCurveIsntMove = segmentType != "move"
                elif self.shouldBeginPath:
                    segmentType = "move"
                if self.shouldBeginPath:
                    self.pen.beginPath()
                    self.pen.addPoint(
                        pt, segmentType, smooth, name, identifier, **kwargs)
                    self.shouldBeginPath = False
                else:
                    if self.offCurves:
                        for data, kwargs_ in self.offCurves:
                            self.pen.addPoint(*data, **kwargs_)
                    assert segmentType != "move"
                    self.pen.addPoint(
                        pt, segmentType, smooth, name, identifier, **kwargs)
                self.offCurves = []
            else:
                self.onCurveDropped = True
                if not self.shouldBeginPath:
                    self.pen.endPath()
                    self.shouldBeginPath = True
            self.atContourStart = False
        else:
            if not self.shouldBeginPath:
                self.offCurves.append(
                    ((pt, segmentType, smooth, name, identifier), kwargs))

    def addComponent(self, *_):
        pass


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
            self.lines.append((self._curPos[0], self._curPos[1],
                               self._initPos[0], self._initPos[1]))
        self._initPos = None

    def _endPath(self):
        self._initPos = None
