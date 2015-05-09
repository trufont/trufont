from defcon.objects.glyph import addRepresentationFactory
#
#from defconQt.representationFactories.qPainterPathFactory import QPainterPathFactory
#
from fontTools.pens.qtPen import QtPen

def QPainterPathFactory(glyph, font):
    pen = QtPen(font)
    glyph.draw(pen)
    return pen.path

#from defconQt.representationFactories.glyphCellFactory import GlyphCellFactory

#
#from defconQt.representationFactories.glyphviewFactory import NoComponentsQPainterPathFactory, OnlyComponentsQPainterPathFactory, OutlineInformationFactory
#
import math
from fontTools.pens.basePen import BasePen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.qtPen import QtPen
from robofab.pens.pointPen import AbstractPointPen


# -------------
# no components
# -------------

def NoComponentsQPainterPathFactory(glyph, font):
    pen = NoComponentsQtPen(font)
    glyph.draw(pen)
    return pen.path

class NoComponentsQtPen(QtPen):
    def addComponent(self, glyphName, transformation):
        pass


# ---------------
# only components
# ---------------

def OnlyComponentsQPainterPathFactory(glyph, font):
    pen = OnlyComponentsQtPen(font)
    glyph.draw(pen)
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

    def _closePath(self):
        pass

    def addComponent(self, glyphName, transformation):
        try:
            glyph = self.glyphSet[glyphName]
        except KeyError:
            return
        else:
            tPen = TransformPen(self.pen, transformation)
            glyph.draw(tPen)


# ----------
# point data
# ----------

class OutlineInformationPen(AbstractPointPen):

    def __init__(self):
        self._rawPointData = []
        self._rawComponentData = []
        self._bezierHandleData = []
        self.index = 0

    def getData(self):
        data = dict(startPoints=[], onCurvePoints=[], offCurvePoints=[], bezierHandles=[], anchors=[], lastSubpathPoints=[], components=self._rawComponentData)

        for contour in self._rawPointData:
            if type(contour) is str:
                print("Hill")
                data["lastSubpathPoints"].append(self.index)
                self.index += 1
                continue
            # anchor
            if len(contour) == 1 and contour[0]["name"] is not None:
                anchor = contour[0]
                data["anchors"].append(anchor)
            # points
            else:
                haveFirst = False
                for pointIndex, point in enumerate(contour):
                    if point["segmentType"] is None:
                        print("OffCurve")
                        data["offCurvePoints"].append((point, self.index, not haveFirst))
                        self.index += 1
                        # look for handles
                        # TODO: calculate this when drawing
                        back = contour[pointIndex - 1]
                        forward = contour[(pointIndex + 1) % len(contour)]
                        if back["segmentType"] in ("curve", "line"):
                            p1 = back["point"]
                            p2 = point["point"]
                            if p1 != p2:
                                data["bezierHandles"].append((p1, p2))
                        elif forward["segmentType"] in ("curve", "line"):
                            p1 = forward["point"]
                            p2 = point["point"]
                            if p1 != p2:
                                data["bezierHandles"].append((p1, p2))
                    else:
                        data["onCurvePoints"].append((point, self.index, not haveFirst))
                        print("OnCurve")
                        self.index += 1
                        # catch first point
                        if not haveFirst:
                            haveFirst = True
                            nextOn = None
                            for nextPoint in contour[pointIndex:] + contour[:pointIndex]:
                                #if nextPoint["segmentType"] is None:
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
                                angle = round(math.atan2(yDiff, xDiff) * 180 / math.pi, 3)
                            data["startPoints"].append((point["point"], angle))
        return data

    def beginPath(self):
        self._rawPointData.append([])

    def endPath(self):
        # TODO: appending a string may not be the most elegant thing to do
        self._rawPointData.append("Subpath")

    def addPoint(self, pt, segmentType=None, smooth=False, name=None, **kwargs):
        d = dict(point=pt, segmentType=segmentType, smooth=smooth, name=name)
        self._rawPointData[-1].append(d)

    def addComponent(self, baseGlyphName, transformation):
        d = dict(baseGlyphName=baseGlyphName, transformation=transformation)
        self._rawComponentData.append((baseGlyphName, transformation))


def OutlineInformationFactory(glyph, font):
    pen = OutlineInformationPen()
    glyph.drawPoints(pen)
    return pen.getData()
#
#
#

_factories = {
    "defconQt.QPainterPath" : QPainterPathFactory,
    "defconQt.OnlyComponentsQPainterPath" : OnlyComponentsQPainterPathFactory,
    "defconQt.NoComponentsQPainterPath" : NoComponentsQPainterPathFactory,
    "defconQt.OutlineInformation" : OutlineInformationFactory,
    #"defconQt.GlyphCell" : GlyphCellFactory,
}

def registerAllFactories():
    for name, factory in _factories.items():
        addRepresentationFactory(name, factory)