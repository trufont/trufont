from defcon import Color
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

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
    fontVerticalMetrics=QColor.fromRgbF(.4, .4, .4, .5),#NSColor.colorWithCalibratedWhite_alpha_(.4, .5),
    fontPostscriptBlues=QColor.fromRgbF(.5, .7, 1, .3),
    fontPostscriptFamilyBlues=QColor.fromRgbF(1, 1, .5, .3),

    # Glyph
    # -----

    # margins
    glyphMarginsFill=QColor.fromRgbF(.5, .5, .5, .11),#NSColor.colorWithCalibratedWhite_alpha_(.5, .11),
    glyphMarginsStroke=QColor.fromRgbF(.7, .7, .7, .5),#NSColor.colorWithCalibratedWhite_alpha_(.7, .5),
    # contour fill
    glyphContourFill=QColor.fromRgbF(.85, .85, .85, .5),#QColor.fromRgbF(0, 0, 0, 1),
    # contour stroke
    glyphContourStroke=QColor.fromRgbF(0, 0, 0, 1),
    # component fill
    glyphComponentFill=QColor.fromRgbF(0, 0, 0, 1),
    # component stroke
    glyphComponentStroke=QColor.fromRgbF(0, 0, 0, 1),
    # points
    glyphPoints=QColor.fromRgbF(.6, .6, .6, 1),
    # anchors
    glyphAnchor=QColor.fromRgbF(1, .2, 0, 1),
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

# TODO: shim shadow
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
    ### TEST
    #painter.fillRect(0, -painter.fontMetrics().ascent(), painter.fontMetrics().width(text), painter.fontMetrics().lineSpacing(), Qt.green)
    ### END TEST
    painter.drawText(0, 0, text)
    painter.restore()

# ----
# Font
# ----

# Vertical Metrics

def drawFontVerticalMetrics(painter, glyph, scale, rect, drawLines=True, drawText=True, color=None):
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
    # TODO: why sorted?
    for y, names in sorted(positions.items()):
        names = ", ".join(names)
        lines.append((y, names))
    # draw lines
    if drawLines:
        lineWidth = 1.0 * scale
        for y, names in lines:
            drawLine(painter, xMin, y, xMax, y, lineWidth=lineWidth)
    # draw text
    if drawText:
        fontSize = 9
        # TODO: maybe add pointSize argument to drawTextAtPoint
        #font = painter.font()
        #font.setPointSize(fontSize)
        #painter.setFont(font)
        x = xMin + 5 * scale
        for y, text in lines:
            y -= (fontSize / 2.0) * scale
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

def drawGlyphImage(painter, glyph, scale, rect, backgroundColor=None):
    pass
    """
    if glyph.image.fileName is None:
        return
    context = NSGraphicsContext.currentContext()
    context.saveGraphicsState()
    aT = NSAffineTransform.transform()
    aT.setTransformStruct_(glyph.image.transformation)
    aT.concat()
    image = glyph.image.getRepresentation("defconAppKit.NSImage")
    image.drawAtPoint_fromRect_operation_fraction_(
        (0, 0), ((0, 0), image.size()), NSCompositeSourceOver, 1.0
    )
    context.restoreGraphicsState()
    """

# Margins

def drawGlyphMargins(painter, glyph, scale, rect, drawFill=True, drawStroke=True, fillColor=None, strokeColor=None):
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

def drawGlyphFillAndStroke(painter, glyph, scale, rect,
    drawFill=True, drawStroke=True,
    contourFillColor=None, contourStrokeColor=None, componentFillColor=None,
    contourStrokeWidth=1.0):
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
    if drawFill:
        # work out the colors
        if contourFillColor is None and layerColor is not None:
            contourFillColor = layerColor
        elif contourFillColor is None and layerColor is None:
            contourFillColor = defaultColor("glyphContourFill")
        if componentFillColor is None and layerColor is not None:
            componentFillColor = layerColor
        elif componentFillColor is None and layerColor is None:
            componentFillColor = defaultColor("glyphComponentFill")
        """
        # make the fill less opaque if stroking
        if drawStroke:
            contourFillColor = QColor(contourFillColor)
            aF = contourFillColor.alphaF()
            contourFillColor.setAlphaF(aF * .6)
            componentFillColor = QColor(componentFillColor)
            aF = componentFillColor.alphaF()
            componentFillColor.setAlphaF(aF * .6)
        """
        # components
        painter.fillPath(componentPath, QBrush(componentFillColor))
        # contours
        painter.fillPath(contourPath, QBrush(contourFillColor))
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
        painter.drawPath(contourPath)
    painter.restore()

# points

def drawGlyphPoints(painter, glyph, scale, rect,
    drawStartPoints=True, drawOnCurves=True, drawOffCurves=True,
    drawCoordinates=True, color=None, backgroundColor=None):
    layer = glyph.layer
    layerColor = None
    if layer is not None:
        if layer.color is not None:
            color = colorToQColor(layer.color)
    if color is None:
        color = defaultColor("glyphPoints")
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
                # XXX
                #path.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_clockwise_(
                #    (x, y), startHalf, angle - 90, angle + 90, True)
                path.closeSubpath()
            else:
                path.addEllipse(x - startHalf, y - startHalf, startWidth, startHeight)
        # TODO: pointColor was named here?
        startPointColor = QColor(color)
        aF = startPointColor.alphaF()
        startPointColor.setAlphaF(aF * .3)
        painter.fillPath(path, startPointColor)
    # off curve
    if drawOffCurves and outlineData["offCurvePoints"]:
        # lines
        painter.save()
        painter.setPen(color)
        for pt1, pt2 in outlineData["bezierHandles"]:
            x1, y1 = pt1
            x2, y2 = pt2
            # TODO: should lineWidth account scale by default
            drawLine(painter, x1, y1, x2, y2, 1.0 * scale)
        # points
        offWidth = 5 * scale
        offHalf = offWidth / 2.0
        path = QPainterPath()
        for point in outlineData["offCurvePoints"]:
            x, y = point["point"]
            points.append((x, y))
            x -= offHalf
            y -= offHalf
            path.addEllipse(x, y, offWidth, offWidth)
        pen = QPen(color)
        pen.setWidthF(3.0 * scale)
        painter.setPen(pen)
        painter.drawPath(path)
        painter.fillPath(path, QBrush(backgroundColor))
        painter.restore()
    # on curve
    if drawOnCurves and outlineData["onCurvePoints"]:
        width = 7 * scale
        half = width / 2.0
        smoothWidth = 8 * scale
        smoothHalf = smoothWidth / 2.0
        painter.save()
        path = QPainterPath()
        for point in outlineData["onCurvePoints"]:
            x, y = point["point"]
            points.append((x, y))
            if point["smooth"]:
                x -= smoothHalf
                y -= smoothHalf
                path.addEllipse(x, y, smoothWidth, smoothWidth)
            else:
                x -= half
                y -= half
                path.addRect(x, y, width, width)
        pen = QPen(backgroundColor)
        pen.setWidthF(3.0 * scale)
        painter.setPen(pen)
        painter.drawPath(path)
        painter.fillPath(path, QBrush(color))
        painter.restore()
    # coordinates
    if drawCoordinates:
        color = QColor(color)
        color.setAlphaF(color.alphaF() * .6)
        painter.save()
        #font = painter.font()
        #font.setPointSize(9)
        #painter.setFont(font)
        painter.setPen(color)
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
            drawTextAtPoint(painter, text, posX, posY, scale, xAlign="center", yAlign="top")
        painter.restore()

# Anchors

def drawGlyphAnchors(painter, glyph, scale, rect, drawAnchor=True, drawText=True, color=None):#, backgroundColor=None
    if not glyph.anchors:
        return
    if color is None:
        color = defaultColor("glyphAnchor")
    fallbackColor = color
    """
    if backgroundColor is None:
        backgroundColor = defaultColor("background")
    """
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
        """
        shadow = NSShadow.alloc().init()
        shadow.setShadowColor_(backgroundColor)
        shadow.setShadowOffset_((0, 0))
        shadow.setShadowBlurRadius_(3)
        shadow.set()
        """
        if drawAnchor:
            path = QPainterPath()
            path.addEllipse(x - anchorHalfSize, y - anchorHalfSize,
                anchorSize, anchorSize)
            painter.fillPath(path, color)
        if drawText and name:
            #font = painter.font()
            #font.setPointSize(9)
            #painter.setFont(font)
            painter.setPen(color)
            # TODO: we're using + before we shift to top, ideally this should
            # be abstracted w drawTextAtPoint taking a dy parameter that will
            # offset the drawing region from origin regardless of whether we
            # are aligning to top or bottom.
            y += 3 * scale
            drawTextAtPoint(painter, name, x, y, scale, xAlign="center", yAlign="top")
        painter.restore()
