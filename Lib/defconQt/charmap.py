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

import os
import representationFactories
import unicodedata

from defcon import Font
from PyQt5.QtCore import pyqtSignal, QSize, Qt
from PyQt5.QtGui import (QClipboard, QFont, QFontDatabase, QFontMetrics,
        QIcon, QPainter)
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QFontComboBox,
        QHBoxLayout, QLabel, QLineEdit, QMainWindow, QPushButton, QScrollArea,
        QToolTip, QVBoxLayout, QWidget)

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

    def updateFont(self, fontFamily):
        self.displayFont.setFamily(fontFamily)
        self.squareSize = max(24, QFontMetrics(self.displayFont).xHeight() * 3)
        self.adjustSize()
        self.update()

    def updateSize(self, fontSize):
#        fontSize, _ = fontSize.toInt()
        self.displayFont.setPointSize(int(fontSize))
        self.squareSize = max(24, QFontMetrics(self.displayFont).xHeight() * 3)
        self.adjustSize()
        self.update() 

    def updateStyle(self, fontStyle):
        fontDatabase = QFontDatabase()
        oldStrategy = self.displayFont.styleStrategy()
        self.displayFont = fontDatabase.font(self.displayFont.family(),
                fontStyle, self.displayFont.pointSize())
        self.displayFont.setStyleStrategy(oldStrategy)
        self.squareSize = max(24, QFontMetrics(self.displayFont).xHeight() * 3)
        self.adjustSize()
        self.update()

    def updateFontMerging(self, enable):
        if enable:
            self.displayFont.setStyleStrategy(QFont.PreferDefault)
        else:
            self.displayFont.setStyleStrategy(QFont.NoFontMerging)
        self.adjustSize()
        self.update()

    def sizeHint(self):
        return QSize(self.columns * self.squareSize,
                (65536 / self.columns) * self.squareSize)

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
        #painter.setFont(self.displayFont)

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

#        fontMetrics = QFontMetrics(self.displayFont)
#        painter.setPen(Qt.black)
        
        
        """
        draw = self.displayFont["a"].getRepresentation("defconQt.QPainterPath")
        painter.save()
        painter.setBrushOrigin(50, 150)
#        painter.scale(1.0, -1.0)
#        painter.translate(0,-self.squareSize)
#        p_x,p_y,p_w,p_h = draw.controlPointRect().getRect()
#        measure = max(p_w, p_h)
#        painter.scale(measure/self.squareSize, measure/self.squareSize)
        painter.fillPath(draw, Qt.black)
        painter.restore()
        """
        for row in range(beginRow, endRow + 1):
            for column in range(beginColumn, endColumn + 1):
                key = row * self.columns + column
                x,y,w,h = column * self.squareSize, row * self.squareSize, self.squareSize, self.squareSize
#                painter.setClipRect(x,y,w,h)

                if key == self.lastKey:
                    painter.fillRect(column * self.squareSize + 1,
                            row * self.squareSize + 1, self.squareSize - 2,
                            self.squareSize - 2, self.col)

                key_ch = str(self._chr(key))
#                painter.drawText(column * self.squareSize + (self.squareSize / 2) - fontMetrics.width(key_ch) / 2,
#                        row * self.squareSize + 4 + fontMetrics.ascent(),
#                        key_ch)
#                print(key)
                if key > len(self.glyphs)-1: break
                glyph = self.glyphs[key].getRepresentation("defconQt.QPainterPath")
#                if key_ch not in self.displayFont: continue
#                glyph = self.displayFont[key_ch].getRepresentation("defconQt.QPainterPath") # , width=self.squareSize, height=self.squareSize
                # When need to move the painter so that the path draws at the right place
#                print(glyph)
#                p_x,p_y,p_w,p_h = glyph.controlPointRect().getRect()
#                print(p_h, h)
                painter.save()
                if not self.font.info.unitsPerEm > 0: self.font.info.unitsPerEm = 1000
                factor = self.squareSize/(self.font.info.unitsPerEm*(1+2*.125))
                x_offset = (self.squareSize-self.glyphs[key].width*factor)/2
                if x_offset < 0:
                    factor *= 1+2*x_offset/(self.glyphs[key].width*factor)
                    x_offset = 0
                y_offset = self.font.info.descender*factor
#                print(self.glyphs[key].width)
#                print("xo: "+str(x_offset))
                painter.translate(column * self.squareSize + x_offset, row * self.squareSize + self.squareSize + y_offset)
#                painter.setBrushOrigin((self.squareSize-self.glyphs[key].width)/2,self.font.info.descender)
#                painter.translate(column * self.squareSize + (self.squareSize / 2) - self.glyphs[key].width / 2,
#                        row * self.squareSize + 4 + self.displayFont['hhea'].ascent)
#                painter.translate(p_x-x, p_y-y)
#                painter.scale(1.0, -1.0)
#                painter.translate(0,-self.squareSize)
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

        """
        fontLabel = QLabel("Font:")
        self.fontCombo = QFontComboBox()
        sizeLabel = QLabel("Size:")
        self.sizeCombo = QComboBox()
        styleLabel = QLabel("Style:")
        self.styleCombo = QComboBox()
        fontMergingLabel = QLabel("Automatic Font Merging:")
        self.fontMerging = QCheckBox()
        self.fontMerging.setChecked(True)
        """

        self.scrollArea = QScrollArea()
        self.characterWidget = CharacterWidget(self.font)
        self.scrollArea.setWidget(self.characterWidget)

        """
        self.findStyles(self.fontCombo.currentFont())
        self.findSizes(self.fontCombo.currentFont())

        self.lineEdit = QLineEdit()
        clipboardButton = QPushButton("&To clipboard")

        self.clipboard = QApplication.clipboard()

        self.fontCombo.currentFontChanged.connect(self.findStyles)
        self.fontCombo.activated[str].connect(self.characterWidget.updateFont)
        self.styleCombo.activated[str].connect(self.characterWidget.updateStyle)
        self.sizeCombo.currentIndexChanged[str].connect(self.characterWidget.updateSize)
        self.characterWidget.characterSelected.connect(self.insertCharacter)
        clipboardButton.clicked.connect(self.updateClipboard)

        controlsLayout = QHBoxLayout()
        controlsLayout.addWidget(fontLabel)
        controlsLayout.addWidget(self.fontCombo, 1)
        controlsLayout.addWidget(sizeLabel)
        controlsLayout.addWidget(self.sizeCombo, 1)
        controlsLayout.addWidget(styleLabel)
        controlsLayout.addWidget(self.styleCombo, 1)
        controlsLayout.addWidget(fontMergingLabel)
        controlsLayout.addWidget(self.fontMerging, 1)
        controlsLayout.addStretch(1)

        lineLayout = QHBoxLayout()
        lineLayout.addWidget(self.lineEdit, 1)
        lineLayout.addSpacing(12)
        lineLayout.addWidget(clipboardButton)
        """

        centralLayout = QVBoxLayout()
        #centralLayout.addLayout(controlsLayout)
        centralLayout.addWidget(self.scrollArea, 1)
        #centralLayout.addSpacing(4)
        #centralLayout.addLayout(lineLayout)
        centralWidget.setLayout(centralLayout)

        self.setCentralWidget(centralWidget)
        self.setWindowTitle(os.path.basename(self.font.path.rstrip(os.sep)))
        self.setWindowIcon(QIcon("C:\\Users\\Adrien\\Downloads\\defconQt\\Lib\\defconQt\\resources\\icon.png"));

    def findStyles(self, font):
        fontDatabase = QFontDatabase()
        currentItem = self.styleCombo.currentText()
        self.styleCombo.clear()

        for style in fontDatabase.styles(font.family()):
            self.styleCombo.addItem(style)

        styleIndex = self.styleCombo.findText(currentItem)
        if styleIndex == -1:
            self.styleCombo.setCurrentIndex(0)
        else:
            self.styleCombo.setCurrentIndex(styleIndex)

    def findSizes(self, font):
        fontDatabase = QFontDatabase()
        currentSize = self.sizeCombo.currentText()
        self.sizeCombo.blockSignals(True)
        self.sizeCombo.clear()

        if fontDatabase.isSmoothlyScalable(font.family(), fontDatabase.styleString(font)):
            for size in QFontDatabase.standardSizes():
                self.sizeCombo.addItem(str(size))
                self.sizeCombo.setEditable(True)
        else:
            for size in fontDatabase.smoothSizes(font.family(), fontDatabase.styleString(font)):
                self.sizeCombo.addItem(str(size))
                self.sizeCombo.setEditable(False)

        self.sizeCombo.blockSignals(False)

        sizeIndex = self.sizeCombo.findText(currentSize)
        if sizeIndex == -1:
            self.sizeCombo.setCurrentIndex(max(0, self.sizeCombo.count() / 3))
        else:
            self.sizeCombo.setCurrentIndex(sizeIndex)

    def insertCharacter(self, character):
        self.lineEdit.insert(character)

    def updateClipboard(self):
        self.clipboard.setText(self.lineEdit.text(), QClipboard.Clipboard)
        self.clipboard.setText(self.lineEdit.text(), QClipboard.Selection)


if __name__ == '__main__':

    import sys

    representationFactories.registerAllFactories()
    app = QApplication(sys.argv)
    window = MainWindow(Font("C:\\Veloce.ufo"))
    window.show()
    sys.exit(app.exec_())
