from collections import namedtuple
from defconQt.objects.defcon import TContour, TGlyph
from fontTools.pens.basePen import BasePen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.qtPen import QtPen
import math
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from robofab.pens.pointPen import AbstractPointPen

# -------------
# no components
# -------------


def NoComponentsQPainterPathFactory(glyph):
    pen = NoComponentsQtPen(glyph.layer)
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
    pen = OnlyComponentsQtPen(glyph.layer)
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

# ---------------
# selection glyph
# ---------------


def FilterSelectionFactory(glyph):
    # TODO: somehow make this all a pen?
    # I'm wary of doing it because it warrants reordering and so on
    copyGlyph = TGlyph()
    pen = copyGlyph.getPointPen()
    for anchor in glyph.anchors:
        if anchor.selected:
            anchorDict = dict(
                x=anchor.x,
                y=anchor.y,
                name=anchor.name,
                color=anchor.color,
                identifier=anchor.identifier,
            )
            copyGlyph.appendAnchor(anchorDict)
    for contour in glyph:
        onCurvesSelected = True
        for point in contour:
            if point.segmentType and not point.selected:
                onCurvesSelected = False
                break
        # TODO: should we care about offCurves not selected?
        if onCurvesSelected:
            contour.drawPoints(pen)
        else:
            workContour = TContour()
            workContour._points = contour._points
            lastSubcontour = None
            segments = workContour.segments
            # put start point at the beginning of a subcontour
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
            pen.beginPath()
            shouldMoveTo = False
            for index, segment in enumerate(segments):
                on = segment[-1]
                if not on.selected:
                    if not shouldMoveTo:
                        pen.endPath()
                        shouldMoveTo = True
                    continue
                if shouldMoveTo or not index:
                    if shouldMoveTo:
                        pen.beginPath()
                        shouldMoveTo = False
                    pen.addPoint(
                        (on.x, on.y), segmentType="move", smooth=on.smooth,
                        name=on.name)
                    continue
                for point in segment:
                    pen.addPoint(
                        (point.x, point.y), segmentType=point.segmentType,
                        smooth=point.smooth, name=point.name)
            if not shouldMoveTo:
                pen.endPath()
    for component in glyph.components:
        if component.selected:
            component.drawPoints(pen)
    return copyGlyph


def FilterSelectionQPainterPathFactory(glyph):
    copyGlyph = glyph.getRepresentation("defconQt.FilterSelection")
    path = copyGlyph.getRepresentation("defconQt.NoComponentsQPainterPath")
    for anchor in glyph.anchors:
        if anchor.selected:
            pass  # XXX
            """
            aPath = anchor.getRepresentation("defconQt.QPainterPath")
            path.addPath(aPath)
            """
    for component in glyph.components:
        if component.selected:
            cPath = component.getRepresentation("defconQt.QPainterPath")
            path.addPath(cPath)
    return path

# --------------
# component path
# --------------


def ComponentQPainterPathFactory(component):
    font = component.font
    try:
        baseGlyph = font[component.baseGlyph]
    except KeyError:
        return
    pen = QtPen({})
    tPen = TransformPen(pen, component.transformation)
    baseGlyph.draw(tPen)
    # XXX: why do we need to call that manually?
    pen.closePath()
    return pen.path

# --------------------
# curve path and lines
# --------------------


def SplitLinesQPainterPathFactory(glyph):
    pen = SplitLinesFromPathQtPen(glyph.layer)
    glyph.draw(pen)
    pen.path.setFillRule(Qt.WindingFill)
    return (pen.path, pen.lines)


class SplitLinesFromPathQtPen(QtPen):
    def __init__(self, glyphSet, path=None):
        super().__init__(glyphSet, path)
        self.lines = []
        self._curPos = (0, 0)
        self._initPos = None

    def _moveTo(self, p):
        super()._moveTo(p)
        self._curPos = (p[0], p[1])
        if self._initPos is None:
            self._initPos = self._curPos

    def _lineTo(self, p):
        self.lines.append((self._curPos[0], self._curPos[1], p[0], p[1]))
        self._moveTo(p)

    def _curveToOne(self, p1, p2, p3):
        super()._curveToOne(p1, p2, p3)
        self._curPos = (p3[0], p3[1])
        if self._initPos is None:
            self._initPos = self._curPos

    def _closePath(self):
        if self._initPos is not None and self._curPos != self._initPos:
            self.lines.append((self._curPos[0], self._curPos[1],
                               self._initPos[0], self._initPos[1]))
        self._initPos = None

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
        self._rawComponentData = []
        self._bezierHandleData = []

    def getData(self):
        data = dict(startPoints=[], onCurvePoints=[], offCurvePoints=[],
                    bezierHandles=[], anchors=[],
                    components=self._rawComponentData)
        for contour in self._rawPointData:
            # anchor
            if len(contour) == 1 and contour[0]["name"] is not None:
                anchor = contour[0]
                data["anchors"].append(anchor)
            # points
            else:
                haveFirst = False
                for pointIndex, point in enumerate(contour):
                    if point["segmentType"] is None:
                        data["offCurvePoints"].append(point)
                        # look for handles
                        back = contour[pointIndex - 1]
                        forward = contour[(pointIndex + 1) % len(contour)]
                        if back["segmentType"] is not None:
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
                        data["onCurvePoints"].append(point)
                        # catch first point
                        if not haveFirst:
                            haveFirst = True
                            nextOn = None
                            for nextPoint in contour[pointIndex:] + \
                                    contour[:pointIndex]:
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
                                angle = round(math.atan2(
                                    yDiff, xDiff) * 180 / math.pi, 3)
                            data["startPoints"].append((point["point"], angle))
        return data

    def beginPath(self):
        self._rawPointData.append([])

    def endPath(self):
        pass

    def addPoint(self, pt, segmentType=None, smooth=False, name=None,
                 selected=False, **kwargs):
        d = dict(point=pt, segmentType=segmentType, smooth=smooth, name=name,
                 selected=selected)
        self._rawPointData[-1].append(d)

    def addComponent(self, baseGlyphName, transformation):
        self._rawComponentData.append((baseGlyphName, transformation))


def OutlineInformationFactory(glyph):
    pen = OutlineInformationPen()
    glyph.drawPoints(pen)
    return pen.getData()


class OutlineInformationPen_(AbstractPointPen):

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


def OutlineInformationFactory_(glyph):
    pen = OutlineInformationPen_()
    glyph.drawPoints(pen)
    return pen.getData()

# -----
# image
# -----


def QPixmapFactory(image):
    font = image.font
    if font is None:
        return
    layer = image.layer
    images = font.images
    if image.fileName not in images:
        return None
    imageColor = image.color
    if imageColor is None:
        imageColor = layer.color
    data = images[image.fileName]
    data = QPixmap.loadFromData(data, len(data))
    if imageColor is None:
        return data
    # XXX: color filter left unimplemented
    return data
    """
    # make the input image
    inputImage = CIImage.imageWithData_(data)
    # make a color filter
    r, g, b, a = imageColor
    color0 = CIColor.colorWithRed_green_blue_(r, g, b)
    color1 = CIColor.colorWithRed_green_blue_(1, 1, 1)
    falseColorFilter = CIFilter.filterWithName_("CIFalseColor")
    falseColorFilter.setValue_forKey_(inputImage, "inputImage")
    falseColorFilter.setValue_forKey_(color0, "inputColor0")
    falseColorFilter.setValue_forKey_(color1, "inputColor1")
    # get the result
    ciImage = falseColorFilter.valueForKey_("outputImage")
    # make an NSImage
    nsImage = NSImage.alloc().initWithSize_(ciImage.extent().size)
    nsImage.lockFocus()
    context = NSGraphicsContext.currentContext().CIContext()
    context.drawImage_atPoint_fromRect_(ciImage, (0, 0), ciImage.extent())
    nsImage.unlockFocus()
    # apply the alpha
    finalImage = NSImage.alloc().initWithSize_(nsImage.size())
    finalImage.lockFocus()
    nsImage.drawAtPoint_fromRect_operation_fraction_(
        (0, 0), ((0, 0), nsImage.size()), NSCompositeSourceOver, a
    )
    finalImage.unlockFocus()
    return finalImage
    """
