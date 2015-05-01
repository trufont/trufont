from PyQt5.QtCore import QAbstractTableModel, QSize, Qt
from PyQt5.QtGui import (QBrush, QColor, QFont, QLinearGradient, QPainter,
        QPainterPath, QPalette, QPen)
from PyQt5.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QGridLayout, QLabel, QLineEdit,
        QMainWindow, QScrollArea, QTableView, QTableWidget, QTableWidgetItem, QVBoxLayout, QSizePolicy, QSpinBox, QToolBar, QWidget)

class MainSpaceWindow(QWidget):
    def __init__(self, font, string, pointSize=200, parent=None):
        super(MainSpaceWindow, self).__init__(parent)

        self.font = font
        self.string = string
        self.toolbar = FontToolBar(self.font, pointSize, self.string, self)
        self.canvas = GlyphsCanvas(self.font, self.string, pointSize, self)
        self.table = SpaceTable(self.font, self.string, self)
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        layout.addWidget(self.table)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        self.resize(600,500)

        self.setWindowTitle("Space center – " + self.font.info.familyName + " " + self.font.info.styleName)

    def setupFileMenu(self):
        fileMenu = QMenu("&File", self)
        self.menuBar().addMenu(fileMenu)

        fileMenu.addAction("&Save...", self.save, "Ctrl+S")
        fileMenu.addAction("E&xit", QApplication.instance().quit, "Ctrl+Q")

pointSizes = [50, 75, 100, 125, 150, 200, 250, 300, 350, 400, 450, 500]

class FontToolBar(QToolBar):
    def __init__(self, font, pointSize, string, parent=None):
        super(FontToolBar, self).__init__(parent)
        self.addWidget(QLineEdit(string))
        comboBox = QComboBox()
        comboBox.setEditable(True)
        for p in pointSizes:
            comboBox.addItem(str(p))
        comboBox.lineEdit().setText(str(pointSize))
        self.addWidget(comboBox)

class GlyphsCanvas(QWidget):
    def __init__(self, font, string, pointSize=150, parent=None):
        super(GlyphsCanvas, self).__init__(parent)

        self.font = font
        self.string = string

        self.ptSize = pointSize
        self.calculateScale(self.font, self.ptSize)
        self.padding = 12

    def calculateScale(self, font, ptSize):
        if font.info.unitsPerEm is None: return
        upm = font.info.unitsPerEm
        if not upm > 0: upm = 1000
        scale = ptSize / float(self.font.info.unitsPerEm)
        if scale < .01: scale = 0.01
        self.scale = scale
    
    # if we have a cell clicked in and we click on the canvas,
    # give focus to the canvas in order to quit editing
    def mousePressEvent(self, event):
        self.setFocus(Qt.MouseFocusReason)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(0, 0, self.width(), self.height(), Qt.white)
        painter.translate(self.padding, self.ptSize+self.font.info.descender*self.scale)

        cur_width = self.padding
        for c in self.string:
            if c not in self.font: continue
            # line wrapping
            if cur_width + self.font[c].width*self.scale + self.padding > self.width():
                painter.translate(-cur_width+self.padding, self.ptSize)
                cur_width = self.font[c].width*self.scale
            else:
                cur_width += self.font[c].width*self.scale
            glyph = self.font[c].getRepresentation("defconQt.QPainterPath")
            painter.save()
            painter.scale(self.scale, -self.scale)
            painter.fillPath(glyph, Qt.black)
            painter.restore()
            painter.translate(self.font[c].width*self.scale, 0)

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
        # always show a scrollbar to fix layout
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.resizeRowsToContents()
        self.setSizePolicy(QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed))
        self.fillGlyphs(self.font, self.glyphs)
        self.setEditTriggers(QAbstractItemView.CurrentChanged)

    def sizeHint(self):
        # http://stackoverflow.com/a/7216486/2037879
        height = sum(self.rowHeight(k) for k in range(self.rowCount()))
        height += self.horizontalScrollBar().height()
        margins = self.contentsMargins()
        height += margins.top() + margins.bottom()
        return QSize(self.width(), height)

    def fillGlyphs(self, font, glyphs):
        '''
        def glyphTableWidgetItem(content):
            item = QTableWidgetItem(content)
            item.setTextAlignment(Qt.AlignCenter)
            return item
        '''
        self.setColumnCount(len(glyphs)+1)
        dropped = 0
        for index, glyph in enumerate(glyphs):
            if glyph not in font: dropped += 1; continue
            # TODO: should glyph name edit really be permitted here?
            # TODO: also find glyphs by /name or should be abstracted by input area or main object?
            self.setItem(0, index-dropped+1, QTableWidgetItem(font[glyph].name))
            self.setItem(1, index-dropped+1, QTableWidgetItem(str(font[glyph].width)))
            self.setItem(2, index-dropped+1, QTableWidgetItem(str(font[glyph].leftMargin)))
            self.setItem(3, index-dropped+1, QTableWidgetItem(str(font[glyph].rightMargin)))
        self.setColumnCount(len(glyphs)+1-dropped)
    
    def wheelEvent(self, event):
        cur = self.horizontalScrollBar().value()
        self.horizontalScrollBar().setValue(cur - event.angleDelta().y() / 120)
        event.accept()

if __name__ == '__main__':

    import sys
# registerallfactories
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
