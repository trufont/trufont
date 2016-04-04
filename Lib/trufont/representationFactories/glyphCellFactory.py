from defconQt.representationFactories.glyphCellFactory import (
    GlyphCellFactoryDrawingController, GlyphCellHeaderHeight,
    GlyphCellMinHeightForHeader, GlyphCellMinHeightForMetrics)
from PyQt5.QtCore import Qt


def TFGlyphCellFactory(
        glyph, width, height, drawMarkColor=True, drawTemplate=True,
        drawHeader=None, drawMetrics=None):
    if drawHeader is None:
        drawHeader = height >= GlyphCellMinHeightForHeader
    if drawMetrics is None:
        drawMetrics = height >= GlyphCellMinHeightForMetrics
    obj = TFGlyphCellFactoryDrawingController(
        glyph=glyph, font=glyph.font, width=width, height=height,
        drawMarkColor=drawMarkColor, drawTemplate=drawTemplate,
        drawHeader=drawHeader, drawMetrics=drawMetrics)
    return obj.getPixmap()


class TFGlyphCellFactoryDrawingController(GlyphCellFactoryDrawingController):

    def __init__(self, *args, **kwargs):
        if "drawTemplate" in kwargs:
            drawTemplate = kwargs.pop("drawTemplate")
        else:
            drawTemplate = True
        super().__init__(*args, **kwargs)
        self.shouldDrawTemplate = drawTemplate

    def drawCellForeground(self, painter, rect):
        if self.shouldDrawTemplate and self.glyph.template:
            painter.save()
            font = painter.font()
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
