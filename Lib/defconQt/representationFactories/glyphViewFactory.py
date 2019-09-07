"""
The *glyphViewFactory* submodule
-----------------------------

The *glyphViewFactory* submodule, as the name suggests, provides suitable
representations for the rendering of a Glyph_’s elements (points, Bézier
handles, components etc.).

.. _Glyph: http://ts-defcon.readthedocs.org/en/ufo3/objects/glyph.html
"""

import math

from fontTools.pens.basePen import BasePen
from fontTools.pens.qtPen import QtPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ufoLib.pointPen import AbstractPointPen
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QGraphicsColorizeEffect

from defconQt.tools.drawing import applyEffectToPixmap, colorToQColor

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
        super().__init__(glyphSet)
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


# ----------
# point data
# ----------


def OutlineInformationFactory(glyph):
    pen = OutlineInformationPen()
    glyph.drawPoints(pen)
    return pen.getData()


class OutlineInformationPen(AbstractPointPen):
    def __init__(self):
        self._rawPointData = []
        self._rawComponentData = []
        self._bezierHandleData = []

    def getData(self):
        data = dict(
            onCurvePoints=[],
            offCurvePoints=[],
            bezierHandles=[],
            anchors=[],
            components=self._rawComponentData,
        )
        for contour in self._rawPointData:
            # anchor
            # TODO: UFO3 doesn't do this?
            if len(contour) == 1 and contour[0]["name"] is not None:
                anchor = contour[0]
                data["anchors"].append(anchor)
            # points
            else:
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
                                data["bezierHandles"].append(p1 + p2)
                            # only allow two handles a point for qcurve
                            if forward["segmentType"] != "qcurve":
                                continue
                        if forward["segmentType"] is not None:
                            p1 = forward["point"]
                            p2 = point["point"]
                            if p1 != p2:
                                data["bezierHandles"].append(p1 + p2)
                    else:
                        # catch first point
                        if not pointIndex or point["smooth"]:
                            nextOn = None
                            for nextPoint in (
                                contour[pointIndex:] + contour[:pointIndex]
                            ):
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
                                angle = math.atan2(yDiff, xDiff)
                            # store
                            if not pointIndex:
                                point["startPointAngle"] = angle
                            if point["smooth"]:
                                # no point storing None angle here
                                if angle is not None:
                                    angle -= 0.5 * math.pi
                                    point["smoothAngle"] = angle
                        data["onCurvePoints"].append(point)
        return data

    def beginPath(self):
        self._rawPointData.append([])

    def endPath(self):
        pass

    def addPoint(self, pt, segmentType=None, smooth=False, name=None, **kwargs):
        d = dict(point=pt, segmentType=segmentType, smooth=smooth, name=name, **kwargs)
        self._rawPointData[-1].append(d)

    def addComponent(self, baseGlyphName, transformation):
        self._rawComponentData.append((baseGlyphName, transformation))


# -----
# image
# -----


def QPixmapFactory(image):
    font = image.font
    if font is None:
        return None
    _ = image.layer
    images = font.images
    if image.fileName not in images:
        return None
    imageColor = image.color
    data = images[image.fileName]
    pixmap = QPixmap()
    pixmap.loadFromData(data)
    if imageColor is not None:
        colorEffect = QGraphicsColorizeEffect()
        colorEffect.setColor(colorToQColor(imageColor))
        colorEffect.setStrength(0.8)
        return applyEffectToPixmap(pixmap, colorEffect)
    return pixmap
