from defcon import Color
from defconQt.tools.drawing import drawTextAtPoint
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import (
    QBrush, QColor, QPainter, QPainterPath, QPen, QTransform)

# ------
# Colors
# ------

_defaultColors = dict(

    # General
    # -------

    background=QColor(Qt.white),

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
)


def colorToQColor(color):
    return QColor.fromRgbF(*Color(color))


def defaultColor(name):
    return _defaultColors[name]

# ----------
# Primitives
# ----------


def drawLine(painter, x1, y1, x2, y2, lineWidth=1.0):
    painter.save()
    turnOffAntiAliasing = False
    if x1 == x2 or y1 == y2:
        turnOffAntiAliasing = True
    if turnOffAntiAliasing:
        painter.setRenderHint(QPainter.Antialiasing, False)
        if lineWidth == 1.0:
            # cosmetic pen
            lineWidth = 0
    pen = painter.pen()
    pen.setWidthF(lineWidth)
    painter.setPen(pen)
    painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
    painter.restore()


def drawGlyphWithAliasedLines(painter, glyph):
    curvePath, lines = glyph.getRepresentation(
        "TruFont.SplitLinesQPainterPath")
    painter.drawPath(curvePath)
    painter.save()
    # antialiased drawing blend a little in color with the background
    # reduce alpha before drawing aliased
    pen = painter.pen()
    color = pen.color()
    color.setAlphaF(.75 * color.alphaF())
    pen.setColor(color)
    painter.setPen(pen)
    # TODO: maybe switch to QLineF for this repr
    for x1, y1, x2, y2 in lines:
        drawLine(painter, x1, y1, x2, y2, painter.pen().widthF())
    painter.restore()

# ----
# Font
# ----

# Image


def drawGlyphImage(painter, glyph, scale, rect, selectionColor=None):
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
    if image.selected:
        pen = QPen(selectionColor)
        pen.setWidthF(5.0 * scale)
        painter.setPen(pen)
        painter.drawRect(pixmap.rect())
    painter.restore()

# Fill and Stroke


def drawGlyphFillAndStroke(
        painter, glyph, scale, rect, drawFill=True, drawStroke=True,
        drawSelection=True, partialAliasing=True, contourFillColor=None,
        contourStrokeColor=None, componentFillColor=None,
        contourStrokeWidth=1.0, selectionColor=None):
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
        pen.setWidthF(5.0 * scale)
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
        pen.setWidthF(contourStrokeWidth * scale)
        painter.setPen(pen)
        if partialAliasing:
            drawGlyphWithAliasedLines(painter, glyph)
        else:
            painter.drawPath(contourPath)
    painter.restore()

# points


def drawGlyphPoints(
        painter, glyph, scale, rect,
        drawStartPoints=True, drawOnCurves=True, drawOffCurves=True,
        drawCoordinates=True, drawSelection=True, onCurveColor=None,
        otherColor=None, backgroundColor=None):
    layer = glyph.layer
    onCurveColor = None
    if layer is not None:
        if layer.color is not None:
            onCurveColor = colorToQColor(layer.color)
    if onCurveColor is None:
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
    # off curve
    if drawOffCurves and outlineData["offCurvePoints"]:
        # lines
        painter.save()
        painter.setPen(otherColor)
        for pt1, pt2 in outlineData["bezierHandles"]:
            x1, y1 = pt1
            x2, y2 = pt2
            # TODO: should lineWidth account scale by default
            drawLine(painter, x1, y1, x2, y2, 1.0 * scale)
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
        painter.setPen(pen)
        painter.drawPath(path)
        painter.fillPath(path, QBrush(backgroundColor))
        painter.drawPath(selectedPath)
        painter.fillPath(selectedPath, QBrush(otherColor))
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
    # coordinates
    if drawCoordinates:
        otherColor = QColor(otherColor)
        otherColor.setAlphaF(otherColor.alphaF() * .6)
        painter.save()
        painter.setPen(otherColor)
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
