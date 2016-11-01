from defconQt.representationFactories.glyphCellFactory import (
    GlyphCellFactoryDrawingController, GlyphCellHeaderHeight,
    GlyphCellMinHeightForHeader, GlyphCellMinHeightForMetrics)
from defconQt.tools import platformSpecific
from PyQt5.QtCore import Qt


def TFGlyphCellFactory(
        glyph, width, height, drawMarkColor=True, drawTemplate=True,
        drawHeader=None, drawMetrics=None, pixelRatio=1.0):
    if drawHeader is None:
        drawHeader = height >= GlyphCellMinHeightForHeader
    if drawMetrics is None:
        drawMetrics = height >= GlyphCellMinHeightForMetrics
    obj = TFGlyphCellFactoryDrawingController(
        glyph=glyph, font=glyph.font, width=width, height=height,
        drawMarkColor=drawMarkColor, drawTemplate=drawTemplate,
        drawHeader=drawHeader, drawMetrics=drawMetrics, pixelRatio=pixelRatio)
    return obj.getPixmap()


class TFGlyphCellFactoryDrawingController(GlyphCellFactoryDrawingController):

    def __init__(self, *args, **kwargs):
        if "drawTemplate" in kwargs:
            drawTemplate = kwargs.pop("drawTemplate")
        else:
            drawTemplate = True
        super().__init__(*args, **kwargs)
        self.shouldDrawTemplate = drawTemplate

    def drawCellHorizontalMetrics(self, painter, rect):
        if not self.glyph.template:
            super().drawCellHorizontalMetrics(painter, rect)

    def drawCellVerticalMetrics(self, painter, rect):
        if not self.glyph.template:
            super().drawCellVerticalMetrics(painter, rect)

    def drawCellForeground(self, painter, rect):
        if self.shouldDrawTemplate and self.glyph.template:
            painter.save()
            font = platformSpecific.otherUIFont()
            font.setPointSize(.425 * self.height)
            painter.setFont(font)
            painter.setPen(Qt.lightGray)
            if self.glyph.unicode is not None:
                text = chr(self.glyph.unicode)
            else:
                text = "✌"
            painter.drawText(
                0, 0, self.width, self.height - GlyphCellHeaderHeight,
                Qt.AlignVCenter | Qt.AlignCenter, text)
            painter.restore()
