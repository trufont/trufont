#!/usr/bin/env python


#############################################################################
##
## Copyright (C) 2013 Riverbank Computing Limited.
## Copyright (C) 2010 Nokia Corporation and/or its subsidiary(-ies).
## All rights reserved.
##
## This file is part of the examples of PyQt.
##
## $QT_BEGIN_LICENSE:BSD$
## You may use this file under the terms of the BSD license as follows:
##
## "Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are
## met:
##   * Redistributions of source code must retain the above copyright
##     notice, this list of conditions and the following disclaimer.
##   * Redistributions in binary form must reproduce the above copyright
##     notice, this list of conditions and the following disclaimer in
##     the documentation and/or other materials provided with the
##     distribution.
##   * Neither the name of Nokia Corporation and its Subsidiary(-ies) nor
##     the names of its contributors may be used to endorse or promote
##     products derived from this software without specific prior written
##     permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
## "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
## LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
## A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
## OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
## SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
## LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
## DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
## THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
## (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
## OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
## $QT_END_LICENSE$
##
#############################################################################

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

    characterSelected = pyqtSignal(str)

    def __init__(self, font, parent=None):
        super(CharacterWidget, self).__init__(parent)

        self.font = font
        self.glyphs = [font[k] for k in font.unicodeData.sortGlyphNames(font.keys(), glyphSortDescriptors)]
        self.squareSize = 48
        self.columns = 11
        self.lastKey = -1
#        self.setMouseTracking(True)
        self.col = Qt.red

    def updateFont(self, font):
        self.font = font
#        self.squareSize = max(24, QFontMetrics(self.displayFont).xHeight() * 3)
#        self.adjustSize()
        self.glyphs = [font[k] for k in font.unicodeData.sortGlyphNames(font.keys(), glyphSortDescriptors)]
        self.update()

    def updateSize(self, squareSize):
#        fontSize, _ = fontSize.toInt()
#        self.displayFont.setPointSize(int(fontSize))
        self.squareSize = squareSize
        self.adjustSize()
        self.update()

    def sizeHint(self):
        # TODO: adding 2 to glyphlen is cheating, need to find how to properly compensate x_offset
        return QSize(self.columns * self.squareSize,
                (len(self.glyphs)+2) / self.columns * self.squareSize)

    '''
    def mouseMoveEvent(self, event):
        widgetPosition = self.mapFromGlobal(event.globalPos())
        key = (widgetPosition.y() // self.squareSize) * self.columns + widgetPosition.x() // self.squareSize

        # http://stackoverflow.com/questions/6598554/is-there-any-way-to-insert-qpixmap-object-in-html
        text = '<p>Character: <span style="font-size: 24pt; font-family: %s">%s</span><p>Value: 0x%x' % (QFont().family(), self._chr(key), key)
        QToolTip.showText(event.globalPos(), text, self)
    '''

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.lastKey = (event.y() // self.squareSize) * self.columns + event.x() // self.squareSize
            key_ch = self._chr(self.lastKey)
            self.col = Qt.red

            if unicodedata.category(key_ch) != 'Cn':
                self.characterSelected.emit(key_ch)
            self.update()
        else:
            super(CharacterWidget, self).mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.lastKey = (event.y() // self.squareSize) * self.columns + event.x() // self.squareSize
            key_ch = self._chr(self.lastKey)
            self.col = Qt.green

            if unicodedata.category(key_ch) != 'Cn':
                self.characterSelected.emit(key_ch)
            self.update()
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

                key_ch = str(self._chr(key))

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

    @staticmethod
    def _chr(codepoint):
        try:
            # Python v2.
            return unichr(codepoint)
        except NameError:
            # Python v3.
            return chr(codepoint)

class MainWindow(QMainWindow):
    def __init__(self, font=Font()):
        super(MainWindow, self).__init__()

        centralWidget = QWidget()

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
        fileMenu.addMenu(QMenu("Open &Recent...", self))
        fileMenu.addSeparator()
        fileMenu.addAction("&Save", self.saveFile, "Ctrl+S")
        fileMenu.addAction("Save &As...", self.saveFileAs, "Ctrl+Shift+S")
        fileMenu.addAction("E&xit", QApplication.instance().quit, "Ctrl+Q")

        fontMenu = QMenu("&Font", self)
        self.menuBar().addMenu(fontMenu)

        fontMenu.addAction("Font &info", self.fontInfo, "Ctrl+I")
        fontMenu.addAction("Font &features", self.fontFeatures, "Ctrl+F")
        fontMenu.addSeparator()
        fontMenu.addAction("&Space center", self.spaceCenter, "Ctrl+Y")

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


    def fontInfo(self):
        # If a window is already opened, bring it to the front, else make another one.
        # TODO: see about calling super from the widget and del'eting the ptr to the widget
        # otherwise it doesn't get swept?
        # Else we can just play with visibility instead of respawning, given that the window
        # is still valid by its ref after it's been closed
        from fontinfo import TabDialog
        if not (hasattr(self, 'fontInfoWindow') and self.fontInfoWindow.isVisible()):
           self.fontInfoWindow = TabDialog(self.font)
           self.fontInfoWindow.show()
        else:
           print(self.fontInfoWindow)
           self.fontInfoWindow.raise_()

    def fontFeatures(self):
        # TODO: see up here
        from syntaxhighlighter import MainEditWindow
        if not (hasattr(self, 'fontFeaturesWindow') and self.fontFeaturesWindow.isVisible()):
           self.fontFeaturesWindow = MainEditWindow(self.font.features)
           self.fontFeaturesWindow.show()
        else:
           self.fontFeaturesWindow.raise_()

    def spaceCenter(self):
        # TODO: see up here
        from spacecenter import MainSpaceWindow
        if not (hasattr(self, 'spaceCenterWindow') and self.spaceCenterWindow.isVisible()):
           # XXX: trying to make a child window, let's see
           self.spaceCenterWindow = MainSpaceWindow(self.font, "Hiyazee")
           self.spaceCenterWindow.show()
        else:
           self.spaceCenterWindow.raise_()

    def about(self):
        QMessageBox.about(self, "About Fontes",
                "<p>The <b>Fontes</b> font editor is a new UFO-centric " \
                "font editor that brings the robofab ecosystem to all " \
                "main platforms, in a fast and dependency-free package.</p>")

if __name__ == '__main__':

    import sys

    representationFactories.registerAllFactories()
    app = QApplication(sys.argv)
    window = MainWindow(Font("C:\\Veloce.ufo"))
    window.resize(565, 430)
    window.show()
    sys.exit(app.exec_())
