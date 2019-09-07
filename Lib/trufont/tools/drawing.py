import math

from fontTools.misc.transform import Identity
from PyQt5.QtCore import QLineF, QPointF, Qt
from PyQt5.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen, QTransform

from defconQt.tools import platformSpecific
from defconQt.tools.drawing import (
    colorToQColor,
    drawTextAtPoint,
    ellipsePath,
    lozengePath,
    rectanglePath,
    trianglePath,
)

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
    # selection
    glyphSelection=QColor(145, 170, 196, 155),
    # guidelines
    glyphGuideline=QColor.fromRgbF(0.3, 0.4, 0.85, 0.5),
    # marker
    glyphBluesMarker=QColor(235, 191, 202, 225),
    # grid
    gridColor=QColor(220, 220, 220),
)


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
        # antialiased drawing blends a little in color with the background
        # reduce alpha before drawing aliased
        color = pen.color()
        color.setAlphaF(0.9 * color.alphaF())
        pen.setColor(color)
    pen.setWidthF(lineWidth)
    painter.setPen(pen)
    painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
    painter.restore()


def drawGlyphWithAliasedLines(painter, glyph):
    curvePath, lines = glyph.getRepresentation("TruFont.SplitLinesQPainterPath")
    painter.drawPath(curvePath)
    for x1, y1, x2, y2 in lines:
        drawLine(painter, x1, y1, x2, y2)


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
    _drawGuidelines(painter, glyph, scale, rect, font.guidelines, color=color)


def drawGlyphGuidelines(
    painter, glyph, scale, rect, drawLines=True, drawText=True, color=None
):
    if not (drawLines or drawText):
        return
    if color is None:
        color = defaultColor("glyphGuideline")
    _drawGuidelines(painter, glyph, scale, rect, glyph.guidelines, color=color)


def _drawGuidelines(
    painter,
    glyph,
    scale,
    rect,
    guidelines,
    drawLines=True,
    drawText=True,
    drawSelection=True,
    color=None,
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
                # 1. make horizontal line from *(line.x, line.y)* of length
                # *diagonal*
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
                    fontSize = painter.font().pointSize()
                    textX = glyph.width + 6 * scale
                    textY = line.y - (fontSize / 3.5) * scale
                elif line.x is not None:
                    textX = line.x + 6 * scale
                    textY = 0
                xAlign = "left"
            drawTextAtPoint(painter, line.name, textX, textY, scale, xAlign=xAlign)
        painter.restore()


# Image


def drawGlyphImage(painter, glyph, scale, drawSelection=True, selectionColor=None):
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
    painter,
    glyph,
    scale,
    drawFill=True,
    drawStroke=True,
    drawSelection=True,
    drawComponentFill=True,
    drawComponentStroke=False,
    contourFillColor=None,
    contourStrokeColor=None,
    componentFillColor=None,
    componentStrokeColor=None,
    selectionColor=None,
    partialAliasing=True,
):
    if glyph.template:
        if glyph.unicode is None:
            return
        text = chr(glyph.unicode)
        font = glyph.font
        height = 750
        if font is not None and font.info.ascender:
            height = font.info.ascender
        painter.save()
        font = platformSpecific.otherUIFont()
        font.setPointSize(height)
        painter.setFont(font)
        color = QColor(Qt.lightGray)
        color.setAlphaF(0.4)
        painter.setPen(color)
        metrics = painter.fontMetrics()
        xOffset = -(metrics.width(text) - glyph.width) / 2
        painter.translate(xOffset, 0)
        painter.scale(1, -1)
        painter.drawText(0, 0, text)
        painter.restore()
        return
    # get the layer color
    layer = glyph.layer
    layerColor = None
    if layer is not None and layer.color is not None:
        layerColor = colorToQColor(layer.color)
    if selectionColor is None:
        selectionColor = defaultColor("glyphSelection")
    # get the paths
    contourPath = glyph.getRepresentation("defconQt.NoComponentsQPainterPath")
    componentPath, selectedComponentPath, originPts = glyph.getRepresentation(
        "TruFont.SelectedComponentsQPainterPath"
    )
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
        selectedComponentFillColor = QColor(componentFillColor)
        selectedComponentFillColor.setRed(0)
        selectedComponentFillColor.setGreen(0)
        selectedComponentFillColor.setBlue(0)
        painter.fillPath(componentPath, QBrush(componentFillColor))
        if drawSelection:
            painter.fillPath(selectedComponentPath, QBrush(selectedComponentFillColor))
        else:
            painter.fillPath(selectedComponentPath, QBrush(componentFillColor))
        # components origin
        # TODO: make this a parameter, disable on sizes < MinDetails
        if drawSelection:
            painter.save()
            pen = QPen(componentFillColor)
            pen.setWidth(0)
            painter.setPen(pen)
            for x, y in originPts:
                painter.drawLine(x, y + 5 * scale, x, y)
                painter.drawLine(x, y, x + 4.5 * scale, y)
            painter.restore()
    # selection
    if drawSelection:
        selectionPath = glyph.getRepresentation("TruFont.SelectedContoursQPainterPath")
        pen = QPen(selectionColor)
        pen.setWidthF(3.5 * scale)
        painter.setPen(pen)
        painter.drawPath(selectionPath)
    # stroke
    if drawStroke:
        # work out the color
        if contourStrokeColor is None:
            if layerColor is not None:
                contourStrokeColor = layerColor
            else:
                contourStrokeColor = defaultColor("glyphContourStroke")
        # contours
        pen = QPen(contourStrokeColor)
        pen.setWidth(0)
        painter.setPen(pen)
        if partialAliasing:
            drawGlyphWithAliasedLines(painter, glyph)
        else:
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
        painter.drawPath(selectedComponentPath)
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
    drawSelection=True,
    drawBluesMarkers=True,
    onCurveColor=None,
    onCurveSmoothColor=None,
    offCurveColor=None,
    otherColor=None,
    backgroundColor=None,
):
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
            selectedSize = 15 * scale
            snapSize = 17 * scale
            selectedSnapSize = 20 * scale
            painter.save()
            pen = painter.pen()
            pen.setColor(QColor(255, 255, 255, 125))
            pen.setWidth(0)
            painter.setPen(pen)
            for point in outlineData["onCurvePoints"]:
                x, y = point["point"]
                # TODO: we could add a non-overlapping interval tree special
                # cased for borders
                selected = drawSelection and point.get("selected", False)
                if selected:
                    size_ = selectedSize
                    snapSize_ = selectedSnapSize
                else:
                    size_ = size
                    snapSize_ = snapSize
                for yMin, yMax in zip(blues[::2], blues[1::2]):
                    if not (y >= yMin and y <= yMax):
                        continue
                    # if yMin > 0 and y == yMin or yMin <= 0 and y == yMax:
                    if y in blues_:
                        path = lozengePath(x, y, snapSize_)
                    else:
                        path = ellipsePath(x, y, size_)
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
        selectedSize = 8.5 * scale
        smoothSize = 8 * scale
        selectedSmoothSize = 10 * scale
        startSize = 7 * scale
        selectedStartSize = 9 * scale
        loneStartSize = 12 * scale
        selectedLoneStartSize = 14 * scale
        painter.save()
        notchPath = QPainterPath()
        paths = (QPainterPath(), QPainterPath())
        smoothPaths = (QPainterPath(), QPainterPath())
        for point in outlineData["onCurvePoints"]:
            x, y = point["point"]
            points.append((x, y))
            # notch
            if "smoothAngle" in point:
                angle = point["smoothAngle"]
                t = Identity.rotate(angle)
                x1, y1 = t.transformPoint((-1.35 * scale, 0))
                x2, y2 = -x1, -y1
                x1 += x
                y1 += y
                x2 += x
                y2 += y
                notchPath.moveTo(x1, y1)
                notchPath.lineTo(x2, y2)
            # points
            selected = drawSelection and point.get("selected", False)
            if selected:
                size_ = selectedSize
                smoothSize_ = selectedSmoothSize
                startSize_ = selectedStartSize
                loneStartSize_ = selectedLoneStartSize
            else:
                size_ = size
                smoothSize_ = smoothSize
                startSize_ = startSize
                loneStartSize_ = loneStartSize
            if drawStartPoints and "startPointAngle" in point:
                angle = point["startPointAngle"]
                if angle is not None:
                    pointPath = trianglePath(x, y, startSize_, angle)
                else:
                    pointPath = ellipsePath(x, y, loneStartSize_)
            elif point["smooth"]:
                pointPath = ellipsePath(x, y, smoothSize_)
            else:
                pointPath = rectanglePath(x, y, size_)
            # store the path
            if point["smooth"]:
                smoothPaths[selected].addPath(pointPath)
            else:
                paths[selected].addPath(pointPath)
        path, selectedPath = paths
        smoothPath, selectedSmoothPath = smoothPaths
        # fill
        selectedPath.setFillRule(Qt.WindingFill)
        selectedSmoothPath.setFillRule(Qt.WindingFill)
        painter.fillPath(selectedPath, onCurveColor)
        painter.fillPath(selectedSmoothPath, onCurveSmoothColor)
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
        selectedOffSize = 6.75 * scale
        path = QPainterPath()
        selectedPath = QPainterPath()
        selectedPath.setFillRule(Qt.WindingFill)
        for point in outlineData["offCurvePoints"]:
            x, y = point["point"]
            selected = drawSelection and point.get("selected", False)
            if selected:
                offSize_ = selectedOffSize
            else:
                offSize_ = offSize
            pointPath = ellipsePath(x, y, offSize_)
            if selected:
                selectedPath.addPath(pointPath)
            else:
                path.addPath(pointPath)
        pen = QPen(offCurveColor)
        pen.setWidthF(2.5 * scale)
        painter.save()
        painter.setPen(pen)
        painter.drawPath(path)
        painter.fillPath(path, QBrush(backgroundColor))
        painter.fillPath(selectedPath, QBrush(offCurveColor.lighter(135)))
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
    painter,
    glyph,
    scale,
    drawAnchors=True,
    drawSelection=True,
    drawText=True,
    color=None,
):
    if not glyph.anchors:
        return
    if color is None:
        color = defaultColor("glyphAnchor")
    fallbackColor = color
    anchorSize = 9 * scale
    selectedAnchorSize = 11 * scale
    for anchor in glyph.anchors:
        if anchor.color is not None:
            color = colorToQColor(anchor.color)
        else:
            color = fallbackColor
        x, y = anchor.x, anchor.y
        name = anchor.name
        painter.save()
        if drawAnchors:
            if drawSelection and anchor.selected:
                size = selectedAnchorSize
            else:
                size = anchorSize
            path = lozengePath(x, y, size)
            painter.fillPath(path, color)
        if drawText and name and drawSelection and anchor.selected:
            painter.setPen(color)
            # TODO: we're using + before we shift to top, ideally this should
            # be abstracted w drawTextAtPoint taking a dy parameter that will
            # offset the drawing region from origin regardless of whether we
            # are aligning to top or bottom.
            y += 6 * scale
            drawTextAtPoint(painter, name, x, y, scale, xAlign="center", yAlign="top")
        painter.restore()


# Grid


def drawGrid(painter, scale, rect, color=None):
    if color is None:
        color = defaultColor("gridColor")
    xMin, yMin, width, height = rect
    xMax = x = round(xMin + width)
    yMax = y = round(yMin + height)
    xMin, yMin = int(xMin), int(yMin)
    painter.save()
    pen = QPen(color)
    pen.setWidth(0)
    painter.setPen(pen)
    while x > xMin:
        painter.drawLine(x, yMin, x, yMax)
        x -= 1
    while y > yMin:
        painter.drawLine(xMin, y, xMax, y)
        y -= 1
    painter.restore()
