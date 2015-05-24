from defcon.objects.glyph import addRepresentationFactory
#
#from defconQt.representationFactories.qPainterPathFactory import QPainterPathFactory
#
from fontTools.pens.qtPen import QtPen
from PyQt5.QtCore import Qt

def QPainterPathFactory(glyph, font):
    pen = QtPen(font)
    glyph.draw(pen)
    pen.path.setFillRule(Qt.WindingFill)
    return pen.path

#from defconQt.representationFactories.glyphCellFactory import GlyphCellFactory

#
#from defconQt.representationFactories.glyphviewFactory import NoComponentsQPainterPathFactory, OnlyComponentsQPainterPathFactory, OutlineInformationFactory
#
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

def NoComponentsQPainterPathFactory(glyph, font):
    pen = NoComponentsQtPen(font)
    glyph.draw(pen)
    pen.path.setFillRule(Qt.WindingFill)
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
        self.cIndex = 0
        self.index = 0

    def getData(self):
        data = dict(startPoints=[], onCurvePoints=[], offCurvePoints=[], bezierHandles=[], anchors=[], components=self._rawComponentData)
        CPoint = namedtuple('Point', ['x', 'y', 'contourIndex', 'pointIndex', 'isSmooth', 'isFirst', 'prevCP', 'nextCP'])
        
        for contour in self._rawPointData:
            # anchor
            if len(contour) == 1 and contour[0]["name"] is not None:
                anchor = contour[0]
                data["anchors"].append(anchor)
            # points
            else:
                haveFirst = False
                for pointIndex, point in enumerate(contour):
                    back = contour[pointIndex - 1]
                    forward = contour[(pointIndex + 1) % len(contour)]
                    if point["segmentType"] is not None:
                        prevCP, nextCP = None, None
                        if back["segmentType"] is None:
                            prevCP = back["point"]
                        if forward["segmentType"] is None:
                            nextCP = forward["point"]
                        x, y = point["point"]
                        pt = CPoint(x, y, self.cIndex, self.index, point["smooth"], not haveFirst, prevCP, nextCP)
                        data["onCurvePoints"].append(pt)
                        # catch first point
                        if not haveFirst:
                            haveFirst = True
                            '''
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
                            '''
                        self.index += 1
                    else:
                        '''
                        if back["segmentType"] is not None:
                            onCurveNeighbor = back
                        elif forward["segmentType"] is not None:
                            onCurveNeighbor = forward
                        else:
                            print("Whoops")
                            continue
                        # QPainterPath elides no-op moveTo's, so do the same when indexing here
                        if onCurveNeighbor["point"] == point["point"]:
                            print("Skipped: {}".format(self.index))
                            continue
                        '''
                        self.index += 1
                            
                        
                    '''
                    else:
                        onCurveParent = self.index+1
                        print("OffCurve")
                        # look for handles
                        # TODO: calculate this when drawing
                        back = contour[pointIndex - 1]
                        forward = contour[(pointIndex + 1) % len(contour)]
                        if back["segmentType"] in ("curve", "line"):
                            onCurveParent = self.index-1
                            p1 = back["point"]
                            p2 = point["point"]
                            if p1 != p2:
                                data["bezierHandles"].append((p1, p2, self.index, onCurveParent))
                        elif forward["segmentType"] in ("curve", "line"):
                            p1 = forward["point"]
                            p2 = point["point"]
                            if p1 != p2:
                                data["bezierHandles"].append((p1, p2, self.index, onCurveParent))
                        data["offCurvePoints"].append((point, self.index, onCurveParent))
                        self.index += 1
                    '''
            self.index = 0
            self.cIndex += 1
        return data

    def beginPath(self):
        self._rawPointData.append([])

    def endPath(self):
        pass

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