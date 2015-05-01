import math
import os
import representationFactories
import unicodedata

from defcon import Font
from PyQt5.QtCore import pyqtSignal, QSize, Qt
from PyQt5.QtGui import (QClipboard, QFont, QFontDatabase, QFontMetrics,
        QIcon, QPainter)
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialogButtonBox, QFileDialog, QFontComboBox,
        QFrame, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QMenu, QPushButton,
        QScrollArea, QTabWidget, QToolTip, QVBoxLayout, QWidget)

glyphSortDescriptors = [
    dict(type="alphabetical", allowPseudoUnicode=True),
    dict(type="category", allowPseudoUnicode=True),
    dict(type="unicode", allowPseudoUnicode=True),
    dict(type="script", allowPseudoUnicode=True),
    dict(type="suffix", allowPseudoUnicode=True),
    dict(type="decompositionBase", allowPseudoUnicode=True)
]

class CharacterWidget(QWidget):
    #characterSelected = pyqtSignal(str)

    def __init__(self, font, parent=None):
        super(CharacterWidget, self).__init__(parent)

        self.font = font
        self.glyphs = [font[k] for k in font.unicodeData.sortGlyphNames(font.keys(), glyphSortDescriptors)]
        self.squareSize = 48
        self.columns = 11
        self.lastKey = -1
        self.setMouseTracking(True)
        self.col = Qt.red

    def updateFont(self, font):
        self.font = font
#        self.squareSize = max(24, QFontMetrics(self.displayFont).xHeight() * 3)
#        self.adjustSize()
        self.glyphs = [font[k] for k in font.unicodeData.sortGlyphNames(font.keys(), glyphSortDescriptors)]
        self.update()

    def updateSize(self, squareSize):
        self.squareSize = squareSize
        self.adjustSize() # Is this needed? The goal is to fit the cells to the widget, not the other way around
        self.update()

    def sizeHint(self):
        # TODO: adding 2 to glyphlen is cheating, need to find how to properly compensate y_offset
        # But why does it even have to be? Does Qt take the origin the painting as the basis for size calculation? Likely...
        return QSize(self.columns * self.squareSize,
                (len(self.glyphs)+2) / self.columns * self.squareSize)

    def mouseMoveEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            widgetPosition = self.mapFromGlobal(event.globalPos())
            key = (widgetPosition.y() // self.squareSize) * self.columns + widgetPosition.x() // self.squareSize
            uni = self.glyphs[key].unicode
            char = chr(self.glyphs[key].unicode) if uni is not None else "?"

            # http://stackoverflow.com/questions/6598554/is-there-any-way-to-insert-qpixmap-object-in-html
            text = '<p align="center" style="font-size: 36pt; font-family: %s">%s</p>' % (QFont().family(), char)
            if uni is not None:
                text += '<p>U+%04x<p>' % self.glyphs[key].unicode
            QToolTip.showText(event.globalPos(), text, self)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.lastKey = (event.y() // self.squareSize) * self.columns + event.x() // self.squareSize
            #key_ch = self._chr(self.lastKey)
            self.col = Qt.red

            """
            if unicodedata.category(key_ch) != 'Cn':
                self.characterSelected.emit(key_ch)
            """
            self.update()
        else:
            super(CharacterWidget, self).mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.lastKey = (event.y() // self.squareSize) * self.columns + event.x() // self.squareSize
            #key_ch = self._chr(self.lastKey)
            self.col = Qt.green

            """
            if unicodedata.category(key_ch) != 'Cn':
                self.characterSelected.emit(key_ch)
            """
            self.update()
        else:
            super(CharacterWidget, self).mousePressEvent(event)

    '''
    def resizeEvent(self, event):
        self.columns = event.rect().right() // self.squareSize
    '''

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(event.rect(), Qt.white)

        redrawRect = event.rect()
        beginRow = redrawRect.top() // self.squareSize
        endRow = redrawRect.bottom() // self.squareSize
        beginColumn = redrawRect.left() // self.squareSize
        endColumn = redrawRect.right() // self.squareSize

        painter.setPen(Qt.gray)
        for row in range(beginRow, endRow + 1):
            for column in range(beginColumn, endColumn + 1):
                painter.drawRect(column * self.squareSize,
                        row * self.squareSize, self.squareSize,
                        self.squareSize)

        for row in range(beginRow, endRow + 1):
            for column in range(beginColumn, endColumn + 1):
                key = row * self.columns + column

                if key == self.lastKey:
                    painter.fillRect(column * self.squareSize + 1,
                            row * self.squareSize + 1, self.squareSize - 2,
                            self.squareSize - 2, self.col)

                if key > len(self.glyphs)-1: break
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
        self.scrollArea = QScrollArea()
        self.characterWidget = CharacterWidget(self.font)
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

        self.setCentralWidget(self.scrollArea)
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
            self.glyphViewWindow = MainGfxWindow(self.font["a"], self)
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
    window = MainWindow(Font("C:\\Veloce.ufo"))
    window.resize(565, 430)
    window.show()
    sys.exit(app.exec_())
