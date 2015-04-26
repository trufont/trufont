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


from math import cos, pi, sin

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import (QBrush, QColor, QFont, QLinearGradient, QPainter,
        QPainterPath, QPalette, QPen)
from PyQt5.QtWidgets import (QApplication, QComboBox, QGridLayout, QLabel,
        QMainWindow, QSizePolicy, QSpinBox, QWidget)

class MainSpaceWindow(QMainWindow):
    def __init__(self, font, string, height=400, parent=None):
        super(MainSpaceWindow, self).__init__(parent)

        self.height = height
        self.font = font
        self.string = string
#        self.setupHelpMenu()
        self.canvas = GlyphsCanvas(self.font, self.string, self.height, self)
#        self.resize(600,500)

        self.setCentralWidget(self.canvas)
        self.setWindowTitle("Space center")

    def about(self):
        QMessageBox.about(self, "About Syntax Highlighter",
                "<p>The <b>Syntax Highlighter</b> example shows how to " \
                "perform simple syntax highlighting by subclassing the " \
                "QSyntaxHighlighter class and describing highlighting " \
                "rules using regular expressions.</p>")

    def newFile(self):
        self.editor.clear()

    def openFile(self, path=None):
        if not path:
            path, _ = QFileDialog.getOpenFileName(self, "Open File", '',
                    "C++ Files (*.cpp *.h)")

        if path:
            inFile = QFile(path)
            if inFile.open(QFile.ReadOnly | QFile.Text):
                text = inFile.readAll()

                try:
                    # Python v3.
                    text = str(text, encoding='ascii')
                except TypeError:
                    # Python v2.
                    text = str(text)

                self.editor.setPlainText(text)

    def save(self):
        self.editor.write(self.features)

    def setupFileMenu(self):
        fileMenu = QMenu("&File", self)
        self.menuBar().addMenu(fileMenu)

#        fileMenu.addAction("&New...", self.newFile, "Ctrl+N")
#        fileMenu.addAction("&Open...", self.openFile, "Ctrl+O")
        fileMenu.addAction("&Save...", self.save, "Ctrl+S")
        fileMenu.addAction("E&xit", QApplication.instance().quit, "Ctrl+Q")

    def setupHelpMenu(self):
        helpMenu = QMenu("&Help", self)
        self.menuBar().addMenu(helpMenu)

        helpMenu.addAction("&About", self.about)
        helpMenu.addAction("About &Qt", QApplication.instance().aboutQt)

class GlyphsCanvas(QWidget):
    def __init__(self, font, string, height, parent=None):
        super(GlyphsCanvas, self).__init__(parent)

        self.font = font
        self.string = string

        self.height = height
        self.padding = 30

        self.penWidth = 1
        self.rotationAngle = 0
        self.setBackgroundRole(QPalette.Base)

    '''
    def minimumSizeHint(self):
        return QSize(50, 50)

    def sizeHint(self):
        return QSize(100, 100)

    def setFillRule(self, rule):
        self.path.setFillRule(rule)
        self.update()

    def setFillGradient(self, color1, color2):
        self.fillColor1 = color1
        self.fillColor2 = color2
        self.update()

    def setPenWidth(self, width):
        self.penWidth = width
        self.update()

    def setPenColor(self, color):
        self.penColor = color
        self.update()

    def setRotationAngle(self, degrees):
        self.rotationAngle = degrees
        self.update()
    '''

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if self.font.info.unitsPerEm is None: return
        if not self.font.info.unitsPerEm > 0: self.font.info.unitsPerEm = 1000
        factor = self.height/(self.font.info.unitsPerEm*(1+2*.125))
        painter.save()
        painter.translate(self.padding, self.height+self.font.info.descender*factor)
#        painter.scale(self.width() / 100.0, self.height() / 100.0)
#        painter.rotate(-self.rotationAngle)
#        painter.translate(-50.0, -50.0)

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
#        painter.fillRect(0, 0, width, self.height, Qt.white)
#        self.sizeHint(offset) whatever

#        for index, char in enumerate(self.string):

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


if __name__ == '__main__':

    import sys
# registerallfactories
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
