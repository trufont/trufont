from defcon import Color
from defconQt.tools.drawing import drawTextAtPoint
from PyQt5.QtCore import QLineF, QPointF, Qt
from PyQt5.QtGui import (
    QBrush, QColor, QPainter, QPainterPath, QPen, QTransform)
from PyQt5.QtWidgets import QApplication
import math

# ------
# Colors
# ------

_defaultColors = dict(

    # General
    # -------

    background=QColor(Qt.white),

    # Font
    # ----

    # guidelines
    fontGuideline=QColor.fromRgbF(1, 0, 0, .5),

    # Glyph
    # -----

    # contour fill
    glyphContourFill=QColor.fromRgbF(.85, .85, .85, .5),
    # contour stroke
    glyphContourStroke=QColor.fromRgbF(0, 0, 0, 1),
    # component fill
    glyphComponentFill=QColor.fromRgbF(0, 0, 0, .4),
    # component stroke
    glyphComponentStroke=QColor.fromRgbF(0, 0, 0, 1),
    # points
    glyphOnCurvePoints=QColor(4, 100, 166, 190),
    glyphOtherPoints=QColor.fromRgbF(.6, .6, .6, 1),
    # anchors
    glyphAnchor=QColor(228, 96, 15, 200),
    # selection
    glyphSelection=QColor(165, 190, 216, 155),
    # guidelines
    glyphGuideline=QColor.fromRgbF(.3, .4, .85, .5),
)


def colorToQColor(color):
    return QColor.fromRgbF(*Color(color))


def defaultColor(name):
    return _defaultColors[name]

# ----------
# Primitives
# ----------


def drawLine(painter, x1, y1, x2, y2, lineWidth=0):
    painter.save()
    pen = painter.pen()
    if x1 == x2 or y1 == y2:
        painter.setRenderHint(QPainter.Antialiasing, False)
        # antialiased drawing blend a little in color with the background
        # reduce alpha before drawing aliased
        color = pen.color()
        color.setAlphaF(.9 * color.alphaF())
        pen.setColor(color)
    pen.setWidthF(lineWidth)
    painter.setPen(pen)
    painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
    painter.restore()


def drawGlyphWithAliasedLines(painter, glyph):
    curvePath, lines = glyph.getRepresentation(
        "TruFont.SplitLinesQPainterPath")
    painter.drawPath(curvePath)
    painter.save()
    pen = painter.pen()
    color = pen.color()
    color.setAlphaF(.9 * color.alphaF())
    pen.setColor(color)
    painter.setPen(pen)
    for x1, y1, x2, y2 in lines:
        drawLine(painter, x1, y1, x2, y2, painter.pen().widthF())
    painter.restore()

# ----
# Font
# ----

# Guidelines


def drawFontGuidelines(painter, glyph, scale, rect, drawLines=True,
                       drawText=True, color=None):
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
    _drawGuidelines(painter, glyph, scale, rect, font.guidelines, color=color)


def drawGlyphGuidelines(painter, glyph, scale, rect, drawLines=True,
                        drawText=True, color=None):
    if not (drawLines or drawText):
        return
    if color is None:
        color = defaultColor("glyphGuideline")
    _drawGuidelines(painter, glyph, scale, rect, glyph.guidelines, color=color)


def _drawGuidelines(painter, glyph, scale, rect, guidelines, drawLines=True,
                    drawText=True, drawSelection=True, color=None):
    if not (drawLines or drawText):
        return
    xMin, yMin, width, height = rect
    xMax = xMin + width
    yMax = yMin + height
    fontSize = painter.font().pointSize()
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
                # 1. make horizontal line from *(line.x, line.y)* of length
                # *diagonal*
                diagonal = math.sqrt(width**2 + height**2)
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
                drawLine(
                    painter, line1.x1(), line1.y1(), line1.x2(), line1.y2())
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
                if drawSelection and line.selected:
                    painter.fillPath(pointPath, color_)
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
                    textX = glyph.width + 6 * scale
                    textY = line.y - (fontSize / 3.5) * scale
                elif line.x is not None:
                    textX = line.x + 6 * scale
                    textY = 0
                xAlign = "left"
            drawTextAtPoint(
                painter, line.name, textX, textY, scale, xAlign=xAlign)
        painter.restore()

# Image


def drawGlyphImage(
        painter, glyph, scale, rect, drawSelection=True, selectionColor=None):
    image = glyph.image
    pixmap = image.getRepresentation("defconQt.QPixmap")
    if pixmap is None:
        return
    if selectionColor is None:
        selectionColor = defaultColor("glyphSelection")
    painter.save()
    painter.setTransform(QTransform(*image.transformation), True)
    painter.save()
    painter.translate(0, pixmap.height())
    painter.scale(1, -1)
    painter.drawPixmap(0, 0, pixmap)
    painter.restore()
    if drawSelection and image.selected:
        pen = QPen(selectionColor)
        pen.setWidthF(3.5 * scale)
        painter.setPen(pen)
        painter.drawRect(pixmap.rect())
    painter.restore()

# Fill and Stroke


def drawGlyphFillAndStroke(
        painter, glyph, scale, rect, drawFill=True, drawStroke=True,
        drawSelection=True, contourFillColor=None, contourStrokeColor=None,
        componentFillColor=None, componentStrokeColor=None,
        strokeWidth=1.0, partialAliasing=True, selectionColor=None):
    strokeWidth /= QApplication.instance().devicePixelRatio()
    # get the layer color
    layer = glyph.layer
    layerColor = None
    if layer is not None and layer.color is not None:
        layerColor = colorToQColor(layer.color)
    if selectionColor is None:
        selectionColor = defaultColor("glyphSelection")
    # get the paths
    contourPath = glyph.getRepresentation("defconQt.NoComponentsQPainterPath")
    componentPath = glyph.getRepresentation(
        "defconQt.OnlyComponentsQPainterPath")
    selectionPath = glyph.getRepresentation(
        "TruFont.FilterSelectionQPainterPath")
    painter.save()
    # fill
    if drawFill:
        # contours
        if contourFillColor is None and layerColor is not None:
            contourFillColor = layerColor
        elif contourFillColor is None and layerColor is None:
            contourFillColor = defaultColor("glyphContourFill")
        painter.fillPath(contourPath, QBrush(contourFillColor))
    # components
    if componentFillColor is None and layerColor is not None:
        componentFillColor = layerColor
    elif componentFillColor is None and layerColor is None:
        componentFillColor = defaultColor("glyphComponentFill")
    painter.fillPath(componentPath, QBrush(componentFillColor))
    # selection
    if drawSelection:
        pen = QPen(selectionColor)
        pen.setWidthF(3.5 * scale)
        painter.setPen(pen)
        painter.drawPath(selectionPath)
    # stroke
    if drawStroke:
        # work out the color
        if contourStrokeColor is None and layerColor is not None:
            contourStrokeColor = layerColor
        elif contourStrokeColor is None and layerColor is None:
            contourStrokeColor = defaultColor("glyphContourStroke")
        # contours
        pen = QPen(contourStrokeColor)
        pen.setWidthF(strokeWidth * scale)
        painter.setPen(pen)
        if partialAliasing:
            drawGlyphWithAliasedLines(painter, glyph)
        else:
            painter.drawPath(contourPath)
    # components
    if componentStrokeColor is not None:
        pen = QPen(componentStrokeColor)
        pen.setWidthF(strokeWidth * scale)
        painter.setPen(pen)
        painter.drawPath(componentPath)
    painter.restore()

# points


def drawGlyphPoints(
        painter, glyph, scale, rect,
        drawStartPoints=True, drawOnCurves=True, drawOffCurves=True,
        drawCoordinates=False, drawSelection=True, onCurveColor=None,
        otherColor=None, backgroundColor=None):
    if onCurveColor is None:
        layer = glyph.layer
        if layer is not None and layer.color is not None:
            onCurveColor = colorToQColor(layer.color)
        else:
            onCurveColor = defaultColor("glyphOnCurvePoints")
    if otherColor is None:
        otherColor = defaultColor("glyphOtherPoints")
    if backgroundColor is None:
        backgroundColor = defaultColor("background")
    # get the outline data
    outlineData = glyph.getRepresentation("defconQt.OutlineInformation")
    points = []
    # start points
    if drawStartPoints and outlineData["startPoints"]:
        startWidth = startHeight = 15 * scale
        startHalf = startWidth / 2.0
        path = QPainterPath()
        for point, angle in outlineData["startPoints"]:
            x, y = point
            if angle is not None:
                path.moveTo(x, y)
                path.arcTo(x - startHalf, y - startHalf, startWidth,
                           startHeight, 180 - angle, 180)
                path.closeSubpath()
            else:
                path.addEllipse(
                    x - startHalf, y - startHalf, startWidth, startHeight)
        startPointColor = QColor(otherColor)
        aF = startPointColor.alphaF()
        startPointColor.setAlphaF(aF * .3)
        painter.fillPath(path, startPointColor)
    # handles
    if drawOffCurves and outlineData["offCurvePoints"]:
        painter.save()
        painter.setPen(otherColor)
        for pt1, pt2 in outlineData["bezierHandles"]:
            x1, y1 = pt1
            x2, y2 = pt2
            # TODO: should lineWidth account scale by default
            drawLine(painter, x1, y1, x2, y2, 1.0 * scale)
        painter.restore()
    # on curve
    if drawOnCurves and outlineData["onCurvePoints"]:
        width = 7 * scale
        half = width / 2.0
        smoothWidth = 8 * scale
        smoothHalf = smoothWidth / 2.0
        painter.save()
        path = QPainterPath()
        selectedPath = QPainterPath()
        for point in outlineData["onCurvePoints"]:
            x, y = point["point"]
            points.append((x, y))
            pointPath = QPainterPath()
            if point["smooth"]:
                x -= smoothHalf
                y -= smoothHalf
                pointPath.addEllipse(x, y, smoothWidth, smoothWidth)
            else:
                x -= half
                y -= half
                pointPath.addRect(x, y, width, width)
            if drawSelection and point["selected"]:
                selectedPath.addPath(pointPath)
            path.addPath(pointPath)
        pen = QPen(onCurveColor)
        pen.setWidthF(1.5 * scale)
        painter.setPen(pen)
        painter.fillPath(selectedPath, onCurveColor)
        painter.drawPath(path)
        painter.restore()
    # off curve
    if drawOffCurves and outlineData["offCurvePoints"]:
        # lines
        # points
        offWidth = 5 * scale
        offHalf = offWidth / 2.0
        path = QPainterPath()
        selectedPath = QPainterPath()
        for point in outlineData["offCurvePoints"]:
            x, y = point["point"]
            points.append((x, y))
            pointPath = QPainterPath()
            x -= offHalf
            y -= offHalf
            pointPath.addEllipse(x, y, offWidth, offWidth)
            if drawSelection and point["selected"]:
                selectedPath.addPath(pointPath)
            else:
                path.addPath(pointPath)
        pen = QPen(otherColor)
        pen.setWidthF(3.0 * scale)
        painter.save()
        painter.setPen(pen)
        painter.drawPath(path)
        painter.fillPath(path, QBrush(backgroundColor))
        painter.drawPath(selectedPath)
        painter.fillPath(selectedPath, QBrush(otherColor))
        painter.restore()
    # coordinates
    if drawCoordinates:
        otherColor = QColor(otherColor)
        otherColor.setAlphaF(otherColor.alphaF() * .6)
        painter.save()
        painter.setPen(otherColor)
        # TODO: decision + color
        font = painter.font()
        font.setPointSize(7)
        painter.setFont(font)
        for x, y in points:
            posX = x
            # TODO: We use + here because we align on top. Consider abstracting
            # yOffset.
            posY = y + 3
            x = round(x, 1)
            if int(x) == x:
                x = int(x)
            y = round(y, 1)
            if int(y) == y:
                y = int(y)
            text = "%d  %d" % (x, y)
            drawTextAtPoint(painter, text, posX, posY, scale,
                            xAlign="center", yAlign="top")
        painter.restore()

# Anchors


def drawGlyphAnchors(painter, glyph, scale, rect, drawAnchors=True,
                     drawSelection=True, drawText=True, color=None,
                     selectionColor=None):
    if not glyph.anchors:
        return
    if color is None:
        color = defaultColor("glyphAnchor")
    if selectionColor is None:
        selectionColor = defaultColor("glyphSelection")
    fallbackColor = color
    anchorSize = 6 * scale
    anchorHalfSize = anchorSize / 2
    for anchor in glyph.anchors:
        if anchor.color is not None:
            color = colorToQColor(anchor.color)
        else:
            color = fallbackColor
        x = anchor.x
        y = anchor.y
        name = anchor.name
        painter.save()
        if drawAnchors:
            path = QPainterPath()
            path.addEllipse(x - anchorHalfSize, y - anchorHalfSize,
                            anchorSize, anchorSize)
            painter.fillPath(path, color)
            if drawSelection and anchor.selected:
                pen = QPen(selectionColor)
                pen.setWidthF(5.0 * scale)
                painter.setPen(pen)
                painter.drawPath(path)
        if drawText and name:
            painter.setPen(color)
            # TODO: we're using + before we shift to top, ideally this should
            # be abstracted w drawTextAtPoint taking a dy parameter that will
            # offset the drawing region from origin regardless of whether we
            # are aligning to top or bottom.
            y += 3 * scale
            drawTextAtPoint(painter, name, x, y, scale,
                            xAlign="center", yAlign="top")
        painter.restore()
