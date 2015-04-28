from PyQt5.QtCore import QAbstractTableModel, QSize, Qt
from PyQt5.QtGui import (QBrush, QColor, QFont, QLinearGradient, QPainter,
        QPainterPath, QPalette, QPen)
from PyQt5.QtWidgets import (QApplication, QComboBox, QGridLayout, QLabel,
        QMainWindow, QTableView, QTableWidget, QTableWidgetItem, QVBoxLayout, QSizePolicy, QSpinBox, QWidget)

class MainSpaceWindow(QWidget):
    def __init__(self, font, string, height=400, parent=None):
        super(MainSpaceWindow, self).__init__(parent)

        self.height = height
        self.font = font
        self.string = string
        self.canvas = GlyphsCanvas(self.font, self.string, self.height, self)
        self.resize(600,500)
        self.table = SpaceTable(self.font, self.string, self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.setWindowTitle("Space center")

    def setupFileMenu(self):
        fileMenu = QMenu("&File", self)
        self.menuBar().addMenu(fileMenu)

        fileMenu.addAction("&Save...", self.save, "Ctrl+S")
        fileMenu.addAction("E&xit", QApplication.instance().quit, "Ctrl+Q")

class GlyphsCanvas(QWidget):
    def __init__(self, font, string, height, parent=None):
        super(GlyphsCanvas, self).__init__(parent)

        self.font = font
        self.string = string

        self.height = height
        self.width = 500
        self.padding = 30

    '''
    def minimumSizeHint(self):
        return QSize(50, 50)
    '''

    def sizeHint(self):
        return QSize(self.width, self.height)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if self.font.info.unitsPerEm is None: return
        if not self.font.info.unitsPerEm > 0: self.font.info.unitsPerEm = 1000
        factor = self.height/(self.font.info.unitsPerEm*(1+2*.125))
        painter.save()
        painter.translate(self.padding, self.height+self.font.info.descender*factor)

        width = 0
        for c in self.string:
            if c not in self.font: continue
            glyph = self.font[c].getRepresentation("defconQt.QPainterPath")
            painter.save()
            painter.scale(factor, -factor)
            painter.fillPath(glyph, Qt.black)
            painter.restore()
            painter.translate(self.font[c].width*factor, 0)
            width += self.font[c].width*factor
        painter.restore()
        self.width = width
#        painter.fillRect(0, 0, width, self.height, Qt.white)
#        self.sizeHint(offset) whatever

    '''
        painter.setPen(
                QPen(self.penColor, self.penWidth, Qt.SolidLine, Qt.RoundCap,
                        Qt.RoundJoin))
        gradient = QLinearGradient(0, 0, 0, 100)
        gradient.setColorAt(0.0, self.fillColor1)
        gradient.setColorAt(1.0, self.fillColor2)
        painter.setBrush(QBrush(gradient))
        painter.drawPath(self.path)
    '''

class SpaceTable(QTableWidget):
    def __init__(self, font, glyphs="", parent=None):
        self.font = font
        self.glyphs = glyphs
        super(SpaceTable, self).__init__(4, len(self.glyphs), parent)
        data = [None, "Width", "Left", "Right"]
        for index, item in enumerate(data):
            cell = QTableWidgetItem(item)
            # don't set ItemIsEditable
            cell.setFlags(Qt.ItemIsEnabled)
            self.setItem(index, 0, cell)
        self.horizontalHeader().hide()
        self.verticalHeader().hide()
        self.fillGlyphs(self.font, self.glyphs)

    """
    # Does not seem to work...
    def maximumSizeHint(self):
        return QSize(None, self.rowHeight(0)*4)
    """

    def fillGlyphs(self, font, glyphs):
        self.setColumnCount(len(glyphs)+1)
        dropped = 0
        for index, glyph in enumerate(glyphs):
            if glyph not in font: dropped += 1; continue
            self.setItem(0, index+1, QTableWidgetItem(font[glyph].name)) # also find glyph by name or abstracted by input area?
            self.setItem(1, index+1, QTableWidgetItem(str(font[glyph].width)))
            self.setItem(2, index+1, QTableWidgetItem(str(font[glyph].leftMargin)))
            self.setItem(3, index+1, QTableWidgetItem(str(font[glyph].rightMargin)))
        self.setColumnCount(len(glyphs)+1-dropped)

if __name__ == '__main__':

    import sys
# registerallfactories
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
