from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFontMetrics, QPainter, QPainterPath, QPixmap

from defconQt.tools import platformSpecific
from defconQt.tools.drawing import colorToQColor

GlyphCellHeaderHeight = 13
GlyphCellMinHeightForHeader = 40
GlyphCellMinHeightForMetrics = 100

cellMetricsFillColor = cellMetricsLineColor = QColor(224, 226, 220)
cellMetricsTextColor = QColor(72, 72, 72)
cellDirtyColor = QColor(240, 240, 240, 170)

headerFont = platformSpecific.otherUIFont()

# TODO: fine-tune dirty appearance


def GlyphCellFactory(
    glyph,
    width,
    height,
    drawLayers=False,
    drawMarkColor=True,
    drawHeader=None,
    drawMetrics=None,
    pixelRatio=1.0,
):
    if drawHeader is None:
        drawHeader = height >= GlyphCellMinHeightForHeader
    if drawMetrics is None:
        drawMetrics = height >= GlyphCellMinHeightForMetrics
    obj = GlyphCellFactoryDrawingController(
        glyph=glyph,
        font=glyph.font,
        width=width,
        height=height,
        drawLayers=False,
        drawMarkColor=drawMarkColor,
        drawHeader=drawHeader,
        drawMetrics=drawMetrics,
        pixelRatio=pixelRatio,
    )
    return obj.getPixmap()


class GlyphCellFactoryDrawingController:
    """
    This draws the cell with the layers stacked in this order:

    ------------------
    header text
    ------------------
    header background
    ------------------
    foreground
    ------------------
    glyph
    ------------------
    vertical metrics
    ------------------
    horizontal metrics
    ------------------
    background
    ------------------

    Subclasses may override the layer drawing methods to customize
    the appearance of cells.
    """

    def __init__(
        self,
        glyph,
        font,
        width,
        height,
        pixelRatio=1.0,
        drawLayers=False,
        drawMarkColor=True,
        drawHeader=True,
        drawMetrics=True,
    ):
        self.glyph = glyph
        self.font = font
        self.pixelRatio = pixelRatio
        self.width = width
        self.height = height
        self.bufferPercent = 0.10
        self.shouldDrawHeader = drawHeader
        self.shouldDrawLayers = drawLayers
        self.shouldDrawMarkColor = drawMarkColor
        self.shouldDrawMetrics = drawMetrics

        self.headerAtBottom = True
        self.headerHeight = 0
        if drawHeader:
            self.headerHeight = GlyphCellHeaderHeight
        availableHeight = (height - self.headerHeight) * (
            1.0 - (self.bufferPercent * 2)
        )
        descender = font.info.descender or -250
        # some fonts overflow their upm, try to infer
        if font.info.descender and font.info.ascender:
            unitsPerEm = font.info.ascender - descender
        else:
            unitsPerEm = font.info.unitsPerEm or 1000
        self.buffer = height * self.bufferPercent
        self.scale = availableHeight / unitsPerEm
        self.xOffset = (width - (glyph.width * self.scale)) / 2
        self.yOffset = abs(descender * self.scale) + 0.4 * self.buffer

    def getPixmap(self):
        pixmap = QPixmap(self.width * self.pixelRatio, self.height * self.pixelRatio)
        pixmap.setDevicePixelRatio(self.pixelRatio)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(0, self.height)
        painter.scale(1, -1)
        if self.headerAtBottom:
            bodyRect = (0, 0, self.width, self.height - self.headerHeight)
            headerRect = (0, 0, self.width, self.headerHeight)
        else:
            bodyRect = (0, 0, self.width, self.height - self.headerHeight)
            headerRect = (0, 0, self.width, self.headerHeight)
        # background
        painter.save()
        if self.headerAtBottom:
            h = self.height
        else:
            h = self.height - self.headerHeight
        painter.translate(0, h)
        painter.scale(1, -1)
        self.drawCellBackground(painter, bodyRect)
        painter.restore()
        # glyph
        if self.headerAtBottom:
            painter.translate(0, self.headerHeight)
        if self.shouldDrawMetrics:
            self.drawCellHorizontalMetrics(painter, bodyRect)
            self.drawCellVerticalMetrics(painter, bodyRect)
        painter.save()
        painter.setClipRect(0, 0, self.width, self.height - self.headerHeight)
        painter.translate(self.xOffset, self.yOffset)
        painter.scale(self.scale, self.scale)
        self.drawCellGlyph(painter)
        painter.restore()
        # foreground
        painter.save()
        painter.translate(0, self.height - self.headerHeight)
        painter.scale(1, -1)
        self.drawCellForeground(painter, bodyRect)
        painter.restore()
        # header
        if self.shouldDrawHeader:
            painter.save()
            if self.headerAtBottom:
                h = 0
            else:
                h = self.height
            painter.translate(0, h)
            painter.scale(1, -1)
            self.drawCellHeaderBackground(painter, headerRect)
            self.drawCellHeaderText(painter, headerRect)
            painter.restore()
        return pixmap

    def drawCellBackground(self, painter, rect):
        if self.shouldDrawMarkColor:
            markColor = self.glyph.markColor
            if markColor is not None:
                color = colorToQColor(markColor)
                color.setAlphaF(0.7 * color.alphaF())
                painter.fillRect(*(rect + (color,)))
        if self.shouldDrawHeader:
            if self.glyph.dirty:
                x, _, w, _ = rect
                painter.fillRect(*(rect + (cellDirtyColor,)))
                path = QPainterPath()
                path.moveTo(x + w - 12, 0)
                path.lineTo(x + w, 0)
                path.lineTo(x + w, 12)
                path.closeSubpath()
                painter.fillPath(path, QColor(255, 0, 0, 170))

    def drawCellHorizontalMetrics(self, painter, rect):
        xMin, yMin, _, _ = rect
        glyph = self.glyph
        scale = self.scale
        xOffset = self.xOffset
        left = round((0 * scale) + xMin + xOffset)
        right = round((glyph.width * scale) + xMin + xOffset)

        hi = 750
        lo = -250
        font = self.font
        yOffset = self.yOffset
        if font is not None:
            ascender = font.info.ascender or 750
            capHeight = font.info.capHeight or 750
            hi = max(ascender, capHeight)
            lo = font.info.descender or -250
        hi = round((hi * scale) + yMin + yOffset)
        lo = round((lo * scale) + yMin + yOffset)

        painter.save()
        painter.setPen(cellMetricsFillColor)
        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.drawLine(left, lo, left, hi)
        painter.drawLine(right, lo, right, hi)
        painter.restore()

    def drawCellVerticalMetrics(self, painter, rect):
        xMin, yMin, _, _ = rect
        font = self.font
        scale = self.scale
        xOffset, yOffset = self.xOffset, self.yOffset
        left = round((0 * scale) + xMin + xOffset)
        right = round((self.glyph.width * scale) + xMin + xOffset)
        lines = {
            0,
            font.info.descender,
            font.info.xHeight,
            font.info.capHeight,
            font.info.ascender,
        }
        painter.save()
        painter.setPen(cellMetricsLineColor)
        painter.setRenderHint(QPainter.Antialiasing, False)
        for y in lines:
            if y is None:
                continue
            y = round((y * scale) + yMin + yOffset)
            painter.drawLine(left, y, right, y)
        painter.restore()

    def drawCellGlyph(self, painter):
        if self.shouldDrawLayers:
            layers = self.font.layers
            for layerName in reversed(layers.layerOrder):
                layer = layers[layerName]
                if self.glyph.name not in layer:
                    continue
                layerColor = None
                if layer.color is not None:
                    layerColor = colorToQColor(layer.color)
                if layerColor is None:
                    layerColor = Qt.black
                glyph = layer[self.glyph.name]
                path = glyph.getRepresentation("defconQt.QPainterPath")
                painter.fillPath(path, layerColor)
        else:
            path = self.glyph.getRepresentation("defconQt.QPainterPath")
            painter.fillPath(path, Qt.black)

    def drawCellForeground(self, painter, rect):
        pass

    def drawCellHeaderBackground(self, painter, rect):
        xMin, yMin, width, height = rect
        # background
        if self.shouldDrawMarkColor and self.glyph.markColor is not None:
            color = colorToQColor(self.glyph.markColor)
        elif self.glyph.dirty:
            color = cellDirtyColor
        else:
            color = Qt.white
        painter.fillRect(xMin, yMin, width, height, color)

    def drawCellHeaderText(self, painter, rect):
        _, _, width, height = rect
        metrics = QFontMetrics(headerFont)
        minOffset = painter.pen().width()

        painter.setFont(headerFont)
        painter.setPen(cellMetricsTextColor)
        name = metrics.elidedText(self.glyph.name, Qt.ElideRight, width - 2)
        painter.drawText(
            1,
            0,
            width - 2,
            height - minOffset,
            Qt.TextSingleLine | Qt.AlignCenter | Qt.AlignBottom,
            name,
        )
