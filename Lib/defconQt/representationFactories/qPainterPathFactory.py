from fontTools.pens.qtPen import QtPen
from PyQt5.QtCore import Qt

def QPainterPathFactory(glyph, font):
    pen = QtPen(font)
    glyph.draw(pen)
    pen.path.setFillRule(Qt.WindingFill)
    return pen.path
