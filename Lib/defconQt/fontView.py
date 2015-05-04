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

class CharacterWidget(QWidget):
    characterSelected = pyqtSignal(int, str)
    glyphOpened = pyqtSignal(str)

    def __init__(self, font, squareSize=48, scrollArea=None, parent=None):
        super(CharacterWidget, self).__init__(parent)

        self.font = font
        self.glyphs = [font[k] for k in font.unicodeData.sortGlyphNames(font.keys(), glyphSortDescriptors)]
        self.scrollArea = scrollArea
        self.squareSize = squareSize
        self.columns = 11
        self.lastKey = -1
        self.moveKey = -1
        #self.setMouseTracking(True)
        self.col = QColor.fromRgbF(.2, .3, .7, .15)

    def updateFont(self, font):
        self.font = font
        self.glyphs = [font[k] for k in font.unicodeData.sortGlyphNames(font.keys(), glyphSortDescriptors)]
        self.update()

    def _sizeEvent(self, width, squareSize=None):
        # TODO: Still some horizontal scrollbar appearing, should disable it entirely
        if self.scrollArea is not None: sw = self.scrollArea.verticalScrollBar().width() + self.scrollArea.contentsMargins().right()
        else: sw = 0
        if squareSize is not None: self.squareSize = squareSize
        columns = (width - sw) // self.squareSize
        if not columns > 0: return
        self.columns = columns
        self.adjustSize()
        #super(CharacterWidget, self).resizeEvent(event)

    def sizeHint(self):
        return QSize(self.columns * self.squareSize,
                math.ceil(len(self.glyphs) / self.columns) * self.squareSize)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.lastKey = (event.y() // self.squareSize) * self.columns + event.x() // self.squareSize
            self.moveKey = -1
            if self.lastKey > len(self.glyphs)-1: return
            
            self.col = QColor.fromRgbF(.2, .3, .7, .15)
            uniValue = self.glyphs[self.lastKey].unicode
            showName = uniValue is None or unicodedata.category(chr(uniValue)) == 'Zs'
            self.characterSelected.emit(1, chr(uniValue) if not showName else self.glyphs[self.lastKey].name)
            event.accept()
            self.update()
        else:
            super(CharacterWidget, self).mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            moveKey = (event.y() // self.squareSize) * self.columns + event.x() // self.squareSize
            event.accept()
            if (moveKey == self.lastKey and self.moveKey != -1):
                self.moveKey = -1
                # code duplication :(
                uniValue = self.glyphs[self.lastKey].unicode
                showName = uniValue is None or unicodedata.category(chr(uniValue)) == 'Zs'
                self.characterSelected.emit(1, chr(uniValue) if not showName else self.glyphs[self.lastKey].name)
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
            key = (event.y() // self.squareSize) * self.columns + event.x() // self.squareSize
            if key != self.lastKey: return
            event.accept()
            self.glyphOpened.emit(self.glyphs[key].name)
        else:
            super(CharacterWidget, self).mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(event.rect(), Qt.white)

        redrawRect = event.rect()
        beginRow = redrawRect.top() // self.squareSize
        endRow = redrawRect.bottom() // self.squareSize
        beginColumn = redrawRect.left() // self.squareSize
        endColumn = redrawRect.right() // self.squareSize
        
        painter.drawLine(redrawRect.left(), redrawRect.top(), redrawRect.left(), redrawRect.bottom())
        painter.drawLine(0, 0, redrawRect.right(), 0)

        # selection code
        firstKey = min(self.lastKey, self.moveKey)
        lastKey = max(self.lastKey, self.moveKey)
        minKeyInViewport = beginRow * self.columns + beginColumn
        select = False
        if firstKey != -1 and firstKey < minKeyInViewport and lastKey > minKeyInViewport:
            select = True

        painter.setPen(Qt.gray)
        for row in range(beginRow, endRow + 1):
            for column in range(beginColumn, endColumn + 1):
                key = row * self.columns + column
                if key > len(self.glyphs)-1: break

                rightEdgeX = column * self.squareSize + self.squareSize
                bottomEdgeY = row * self.squareSize + self.squareSize
                painter.drawLine(rightEdgeX, row * self.squareSize + 1, rightEdgeX, bottomEdgeY)
                painter.drawLine(rightEdgeX, bottomEdgeY, column * self.squareSize + 1, bottomEdgeY)

                # selection code
                if key == firstKey:
                    select = not select
                if select or (key == self.lastKey and self.moveKey == -1):
                    painter.fillRect(column * self.squareSize + 1,
                            row * self.squareSize + 1, self.squareSize - 2,
                            self.squareSize - 2, self.col)
                    if key == lastKey and self.moveKey != -1:
                        select = not select

                glyph = self.glyphs[key].getRepresentation("defconQt.QPainterPath")
                if self.font.info.unitsPerEm is None: break
                if not self.font.info.unitsPerEm > 0: self.font.info.unitsPerEm = 1000
                factor = self.squareSize/(self.font.info.unitsPerEm*(1+2*.125))
                x_offset = (self.squareSize-self.glyphs[key].width*factor)/2
                if x_offset < 0:
                    factor *= 1+2*x_offset/(self.glyphs[key].width*factor)
                    x_offset = 0
                y_offset = self.font.info.descender*factor
                painter.save()
                painter.translate(column * self.squareSize + x_offset, row * self.squareSize + self.squareSize + y_offset)
                painter.scale(factor, -factor)
                painter.fillPath(glyph, Qt.black)
                painter.restore()
        

class MainWindow(QMainWindow):
    def __init__(self, font=Font()):
        super(MainWindow, self).__init__()

        self.font = font
        # TODO: have the scrollarea be part of the widget itself?
        # or better yet, switch to QGraphicsScene
        self.scrollArea = QScrollArea()
        squareSize = 48
        self.characterWidget = CharacterWidget(self.font, squareSize, self.scrollArea, self)
        self.scrollArea.setWidget(self.characterWidget)

        # TODO: make shortcuts platform-independent
        # TODO: work out sensible shortcuts
        fileMenu = QMenu("&File", self)
        self.menuBar().addMenu(fileMenu)

        fileMenu.addAction("&New...", self.newFile, "Ctrl+N")
        fileMenu.addAction("&Open...", self.openFile, "Ctrl+O")
        # TODO: add functionality
        #fileMenu.addMenu(QMenu("Open &Recent...", self))
        fileMenu.addSeparator()
        fileMenu.addAction("&Save", self.saveFile, "Ctrl+S")
        fileMenu.addAction("Save &As...", self.saveFileAs, "Ctrl+Shift+S")
        fileMenu.addAction("E&xit", self.saveAndExit, "Ctrl+Q")

        fontMenu = QMenu("&Font", self)
        self.menuBar().addMenu(fontMenu)

        fontMenu.addAction("Font &info", self.fontInfo, "Ctrl+I")
        fontMenu.addAction("Font &features", self.fontFeatures, "Ctrl+F")
        fontMenu.addSeparator()
        fontMenu.addAction("&Space center", self.spaceCenter, "Ctrl+Y")
        fontMenu.addAction("&Glyph view", self.glyphView, "Ctrl+G")

        helpMenu = QMenu("&Help", self)
        self.menuBar().addMenu(helpMenu)

        helpMenu.addAction("&About", self.about)
        helpMenu.addAction("About &Qt", QApplication.instance().aboutQt)
        
        self.sqSizeSlider = QSlider(Qt.Horizontal)
        self.sqSizeSlider.setMinimum(24)
        self.sqSizeSlider.setMaximum(96)
        #sz = self.sqSizeSlider.sizeHint()
        #self.sqSizeSlider.setSize(.7*sz.width(), sz.height())
        self.sqSizeSlider.setValue(squareSize)
        self.sqSizeSlider.sliderMoved.connect(self._tipValue)
        self.sqSizeSlider.valueChanged.connect(self._squareSizeChanged)
        self.selectionLabel = QLabel()
        self.selectionLabel.setFixedWidth(self.selectionLabel.fontMetrics().width('M') * 15)
        self.characterWidget.characterSelected.connect(self._selectionChanged)
        self.statusBar().addPermanentWidget(self.sqSizeSlider)
        self.statusBar().addWidget(self.selectionLabel)

        self.setCentralWidget(self.scrollArea)
        self.characterWidget.glyphOpened.connect(self._glyphOpened)
        self.setWindowTitle(os.path.basename(self.font.path.rstrip(os.sep)))
        # TODO: dump the hardcoded path
        self.setWindowIcon(QIcon("C:\\Users\\Adrien\\Downloads\\defconQt\\Lib\\defconQt\\resources\\icon.png"));

    def newFile(self):
        self.font = Font()
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

    def saveFile(self, path=None):
        self.font.save(path=path)
#        self.font.path = path # done by defcon

    def saveFileAs(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save File", '',
                "UFO Fonts (*.ufo)")
        print(path)
        self.saveFile(path)
    
    def saveAndExit(self):
        # TODO: check if font changed
        QApplication.instance().quit()
    
    def _tipValue(self):
        text = str(self.sqSizeSlider.value())
        QToolTip.showText(QCursor.pos(), text, self)
    
    def _glyphOpened(self, name):
        from svgViewer import MainGfxWindow
        self.glyphViewWindow = MainGfxWindow(self.font, self.font[name], self)
        self.glyphViewWindow.show()
    
    def _selectionChanged(self, count, glyph):
        self.selectionLabel.setText("%s%s%s%d %s" % (glyph, " " if count <= 1 else "", "(", count, "selected)"))

    def _squareSizeChanged(self):
        self.characterWidget._sizeEvent(self.width(), self.sqSizeSlider.value())

    def resizeEvent(self, event):
        if self.isVisible(): self.characterWidget._sizeEvent(event.size().width())
        super(MainWindow, self).resizeEvent(event)

    def fontInfo(self):
        # If a window is already opened, bring it to the front, else make another one.
        # TODO: see about calling super from the widget and del'eting the ptr to the widget
        # otherwise it doesn't get swept?
        # Else we can just play with visibility instead of respawning, given that the window
        # is still valid by its ref after it's been closed
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
        from spaceCenter import MainSpaceWindow
        if not (hasattr(self, 'spaceCenterWindow') and self.spaceCenterWindow.isVisible()):
            # XXX: window collapses when passing self as parent...
            self.spaceCenterWindow = MainSpaceWindow(self.font, "Hiyazee otaHawa.")
            self.spaceCenterWindow.show()
        else:
            self.spaceCenterWindow.raise_()

    def glyphView(self):
        # TODO: see up here
        from svgViewer import MainGfxWindow
        if not (hasattr(self, 'glyphViewWindow') and self.glyphViewWindow.isVisible()):
            # XXX: window collapses when passing self as parent...
            self.glyphViewWindow = MainGfxWindow(self.font, self.font["a"], self)
            self.glyphViewWindow.show()
        else:
            self.glyphViewWindow.raise_()

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
    window = MainWindow(Font("C:\\CharterNova-Regular.ufo"))
    window.resize(565, 430)
    window.show()
    sys.exit(app.exec_())
