from fontTools.pens.qtPen import QtPen
from PyQt5.QtCore import Qt

def QPainterPathFactory(glyph):
    pen = QtPen(glyph.getParent())
    glyph.draw(pen)
    pen.path.setFillRule(Qt.WindingFill)
    return pen.path
