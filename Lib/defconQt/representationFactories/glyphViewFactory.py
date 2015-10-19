from collections import namedtuple
import math
from fontTools.pens.basePen import BasePen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.qtPen import QtPen
from PyQt5.QtCore import Qt
from robofab.pens.pointPen import AbstractPointPen


# -------------
# no components
# -------------

def NoComponentsQPainterPathFactory(glyph):
    # No need for a glyphSet, because the glyphSet argument is only needed
    #  to draw the components.
    pen = NoComponentsQtPen({})
    glyph.draw(pen)
    pen.path.setFillRule(Qt.WindingFill)
    return pen.path


class NoComponentsQtPen(QtPen):

    def addComponent(self, glyphName, transformation):
        pass


# ---------------
# only components
# ---------------

def OnlyComponentsQPainterPathFactory(glyph):
    pen = OnlyComponentsQtPen(glyph.getParent())
    glyph.draw(pen)
    pen.path.setFillRule(Qt.WindingFill)
    return pen.path


class OnlyComponentsQtPen(BasePen):

    def __init__(self, glyphSet):
        BasePen.__init__(self, glyphSet)
        self.pen = QtPen(glyphSet)
        self.path = self.pen.path

    def _moveTo(self, p):
        pass

    def _lineTo(self, p):
        pass

    def _curveToOne(self, p1, p2, p3):
        pass

    def addComponent(self, glyphName, transformation):
        try:
            glyph = self.glyphSet[glyphName]
        except KeyError:
            return
        else:
            tPen = TransformPen(self.pen, transformation)
            glyph.draw(tPen)

# ------------
# start points
# ------------


def StartPointsInformationFactory(glyph):
    pen = StartPointsInformationPen()
    glyph.drawPoints(pen)
    return pen.getData()


class StartPointsInformationPen(AbstractPointPen):

    def __init__(self):
        self._rawPointData = []

    def getData(self):
        data = []
        for contour in self._rawPointData:
            # TODO: UFO3 special-case anchors so presumably we don't need to do
            # this anymore
            # anchor
            if len(contour) == 1 and contour[0]["name"] is not None:
                pass
            # points
            else:
                haveFirst = False
                for pointIndex, point in enumerate(contour):
                    if not haveFirst:
                        haveFirst = True
                        nextOn = None
                        for nextPoint in contour[pointIndex:] + \
                                contour[:pointIndex]:
                            # if nextPoint["segmentType"] is None:
                            #    continue
                            if nextPoint["point"] == point["point"]:
                                continue
                            nextOn = nextPoint
                            break
                        angle = None
                        if nextOn:
                            x1, y1 = point["point"]
                            x2, y2 = nextOn["point"]
                            xDiff = x2 - x1
                            yDiff = y2 - y1
                            angle = round(math.atan2(yDiff, xDiff)
                                          * 180 / math.pi, 3)
                        data.append((point["point"], angle))
        return data

    def beginPath(self):
        self._rawPointData.append([])

    def endPath(self):
        pass

    def addPoint(self, pt, segmentType=None, smooth=False, name=None,
                 **kwargs):
        d = dict(point=pt, segmentType=segmentType, smooth=smooth, name=name)
        self._rawPointData[-1].append(d)

    def addComponent(self, baseGlyphName, transformation):
        pass

# ----------
# point data
# ----------


class OutlineInformationPen(AbstractPointPen):

    def __init__(self):
        self._rawPointData = []
        self.cIndex = 0
        self.index = 0

    def getData(self):
        data = []
        CPoint = namedtuple('Point', [
            'x', 'y', 'contourIndex', 'pointIndex', 'isSmooth', 'isFirst',
            'prevCP', 'nextCP'])

        for contour in self._rawPointData:
            # anchor
            if len(contour) == 1 and contour[0]["name"] is not None:
                pass
            # points
            else:
                haveFirst = False
                for pointIndex, point in enumerate(contour):
                    back = contour[pointIndex - 1]
                    forward = contour[(pointIndex + 1) % len(contour)]
                    if point["segmentType"] is not None:
                        prevCP, nextCP = None, None
                        if back["segmentType"] is None:
                            # if we have an open contour with a trailing
                            # offCurve, don't signal it to the first point
                            if not (not haveFirst and
                                    contour[pointIndex - 2]["segmentType"] is
                                    not None):
                                prevCP = back["point"]
                        if forward["segmentType"] is None:
                            nextCP = forward["point"]
                        x, y = point["point"]
                        pt = CPoint(x, y, self.cIndex, self.index, point[
                                    "smooth"], not haveFirst, prevCP, nextCP)
                        data.append(pt)
                        # catch first point
                        if not haveFirst:
                            haveFirst = True
                        self.index += 1
                    else:
                        self.index += 1
            self.index = 0
            self.cIndex += 1
        return data

    def beginPath(self):
        self._rawPointData.append([])

    def endPath(self):
        pass

    def addPoint(self, pt, segmentType=None, smooth=False, name=None,
                 **kwargs):
        d = dict(point=pt, segmentType=segmentType, smooth=smooth, name=name)
        self._rawPointData[-1].append(d)

    def addComponent(self, baseGlyphName, transformation):
        pass


def OutlineInformationFactory(glyph):
    pen = OutlineInformationPen()
    glyph.drawPoints(pen)
    return pen.getData()
