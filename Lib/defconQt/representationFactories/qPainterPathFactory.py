from fontTools.pens.qtPen import QtPen

def QPainterPathFactory(glyph, font):
    pen = QtPen(font)
    glyph.draw(pen)
    return pen.path