from defcon import Color
from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import (
    QBrush, QColor, QPainter, QPainterPath, QPen, QTransform)

"""
Adapted from DefconAppKit.

Common glyph drawing functions for all views. Notes:
- all drawing is done in font units
- the scale argument is the factor to scale a glyph unit to a view unit
- the rect argument is the rect that the glyph is being drawn in
"""

"""
setLayer_drawingAttributes_(layerName, attributes)

showGlyphFill
showGlyphStroke
showGlyphOnCurvePoints
showGlyphStartPoints
showGlyphOffCurvePoints
showGlyphPointCoordinates
showGlyphAnchors
showGlyphImage
showGlyphMargins
showFontVerticalMetrics
showFontVerticalMetricsTitles
showFontPostscriptBlues
showFontPostscriptFamilyBlues
"""

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
    fontVerticalMetrics=QColor.fromRgbF(.4, .4, .4, .5),
    fontPostscriptBlues=QColor.fromRgbF(.5, .7, 1, .3),
    fontPostscriptFamilyBlues=QColor.fromRgbF(1, 1, .5, .3),

    # Glyph
    # -----

    # margins
    glyphMarginsFill=QColor.fromRgbF(.5, .5, .5, .11),
    glyphMarginsStroke=QColor.fromRgbF(.7, .7, .7, .5),
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
    glyphAnchor=QColor(228, 96, 15, 200),  # QColor.fromRgbF(1, .2, 0, 1),
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
    painter.drawLine(x1, y1, x2, y2)
    painter.restore()


def drawGlyphWithAliasedLines(painter, glyph):
    curvePath, lines = glyph.getRepresentation(
        "defconQt.SplitLinesQPainterPath")
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


def drawTextAtPoint(painter, text, x, y, scale, xAlign="left", yAlign="bottom",
                    flipped=True):
    if xAlign != "left" or yAlign != "bottom":
        fM = painter.fontMetrics()
        width, height = fM.width(text), fM.lineSpacing()
        width *= scale
        height *= scale
        if xAlign == "center":
            x -= width / 2
        elif xAlign == "right":
            x -= width
        if yAlign == "center":
            y += height / 2
        elif yAlign == "top":
            y += height
    # TODO: shim shadow
    painter.save()
    if flipped:
        s = -scale
        fM = painter.fontMetrics()
        height = fM.ascent() * scale
        y -= height
    else:
        s = scale
    painter.translate(x, y)
    painter.scale(scale, s)
    painter.drawText(0, 0, text)
    painter.restore()

# ----
# Font
# ----

# Vertical Metrics


def drawFontVerticalMetrics(painter, glyph, scale, rect, drawLines=True,
                            drawText=True, color=None):
    font = glyph.font
    if font is None:
        return
    if color is None:
        color = defaultColor("fontVerticalMetrics")
    painter.save()
    painter.setPen(color)
    # gather y positions
    toDraw = [
        ("Descender", font.info.descender),
        ("Baseline", 0),
        ("x-height", font.info.xHeight),
        ("Cap height", font.info.capHeight),
        ("Ascender", font.info.ascender),
    ]
    positions = {}
    for name, position in toDraw:
        if position is None:
            continue
        if position not in positions:
            positions[position] = []
        positions[position].append(name)
    # create lines
    xMin = rect[0]
    xMax = xMin + rect[2]
    lines = []
    for y, names in positions.items():
        names = ", ".join(names)
        if y != 0:
            names = "%s (%d)" % (names, y)
        lines.append((y, names))
    # draw lines
    if drawLines:
        lineWidth = 1.0 * scale
        for y, names in lines:
            drawLine(painter, xMin, y, xMax, y, lineWidth=lineWidth)
    # draw text
    if drawText:
        fontSize = 9
        x = glyph.width + 6 * scale
        for y, text in lines:
            y -= (fontSize / 3.5) * scale
            drawTextAtPoint(painter, text, x, y, scale)
    painter.restore()

# Blues


def drawFontPostscriptBlues(painter, glyph, scale, rect, color=None):
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
    _drawBlues(painter, blues, rect, color)


def drawFontPostscriptFamilyBlues(painter, glyph, scale, rect, color=None):
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
    _drawBlues(painter, blues, rect, color)


def _drawBlues(painter, blues, rect, color):
    x = rect[0]
    w = rect[2]
    for yMin, yMax in zip(blues[::2], blues[1::2]):
        painter.fillRect(x, yMin, w, yMax - yMin, color)

# Image


def drawGlyphImage(painter, glyph, scale, rect):
    if glyph.image.fileName is None:
        return
    painter.save()
    painter.setTransform(QTransform(*glyph.image.transformation), True)
    image = glyph.image.getRepresentation("defconQt.QPixmap")
    painter.drawPixmap(0, 0, image)
    painter.restore()

# Margins


def drawGlyphMargins(painter, glyph, scale, rect, drawFill=True,
                     drawStroke=True, fillColor=None, strokeColor=None):
    if fillColor is None:
        fillColor = defaultColor("glyphMarginsFill")
    if strokeColor is None:
        strokeColor = defaultColor("glyphMarginsStroke")
    x, y, w, h = rect
    painter.save()
    if drawFill:
        left = QRectF(x, y, -x, h)
        right = QRectF(glyph.width, y, w - glyph.width, h)
        for rect in (left, right):
            painter.fillRect(rect, fillColor)
    if drawStroke:
        painter.setPen(strokeColor)
        drawLine(painter, 0, y, 0, y + h)
        drawLine(painter, glyph.width, y, glyph.width, y + h)
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
        "defconQt.FilterSelectionQPainterPath")
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
        drawCoordinates=True, onCurveColor=None, otherColor=None,
        backgroundColor=None):
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
            if point["selected"]:
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
            if point["selected"]:
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
