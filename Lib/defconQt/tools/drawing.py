"""
The *drawing* submodule
--------------------------------

The *drawing* submodule provides common drawing functions for glyph views.
It was adapted from defconAppKit and has similar APIs.

Notes:

- All drawing is done in font units
- The *scale* argument is the factor to scale a glyph unit to a view unit

"""

import math

from defcon import Color
from fontTools.misc.transform import Identity
from fontTools.pens.qtPen import QtPen
from fontTools.pens.transformPen import TransformPen
from PyQt5.QtCore import QLineF, QPointF, Qt
from PyQt5.QtGui import (
    QBrush,
    QColor,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QTransform,
)
from PyQt5.QtWidgets import QApplication, QGraphicsPixmapItem, QGraphicsScene

# ------
# Colors
# ------

_defaultColors = dict(
    # General
    # -------
    background=QColor(Qt.white),
    # Font
    # ----
    # vertical metrics
    fontVerticalMetrics=QColor(204, 206, 200),
    fontPostscriptBlues=QColor(236, 209, 215, 100),
    fontPostscriptFamilyBlues=QColor.fromRgbF(1, 1, 0.5, 0.3),  # TODO: change that
    # guidelines
    fontGuideline=QColor.fromRgbF(1, 0, 0, 0.5),
    # Glyph
    # -----
    # contour fill
    glyphContourFill=QColor.fromRgbF(0.95, 0.95, 0.95, 0.3),
    # contour stroke
    glyphContourStroke=QColor(34, 34, 34),
    # component fill
    glyphComponentFill=QColor(90, 90, 90, 135),
    # component stroke
    glyphComponentStroke=QColor.fromRgbF(0, 0, 0, 1),
    # points
    glyphOnCurvePoints=QColor(4, 100, 166, 190),
    glyphOnCurveSmoothPoints=QColor(41, 172, 118, 190),
    glyphOffCurvePoints=QColor(116, 116, 116),
    glyphOtherPoints=QColor(140, 140, 140, 240),
    # anchors
    glyphAnchor=QColor(178, 102, 76, 200),
    # guidelines
    glyphGuideline=QColor.fromRgbF(0.3, 0.4, 0.85, 0.5),
    # marker
    glyphBluesMarker=QColor(235, 191, 202, 225),
)


def applyEffectToPixmap(pixmap, effect):
    scene = QGraphicsScene()
    item = QGraphicsPixmapItem()
    item.setPixmap(pixmap)
    item.setGraphicsEffect(effect)
    scene.addItem(item)
    res = QPixmap(pixmap.size())
    res.fill(Qt.transparent)
    painter = QPainter(res)
    scene.render(painter)
    return res


def colorToQColor(color):
    """
    Returns the QColor_ that corresponds to the defcon Color_ *color*.

    TODO: Color lacks online documentation.

    .. _Color: https://github.com/typesupply/defcon/blob/ufo3/Lib/defcon/objects/color.py
    .. _QColor: http://doc.qt.io/qt-5/qcolor.html
    """
    r, g, b, a = Color(color)
    return QColor.fromRgbF(r, g, b, a)


def defaultColor(name):
    """
    Returns a fallback QColor_ for a given *name*.

    TODO: name list?

    .. _QColor: http://doc.qt.io/qt-5/qcolor.html
    """
    return _defaultColors[name]


def ellipsePath(x, y, size):
    halfSize = size / 2
    path = QPainterPath()
    path.addEllipse(x - halfSize, y - halfSize, size, size)
    return path


def lozengePath(x, y, size):
    halfSize = size / 2
    path = QPainterPath()
    path.moveTo(x - halfSize, y)
    path.lineTo(x, y + halfSize)
    path.lineTo(x + halfSize, y)
    path.lineTo(x, y - halfSize)
    path.closeSubpath()
    return path


def rectanglePath(x, y, size):
    halfSize = size / 2
    path = QPainterPath()
    path.addRect(x - halfSize, y - halfSize, size, size)
    return path


def trianglePath(x, y, size, angle):
    thirdSize = size / 3
    pen = QtPen({})
    tPen = TransformPen(pen, Identity.rotate(angle))
    tPen.moveTo((-thirdSize, size))
    tPen.lineTo((-thirdSize, -size))
    tPen.lineTo((2 * thirdSize, 0))
    tPen.closePath()
    return pen.path.translated(x, y)


# ----------
# Primitives
# ----------


def drawLine(painter, x1, y1, x2, y2, lineWidth=0):
    """
    Draws a line from *(x1, y1)* to *(x2, y2)* with a thickness of *lineWidth*
    and using QPainter_ *painter*.

    Compared to the built-in ``painter.drawLine(…)`` method, this will disable
    antialiasing for horizontal/vertical lines.

    .. _`cosmetic pen`: http://doc.qt.io/qt-5/qpen.html#isCosmetic
    .. _QPainter: http://doc.qt.io/qt-5/qpainter.html
    """
    painter.save()
    if x1 == x2 or y1 == y2:
        painter.setRenderHint(QPainter.Antialiasing, False)
    pen = painter.pen()
    pen.setWidthF(lineWidth)
    painter.setPen(pen)
    painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
    painter.restore()


def drawTextAtPoint(
    painter, text, x, y, scale, xAlign="left", yAlign="bottom", flipped=True
):
    """
    Draws *text* at *(x, y)* with scale *scale* and a given QPainter_.

    - *xAlign* may be "left", "center" or "right" and specifies the alignment
      of the text (left-aligned text is painted to the right of *x*)
    - *yAlign* may be "top", "center" or "bottom" and specifies the y-positing
      of the text block relative to *y*

    TODO: support LTR http://stackoverflow.com/a/24831796/2037879

    .. _QPainter: http://doc.qt.io/qt-5/qpainter.html
    """
    fM = painter.fontMetrics()
    lines = text.splitlines()
    lineSpacing = fM.lineSpacing()
    if xAlign != "left" or yAlign != "bottom":
        width = scale * max(fM.width(line) for line in lines)
        height = scale * len(lines) * lineSpacing
        if xAlign == "center":
            x -= width / 2
        elif xAlign == "right":
            x -= width
        if yAlign == "center":
            y += height / 2
        elif yAlign == "top":
            y += height
    painter.save()
    if flipped:
        s = -scale
        height = fM.ascent() * scale
        y -= height
    else:
        s = scale
    painter.translate(x, y)
    painter.scale(scale, s)
    for line in lines:
        painter.drawText(0, 0, line)
        painter.translate(0, lineSpacing)
    painter.restore()


def drawTiles(painter, rect, tileSize=6, color=None, backgroundColor=None):
    sz = 2 * tileSize
    tiledPixmap = QPixmap(sz, sz)
    pixmapPainter = QPainter(tiledPixmap)
    pixmapPainter.setPen(Qt.NoPen)
    pixmapPainter.setBrush(Qt.Dense4Pattern)
    brush = pixmapPainter.brush()
    brush.setColor(color)
    pixmapPainter.setBrush(brush)
    pixmapPainter.setBackground(QBrush(backgroundColor))
    pixmapPainter.setBackgroundMode(Qt.OpaqueMode)
    pixmapPainter.scale(tileSize, tileSize)
    pixmapPainter.drawRect(tiledPixmap.rect())
    pixmapPainter.end()
    painter.drawTiledPixmap(rect, tiledPixmap)


# ----
# Font
# ----

# Guidelines


def drawFontGuidelines(
    painter, glyph, scale, rect, drawLines=True, drawText=True, color=None
):
    """
    Draws the font guidelines of the Glyph_ *glyph* in the form of lines if
    *drawLines* is true and text if *drawText* is true using QPainter_
    *painter*.

    *rect* specifies the rectangle which the lines will be drawn in (usually,
    that of the glyph’s advance width).

    .. _Glyph: http://ts-defcon.readthedocs.org/en/ufo3/objects/glyph.html
    .. _QPainter: http://doc.qt.io/qt-5/qpainter.html
    """
    if not (drawLines or drawText):
        return
    font = glyph.font
    if font is None:
        return
    if color is None:
        color = defaultColor("fontGuideline")
    _drawGuidelines(
        painter,
        glyph,
        scale,
        rect,
        font.guidelines,
        drawLines=drawLines,
        drawText=drawText,
        color=color,
    )


def drawGlyphGuidelines(
    painter, glyph, scale, rect, drawLines=True, drawText=True, color=None
):
    if not (drawLines or drawText):
        return
    if color is None:
        color = defaultColor("glyphGuideline")
    _drawGuidelines(
        painter,
        glyph,
        scale,
        rect,
        glyph.guidelines,
        drawLines=drawLines,
        drawText=drawText,
        color=color,
    )


def _drawGuidelines(
    painter, glyph, scale, rect, guidelines, drawLines=True, drawText=True, color=None
):
    if not (drawLines or drawText):
        return
    xMin, yMin, width, height = rect
    xMax = xMin + width
    yMax = yMin + height
    for line in guidelines:
        color_ = color
        if color_ is None:
            if line.color:
                color_ = colorToQColor(line.color)
            else:
                color_ = defaultColor("glyphGuideline")
        painter.save()
        painter.setPen(color)
        line1 = None
        if None not in (line.x, line.y):
            if line.angle is not None:
                # make an infinite line that intersects *(line.x, line.y)*
                # 1. make horizontal line from *(line.x, line.y)* of length *diagonal*
                diagonal = math.sqrt(width ** 2 + height ** 2)
                line1 = QLineF(line.x, line.y, line.x + diagonal, line.y)
                # 2. set the angle
                # defcon guidelines are clockwise
                line1.setAngle(line.angle)
                # 3. reverse the line and set length to 2 * *diagonal*
                line1.setPoints(line1.p2(), line1.p1())
                line1.setLength(2 * diagonal)
            else:
                line1 = QLineF(xMin, line.y, xMax, line.y)
        textX = 0
        textY = 0
        if drawLines:
            if line1 is not None:
                # line
                drawLine(painter, line1.x1(), line1.y1(), line1.x2(), line1.y2())
                # point
                x, y = line.x, line.y
                smoothWidth = 8 * scale
                smoothHalf = smoothWidth / 2.0
                painter.save()
                pointPath = QPainterPath()
                x -= smoothHalf
                y -= smoothHalf
                pointPath.addEllipse(x, y, smoothWidth, smoothWidth)
                pen = QPen(color_)
                pen.setWidthF(1 * scale)
                painter.setPen(pen)
                painter.drawPath(pointPath)
                painter.restore()
            else:
                if line.y is not None:
                    drawLine(painter, xMin, line.y, xMax, line.y)
                elif line.x is not None:
                    drawLine(painter, line.x, yMin, line.x, yMax)
        if drawText and line.name:
            if line1 is not None:
                textX = line.x
                textY = line.y - 6 * scale
                xAlign = "center"
            else:
                if line.y is not None:
                    fontSize = painter.font().pointSize()
                    textX = glyph.width + 6 * scale
                    textY = line.y - (fontSize / 3.5) * scale
                elif line.x is not None:
                    textX = line.x + 6 * scale
                    textY = 0
                xAlign = "left"
            drawTextAtPoint(painter, line.name, textX, textY, scale, xAlign=xAlign)
        painter.restore()


# Blues


def drawFontPostscriptBlues(painter, glyph, scale, color=None):
    """
    Draws a Glyph_ *glyph*’s blue values.

    .. _Glyph: http://ts-defcon.readthedocs.org/en/ufo3/objects/glyph.html
    """
    font = glyph.font
    if font is None:
        return
    blues = []
    if font.info.postscriptBlueValues:
        blues += font.info.postscriptBlueValues
    if font.info.postscriptOtherBlues:
        blues += font.info.postscriptOtherBlues
    if not blues:
        return
    if color is None:
        color = defaultColor("fontPostscriptBlues")
    _drawBlues(painter, glyph, blues, color)


def drawFontPostscriptFamilyBlues(painter, glyph, scale, color=None):
    """
    Draws a Glyph_ *glyph*’s family blue values.

    .. _Glyph: http://ts-defcon.readthedocs.org/en/ufo3/objects/glyph.html
    """
    font = glyph.font
    if font is None:
        return
    blues = []
    if font.info.postscriptFamilyBlues:
        blues += font.info.postscriptFamilyBlues
    if font.info.postscriptFamilyOtherBlues:
        blues += font.info.postscriptFamilyOtherBlues
    if not blues:
        return
    if color is None:
        color = defaultColor("fontPostscriptFamilyBlues")
    _drawBlues(painter, glyph, blues, color)


def _drawBlues(painter, glyph, blues, color):
    for yMin, yMax in zip(blues[::2], blues[1::2]):
        painter.fillRect(0, yMin, glyph.width, yMax - yMin, color)


# Image


def drawGlyphImage(painter, glyph, scale):
    """
    Draws a Glyph_ *glyph*’s image.

    .. _Glyph: http://ts-defcon.readthedocs.org/en/ufo3/objects/glyph.html
    """
    image = glyph.image
    pixmap = image.getRepresentation("defconQt.QPixmap")
    if pixmap is None:
        return
    painter.save()
    painter.setTransform(QTransform(*image.transformation), True)
    painter.translate(0, pixmap.height())
    painter.scale(1, -1)
    painter.drawPixmap(0, 0, pixmap)
    painter.restore()


# Metrics


def drawGlyphMetrics(
    painter,
    glyph,
    scale,
    drawHMetrics=True,
    drawVMetrics=True,
    drawText=False,
    color=None,
    textColor=None,
):
    """
    TODO: doc comment needs update

    Draws vertical metrics of the Glyph_ *glyph* (ascender, descender,
    baseline, x-height, cap height) in the form of lines if *drawLines* is true
    and text if *drawText* is true using QPainter_ *painter*.

    .. _Glyph: http://ts-defcon.readthedocs.org/en/ufo3/objects/glyph.html
    .. _QPainter: http://doc.qt.io/qt-5/qpainter.html
    """
    font = glyph.font
    if font is None:
        return
    if color is None:
        color = defaultColor("fontVerticalMetrics")
    if textColor is None:
        textColor = defaultColor("glyphOtherPoints")
    painter.save()
    pen = QPen(color)
    pen.setWidth(0)
    painter.setPen(pen)
    painter.setRenderHint(QPainter.Antialiasing, False)
    # metrics
    metrics = [
        font.info.descender or -250,
        0,
        font.info.xHeight,
        font.info.capHeight,
        font.info.ascender or 750,
    ]
    if drawHMetrics:
        lo = metrics[0]
        hi = max(y for y in metrics[-2:] if y is not None)
        painter.drawLine(0, lo, 0, hi)
        painter.drawLine(glyph.width, lo, glyph.width, hi)
    if drawVMetrics:
        for y in metrics:
            if y is None:
                continue
            painter.drawLine(0, y, glyph.width, y)
    painter.restore()
    # metrics text
    if drawText:
        toDraw = [
            (QApplication.translate("drawing", "Descender"), font.info.descender),
            (QApplication.translate("drawing", "Baseline"), 0),
            (QApplication.translate("drawing", "x-height"), font.info.xHeight),
            (QApplication.translate("drawing", "Cap height"), font.info.capHeight),
            (QApplication.translate("drawing", "Ascender"), font.info.ascender),
        ]
        # gather y positions
        positions = {}
        for name, position in toDraw:
            if position is None:
                continue
            if position not in positions:
                positions[position] = []
            positions[position].append(name)
        # create lines
        lines = []
        for y, names in positions.items():
            names = ", ".join(names)
            if y != 0:
                names = "%s (%d)" % (names, y)
            lines.append((y, names))
        painter.save()
        painter.setPen(textColor)
        fontSize = painter.font().pointSize()
        x = glyph.width + 6 * scale
        for y, text in lines:
            y -= (fontSize / 3.5) * scale
            drawTextAtPoint(painter, text, x, y, scale)
        painter.restore()


# Fill and Stroke


def drawGlyphFillAndStroke(
    painter,
    glyph,
    scale,
    drawFill=True,
    drawStroke=True,
    drawComponentFill=True,
    drawComponentStroke=False,
    contourFillColor=None,
    contourStrokeColor=None,
    componentFillColor=None,
    componentStrokeColor=None,
):
    """
    Draws a Glyph_ *glyph* contours’ fill and stroke.

    Component fill is always drawn, component stroke is drawn if
    *componentStrokeColor* is not None.

    .. _Glyph: http://ts-defcon.readthedocs.org/en/ufo3/objects/glyph.html
    """
    # get the layer color
    layer = glyph.layer
    layerColor = None
    if layer is not None and layer.color is not None:
        layerColor = colorToQColor(layer.color)
    # get the paths
    contourPath = glyph.getRepresentation("defconQt.NoComponentsQPainterPath")
    componentPath = glyph.getRepresentation("defconQt.OnlyComponentsQPainterPath")
    painter.save()
    # fill
    # contours
    if drawFill:
        if contourFillColor is None:
            if layerColor is not None:
                contourFillColor = layerColor
            else:
                contourFillColor = defaultColor("glyphContourFill")
        painter.fillPath(contourPath, QBrush(contourFillColor))
    # components
    if drawComponentFill:
        if componentFillColor is None:
            if layerColor is not None:
                componentFillColor = layerColor
            else:
                componentFillColor = defaultColor("glyphComponentFill")
        painter.fillPath(componentPath, QBrush(componentFillColor))
    # stroke
    if drawStroke:
        if contourStrokeColor is None:
            if layerColor is not None:
                contourStrokeColor = layerColor
            else:
                contourStrokeColor = defaultColor("glyphContourStroke")
        pen = QPen(contourStrokeColor)
        pen.setWidth(0)
        painter.setPen(pen)
        painter.drawPath(contourPath)
    # components
    if drawComponentStroke:
        if componentStrokeColor is None:
            if layerColor is not None:
                componentStrokeColor = layerColor
            else:
                componentStrokeColor = defaultColor("glyphContourStroke")
        pen = QPen(componentStrokeColor)
        pen.setWidth(0)
        painter.setPen(pen)
        painter.drawPath(componentPath)
    painter.restore()


# points


def drawGlyphPoints(
    painter,
    glyph,
    scale,
    drawStartPoints=True,
    drawOnCurves=True,
    drawOffCurves=True,
    drawCoordinates=False,
    drawBluesMarkers=True,
    onCurveColor=None,
    onCurveSmoothColor=None,
    offCurveColor=None,
    otherColor=None,
    backgroundColor=None,
):
    """
    Draws a Glyph_ *glyph*’s points.

    .. _Glyph: http://ts-defcon.readthedocs.org/en/ufo3/objects/glyph.html
    """
    if onCurveColor is None:
        onCurveColor = defaultColor("glyphOnCurvePoints")
    if onCurveSmoothColor is None:
        onCurveSmoothColor = defaultColor("glyphOnCurveSmoothPoints")
    if offCurveColor is None:
        offCurveColor = defaultColor("glyphOffCurvePoints")
    if otherColor is None:
        otherColor = defaultColor("glyphOtherPoints")
    if backgroundColor is None:
        backgroundColor = defaultColor("background")
    bluesMarkerColor = defaultColor("glyphBluesMarker")
    notchColor = defaultColor("glyphContourStroke").lighter(200)
    # get the outline data
    outlineData = glyph.getRepresentation("defconQt.OutlineInformation")
    points = []
    # blue zones markers
    if drawBluesMarkers and drawOnCurves:
        font = glyph.font
        blues = []
        if font.info.postscriptBlueValues:
            blues += font.info.postscriptBlueValues
        if font.info.postscriptOtherBlues:
            blues += font.info.postscriptOtherBlues
        if blues:
            blues_ = set(blues)
            size = 13 * scale
            snapSize = 17 * scale
            painter.save()
            pen = painter.pen()
            pen.setColor(QColor(255, 255, 255, 125))
            pen.setWidth(0)
            painter.setPen(pen)
            for point in outlineData["onCurvePoints"]:
                x, y = point["point"]
                # TODO: we could add a non-overlapping interval tree special
                # cased for borders
                for yMin, yMax in zip(blues[::2], blues[1::2]):
                    if not (y >= yMin and y <= yMax):
                        continue
                    # if yMin > 0 and y == yMin or yMin <= 0 and y == yMax:
                    if y in blues_:
                        path = lozengePath(x, y, snapSize)
                    else:
                        path = ellipsePath(x, y, size)
                    painter.fillPath(path, bluesMarkerColor)
                    painter.drawPath(path)
            painter.restore()
    # handles
    if drawOffCurves and outlineData["offCurvePoints"]:
        painter.save()
        painter.setPen(otherColor)
        for x1, y1, x2, y2 in outlineData["bezierHandles"]:
            drawLine(painter, x1, y1, x2, y2)
        painter.restore()
    # on curve
    if drawOnCurves and outlineData["onCurvePoints"]:
        size = 6.5 * scale
        smoothSize = 8 * scale
        startSize = 7 * scale
        loneStartSize = 12 * scale
        painter.save()
        notchPath = QPainterPath()
        path = QPainterPath()
        smoothPath = QPainterPath()
        for point in outlineData["onCurvePoints"]:
            x, y = point["point"]
            points.append((x, y))
            # notch
            if "smoothAngle" in point:
                angle = point["smoothAngle"]
                t = Identity.rotate(angle)
                x1, y1 = t.transformPoint((-1.35 * scale, 0))
                x2, y2 = -x1, -y1
                notchPath.moveTo(x1 + x, y1 + y)
                notchPath.lineTo(x2 + x, y2 + y)
            # points
            if drawStartPoints and "startPointAngle" in point:
                angle = point["startPointAngle"]
                if angle is not None:
                    pointPath = trianglePath(x, y, startSize, angle)
                else:
                    pointPath = ellipsePath(x, y, loneStartSize)
            elif point["smooth"]:
                pointPath = ellipsePath(x, y, smoothSize)
            else:
                pointPath = rectanglePath(x, y, size)
            # store the path
            if point["smooth"]:
                smoothPath.addPath(pointPath)
            else:
                path.addPath(pointPath)
        # stroke
        pen = QPen(onCurveColor)
        pen.setWidthF(1.2 * scale)
        painter.setPen(pen)
        painter.drawPath(path)
        pen.setColor(onCurveSmoothColor)
        painter.setPen(pen)
        painter.drawPath(smoothPath)
        # notch
        pen.setColor(notchColor)
        pen.setWidth(0)
        painter.setPen(pen)
        painter.drawPath(notchPath)
        painter.restore()
    # off curve
    if drawOffCurves and outlineData["offCurvePoints"]:
        # points
        offSize = 4.25 * scale
        path = QPainterPath()
        for point in outlineData["offCurvePoints"]:
            x, y = point["point"]
            pointPath = ellipsePath(x, y, offSize)
            path.addPath(pointPath)
        pen = QPen(offCurveColor)
        pen.setWidthF(2.5 * scale)
        painter.save()
        painter.setPen(pen)
        painter.drawPath(path)
        painter.fillPath(path, QBrush(backgroundColor))
        painter.restore()
    # coordinates
    if drawCoordinates:
        painter.save()
        painter.setPen(otherColor)
        font = painter.font()
        font.setPointSize(7)
        painter.setFont(font)
        for x, y in points:
            posX = x
            # TODO: We use + here because we align on top. Consider abstracting
            # yOffset.
            posY = y + 6 * scale
            x = round(x, 1)
            if int(x) == x:
                x = int(x)
            y = round(y, 1)
            if int(y) == y:
                y = int(y)
            text = "%d  %d" % (x, y)
            drawTextAtPoint(
                painter, text, posX, posY, scale, xAlign="center", yAlign="top"
            )
        painter.restore()


# Anchors


def drawGlyphAnchors(
    painter, glyph, scale, drawAnchors=True, drawText=True, color=None
):
    """
    Draws a Glyph_ *glyph*’s anchors.

    .. _Glyph: http://ts-defcon.readthedocs.org/en/ufo3/objects/glyph.html
    """
    if not glyph.anchors:
        return
    if color is None:
        color = defaultColor("glyphAnchor")
    fallbackColor = color
    anchorSize = 9 * scale
    for anchor in glyph.anchors:
        if anchor.color is not None:
            color = colorToQColor(anchor.color)
        else:
            color = fallbackColor
        x, y = anchor.x, anchor.y
        name = anchor.name
        painter.save()
        if drawAnchors:
            path = lozengePath(x, y, anchorSize)
            painter.fillPath(path, color)
        if drawText and name:
            painter.setPen(color)
            # TODO: we're using + before we shift to top, ideally this should
            # be abstracted w drawTextAtPoint taking a dy parameter that will
            # offset the drawing region from origin regardless of whether we
            # are aligning to top or bottom.
            y += 6 * scale
            drawTextAtPoint(painter, name, x, y, scale, xAlign="center", yAlign="top")
        painter.restore()
