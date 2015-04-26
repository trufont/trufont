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
from PyQt5.QtGui import (QClipboard, QDoubleValidator, QFont, QFontDatabase, QFontMetrics,
        QIcon, QIntValidator, QPainter)
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFontComboBox,
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
                if self.font.info.unitsPerEm is None: break
                if not self.font.info.unitsPerEm > 0: self.font.info.unitsPerEm = 1000
                factor = self.squareSize/(self.font.info.unitsPerEm*(1+2*.125))
                x_offset = (self.squareSize-self.glyphs[key].width*factor)/2
                if x_offset < 0:
                    factor *= 1+2*x_offset/(self.glyphs[key].width*factor)
                    x_offset = 0
                y_offset = self.font.info.descender*factor
#                print(self.glyphs[key].width)
#                print("xo: "+str(x_offset))
                painter.save()
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

class TabDialog(QDialog):

    def __init__(self, font, parent=None):
        super(TabDialog, self).__init__(parent)

        # TODO: figure a proper correspondence to set and fetch widgets...
        self.tabs = {
            "General": 0
        }

#        fileInfo = QFileInfo(fileName)
        self.font = font
        self.tabWidget = QTabWidget()
        self.tabWidget.addTab(GeneralTab(self.font), "General")
#        tabWidget.addTab(PermissionsTab(fileInfo), "OpenType")
#        tabWidget.addTab(ApplicationsTab(fileInfo), "PostScript")
#        tabWidget.addTab(ApplicationsTab(fileInfo), "Miscellaneous")

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.tabWidget)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

        self.setWindowTitle("Font Info")

    def accept(self):
        self.font.info.familyName = self.tabWidget.widget(self.tabs["General"]).fileNameEdit.text()
        self.font.info.styleName = self.tabWidget.widget(self.tabs["General"]).styleNameEdit.text()
        self.font.info.styleMapFamilyName = self.tabWidget.widget(self.tabs["General"]).styleMapFamilyEdit.text()
        sn = self.tabWidget.widget(self.tabs["General"]).styleMapStyleDrop.currentIndex()
        print(sn)
        if sn == 1: self.font.info.styleMapStyleName = "regular"
        elif sn == 2: self.font.info.styleMapStyleName = "italic"
        elif sn == 3: self.font.info.styleMapStyleName = "bold"
        elif sn == 4: self.font.info.styleMapStyleName = "bold italic"
        else: self.font.info.styleMapStyleName = None
        self.font.info.versionMajor = int(self.tabWidget.widget(self.tabs["General"]).versionMajorEdit.text())
        self.font.info.versionMinor = int(self.tabWidget.widget(self.tabs["General"]).versionMinorEdit.text())
        super(TabDialog, self).accept()

class GeneralTab(QWidget):
    def __init__(self, font, parent=None):
        super(GeneralTab, self).__init__(parent)

        identLabel = QLabel("Identification")
        identLine = QFrame()
        identLine.setFrameShape(QFrame.HLine)
        
        fileNameLabel = QLabel("Family name:")
        self.fileNameEdit = QLineEdit(font.info.familyName)

        styleNameLabel = QLabel("Style name:")
        self.styleNameEdit = QLineEdit(font.info.styleName)
        
        styleMapFamilyLabel = QLabel("Style map family name:")
        self.styleMapFamilyEdit = QLineEdit(font.info.styleMapFamilyName)
#        self.styleMapFamilyCBox = QCheckBox("Use default value")

        styleMapStyleLabel = QLabel("Style map style name:")
        self.styleMapStyleDrop = QComboBox()
#        items = ["None", "Regular", "Italic", "Bold", "Bold Italic"]
        styleMapStyle = {
            "None": 0,
            "Regular": 1,
            "Italic": 2,
            "Bold": 3,
            "Bold Italic": 4
        }
        for name,index in styleMapStyle.items():
            self.styleMapStyleDrop.insertItem(index, name)
        sn = font.info.styleMapStyleName
        # TODO: index to set is statically known, should eventually get rid of dict overhead if any?
        if sn == "regular": self.styleMapStyleDrop.setCurrentIndex(styleMapStyle["Regular"])
        elif sn == "regular italic": self.styleMapStyleDrop.setCurrentIndex(styleMapStyle["Italic"])
        elif sn == "bold": self.styleMapStyleDrop.setCurrentIndex(styleMapStyle["Bold"])
        elif sn == "bold italic": self.styleMapStyleDrop.setCurrentIndex(styleMapStyle["Bold Italic"])
        else: self.styleMapStyleDrop.setCurrentIndex(styleMapStyle["None"])
#        self.styleMapStyleCBox = QCheckBox("Use default value")

        # TODO: give visual feedback of input data validity using QLineEdit lose focus event
        # http://snorf.net/blog/2014/08/09/using-qvalidator-in-pyqt4-to-validate-user-input/
        versionLabel = QLabel("Version:")
        self.versionMajorEdit = QLineEdit(str(font.info.versionMajor))
        self.versionMajorEdit.setValidator(QIntValidator())
        self.versionMinorEdit = QLineEdit(str(font.info.versionMinor))
        self.versionMinorEdit.setValidator(QIntValidator())
        
        dimensionsLabel = QLabel("Dimensions")
        dimensionsLine = QFrame()
        dimensionsLine.setFrameShape(QFrame.HLine)
        
        unitsPerEmLabel = QLabel("Units per em:")
        self.unitsPerEmEdit = QLineEdit(str(font.info.unitsPerEm))
        self.unitsPerEmEdit.setValidator(QIntValidator())
        
        ascenderLabel = QLabel("Ascender:")
        self.ascenderEdit = QLineEdit(str(font.info.ascender))
        self.ascenderEdit.setValidator(QIntValidator())
        
        descenderLabel = QLabel("Descender:")
        self.descenderEdit = QLineEdit(str(font.info.descender))
        self.descenderEdit.setValidator(QIntValidator())
        
        xHeightLabel = QLabel("x-height:")
        self.xHeightEdit = QLineEdit(str(font.info.xHeight))
        self.xHeightEdit.setValidator(QIntValidator())
        
        capHeightLabel = QLabel("Cap height:")
        self.capHeightEdit = QLineEdit(str(font.info.capHeight))
        self.capHeightEdit.setValidator(QIntValidator())
        
        italicAngleLabel = QLabel("Italic angle:")
        self.italicAngleEdit = QLineEdit(str(font.info.italicAngle))
        self.italicAngleEdit.setValidator(QDoubleValidator())

        legalLabel = QLabel("Legal")
        legalLine = QFrame()
        legalLine.setFrameShape(QFrame.HLine)

        copyrightLabel = QLabel("Copyright:")
        self.copyrightEdit = QLineEdit(font.info.copyright)
        
        trademarkLabel = QLabel("Trademark:")
        self.trademarkEdit = QLineEdit(font.info.trademark)
        
        licenseLabel = QLabel("License:")
        self.licenseEdit = QLineEdit(font.info.openTypeNameLicense)

        licenseURLLabel = QLabel("License URL:")
        self.licenseURLEdit = QLineEdit(font.info.openTypeNameLicenseURL)
        
        partiesLabel = QLabel("Parties")
        partiesLine = QFrame()
        partiesLine.setFrameShape(QFrame.HLine)
        
        designerLabel = QLabel("Designer:")
        self.designerEdit = QLineEdit(font.info.openTypeNameDesigner)
        
        designerURLLabel = QLabel("Designer URL:")
        self.designerURLEdit = QLineEdit(font.info.openTypeNameDesignerURL)
        
        manufacturerLabel = QLabel("Manufacturer:")
        self.manufacturerEdit = QLineEdit(font.info.openTypeNameManufacturer)

        manufacturerURLLabel = QLabel("Manufacturer URL:")
        self.manufacturerURLEdit = QLineEdit(font.info.openTypeNameManufacturerURL)
        
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(identLabel)
        mainLayout.addWidget(identLine)
        mainLayout.addWidget(fileNameLabel)
        mainLayout.addWidget(self.fileNameEdit)
        mainLayout.addWidget(styleNameLabel)
        mainLayout.addWidget(self.styleNameEdit)
        mainLayout.addWidget(styleMapFamilyLabel)
        mainLayout.addWidget(self.styleMapFamilyEdit)
        mainLayout.addWidget(styleMapStyleLabel)
        mainLayout.addWidget(self.styleMapStyleDrop)
        mainLayout.addWidget(versionLabel)
        mainLayout.addWidget(self.versionMajorEdit)
        mainLayout.addWidget(self.versionMinorEdit)
        
        mainLayout.addWidget(dimensionsLabel)
        mainLayout.addWidget(dimensionsLine)
        mainLayout.addWidget(unitsPerEmLabel)
        mainLayout.addWidget(self.unitsPerEmEdit)
        mainLayout.addWidget(ascenderLabel)
        mainLayout.addWidget(self.ascenderEdit)
        mainLayout.addWidget(descenderLabel)
        mainLayout.addWidget(self.descenderEdit)
        mainLayout.addWidget(xHeightLabel)
        mainLayout.addWidget(self.xHeightEdit)
        mainLayout.addWidget(capHeightLabel)
        mainLayout.addWidget(self.capHeightEdit)
        mainLayout.addWidget(italicAngleLabel)
        mainLayout.addWidget(self.italicAngleEdit)
        
        mainLayout.addWidget(legalLabel)
        mainLayout.addWidget(legalLine)
        mainLayout.addWidget(copyrightLabel)
        mainLayout.addWidget(self.copyrightEdit)
        mainLayout.addWidget(trademarkLabel)
        mainLayout.addWidget(self.trademarkEdit)
        mainLayout.addWidget(licenseLabel)
        mainLayout.addWidget(self.licenseEdit)
        mainLayout.addWidget(licenseURLLabel)
        mainLayout.addWidget(self.licenseURLEdit)
        
        mainLayout.addWidget(partiesLabel)
        mainLayout.addWidget(partiesLine)
        mainLayout.addWidget(designerLabel)
        mainLayout.addWidget(self.designerEdit)
        mainLayout.addWidget(designerURLLabel)
        mainLayout.addWidget(self.designerURLEdit)
        mainLayout.addWidget(manufacturerLabel)
        mainLayout.addWidget(self.manufacturerEdit)
        mainLayout.addWidget(manufacturerURLLabel)
        mainLayout.addWidget(self.manufacturerURLEdit)
        mainLayout.addStretch(1)
        
        # http://nealbuerger.com/2013/11/pyside-qvboxlayout-with-qscrollarea/
        # Why so many layers of indirection? It might be possible to do this
        # in a simpler way...
        widget = QWidget()
        widget.setLayout(mainLayout)
        scrollArea = QScrollArea()
        scrollArea.setWidget(widget)
        scrollArea.setMinimumSize(170, 200)
        vLayout = QVBoxLayout()
        vLayout.addWidget(scrollArea)
        
        self.setLayout(vLayout)

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
        if not (hasattr(self, 'fontInfoWindow') and self.fontInfoWindow.isVisible()):
           self.fontInfoWindow = TabDialog(self.font)
           self.fontInfoWindow.show()
        else:
           print(self.fontInfoWindow)
           self.fontInfoWindow.raise_()

    def fontFeatures(self):
        # TODO: see up here
        import syntaxhighlighter
        if not (hasattr(self, 'fontFeaturesWindow') and self.fontFeaturesWindow.isVisible()):
           # XXX: trying to make a child window, let's see
           self.fontFeaturesWindow = syntaxhighlighter.MainWindow(self.font.features, self)
           self.fontFeaturesWindow.show()
        else:
           self.fontFeaturesWindow.raise_()

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
