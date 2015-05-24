import math
import os
import representationFactories
import unicodedata

from defcon import Font
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

glyphSortDescriptors = [
    dict(type="alphabetical", allowPseudoUnicode=True),
    dict(type="category", allowPseudoUnicode=True),
    dict(type="unicode", allowPseudoUnicode=True),
    dict(type="script", allowPseudoUnicode=True),
    dict(type="suffix", allowPseudoUnicode=True),
    dict(type="decompositionBase", allowPseudoUnicode=True)
]

cellGridColor = QColor(130, 130, 130)
cellHeaderBaseColor = QColor(230, 230, 230)
cellHeaderLineColor = QColor(220, 220, 220)
cellHeaderHighlightLineColor = QColor(240, 240, 240)
cellSelectionColor = QColor.fromRgbF(.2, .3, .7, .15)

GlyphCellBufferHeight = .2
GlyphCellHeaderHeight = 14

class CharacterWidget(QWidget):
    characterSelected = pyqtSignal(int, str)
    glyphOpened = pyqtSignal(str)

    def __init__(self, font, squareSize=56, scrollArea=None, parent=None):
        super(CharacterWidget, self).__init__(parent)

        self.font = font
        self.glyphs = [font[k] for k in font.unicodeData.sortGlyphNames(font.keys(), glyphSortDescriptors)]
        self.scrollArea = scrollArea
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.squareSize = squareSize
        self.columns = 10
        self.lastKey = -1
        self.moveKey = -1
        #self.setMouseTracking(True)

    def updateFont(self, font):
        self.font = font
        self.glyphs = [font[k] for k in font.unicodeData.sortGlyphNames(font.keys(), glyphSortDescriptors)]
        self.adjustSize()
        self.update()
    
    def updateGlyphs(self):
        self.glyphs = [self.font[k] for k in self.font.unicodeData.sortGlyphNames(self.font.keys(), glyphSortDescriptors)]
        self.adjustSize()
        self.update()

    def _sizeEvent(self, width, squareSize=None):
        if self.scrollArea is not None: sw = self.scrollArea.verticalScrollBar().width() + self.scrollArea.contentsMargins().right()
        else: sw = 0
        if squareSize is not None: self.squareSize = squareSize
        columns = (width - sw) // self.squareSize
        if not columns > 0: return
        self.columns = columns
        self.adjustSize()

    def sizeHint(self):
        return QSize(self.columns * self.squareSize,
                math.ceil(len(self.glyphs) / self.columns) * self.squareSize)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.lastKey = (event.y() // self.squareSize) * self.columns + event.x() // self.squareSize
            self.moveKey = -1
            if self.lastKey > len(self.glyphs)-1: return

            self.characterSelected.emit(1, self.glyphs[self.lastKey].name)
            event.accept()
            self.update()
        else:
            super(CharacterWidget, self).mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            moveKey = (event.y() // self.squareSize) * self.columns + min(event.x() // self.squareSize, self.columns-1)
            event.accept()
            if (moveKey == self.lastKey and self.moveKey != -1):
                self.moveKey = -1
                self.characterSelected.emit(1, self.glyphs[self.lastKey].name)
            elif moveKey > len(self.glyphs)-1 \
                or not (moveKey != self.lastKey and moveKey != self.moveKey): return
            else:
                self.moveKey = moveKey
                self.characterSelected.emit(abs(self.moveKey - self.lastKey)+1, "")
            self.update()
        # elif event.modifiers() & Qt.ControlModifier:
            # widgetPosition = self.mapFromGlobal(event.globalPos())
            # key = (widgetPosition.y() // self.squareSize) * self.columns + widgetPosition.x() // self.squareSize
            # uni = self.glyphs[key].unicode
            # char = chr(self.glyphs[key].unicode) if uni is not None else chr(0xFFFD)

            # # http://stackoverflow.com/questions/6598554/is-there-any-way-to-insert-qpixmap-object-in-html
            # text = '<p align="center" style="font-size: 36pt; font-family: %s">%s</p>' % (QFont().family(), char)
            # if uni is not None:
                # more = ['<p>U+%04x<p>' % self.glyphs[key].unicode, '<p>%s<p>' % unicodedata.name(chr(self.glyphs[key].unicode))]
                # text = text.join(more)
            # QToolTip.showText(event.globalPos(), text, self)
        else:
            super(CharacterWidget, self).mouseMoveEvent(event)
   
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            key = (event.y() // self.squareSize) * self.columns + min(event.x() // self.squareSize, self.columns-1)
            if key != self.lastKey: return
            event.accept()
            self.glyphOpened.emit(self.glyphs[key].name)
        else:
            super(CharacterWidget, self).mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        redrawRect = event.rect()
        beginRow = redrawRect.top() // self.squareSize
        endRow = redrawRect.bottom() // self.squareSize
        beginColumn = redrawRect.left() // self.squareSize
        endColumn = redrawRect.right() // self.squareSize
        
        painter.setPen(cellGridColor)
        painter.drawLine(redrawRect.left(), redrawRect.top(), redrawRect.left(), redrawRect.bottom())
        painter.drawLine(0, 0, redrawRect.right(), 0)

        # selection code
        firstKey = min(self.lastKey, self.moveKey)
        lastKey = max(self.lastKey, self.moveKey)
        minKeyInViewport = beginRow * self.columns + beginColumn
        select = False
        if firstKey != -1 and firstKey < minKeyInViewport and lastKey > minKeyInViewport:
            select = True
            
        gradient = QLinearGradient(0, 0, 0, GlyphCellHeaderHeight)
        gradient.setColorAt(0.0, cellHeaderBaseColor)
        gradient.setColorAt(1.0, cellHeaderLineColor)

        for row in range(beginRow, endRow + 1):
            for column in range(beginColumn, endColumn + 1):
                key = row * self.columns + column
                if key > len(self.glyphs)-1: break

                painter.save()
                painter.translate(column * self.squareSize, row * self.squareSize)
                # background
                painter.fillRect(0, 0, self.squareSize, self.squareSize, Qt.white)
                # header gradient
                painter.fillRect(0, 0, self.squareSize,
                      GlyphCellHeaderHeight, QBrush(gradient))
                # header lines
                painter.setPen(cellHeaderHighlightLineColor)
                minOffset = painter.pen().width()
                painter.setRenderHint(QPainter.Antialiasing, False)
                painter.drawLine(0, 0, 0, GlyphCellHeaderHeight - 1)
                painter.drawLine(self.squareSize - 2, 0, self.squareSize - 2, GlyphCellHeaderHeight -1)
                painter.setPen(QColor(170, 170, 170))
                painter.drawLine(0, GlyphCellHeaderHeight, self.squareSize, GlyphCellHeaderHeight)
                painter.setRenderHint(QPainter.Antialiasing)
                # header text
                headerFont = QFont()
                headerFont.setFamily('Lucida Sans Unicode')
                painter.setFont(headerFont)
                painter.setPen(QColor(80, 80, 80))
                metrics = QFontMetrics(headerFont)
                name = metrics.elidedText(self.glyphs[key].name, Qt.ElideRight, self.squareSize - 2)
                painter.drawText(1, 0, self.squareSize - 2, GlyphCellHeaderHeight - minOffset,
                      Qt.TextSingleLine | Qt.AlignCenter, name)
                painter.restore()

                painter.setPen(cellGridColor)
                rightEdgeX = column * self.squareSize + self.squareSize
                bottomEdgeY = row * self.squareSize + self.squareSize
                painter.drawLine(rightEdgeX, row * self.squareSize + 1, rightEdgeX, bottomEdgeY)
                painter.drawLine(rightEdgeX, bottomEdgeY, column * self.squareSize + 1, bottomEdgeY)

                painter.setRenderHint(QPainter.Antialiasing, False)
                # selection code
                if key == firstKey:
                    select = not select
                if select or (key == self.lastKey and self.moveKey == -1):
                    painter.fillRect(column * self.squareSize + 1,
                            row * self.squareSize + 1, self.squareSize - 3,
                            self.squareSize - 3, cellSelectionColor)
                    if key == lastKey and self.moveKey != -1:
                        select = not select
                painter.setRenderHint(QPainter.Antialiasing)

                glyph = self.glyphs[key].getRepresentation("defconQt.QPainterPath")
                if self.font.info.unitsPerEm is None: break
                if not self.font.info.unitsPerEm > 0: self.font.info.unitsPerEm = 1000
                factor = (self.squareSize-GlyphCellHeaderHeight)/(self.font.info.unitsPerEm*(1+2*GlyphCellBufferHeight))
                x_offset = (self.squareSize-self.glyphs[key].width*factor)/2
                # If the glyph overflows horizontally we need to adjust the scaling factor
                if x_offset < 0:
                    factor *= 1+2*x_offset/(self.glyphs[key].width*factor)
                    x_offset = 0
                # TODO: the * 1.8 below is somewhat artificial
                y_offset = self.font.info.descender*factor * 1.8
                painter.save()
                painter.setClipRect(column * self.squareSize, row * self.squareSize+GlyphCellHeaderHeight,
                      self.squareSize, self.squareSize-GlyphCellHeaderHeight)
                painter.translate(column * self.squareSize + x_offset, row * self.squareSize + self.squareSize + y_offset)
                painter.scale(factor, -factor)
                painter.fillPath(glyph, Qt.black)
                painter.restore()

class MainWindow(QMainWindow):
    def __init__(self, font=Font()):
        super(MainWindow, self).__init__()

        self.font = font
        self.font.addObserver(self, "_fontChanged", "Font.Changed")
        # TODO: have the scrollarea be part of the widget itself?
        # or better yet, switch to QGraphicsScene
        self.scrollArea = QScrollArea(self)
        squareSize = 56
        self.characterWidget = CharacterWidget(self.font, squareSize, self.scrollArea, self)
        self.scrollArea.setWidget(self.characterWidget)

        # TODO: make shortcuts platform-independent
        fileMenu = QMenu("&File", self)
        self.menuBar().addMenu(fileMenu)

        fileMenu.addAction("&New…", self.newFile, QKeySequence.New)
        fileMenu.addAction("&Open…", self.openFile, QKeySequence.Open)
        # TODO: add functionality
        #fileMenu.addMenu(QMenu("Open &Recent...", self))
        fileMenu.addSeparator()
        fileMenu.addAction("&Save", self.saveFile, QKeySequence.Save)
        fileMenu.addAction("Save &As…", self.saveFileAs, QKeySequence.SaveAs)
        fileMenu.addAction("E&xit", self.close, QKeySequence.Quit)

        fontMenu = QMenu("&Font", self)
        self.menuBar().addMenu(fontMenu)

        # TODO: work out sensible shortcuts
        fontMenu.addAction("Font &info", self.fontInfo, "Ctrl+I")
        fontMenu.addAction("Font &features", self.fontFeatures, "Ctrl+F")
        fontMenu.addAction("&Add glyph", self.addGlyph, "Ctrl+U")
        fontMenu.addSeparator()
        fontMenu.addAction("&Space center", self.spaceCenter, "Ctrl+Y")

        helpMenu = QMenu("&Help", self)
        self.menuBar().addMenu(helpMenu)

        helpMenu.addAction("&About", self.about)
        helpMenu.addAction("About &Qt", QApplication.instance().aboutQt)
        
        self.sqSizeSlider = QSlider(Qt.Horizontal, self)
        self.sqSizeSlider.setMinimum(36)
        self.sqSizeSlider.setMaximum(96)
        self.sqSizeSlider.setFixedWidth(.9*self.sqSizeSlider.width())
        self.sqSizeSlider.setValue(squareSize)
        self.sqSizeSlider.valueChanged.connect(self._squareSizeChanged)
        self.selectionLabel = QLabel(self)
        self.characterWidget.characterSelected.connect(self._selectionChanged)
        self.statusBar().addPermanentWidget(self.sqSizeSlider)
        self.statusBar().addWidget(self.selectionLabel)

        self.setCentralWidget(self.scrollArea)
        self.characterWidget.glyphOpened.connect(self._glyphOpened)
        self.setWindowTitle()
        # TODO: dump the hardcoded path
        #self.setWindowIcon(QIcon("C:\\Users\\Adrien\\Downloads\\defconQt\\Lib\\defconQt\\resources\\icon.png"))

    def newFile(self):
        # TODO: ask for save before leaving
        self.font = Font()
        self.font.info.upm = 1000
        self.font.info.ascender = 750
        self.font.info.descender = -250
        self.font.info.capHeight = 750
        self.font.info.xHeight = 500
        self.setWindowTitle("Untitled.ufo")
        self.characterWidget.updateFont(self.font)

    def openFile(self, path=None):
        if not path:
            path, _ = QFileDialog.getOpenFileName(self, "Open File", '',
                    "UFO Fonts (metainfo.plist)")

        if path:
            # TODO: error handling
            path = os.path.dirname(path)
            self.font = Font(path)
            self.characterWidget.updateFont(self.font)
            self.setWindowTitle()

    def saveFile(self, path=None):
        self.font.save(path=path)
#        self.font.dirty = False
#        self.font.path = path # done by defcon

    def saveFileAs(self):
        path, ok = QFileDialog.getSaveFileName(self, "Save File", '',
                "UFO Fonts (*.ufo)")
        if ok:
            self.saveFile(path)
        #return ok
    
    def close(self):
        # TODO: check if font changed
        self.font.removeObserver(self, "Font.Changed")
        QApplication.instance().quit()
        
    def closeEvent(self, event):
        if self.font.dirty:
            closeDialog = QMessageBox(QMessageBox.Question, "Save your work?", "Will you save, dear",
                  QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, self)
            closeDialog.setModal(True)
            ret = closeDialog.exec_()
            if ret == QMessageBox.Yes:
                self.saveFile()
                event.accept()
            elif ret == QMessageBox.No:
                event.accept()
            elif ret == QMessageBox.Cancel:
                event.ignore()
    
    def _fontChanged(self, event):
        self.characterWidget.update()

    def _glyphOpened(self, name):
        from svgViewer import MainGfxWindow
        glyphViewWindow = MainGfxWindow(self.font, self.font[name], self)
        glyphViewWindow.setAttribute(Qt.WA_DeleteOnClose)
        glyphViewWindow.show()
    
    def _selectionChanged(self, count, glyph):
        self.selectionLabel.setText("%s%s%s%d %s" % (glyph, " " if count <= 1 else "", "(", count, "selected)"))

    def _squareSizeChanged(self):
        val = self.sqSizeSlider.value()
        self.characterWidget._sizeEvent(self.width(), val)
        QToolTip.showText(QCursor.pos(), str(val), self)

    def resizeEvent(self, event):
        if self.isVisible(): self.characterWidget._sizeEvent(event.size().width())
        super(MainWindow, self).resizeEvent(event)
    
    def setWindowTitle(self, title=None):
        if title is None: title = os.path.basename(self.font.path.rstrip(os.sep))
        super(MainWindow, self).setWindowTitle(title)

    def fontInfo(self):
        # If a window is already opened, bring it to the front, else spawn one.
        # TODO: see about using widget.setAttribute(Qt.WA_DeleteOnClose) otherwise
        # it seems we're just leaking memory after each close... (both raise_ and
        # show allocate memory instead of using the hidden widget it seems)
        from fontInfo import TabDialog
        if not (hasattr(self, 'fontInfoWindow') and self.fontInfoWindow.isVisible()):
           self.fontInfoWindow = TabDialog(self.font, self)
           self.fontInfoWindow.show()
        else:
           # Should data be rewind if user calls font info while one is open?
           # I'd say no, but this has yet to be settled.
           self.fontInfoWindow.raise_()

    def fontFeatures(self):
        # TODO: see up here
        from syntaxHighlighter import MainEditWindow
        if not (hasattr(self, 'fontFeaturesWindow') and self.fontFeaturesWindow.isVisible()):
           self.fontFeaturesWindow = MainEditWindow(self.font, self)
           self.fontFeaturesWindow.show()
        else:
           self.fontFeaturesWindow.raise_()

    def spaceCenter(self):
        # TODO: see up here
        # TODO: show selection in a space center, rewind selection if we raise window (rf)
        from spaceCenter import MainSpaceWindow
        if not (hasattr(self, 'spaceCenterWindow') and self.spaceCenterWindow.isVisible()):
            self.spaceCenterWindow = MainSpaceWindow(self.font, "Hiyazee otaHawa.", parent=self)
            self.spaceCenterWindow.show()
        else:
            self.spaceCenterWindow.raise_()
    
    def addGlyph(self):
        gName, ok = QInputDialog.getText(self, "Add glyph", "Name of the glyph:")
        # Not overwriting existing glyphs. Should it warn in this case? (rf)
        if ok and gName != '':
            self.font.newGlyph(gName)
            self.characterWidget.updateGlyphs()

    def about(self):
        QMessageBox.about(self, "About Me",
                "<h3>About Me</h3>" \
                "<p>I am a new UFO-centric font editor and I aim to bring the <b>robofab</b> " \
                "ecosystem to all main operating systems, in a fast and dependency-free " \
                "package.</p>")

if __name__ == '__main__':
    import sys

    #from pycallgraph import PyCallGraph
    #from pycallgraph.output import GraphvizOutput

    representationFactories.registerAllFactories()
    #with PyCallGraph(output=GraphvizOutput()):
    app = QApplication(sys.argv)
    # TODO: http://stackoverflow.com/a/21330349/2037879
    app.setWindowIcon(QIcon("C:\\Users\\Adrien\\Downloads\\defconQt\\Lib\\defconQt\\resources\\icon.png"))
    window = MainWindow(Font("C:\\CharterNova-Regular.ufo"))
    window.resize(605, 430)
    window.show()
    sys.exit(app.exec_())
