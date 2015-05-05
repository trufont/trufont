from PyQt5.QtCore import QAbstractTableModel, QSize, Qt
from PyQt5.QtGui import (QBrush, QColor, QFont, QLinearGradient, QPainter,
        QPainterPath, QPalette, QPen)
from PyQt5.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QGridLayout, QLabel, QLineEdit,
        QMainWindow, QScrollArea, QTableView, QTableWidget, QTableWidgetItem, QVBoxLayout, QSizePolicy, QSpinBox, QToolBar, QWidget)

defaultPointSize = 150

class MainSpaceWindow(QWidget):
    def __init__(self, font, string="Hello World", pointSize=defaultPointSize, parent=None):
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
        self.toolbar.comboBox.currentIndexChanged[str].connect(self.canvas._pointSizeChanged)
        self.toolbar.textField.textEdited.connect(self.canvas._textChanged)
        self.toolbar.textField.textEdited.connect(self.table._textChanged)
        self.table.cellChanged.connect(self.canvas._metricsChanged)

        self.setWindowTitle("%s%s%s%s" % ("Space center – ", self.font.info.familyName, " ", self.font.info.styleName))

    def setupFileMenu(self):
        fileMenu = QMenu("&File", self)
        self.menuBar().addMenu(fileMenu)

        fileMenu.addAction("&Save...", self.save, "Ctrl+S")
        fileMenu.addAction("E&xit", QApplication.instance().quit, "Ctrl+Q")

pointSizes = [50, 75, 100, 125, 150, 200, 250, 300, 350, 400, 450, 500]

class FontToolBar(QToolBar):
    def __init__(self, font, pointSize, string, parent=None):
        super(FontToolBar, self).__init__(parent)
        self.textField = QLineEdit(string)
        self.comboBox = QComboBox()
        self.comboBox.setEditable(True)
        # Should I allow this? What does robofont do here?
        #self.comboBox.setInsertPolicy(QComboBox.NoInsert)
        for p in pointSizes:
            self.comboBox.addItem(str(p))
        self.comboBox.lineEdit().setText(str(pointSize))

        self.addWidget(self.textField)
        self.addWidget(self.comboBox)

class GlyphsCanvas(QWidget):
    def __init__(self, font, string, pointSize=defaultPointSize, parent=None):
        super(GlyphsCanvas, self).__init__(parent)

        self.font = font
        self.string = string

        self.ptSize = pointSize
        self.calculateScale()
        self.padding = 10

    def calculateScale(self):
        if self.font.info.unitsPerEm is None: return
        upm = self.font.info.unitsPerEm
        if not upm > 0: upm = 1000
        scale = self.ptSize / float(self.font.info.unitsPerEm)
        if scale < .01: scale = 0.01
        self.scale = scale
    
    def _pointSizeChanged(self, pointSize):
        self.ptSize = int(pointSize)
        self.calculateScale()
        self.update()
    
    def _textChanged(self, newText):
        self.string = newText
        self.update()
    
    def _metricsChanged(self, row, col):
        item = int(self.parent().table.item(row, col).text())
        # TODO: update width on the QTableWidget when sidebearing changes.
        # stop passing signals and use defcon notificationHandler instead
        # -1 because the first col contains descriptive text
        glyph = self.font.unicodeData.glyphNameForUnicode(ord(self.string[col-1]))
        if row == 1:
            self.font[glyph].width = item
        elif row == 2:
            self.font[glyph].leftMargin = item
        elif row == 3:
            self.font[glyph].rightMargin = item
        self.update()
    
    # if we have a cell clicked in and we click on the canvas,
    # give focus to the canvas in order to quit editing
    # TODO: Focus on individual chars and show BBox + active cell (see how rf does active cells)
    # QTableWidget.scrollToItem()
    def mousePressEvent(self, event):
        self.setFocus(Qt.MouseFocusReason)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(0, 0, self.width(), self.height(), Qt.white)
        # TODO: should padding be added for the right boundary as well? I'd say no but not sure
        painter.translate(self.padding, self.padding+self.ptSize+self.font.info.descender*self.scale)

        cur_width = 0
        for c in self.string:
            glyph = self.font.unicodeData.glyphNameForUnicode(ord(c))
            if glyph not in self.font: continue
            # line wrapping
            if cur_width + self.font[glyph].width*self.scale + self.padding > self.width():
                painter.translate(-cur_width, self.ptSize)
                cur_width = self.font[glyph].width*self.scale
            else:
                cur_width += self.font[glyph].width*self.scale
            glyphPath = self.font[glyph].getRepresentation("defconQt.QPainterPath")
            painter.save()
            painter.scale(self.scale, -self.scale)
            painter.fillPath(glyphPath, Qt.black)
            painter.restore()
            painter.translate(self.font[glyph].width*self.scale, 0)

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
    def __init__(self, font, string="", parent=None):
        self.font = font
        self.string = string
        super(SpaceTable, self).__init__(4, len(self.string), parent)
        data = [None, "Width", "Left", "Right"]
        for index, item in enumerate(data):
            cell = QTableWidgetItem(item)
            # don't set ItemIsEditable
            cell.setFlags(Qt.ItemIsEnabled)
            self.setItem(index, 0, cell)
        # let's use this one column to compute the width of others
        self._cellWidth = .7*self.columnWidth(0)
        self.setColumnWidth(0, .6*self.columnWidth(0))
        self.horizontalHeader().hide()
        self.verticalHeader().hide()

        # always show a scrollbar to fix layout
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.resizeRowsToContents()
        self.setSizePolicy(QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed))
        self.fillGlyphs()
        # edit cell on single click, not double
        self.setEditTriggers(QAbstractItemView.CurrentChanged)
        # TODO: insvestigate changing cell color as in robofont
        # http://stackoverflow.com/a/13926342/2037879

    def _textChanged(self, newText):
        self.string = newText
        # TODO: we don't need to reallocate cells, split alloc and fill
        self.fillGlyphs()

    def sizeHint(self):
        # http://stackoverflow.com/a/7216486/2037879
        height = sum(self.rowHeight(k) for k in range(self.rowCount()))
        height += self.horizontalScrollBar().height()
        margins = self.contentsMargins()
        height += margins.top() + margins.bottom()
        return QSize(self.width(), height)

    def fillGlyphs(self):
        def glyphTableWidgetItem(content, blockEdition=False):
            if content is not None: content = str(content)
            item = QTableWidgetItem(content)
            if content is None or blockEdition:
                # don't set ItemIsEditable
                item.setFlags(Qt.ItemIsEnabled)
            # TODO: also set alignment during edition
            # or leave it as it is now, is fine by me...
            #item.setTextAlignment(Qt.AlignCenter)
            return item

        self.setColumnCount(len(self.string)+1)
        dropped = 0
        for index, char in enumerate(self.string):
            glyph = self.font.unicodeData.glyphNameForUnicode(ord(char))
            i = index-dropped+1
            if glyph not in self.font: dropped += 1; continue
            # TODO: should glyph name edit really be permitted here?
            # TODO: also find glyphs by /name or should be abstracted by input area or main object?
            self.setItem(0, i, glyphTableWidgetItem(self.font[glyph].name, True))
            self.setItem(1, i, glyphTableWidgetItem(self.font[glyph].width))
            self.setItem(2, i, glyphTableWidgetItem(self.font[glyph].leftMargin))
            self.setItem(3, i, glyphTableWidgetItem(self.font[glyph].rightMargin))
            self.setColumnWidth(i, self._cellWidth)
        self.setColumnCount(len(self.string)+1-dropped)
        
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
