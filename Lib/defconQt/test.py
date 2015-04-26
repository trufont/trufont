from controls.glyphCellView_ex import Window
import representationFactories
from PyQt5.QtWidgets import QApplication

if __name__ == '__main__':
    import sys
    from defcon import Font
    path = "C:\\Veloce.ufo"
    font = Font(path)
    #glyph = font[b"a"]
    app = QApplication(sys.argv)
    window = Window()
    #window.setGlyphs_(glyph)
    representationFactories.registerAllFactories()
    #window.setGlyph(font, "a")
    window.glyphsGrid[0].drawGlyphCell("a", font)
    #window.glyphsGrid.setShape(glyph.getRepresentation("defconQt.QPainterPath"))
    window.show()
    sys.exit(app.exec_())