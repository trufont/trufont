from defcon.tools.notifications import NotificationCenter
from defcon import Color
from trufont import __version__
from trufont.featureTextEditor import MainEditWindow
from trufont.fontInfo import TabDialog
from trufont.glyphCollectionView import GlyphCollectionWidget
from trufont.glyphView import MainGlyphWindow
from trufont.groupsView import GroupsWindow
from trufont.scriptingWindow import MainScriptingWindow
from trufont.objects import errorReports
from trufont.objects.colorWidgets import ColorVignette
from trufont.objects.defcon import GlyphSet, TComponent, TFont, TGlyph
from trufont.util import platformSpecific
from trufont.metricsWindow import MainMetricsWindow, comboBoxItems
from PyQt5.QtCore import (
    pyqtSignal, QEvent, QMimeData, QRegularExpression, QSettings, Qt)
from PyQt5.QtGui import (
    QColor, QCursor, QIcon, QIntValidator, QKeySequence, QPixmap,
    QRegularExpressionValidator, QTextCursor)
from PyQt5.QtWidgets import (
    QAbstractItemView, QAction, QApplication, QCheckBox, QComboBox, QDialog,
    QDialogButtonBox, QFileDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMenu, QMessageBox,
    QPlainTextEdit, QPushButton, QRadioButton, QSlider, QSplitter, QTabWidget,
    QTextEdit, QToolTip, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)
from trufont.util.rlabel import RLabel
from collections import OrderedDict
import os
import pickle
import platform
import subprocess

cannedDesign = [
    dict(type="cannedDesign", allowPseudoUnicode=True)
]
sortItems = ["alphabetical", "category", "unicode", "script", "suffix",
             "decompositionBase", "weightedSuffix", "ligature"]
latinDefault = GlyphSet(
    ["space", "exclam", "quotesingle", "quotedbl", "numbersign", "dollar",
     "percent", "ampersand", "parenleft", "parenright", "asterisk", "plus",
     "comma", "hyphen", "period", "slash", "zero", "one", "two", "three",
     "four", "five", "six", "seven", "eight", "nine", "colon", "semicolon",
     "less", "equal", "greater", "question", "at", "A", "B", "C", "D", "E",
     "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S",
     "T", "U", "V", "W", "X", "Y", "Z", "bracketleft", "backslash",
     "bracketright", "asciicircum", "underscore", "grave", "a", "b", "c", "d",
     "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s",
     "t", "u", "v", "w", "x", "y", "z", "braceleft", "bar", "braceright",
     "asciitilde", "exclamdown", "cent", "sterling", "currency", "yen",
     "brokenbar", "section", "copyright", "ordfeminine", "guillemotleft",
     "logicalnot", "registered", "macron", "degree", "plusminus",
     "twosuperior", "threesuperior", "mu", "paragraph", "periodcentered",
     "onesuperior", "ordmasculine", "guillemotright", "onequarter", "onehalf",
     "threequarters", "questiondown", "Agrave", "Aacute", "Acircumflex",
     "Atilde", "Adieresis", "Aring", "AE", "Ccedilla", "Egrave", "Eacute",
     "Ecircumflex", "Edieresis", "Igrave", "Iacute", "Icircumflex",
     "Idieresis", "Eth", "Ntilde", "Ograve", "Oacute", "Ocircumflex",
     "Otilde", "Odieresis", "multiply", "Oslash", "Ugrave", "Uacute",
     "Ucircumflex", "Udieresis", "Yacute", "Thorn", "germandbls", "agrave",
     "aacute", "acircumflex", "atilde", "adieresis", "aring", "ae", "ccedilla",
     "egrave", "eacute", "ecircumflex", "edieresis", "igrave", "iacute",
     "icircumflex", "idieresis", "eth", "ntilde", "ograve", "oacute",
     "ocircumflex", "otilde", "odieresis", "divide", "oslash", "ugrave",
     "uacute", "ucircumflex", "udieresis", "yacute", "thorn", "ydieresis",
     "dotlessi", "gravecomb", "acutecomb", "uni0302", "uni0308", "uni030A",
     "tildecomb", "uni0327", "quoteleft", "quoteright", "minus"],
    "Latin-default")

try:
    gitShortHash = subprocess.check_output(
        ['git', 'rev-parse', '--short', 'HEAD'], stderr=subprocess.DEVNULL
    ).decode()
except:
    gitShortHash = ""


class Application(QApplication):
    # TODO: maybe remove this redundancy
    currentFontChanged = pyqtSignal()
    currentGlyphChanged = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(Application, self).__init__(*args, **kwargs)
        self._currentGlyph = None
        self._currentMainWindow = None
        self._launched = False
        self.dispatcher = NotificationCenter()
        self.focusChanged.connect(lambda: self.updateCurrentMainWindow())
        self.GL2UV = None

    def event(self, event):
        eventType = event.type()
        # respond to OSX open events
        if eventType == QEvent.FileOpen:
            filePath = event.file()
            self.openFile(filePath)
            return True
        elif eventType == QEvent.ApplicationStateChange:
            applicationState = self.applicationState()
            if applicationState == Qt.ApplicationActive:
                if not self._launched:
                    notification = "applicationLaunched"
                    self.loadGlyphList()
                    self._launched = True
                else:
                    notification = "applicationActivated"
                self.postNotification(notification)
                self.updateCurrentMainWindow()
            elif applicationState == Qt.ApplicationInactive:
                self.postNotification("applicationWillIdle")
        return super().event(event)

    def postNotification(self, notification, data=None):
        dispatcher = self.dispatcher
        dispatcher.postNotification(
            notification=notification, observable=self, data=data)

    def loadGlyphList(self):
        settings = QSettings()
        glyphListPath = settings.value("settings/glyphListPath", "", str)
        if glyphListPath and os.path.exists(glyphListPath):
            from defconQt.util import glyphList
            try:
                glyphList = glyphList.parseGlyphList(glyphListPath)
            except Exception as e:
                msg = self.tr(
                    "The glyph list at {0} cannot "
                    "be parsed and will be dropped.").format(glyphListPath)
                errorReports.showWarningException(e, msg)
                settings.remove("settings/glyphListPath")
            else:
                self.GL2UV = glyphList

    def newFile(self):
        font = TFont()
        font.info.unitsPerEm = 1000
        font.info.ascender = 750
        font.info.descender = -250
        font.info.capHeight = 750
        font.info.xHeight = 500
        defaultGlyphSet = QSettings().value("settings/defaultGlyphSet",
                                            latinDefault.name, type=str)
        if defaultGlyphSet:
            glyphNames = None
            if defaultGlyphSet == latinDefault.name:
                glyphNames = latinDefault.glyphNames
            else:
                glyphSets = readGlyphSets()
                if defaultGlyphSet in glyphSets:
                    glyphNames = glyphSets[defaultGlyphSet]
            if glyphNames is not None:
                for name in glyphNames:
                    font.newStandardGlyph(name, asTemplate=True)
        font.dirty = False

        data = dict(font=font)
        self.postNotification("newFontWillOpen", data)
        window = MainWindow(font)
        window.show()
        self.postNotification("newFontOpened", data)

    def openFile(self, path):
        if ".plist" in path:
            path = os.path.dirname(path)
        path = os.path.normpath(path)
        for window in self.topLevelWidgets():
            if (isinstance(window, MainWindow) and window._font is not None
                    and window._font.path == path):
                window.raise_()
                return
        try:
            font = TFont(path)
            data = dict(font=font)
            self.postNotification("fontWillOpen", data)
            window = MainWindow(font)
        except Exception as e:
            errorReports.showCriticalException(e)
            return
        window.show()
        self.postNotification("fontOpened", data)

    def allFonts(self):
        fonts = []
        for window in QApplication.topLevelWidgets():
            if isinstance(window, MainWindow):
                fonts.append(window._font)
        return fonts

    def currentFont(self):
        return self._currentMainWindow._font

    def currentGlyph(self):
        return self._currentGlyph

    def setCurrentGlyph(self, glyph):
        if glyph == self._currentGlyph:
            return
        self._currentGlyph = glyph
        self.currentGlyphChanged.emit()
        self.postNotification("currentGlyphChanged")

    def currentMainWindow(self):
        return self._currentMainWindow

    def setCurrentMainWindow(self, mainWindow):
        if mainWindow == self._currentMainWindow:
            return
        self._currentMainWindow = mainWindow
        self.currentFontChanged.emit()
        self.postNotification("currentFontChanged")

    def updateCurrentMainWindow(self):
        window = self.activeWindow()
        if window is None:
            return
        while True:
            parent = window.parent()
            if parent is None:
                break
            window = parent
        if isinstance(window, MainWindow):
            self.setCurrentMainWindow(window)

MAX_RECENT_FILES = 6


class InspectorWindow(QWidget):

    def __init__(self):
        super().__init__(flags=Qt.Tool)
        self.setWindowTitle(self.tr("Inspector"))
        self._blocked = False
        self._glyph = None

        glyphGroup = QGroupBox(self.tr("Glyph"), self)
        glyphGroup.setFlat(True)
        glyphLayout = QGridLayout(self)
        columnOneWidth = self.fontMetrics().width('0') * 7

        nameLabel = RLabel(self.tr("Name:"), self)
        self.nameEdit = QLineEdit(self)
        self.nameEdit.editingFinished.connect(self.writeGlyphName)
        unicodesLabel = RLabel(self.tr("Unicode:"), self)
        self.unicodesEdit = QLineEdit(self)
        self.unicodesEdit.editingFinished.connect(self.writeUnicodes)
        unicodesRegExp = QRegularExpression(
            "(|([a-fA-F0-9]{4,6})( ([a-fA-F0-9]{4,6}))*)")
        unicodesValidator = QRegularExpressionValidator(unicodesRegExp, self)
        self.unicodesEdit.setValidator(unicodesValidator)
        widthLabel = RLabel(self.tr("Width:"), self)
        self.widthEdit = QLineEdit(self)
        self.widthEdit.editingFinished.connect(self.writeWidth)
        self.widthEdit.setMaximumWidth(columnOneWidth)
        self.widthEdit.setValidator(QIntValidator(self))
        leftSideBearingLabel = RLabel(self.tr("Left:"), self)
        self.leftSideBearingEdit = QLineEdit(self)
        self.leftSideBearingEdit.editingFinished.connect(
            self.writeLeftSideBearing)
        self.leftSideBearingEdit.setMaximumWidth(columnOneWidth)
        self.leftSideBearingEdit.setValidator(QIntValidator(self))
        rightSideBearingLabel = RLabel(self.tr("Right:"), self)
        self.rightSideBearingEdit = QLineEdit(self)
        self.rightSideBearingEdit.editingFinished.connect(
            self.writeRightSideBearing)
        self.rightSideBearingEdit.setMaximumWidth(columnOneWidth)
        self.rightSideBearingEdit.setValidator(QIntValidator(self))
        markColorLabel = RLabel(self.tr("Flag:"), self)
        self.markColorWidget = ColorVignette(self)
        self.markColorWidget.colorChanged.connect(
            self.writeMarkColor)
        self.markColorWidget.setMaximumWidth(columnOneWidth)

        l = 0
        glyphLayout.addWidget(nameLabel, l, 0)
        glyphLayout.addWidget(self.nameEdit, l, 1, 1, 5)
        l += 1
        glyphLayout.addWidget(unicodesLabel, l, 0)
        glyphLayout.addWidget(self.unicodesEdit, l, 1, 1, 5)
        l += 1
        glyphLayout.addWidget(widthLabel, l, 0)
        glyphLayout.addWidget(self.widthEdit, l, 1)
        l += 1
        glyphLayout.addWidget(leftSideBearingLabel, l, 0)
        glyphLayout.addWidget(self.leftSideBearingEdit, l, 1)
        glyphLayout.addWidget(rightSideBearingLabel, l, 2)
        glyphLayout.addWidget(self.rightSideBearingEdit, l, 3)
        l += 1
        glyphLayout.addWidget(markColorLabel, l, 0)
        glyphLayout.addWidget(self.markColorWidget, l, 1)
        glyphGroup.setLayout(glyphLayout)

        transformGroup = QGroupBox(self.tr("Transform"), self)
        transformGroup.setFlat(True)
        transformLayout = QGridLayout(self)

        # TODO: should this be implemented for partial selection?
        # TODO: phase out fake button
        symmetryButton = QPushButton(self.tr("Symmetry"), self)
        symmetryButton.setEnabled(False)
        hSymmetryButton = QPushButton(self.tr("H"), self)
        hSymmetryButton.clicked.connect(self.hSymmetry)
        vSymmetryButton = QPushButton(self.tr("V"), self)
        vSymmetryButton.clicked.connect(self.vSymmetry)

        moveButton = QPushButton(self.tr("Move"), self)
        moveButton.clicked.connect(self.moveGlyph)
        moveXLabel = RLabel("x:", self)
        self.moveXEdit = QLineEdit("0", self)
        self.moveXEdit.setValidator(QIntValidator(self))
        moveYLabel = RLabel("y:", self)
        self.moveYEdit = QLineEdit("0", self)
        self.moveYEdit.setValidator(QIntValidator(self))
        moveXYBox = QCheckBox("x=y", self)
        moveXYBox.clicked.connect(self.lockMove)

        scaleButton = QPushButton(self.tr("Scale"), self)
        scaleButton.clicked.connect(self.scaleGlyph)
        scaleXLabel = RLabel("x:", self)
        self.scaleXEdit = QLineEdit("100", self)
        self.scaleXEdit.setValidator(QIntValidator(self))
        scaleYLabel = RLabel("y:", self)
        self.scaleYEdit = QLineEdit("100", self)
        self.scaleYEdit.setValidator(QIntValidator(self))
        scaleXYBox = QCheckBox("x=y", self)
        scaleXYBox.clicked.connect(self.lockScale)

        l = 0
        transformLayout.addWidget(symmetryButton, l, 0)
        transformLayout.addWidget(hSymmetryButton, l, 2)
        transformLayout.addWidget(vSymmetryButton, l, 4)
        l += 1
        transformLayout.addWidget(moveButton, l, 0)
        transformLayout.addWidget(moveXLabel, l, 1)
        transformLayout.addWidget(self.moveXEdit, l, 2)
        transformLayout.addWidget(moveYLabel, l, 3)
        transformLayout.addWidget(self.moveYEdit, l, 4)
        transformLayout.addWidget(moveXYBox, l, 5)
        l += 1
        transformLayout.addWidget(scaleButton, l, 0)
        transformLayout.addWidget(scaleXLabel, l, 1)
        transformLayout.addWidget(self.scaleXEdit, l, 2)
        transformLayout.addWidget(scaleYLabel, l, 3)
        transformLayout.addWidget(self.scaleYEdit, l, 4)
        transformLayout.addWidget(scaleXYBox, l, 5)
        transformGroup.setLayout(transformLayout)

        layerSetGroup = QGroupBox(self.tr("Layers"), self)
        layerSetGroup.setFlat(True)
        layerSetLayout = QVBoxLayout(self)

        self.layerSetWidget = QTreeWidget(self)
        self.layerSetWidget.setHeaderLabels(
            (self.tr("Layer Name"), self.tr("Color")))
        self.layerSetWidget.setRootIsDecorated(False)
        self.layerSetWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        # TODO: make this work correctly, top-level items only
        # self.layerSetWidget.setDragDropMode(QAbstractItemView.InternalMove)

        layerSetLayout.addWidget(self.layerSetWidget)
        layerSetGroup.setLayout(layerSetLayout)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(glyphGroup)
        mainLayout.addWidget(transformGroup)
        mainLayout.addWidget(layerSetGroup)
        self.setLayout(mainLayout)

        app = QApplication.instance()
        self.updateGlyph()
        app.currentGlyphChanged.connect(self.updateGlyph)

    def showEvent(self, event):
        super().showEvent(event)
        screenRect = QApplication.desktop().availableGeometry(self)
        widgetRect = self.frameGeometry()
        x = screenRect.width() - (widgetRect.width() + 20)
        y = screenRect.center().y() - widgetRect.height() / 2
        self.move(x, y)

    def hSymmetry(self):
        if self._glyph is None:
            return
        controlPointBounds = self._glyph.controlPointBounds
        if controlPointBounds is None:
            return
        xMin, _, xMax, _ = controlPointBounds
        for contour in self._glyph:
            for point in contour:
                point.x = xMin + xMax - point.x
        self._glyph.dirty = True

    def vSymmetry(self):
        if self._glyph is None:
            return
        controlPointBounds = self._glyph.controlPointBounds
        if controlPointBounds is None:
            return
        _, yMin, _, yMax = controlPointBounds
        for contour in self._glyph:
            for point in contour:
                point.y = yMin + yMax - point.y
        self._glyph.dirty = True

    def lockMove(self, checked):
        self.moveYEdit.setEnabled(not checked)

    def moveGlyph(self):
        x = self.moveXEdit.text()
        if not self.moveYEdit.isEnabled():
            y = x
        else:
            y = self.moveYEdit.text()
        x, y = int(x) if x != "" else 0, int(y) if y != "" else 0
        self._glyph.move((x, y))

    def lockScale(self, checked):
        self.scaleYEdit.setEnabled(not checked)

    def scaleGlyph(self):
        if not len(self._glyph):
            return
        controlPointBounds = self._glyph.controlPointBounds
        if controlPointBounds is None:
            return
        sX = self.scaleXEdit.text()
        if not self.scaleYEdit.isEnabled():
            sY = sX
        else:
            sY = self.scaleYEdit.text()
        sX, sY = int(sX) if sX != "" else 1, int(sY) if sY != "" else 1
        sX /= 100
        sY /= 100
        xMin, yMin, _, _ = controlPointBounds
        for contour in self._glyph:
            for point in contour:
                point.x = xMin + (point.x - xMin) * sX
                point.y = yMin + (point.y - yMin) * sY
        self._glyph.dirty = True

    def updateGlyph(self):
        app = QApplication.instance()
        if self._glyph is not None:
            self._glyph.removeObserver(self, "Glyph.Changed")
            layerSet = self._glyph.layerSet
            if layerSet is not None:
                layerSet.removeObserver(self, "LayerSet.Changed")
        self._glyph = app.currentGlyph()
        if self._glyph is not None:
            self._glyph.addObserver(
                self, "updateGlyphAttributes", "Glyph.Changed")
            layerSet = self._glyph.layerSet
            if layerSet is not None:
                layerSet.addObserver(
                    self, "updateLayerAttributes", "LayerSet.Changed")
        self.updateGlyphAttributes()
        self.updateLayerAttributes()

    def updateGlyphAttributes(self, notification=None):
        if self._blocked:
            return
        name = None
        unicodes = None
        width = None
        leftSideBearing = None
        rightSideBearing = None
        markColor = None
        if self._glyph is not None:
            name = self._glyph.name
            unicodes = " ".join("%06X" % u if u > 0xFFFF else "%04X" %
                                u for u in self._glyph.unicodes)
            if self._glyph.width:
                width = str(int(self._glyph.width))
            if self._glyph.leftMargin is not None:
                leftSideBearing = str(int(self._glyph.leftMargin))
            if self._glyph.rightMargin is not None:
                rightSideBearing = str(int(self._glyph.rightMargin))
            if self._glyph.markColor is not None:
                markColor = QColor.fromRgbF(
                    *tuple(self._glyph.markColor))

        self.nameEdit.setText(name)
        self.unicodesEdit.setText(unicodes)
        self.widthEdit.setText(width)
        self.leftSideBearingEdit.setText(leftSideBearing)
        self.rightSideBearingEdit.setText(rightSideBearing)
        self.markColorWidget.setColor(markColor)

    def updateLayerAttributes(self, notification=None):
        self.layerSetWidget.clear()
        if self._glyph is None:
            return
        layerSet = self._glyph.layerSet
        if layerSet is None:
            return
        for layer in layerSet:
            item = QTreeWidgetItem(self.layerSetWidget)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            item.setText(0, layer.name)
            widget = ColorVignette(self)
            color = layer.color
            if color is not None:
                color = QColor.fromRgbF(*tuple(color))
            widget.setColor(color)
            widget.setMargins(2, 2, 2, 2)
            widget.setMayClearColor(False)
            widget.colorChanged.connect(
                self.writeLayerColor)
            widget.setProperty("layer", layer)
            self.layerSetWidget.setItemWidget(item, 1, widget)
        self.layerSetWidget.setColumnWidth(1, 100)

    def writeGlyphName(self):
        if self._glyph is None:
            return
        self._blocked = True
        self._glyph.name = self.nameEdit.text()
        self._blocked = False

    def writeUnicodes(self):
        if self._glyph is None:
            return
        self._blocked = True
        unicodes = self.unicodesEdit.text().split(" ")
        if len(unicodes) == 1 and unicodes[0] == "":
            self._glyph.unicodes = []
        else:
            self._glyph.unicodes = [int(uni, 16) for uni in unicodes]
        self._blocked = False

    def writeWidth(self):
        if self._glyph is None:
            return
        self._blocked = True
        self._glyph.width = int(self.widthEdit.text())
        self._blocked = False

    def writeLeftSideBearing(self):
        if self._glyph is None:
            return
        self._blocked = True
        self._glyph.leftMargin = int(self.leftSideBearingEdit.text())
        self._blocked = False

    def writeRightSideBearing(self):
        if self._glyph is None:
            return
        self._blocked = True
        self._glyph.rightMargin = int(self.rightSideBearingEdit.text())
        self._blocked = False

    def writeMarkColor(self):
        color = self.markColorWidget.color()
        if color is not None:
            color = Color(color.getRgbF())
        self._glyph.markColor = color

    def writeLayerColor(self):
        widget = self.sender()
        color = widget.color()
        layer = widget.property("layer")
        if color is not None:
            color = Color(color.getRgbF())
        layer.color = color


class AddGlyphsDialog(QDialog):

    # TODO: implement Frederik's Glyph Construction Builder
    def __init__(self, currentGlyphs=None, parent=None):
        super(AddGlyphsDialog, self).__init__(parent)
        self.setWindowModality(Qt.WindowModal)
        self.setWindowTitle(self.tr("Add Glyphs…"))
        self.currentGlyphs = currentGlyphs
        self.currentGlyphNames = [glyph.name for glyph in currentGlyphs]

        layout = QGridLayout(self)
        self.markColorWidget = ColorVignette(self)
        self.markColorWidget.setFixedWidth(56)
        self.importCharDrop = QComboBox(self)
        self.importCharDrop.addItem(self.tr("Import glyphnames…"))
        glyphSets = readGlyphSets()
        for name, glyphNames in glyphSets.items():
            self.importCharDrop.addItem(name, glyphNames)
        self.importCharDrop.currentIndexChanged[int].connect(self.importGlyphs)
        self.addGlyphsEdit = QPlainTextEdit(self)
        self.addGlyphsEdit.setFocus(True)

        self.addUnicodeBox = QCheckBox(self.tr("Add Unicode"), self)
        self.addUnicodeBox.setChecked(True)
        self.addAsTemplateBox = QCheckBox(self.tr("Add as template"), self)
        self.addAsTemplateBox.setChecked(True)
        self.sortFontBox = QCheckBox(self.tr("Sort font"), self)
        self.overrideBox = QCheckBox(self.tr("Override"), self)
        buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        l = 0
        layout.addWidget(self.markColorWidget, l, 0)
        layout.addWidget(self.importCharDrop, l, 3, 1, 2)
        l += 1
        layout.addWidget(self.addGlyphsEdit, l, 0, 1, 5)
        l += 1
        layout.addWidget(self.addUnicodeBox, l, 0)
        layout.addWidget(self.addAsTemplateBox, l, 1)
        layout.addWidget(self.sortFontBox, l, 2)
        layout.addWidget(self.overrideBox, l, 3)
        layout.addWidget(buttonBox, l, 4)
        self.setLayout(layout)

    @classmethod
    def getNewGlyphNames(cls, parent, currentGlyphs=None):
        dialog = cls(currentGlyphs, parent)
        result = dialog.exec_()
        markColor = dialog.markColorWidget.color()
        if markColor is not None:
            markColor = markColor.getRgbF()
        params = dict(
            addUnicode=dialog.addUnicodeBox.isChecked(),
            asTemplate=dialog.addAsTemplateBox.isChecked(),
            markColor=markColor,
            override=dialog.overrideBox.isChecked(),
            sortFont=dialog.sortFontBox.isChecked(),
        )
        newGlyphNames = []
        for name in dialog.addGlyphsEdit.toPlainText().split():
            if name not in dialog.currentGlyphNames:
                newGlyphNames.append(name)
        return (newGlyphNames, params, result)

    def importGlyphs(self, index):
        if index == 0:
            return
        glyphNames = self.importCharDrop.currentData()
        editorNames = self.addGlyphsEdit.toPlainText().split()
        currentNames = set(self.currentGlyphNames) ^ set(editorNames)
        changed = False
        for name in glyphNames:
            if name not in currentNames:
                changed = True
                editorNames.append(name)
        if changed:
            self.addGlyphsEdit.setPlainText(" ".join(editorNames))
            cursor = self.addGlyphsEdit.textCursor()
            cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
            self.addGlyphsEdit.setTextCursor(cursor)
        self.importCharDrop.setCurrentIndex(0)
        self.addGlyphsEdit.setFocus(True)


class SortDialog(QDialog):

    def __init__(self, desc=None, parent=None):
        super(SortDialog, self).__init__(parent)
        self.setWindowModality(Qt.WindowModal)
        self.setWindowTitle(self.tr("Sort…"))

        self.smartSortBox = QRadioButton(self.tr("Canned sort"), self)
        self.smartSortBox.setToolTip(
            self.tr("A combination of simple, complex and custom "
                    "sorts that give optimized ordering results."))
        self.glyphSetBox = QRadioButton(self.tr("Glyph set"), self)
        self.glyphSetBox.toggled.connect(self.glyphSetToggle)
        self.glyphSetDrop = QComboBox(self)
        self.glyphSetDrop.setEnabled(False)
        glyphSets = readGlyphSets()
        for name, glyphNames in glyphSets.items():
            self.glyphSetDrop.addItem(name, glyphNames)
        self.customSortBox = QRadioButton(self.tr("Custom…"), self)
        self.customSortBox.toggled.connect(self.customSortToggle)

        self.customSortGroup = QGroupBox(parent=self)
        self.customSortGroup.setEnabled(False)
        descriptorsCount = 6
        if desc is None:
            # sort fetched from public.glyphOrder. no-op
            pass
        elif isinstance(desc, GlyphSet):
            self.glyphSetBox.setChecked(True)
            self.glyphSetDrop.setEnabled(True)
            self.glyphSetDrop.setCurrentText(desc.name)
        elif desc[0]["type"] == "cannedDesign":
            self.smartSortBox.setChecked(True)
        else:
            self.customSortBox.setChecked(True)
            self.customSortGroup.setEnabled(True)
            descriptorsCount = len(desc)
        self.customDescriptors = [[] for i in range(descriptorsCount)]
        self.customSortLayout = QGridLayout()
        for i, line in enumerate(self.customDescriptors):
            line.append(QComboBox(self))
            line[0].insertItems(0, sortItems)
            line.append(QCheckBox(self.tr("Ascending"), self))
            line.append(QCheckBox(self.tr("Allow pseudo-unicode"), self))
            if self.customSortBox.isChecked():
                line[0].setCurrentIndex(
                    self.indexFromItemName(desc[i]["type"]))
                line[1].setChecked(desc[i]["ascending"])
                line[2].setChecked(desc[i]["allowPseudoUnicode"])
            else:
                line[0].setCurrentIndex(i)
                line[1].setChecked(True)
                line[2].setChecked(True)
            self.customSortLayout.addWidget(line[0], i, 0)
            self.customSortLayout.addWidget(line[1], i, 1)
            self.customSortLayout.addWidget(line[2], i, 2)
            btn = QPushButton(self)
            btn.setFixedWidth(32)
            btn.setProperty("index", i)
            line.append(btn)
            self.customSortLayout.addWidget(btn, i, 3)
            if i == 0:
                btn.setText("+")
                btn.clicked.connect(self._addRow)
                self.addLineButton = btn
            else:
                btn.setText("−")
                btn.clicked.connect(self._deleteRow)
        self.customSortGroup.setLayout(self.customSortLayout)

        buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.smartSortBox)
        layout.addWidget(self.glyphSetBox)
        layout.addWidget(self.glyphSetDrop)
        layout.addWidget(self.customSortBox)
        layout.addWidget(self.customSortGroup)
        layout.addWidget(buttonBox)
        self.setLayout(layout)

    def _addRow(self):
        i = len(self.customDescriptors)
        line = []
        line.append(QComboBox(self))
        line[0].insertItems(0, sortItems)
        line[0].setCurrentIndex(0)
        line.append(QCheckBox("Ascending", self))
        line.append(QCheckBox("Allow pseudo-unicode", self))
        btn = QPushButton("−", self)
        btn.setFixedWidth(32)
        btn.setProperty("index", i)
        btn.clicked.connect(self._deleteRow)
        line.append(btn)
        self.customDescriptors.append(line)
        self.customSortLayout.addWidget(line[0], i, 0)
        self.customSortLayout.addWidget(line[1], i, 1)
        self.customSortLayout.addWidget(line[2], i, 2)
        self.customSortLayout.addWidget(line[3], i, 3)
        if i == 7:
            self.sender().setEnabled(False)

    def _deleteRow(self):
        rel = self.sender().property("index")
        desc = self.customDescriptors
        for i in range(rel + 1, len(desc) - 1):
            desc[i][0].setCurrentIndex(desc[i + 1][0].currentIndex())
            desc[i][1].setChecked(desc[i + 1][1].isChecked())
            desc[i][2].setChecked(desc[i + 1][2].isChecked())
        for elem in desc[-1]:
            elem.setParent(None)
        del self.customDescriptors[-1]
        self.addLineButton.setEnabled(True)
        self.adjustSize()

    def indexFromItemName(self, name):
        for index, item in enumerate(sortItems):
            if name == item:
                return index
        print(self.tr("Unknown descriptor name: %s"), name)
        return 0

    @classmethod
    def getDescriptor(cls, parent, sortDescriptor=None):
        dialog = cls(sortDescriptor, parent)
        result = dialog.exec_()
        if dialog.glyphSetBox.isChecked():
            data = dialog.glyphSetDrop.currentData()
            name = dialog.glyphSetDrop.currentText()
            ret = GlyphSet(data, name)
        elif dialog.customSortBox.isChecked():
            descriptors = []
            for line in dialog.customDescriptors:
                descriptors.append(dict(type=line[0].currentText(),
                                        ascending=line[1].isChecked(),
                                        allowPseudoUnicode=line[2].isChecked()
                                        ))
            ret = descriptors
        else:
            ret = cannedDesign
        return (ret, result)

    def glyphSetToggle(self):
        checkBox = self.sender()
        self.glyphSetDrop.setEnabled(checkBox.isChecked())

    def customSortToggle(self):
        checkBox = self.sender()
        self.customSortGroup.setEnabled(checkBox.isChecked())


class MainWindow(QMainWindow):

    def __init__(self, font):
        super(MainWindow, self).__init__()
        self.setAttribute(Qt.WA_DeleteOnClose)
        self._font = None
        self._sortDescriptor = None

        self.collectionWidget = GlyphCollectionWidget(self)
        self.font = font
        self.collectionWidget.glyphSelectedCallback = self._selectionChanged
        self.collectionWidget.doubleClickCallback = self._glyphOpened
        # TODO: should default be True or False?
        self.collectionWidget.updateCurrentGlyph = True
        self.collectionWidget.setFocus()

        menuBar = self.menuBar()
        # TODO: make shortcuts platform-independent
        fileMenu = QMenu(self.tr("&File"), self)
        fileMenu.addAction(self.tr("&New…"), self.newFile, QKeySequence.New)
        fileMenu.addAction(self.tr("&Open…"), self.openFile,
                           QKeySequence.Open)
        # recent files
        self.recentFilesMenu = QMenu(self.tr("Open &Recent"), self)
        for i in range(MAX_RECENT_FILES):
            action = QAction(self.recentFilesMenu)
            action.setVisible(False)
            action.triggered.connect(self.openRecentFile)
            self.recentFilesMenu.addAction(action)
        self.updateRecentFiles()
        fileMenu.addMenu(self.recentFilesMenu)
        fileMenu.addAction(self.tr("&Import…"), self.importFile)
        fileMenu.addSeparator()
        fileMenu.addAction(self.tr("&Save"), self.saveFile, QKeySequence.Save)
        fileMenu.addAction(self.tr("Save &As…"), self.saveFileAs,
                           QKeySequence.SaveAs)
        fileMenu.addAction(self.tr("&Export…"), self.exportFile)
        fileMenu.addAction(self.tr("&Reload From Disk"), self.reloadFile)
        fileMenu.addAction(self.tr("E&xit"), self.close, QKeySequence.Quit)
        menuBar.addMenu(fileMenu)

        editMenu = QMenu(self.tr("&Edit"), self)
        self._undoAction = editMenu.addAction(
            self.tr("&Undo"), self.undo, QKeySequence.Undo)
        self._redoAction = editMenu.addAction(
            self.tr("&Redo"), self.redo, QKeySequence.Redo)
        editMenu.addSeparator()
        self.markColorMenu = QMenu(self.tr("&Flag Color"), self)
        self.updateMarkColors()
        editMenu.addMenu(self.markColorMenu)
        cut = editMenu.addAction(self.tr("C&ut"), self.cut, QKeySequence.Cut)
        copy = editMenu.addAction(self.tr("&Copy"), self.copy,
                                  QKeySequence.Copy)
        copyComponent = editMenu.addAction(
            self.tr("Copy &As Component"), self.copyAsComponent, "Ctrl+Alt+C")
        paste = editMenu.addAction(
            self.tr("&Paste"), self.paste, QKeySequence.Paste)
        self._clipboardActions = (cut, copy, copyComponent, paste)
        editMenu.addSeparator()
        editMenu.addAction(self.tr("&Settings…"), self.settings)
        menuBar.addMenu(editMenu)

        fontMenu = QMenu(self.tr("&Font"), self)
        # TODO: work out sensible shortcuts and make sure they're
        # cross-platform ready - consider extracting them into separate file?
        fontMenu.addAction(self.tr("&Add Glyphs…"), self.addGlyphs,
                           "Ctrl+G")
        fontMenu.addAction(self.tr("Font &Info"), self.fontInfo,
                           "Ctrl+Alt+I")
        fontMenu.addAction(self.tr("Font &Features"), self.fontFeatures,
                           "Ctrl+Alt+F")
        fontMenu.addSeparator()
        fontMenu.addAction(self.tr("&Sort…"), self.sortGlyphs)
        menuBar.addMenu(fontMenu)

        pythonMenu = QMenu(self.tr("&Python"), self)
        pythonMenu.addAction(self.tr("Scripting &Window"), self.scripting,
                             "Ctrl+Alt+R")
        menuBar.addMenu(pythonMenu)

        windowMenu = QMenu(self.tr("&Windows"), self)
        action = windowMenu.addAction(self.tr("&Inspector"), self.inspector,
                                      "Ctrl+I")
        # XXX: we're getting duplicate shortcut when we spawn a new window...
        action.setShortcutContext(Qt.ApplicationShortcut)
        windowMenu.addAction(self.tr("&Metrics Window"), self.metrics,
                             "Ctrl+Alt+S")
        windowMenu.addAction(self.tr("&Groups Window"), self.groups,
                             "Ctrl+Alt+G")
        menuBar.addMenu(windowMenu)

        helpMenu = QMenu(self.tr("&Help"), self)
        helpMenu.addAction(self.tr("&About"), self.about)
        helpMenu.addAction(self.tr("About &Qt"),
                           QApplication.instance().aboutQt)
        menuBar.addMenu(helpMenu)

        self.sqSizeSlider = QSlider(Qt.Horizontal, self)
        self.sqSizeSlider.setMinimum(36)
        self.sqSizeSlider.setMaximum(96)
        self.sqSizeSlider.setFixedWidth(.9 * self.sqSizeSlider.width())
        self.sqSizeSlider.setValue(self.collectionWidget.squareSize)
        self.sqSizeSlider.valueChanged.connect(self._squareSizeChanged)
        self.selectionLabel = QLabel(self)
        statusBar = self.statusBar()
        statusBar.addPermanentWidget(self.sqSizeSlider)
        statusBar.addWidget(self.selectionLabel)

        app = QApplication.instance()
        self._updateGlyphActions()
        app.currentGlyphChanged.connect(self._updateGlyphActions)

        self.setCentralWidget(self.collectionWidget.scrollArea())
        self.resize(605, 430)
        if font is not None:
            self.setCurrentFile(font.path)
        self.setWindowTitle()

    def newFile(self):
        QApplication.instance().newFile()

    def openFile(self):
        path, _ = QFileDialog.getOpenFileName(
            self, self.tr("Open File"), '',
            platformSpecific.fileFormats
        )
        if path:
            QApplication.instance().openFile(path)

    def openRecentFile(self):
        fontPath = self.sender().toolTip()
        QApplication.instance().openFile(fontPath)

    def saveFile(self, path=None, ufoFormatVersion=3):
        if path is None and self.font.path is None:
            self.saveFileAs()
        else:
            if path is None:
                path = self.font.path
            app = QApplication.instance()
            data = dict(
                font=self.font,
                path=path,
            )
            app.postNotification("fontWillSave", data)
            glyphs = self.collectionWidget.glyphs
            # TODO: save sortDescriptor somewhere in lib as well
            glyphNames = []
            for glyph in glyphs:
                glyphNames.append(glyph.name)
            self.font.lib["public.glyphOrder"] = glyphNames
            self.font.save(path, ufoFormatVersion)
            for glyph in self.font:
                glyph.dirty = False
            self.font.dirty = False
            self.setCurrentFile(path)
            self.setWindowModified(False)
            app.postNotification("fontSaved", data)

    def saveFileAs(self):
        fileFormats = OrderedDict([
            (self.tr("UFO Font version 3 {}").format("(*.ufo)"), 3),
            (self.tr("UFO Font version 2 {}").format("(*.ufo)"), 2),
        ])
        # TODO: see if OSX works nicely with UFO as files, then switch
        # to directory on platforms that need it
        dialog = QFileDialog(self, self.tr("Save File"), None,
                             ";;".join(fileFormats.keys()))
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        ok = dialog.exec_()
        if ok:
            nameFilter = dialog.selectedNameFilter()
            path = dialog.selectedFiles()[0]
            self.saveFile(path, fileFormats[nameFilter])
            self.setWindowTitle()
        # return ok

    def importFile(self):
        try:
            import extractor
        except Exception as e:
            errorReports.showCriticalException(e)
            return

        # TODO: systematize this
        fileFormats = (
            self.tr("OpenType Font file {}").format("(*.otf *.ttf)"),
            self.tr("Type1 Font file {}").format("(*.pfa *.pfb)"),
            self.tr("ttx Font file {}").format("(*.ttx)"),
            self.tr("WOFF Font file {}").format("(*.woff)"),
            self.tr("All supported files {}").format(
                "(*.otf *.pfa *.pfb *.ttf *.ttx *.woff)"),
            self.tr("All files {}").format("(*.*)"),
        )

        path, _ = QFileDialog.getOpenFileName(
            self, self.tr("Import File"), None,
            ";;".join(fileFormats), fileFormats[-2])

        if path:
            font = TFont()
            fileFormat = extractor.extractFormat(path)
            try:
                extractor.extractUFO(path, font, fileFormat)
            except Exception as e:
                errorReports.showCriticalException(e)
                return
            else:
                app = QApplication.instance()
                data = dict(
                    font=font,
                    format=fileFormat,
                )
                app.postNotification("binaryFontWillOpen", data)
            window = MainWindow(font)
            window.show()

    def exportFile(self):
        # check for missing required attributes
        missingAttrs = []
        for attr in ("familyName", "styleName", "unitsPerEm", "ascender",
                     "descender", "xHeight", "capHeight"):
            if getattr(self.font.info, attr) is None:
                missingAttrs.append(attr)
        if len(missingAttrs):
            text = self.tr("Attributes required for font generation are "
                           "missing: {}").format(" ".join(missingAttrs))
            QMessageBox.critical(self, "Export Error", text)
            return
        # go ahead
        path, _ = QFileDialog.getSaveFileName(
            self, self.tr("Export File"), None,
            self.tr("OpenType PS font {}").format("(*.otf)"))
        if path:
            app = QApplication.instance()
            data = dict(
                font=self.font,
                format="otf",
                path=path,
            )
            app.postNotification("fontWillGenerate", data)
            try:
                otf = self.font.getRepresentation("trufont.TTFont")
            except Exception as e:
                errorReports.showCriticalException(e)
                return
            otf.save(path)
            app.postNotification("fontGenerated", data)

    def undo(self):
        glyph = self.collectionWidget.lastSelectedGlyph()
        glyph.undo()

    def redo(self):
        glyph = self.collectionWidget.lastSelectedGlyph()
        glyph.redo()

    def setCurrentFile(self, path):
        if path is None:
            return
        settings = QSettings()
        recentFiles = settings.value("core/recentFiles", [], type=str)
        if path in recentFiles:
            recentFiles.remove(path)
        recentFiles.insert(0, path)
        while len(recentFiles) > MAX_RECENT_FILES:
            del recentFiles[-1]
        settings.setValue("core/recentFiles", recentFiles)
        for window in QApplication.topLevelWidgets():
            if isinstance(window, MainWindow):
                window.updateRecentFiles()

    def updateRecentFiles(self):
        settings = QSettings()
        recentFiles = settings.value("core/recentFiles", [], type=str)
        count = min(len(recentFiles), MAX_RECENT_FILES)
        actions = self.recentFilesMenu.actions()
        for index, recentFile in enumerate(recentFiles[:count]):
            action = actions[index]
            shortName = os.path.basename(recentFile.rstrip(os.sep))

            action.setText(shortName)
            action.setToolTip(recentFile)
            action.setVisible(True)
        for index in range(count, MAX_RECENT_FILES):
            actions[index].setVisible(False)

        self.recentFilesMenu.setEnabled(len(recentFiles))

    def updateMarkColors(self):
        entries = readMarkColors()
        self.markColorMenu.clear()
        pixmap = QPixmap(24, 24)
        none = self.markColorMenu.addAction("None", self.markColor)
        none.setData(None)
        for name, color in entries.items():
            action = self.markColorMenu.addAction(name, self.markColor)
            pixmap.fill(color)
            action.setIcon(QIcon(pixmap))
            action.setData(color)

    def _updateGlyphActions(self):
        currentGlyph = self.collectionWidget.lastSelectedGlyph()
        # disconnect eventual signal of previous glyph
        self._undoAction.disconnect()
        self._undoAction.triggered.connect(self.undo)
        self._redoAction.disconnect()
        self._redoAction.triggered.connect(self.redo)
        # now update status
        if currentGlyph is None:
            self._undoAction.setEnabled(False)
            self._redoAction.setEnabled(False)
        else:
            undoManager = currentGlyph.undoManager
            self._undoAction.setEnabled(currentGlyph.canUndo())
            undoManager.canUndoChanged.connect(self._undoAction.setEnabled)
            self._redoAction.setEnabled(currentGlyph.canRedo())
            undoManager.canRedoChanged.connect(self._redoAction.setEnabled)
        # and other actions
        for action in self._clipboardActions:
            action.setEnabled(currentGlyph is not None)
        self.markColorMenu.setEnabled(currentGlyph is not None)

    def closeEvent(self, event):
        ok = self.maybeSaveBeforeExit()
        if ok:
            app = QApplication.instance()
            data = dict(font=self.font)
            app.postNotification("fontWillClose", data)
            self.font.removeObserver(self, "Font.Changed")
            event.accept()
        else:
            event.ignore()

    def maybeSaveBeforeExit(self):
        if self.font.dirty:
            currentFont = self.windowTitle()[3:]
            body = self.tr("Do you want to save the changes you made "
                           "to “{}”?").format(currentFont)
            closeDialog = QMessageBox(
                QMessageBox.Question, None, body,
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                self)
            closeDialog.setInformativeText(
                self.tr("Your changes will be lost if you don’t save them."))
            closeDialog.setModal(True)
            ret = closeDialog.exec_()
            if ret == QMessageBox.Save:
                self.saveFile()
                return True
            elif ret == QMessageBox.Discard:
                return True
            return False
        return True

    def reloadFile(self):
        font = self._font
        if font.path is None:
            return
        font.reloadInfo()
        font.reloadKerning()
        font.reloadGroups()
        font.reloadFeatures()
        font.reloadLib()
        font.reloadGlyphs(font.keys())
        self.setWindowModified(False)

    def _get_font(self):
        return self._font

    # TODO: consider that user may want to change font without sortDescriptor
    # be calculated and set magically (and therefore, arbitrarily)
    # In that case is it reasonable to just leave self._font?
    def _set_font(self, font):
        if self._font is not None:
            self._font.removeObserver(self, "Font.Changed")
            self._font.removeObserver(self, "Font.GlyphOrderChanged")
        self._font = font
        if self._font is None:
            return
        if self._font.glyphOrder is None:
            # TODO: cannedDesign or carry sortDescriptor from prev. font?
            self.sortDescriptor = cannedDesign
        else:
            # use the glyphOrder from the font
            self.sortDescriptor = None
        self._font.addObserver(self, "_fontChanged", "Font.Changed")
        self._font.addObserver(
            self, "_glyphOrderChanged", "Font.GlyphOrderChanged")

    font = property(_get_font, _set_font, doc="The fontView font. Subscribes \
        to the new font, updates the sorting order and cells widget when set.")

    def _get_sortDescriptor(self):
        return self._sortDescriptor

    def _set_sortDescriptor(self, desc):
        if desc is None:
            self.updateGlyphsFromFont()
        elif isinstance(desc, GlyphSet):
            self._font.glyphOrder = desc.glyphNames
        else:
            self._font.glyphOrder = self._font.unicodeData.sortGlyphNames(
                self._font.keys(), desc)
        self._sortDescriptor = desc

    sortDescriptor = property(_get_sortDescriptor, _set_sortDescriptor,
                              doc="The sortDescriptor. Takes glyphs from the "
                              "font and sorts them when set.")

    def getGlyphs(self):
        return self.collectionWidget.glyphs

    def cut(self):
        self.copy()
        glyphs = self.collectionWidget.glyphs
        for index in self.collectionWidget.selection:
            glyph = glyphs[index]
            glyph.clear()

    def copy(self):
        glyphs = self.collectionWidget.glyphs
        pickled = []
        for index in sorted(self.collectionWidget.selection):
            pickled.append(glyphs[index].serialize(
                blacklist=("name", "unicode")
            ))
        clipboard = QApplication.clipboard()
        mimeData = QMimeData()
        mimeData.setData("application/x-trufont-glyph-data",
                         pickle.dumps(pickled))
        clipboard.setMimeData(mimeData)

    def copyAsComponent(self):
        glyphs = self.collectionWidget.glyphs
        pickled = []
        for index in sorted(self.collectionWidget.selection):
            glyph = glyphs[index]
            componentGlyph = TGlyph()
            componentGlyph.width = glyph.width
            component = TComponent()
            component.baseGlyph = glyph.name
            componentGlyph.appendComponent(component)
            pickled.append(componentGlyph.serialize())
        clipboard = QApplication.clipboard()
        mimeData = QMimeData()
        mimeData.setData("application/x-trufont-glyph-data",
                         pickle.dumps(pickled))
        clipboard.setMimeData(mimeData)

    def paste(self):
        clipboard = QApplication.clipboard()
        mimeData = clipboard.mimeData()
        if mimeData.hasFormat("application/x-trufont-glyph-data"):
            data = pickle.loads(mimeData.data(
                "application/x-trufont-glyph-data"))
            glyphs = self.collectionWidget.getSelectedGlyphs()
            if len(data) == len(glyphs):
                for pickled, glyph in zip(data, glyphs):
                    # XXX: prune
                    glyph.prepareUndo()
                    glyph.deserialize(pickled)

    def settings(self):
        if hasattr(self, 'settingsWindow') and self.settingsWindow.isVisible():
            self.settingsWindow.raise_()
        else:
            self.settingsWindow = SettingsDialog(self)
            self.settingsWindow.show()

    def markColor(self):
        color = self.sender().data()
        glyphs = self.collectionWidget.glyphs
        for key in self.collectionWidget.selection:
            glyph = glyphs[key]
            glyph.markColor = Color(
                color.getRgbF()) if color is not None else None

    def _fontChanged(self, notification):
        self.collectionWidget.update()
        self.setWindowModified(self._font.dirty)

    def _glyphOrderChanged(self, notification):
        self.updateGlyphsFromFont()

    def updateGlyphsFromFont(self):
        glyphOrder = self._font.glyphOrder
        if len(glyphOrder):
            glyphs = []
            for glyphName in glyphOrder:
                if glyphName in self._font:
                    glyphs.append(self._font[glyphName])
            if len(glyphs) < len(self._font):
                # if some glyphs in the font are not present in the glyph
                # order, loop again to add them at the end
                for glyph in self._font:
                    if glyph not in glyphs:
                        glyphs.append(glyph)
        else:
            glyphs = list(self._font)
        self.collectionWidget.glyphs = glyphs

    def _glyphOpened(self, glyph):
        glyphViewWindow = MainGlyphWindow(glyph, self)
        glyphViewWindow.show()

    def _selectionChanged(self, selection):
        if selection is not None:
            if isinstance(selection, str):
                count = 1
                text = "%s " % selection
            else:
                count = selection
                text = ""
            if not count == 0:
                text = self.tr("{0}(%n selected)".format(text), n=count)
        else:
            text = ""
        self.selectionLabel.setText(text)

    def _squareSizeChanged(self):
        squareSize = self.sqSizeSlider.value()
        self.collectionWidget.squareSize = squareSize
        QToolTip.showText(QCursor.pos(), str(squareSize), self)

    def event(self, event):
        if event.type() == QEvent.WindowActivate:
            app = QApplication.instance()
            app.setCurrentMainWindow(self)
            lastSelectedGlyph = self.collectionWidget.lastSelectedGlyph()
            if lastSelectedGlyph is not None:
                app.setCurrentGlyph(lastSelectedGlyph)
        return super(MainWindow, self).event(event)

    def setWindowTitle(self, title=None):
        if title is None:
            if self.font.path is not None:
                title = os.path.basename(self.font.path.rstrip(os.sep))
            else:
                title = self.tr("Untitled.ufo")
        super(MainWindow, self).setWindowTitle("[*]{}".format(title))

    def fontInfo(self):
        # If a window is already opened, bring it to the front, else spawn one.
        # TODO: see about using widget.setAttribute(Qt.WA_DeleteOnClose)
        # otherwise it seems we're just leaking memory after each close...
        # (both raise_ and show allocate memory instead of using the hidden
        # widget it seems)
        if not (hasattr(self, 'fontInfoWindow')
                and self.fontInfoWindow.isVisible()):
            self.fontInfoWindow = TabDialog(self.font, self)
            self.fontInfoWindow.show()
        else:
            # Should data be rewind if user calls font info while one is open?
            # I'd say no, but this has yet to be settled.
            self.fontInfoWindow.raise_()

    def fontFeatures(self):
        # TODO: see up here
        if not (hasattr(self, 'fontFeaturesWindow')
                and self.fontFeaturesWindow.isVisible()):
            self.fontFeaturesWindow = MainEditWindow(self.font, self)
            self.fontFeaturesWindow.show()
        else:
            self.fontFeaturesWindow.raise_()

    def metrics(self):
        # TODO: see up here
        if not (hasattr(self, 'metricsWindow')
                and self.metricsWindow.isVisible()):
            self.metricsWindow = MainMetricsWindow(self.font, parent=self)
            self.metricsWindow.show()
        else:
            self.metricsWindow.raise_()
        # TODO: default string kicks-in on the window before this. Figure out
        # how to make a clean interface
        selection = self.collectionWidget.selection
        if selection:
            glyphs = []
            for item in sorted(selection):
                glyph = self.collectionWidget.glyphs[item]
                glyphs.append(glyph)
            self.metricsWindow.setGlyphs(glyphs)

    def groups(self):
        # TODO: see up here
        if not (hasattr(self, 'groupsWindow')
                and self.groupsWindow.isVisible()):
            self.groupsWindow = GroupsWindow(self.font, self)
            self.groupsWindow.show()
        else:
            self.groupsWindow.raise_()

    def scripting(self):
        app = QApplication.instance()
        if not hasattr(app, 'scriptingWindow'):
            app.scriptingWindow = MainScriptingWindow()
            app.scriptingWindow.show()
        elif app.scriptingWindow.isVisible():
            app.scriptingWindow.raise_()
        else:
            app.scriptingWindow.show()

    def inspector(self):
        app = QApplication.instance()
        if not hasattr(app, 'inspectorWindow'):
            app.inspectorWindow = InspectorWindow()
            app.inspectorWindow.show()
        elif app.inspectorWindow.isVisible():
            # TODO: do this only if the widget is user-visible, otherwise the
            # key press feels as if it did nothing
            # toggle
            app.inspectorWindow.close()
        else:
            app.inspectorWindow.show()

    def sortGlyphs(self):
        sortDescriptor, ok = SortDialog.getDescriptor(self,
                                                      self.sortDescriptor)
        if ok:
            self.sortDescriptor = sortDescriptor

    def addGlyphs(self):
        glyphs = self.collectionWidget.glyphs
        newGlyphNames, params, ok = AddGlyphsDialog.getNewGlyphNames(
            self, glyphs)
        if ok:
            sortFont = params.pop("sortFont")
            for name in newGlyphNames:
                glyph = self.font.newStandardGlyph(name, **params)
                if glyph is not None:
                    glyphs.append(glyph)
            self.collectionWidget.glyphs = glyphs
            if sortFont:
                # TODO: when the user add chars from a glyphSet and no others,
                # should we try to sort according to that glyphSet?
                # The above would probably warrant some rearchitecturing.
                # kick-in the sort mechanism
                self.sortDescriptor = self.sortDescriptor

    def about(self):
        name = QApplication.applicationName()
        domain = QApplication.organizationDomain()
        text = self.tr(
            "<h3>About {n}</h3>"
            "<p>{n} is a cross-platform, modular typeface design "
            "application.</p><p>{n} is built on top of "
            "<a href='http://ts-defcon.readthedocs.org/en/ufo3/'>defcon</a> "
            "and includes scripting support "
            "with a <a href='http://robofab.com/'>robofab</a>-like API.</p>"
            "<p>Version {} {} – Python {}.").format(
            __version__, gitShortHash, platform.python_version(), n=name)
        if domain:
            text += self.tr("<br>See <a href='http://{d}'>{d}</a> for more "
                            "information.</p>").format(d=domain)
        else:
            text += "</p>"
        QMessageBox.about(self, self.tr("About {}").format(name), text)


class SettingsDialog(QDialog):

    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        # self.setWindowModality(Qt.WindowModal)
        self.setWindowTitle(self.tr("Settings"))

        self.tabWidget = QTabWidget(self)
        self.tabWidget.addTab(GlyphSetTab(self), self.tr("Glyph sets"))
        self.tabWidget.addTab(MetricsWindowTab(self),
                              self.tr("Metrics Window"))
        self.tabWidget.addTab(MiscTab(self), self.tr("Misc"))

        buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.tabWidget)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

    def accept(self):
        for i in range(self.tabWidget.count()):
            self.tabWidget.widget(i).writeValues()
        app = QApplication.instance()
        app.postNotification("preferencesChanged")
        # TODO: cleanup this in favor of notification subscribe
        # and implement subscription in the widgets
        for window in app.topLevelWidgets():
            if isinstance(window, MainWindow):
                window.updateMarkColors()
        super(SettingsDialog, self).accept()


def getDefaultGlyphSet(settings=None):
    if settings is None:
        settings = QSettings()
    settings.value("settings/defaultGlyphSet", latinDefault.name, str)


def readGlyphSets(settings=None):
    if settings is None:
        settings = QSettings()
    size = settings.beginReadArray("glyphSets")
    # TODO: maybe cache this in qApp
    glyphSets = {}
    if not size:
        glyphSets[latinDefault.name] = latinDefault.glyphNames
    for i in range(size):
        settings.setArrayIndex(i)
        glyphSetName = settings.value("name", type=str)
        glyphSetGlyphNames = settings.value("glyphNames", type=str)
        glyphSets[glyphSetName] = glyphSetGlyphNames
    settings.endArray()
    return glyphSets


class GlyphSetTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        settings = QSettings()
        self.defaultGlyphSetBox = QCheckBox(self.tr("Default glyph set:"),
                                            self)
        self.defaultGlyphSetDrop = QComboBox(self)
        defaultGlyphSet = settings.value(
            "settings/defaultGlyphSet", latinDefault.name, str)
        self.defaultGlyphSetBox.toggled.connect(self.toggleGlyphSetDrop)
        self.defaultGlyphSetBox.setChecked(len(defaultGlyphSet))
        self.glyphSets = readGlyphSets()
        glyphSetNames = self.glyphSets.keys()
        self.defaultGlyphSetDrop.addItems(glyphSetNames)

        self.glyphSetList = QListWidget(self)
        self.glyphSetList.setSortingEnabled(True)
        self.glyphSetContents = QTextEdit(self)
        self.glyphSetContents.setAcceptRichText(False)
        self.glyphSetList.currentItemChanged.connect(
            self.updateGlyphSetContents)
        self.glyphSetList.itemChanged.connect(self.renameGlyphSet)
        self._cachedName = None
        # Normally we should enforce this rather decently in the interface
        # already
        if glyphSetNames:
            for glyphSetName in glyphSetNames:
                item = QListWidgetItem(glyphSetName, self.glyphSetList)
                item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.glyphSetList.setCurrentRow(0)
        splitter = QSplitter()
        splitter.addWidget(self.glyphSetList)
        splitter.addWidget(self.glyphSetContents)
        self.addGlyphSetButton = QPushButton("+", self)
        self.addGlyphSetButton.clicked.connect(lambda: self.addGlyphSet())
        self.removeGlyphSetButton = QPushButton("−", self)
        self.removeGlyphSetButton.setEnabled(len(self.glyphSets) > 1)
        self.removeGlyphSetButton.clicked.connect(self.removeGlyphSet)
        self.importButton = QPushButton(self.tr("Import"), self)
        importMenu = QMenu(self)
        importMenu.addAction(self.tr("Import from current font"),
                             self.importFromCurrentFont)
        self.importButton.setMenu(importMenu)
        glyphListPath = settings.value("settings/glyphListPath", type=str)
        self.glyphListBox = QCheckBox(self.tr("Glyph list path:"), self)
        self.glyphListBox.setChecked(bool(glyphListPath))
        self.glyphListEdit = QLineEdit(glyphListPath, self)
        self.glyphListEdit.setEnabled(bool(glyphListPath))
        self.glyphListEdit.setReadOnly(True)
        self.glyphListButton = QPushButton(self.tr("Browse…"), self)
        self.glyphListButton.setEnabled(bool(glyphListPath))
        self.glyphListButton.clicked.connect(self.getGlyphList)
        # TODO: find correct solution for this and maybe make a widget w
        # setSizesToText()
        # http://stackoverflow.com/a/19502467/2037879
        textWidth = self.glyphListButton.fontMetrics().boundingRect(
            self.glyphListButton.text()).width() + 16
        self.glyphListButton.setMaximumWidth(textWidth)
        self.glyphListBox.toggled.connect(self.glyphListEdit.setEnabled)
        self.glyphListBox.toggled.connect(self.glyphListButton.setEnabled)

        firstLayout = QGridLayout()
        l = 0
        firstLayout.addWidget(self.defaultGlyphSetBox, l, 0, 1, 2)
        firstLayout.addWidget(self.defaultGlyphSetDrop, l, 3, 1, 3)
        l += 1
        firstLayout.addWidget(splitter, l, 0, 1, 6)
        l += 1
        firstLayout.addWidget(self.addGlyphSetButton, l, 0)
        firstLayout.addWidget(self.removeGlyphSetButton, l, 1)
        firstLayout.addWidget(self.importButton, l, 2)
        secondLayout = QHBoxLayout()
        secondLayout.addWidget(self.glyphListBox, 0)
        secondLayout.addWidget(self.glyphListEdit, 1)
        secondLayout.addWidget(self.glyphListButton, 2)
        mainLayout = QVBoxLayout()
        mainLayout.addLayout(firstLayout)
        mainLayout.addLayout(secondLayout)
        self.setLayout(mainLayout)

    def addGlyphSet(self, glyphNames=[], glyphSetName=None):
        if glyphSetName is None:
            glyphSetName = self.tr("New glyph set")
        if glyphSetName in self.glyphSets:
            index = 1
            while "%s %d" % (glyphSetName, index) in self.glyphSets:
                index += 1
            glyphSetName = "%s %d" % (glyphSetName, index)
        self.glyphSets[glyphSetName] = glyphNames
        item = QListWidgetItem(glyphSetName, self.glyphSetList)
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        self.glyphSetList.setCurrentItem(item)
        self.glyphSetList.editItem(item)
        self.removeGlyphSetButton.setEnabled(True)

    def removeGlyphSet(self):
        i = self.glyphSetList.currentRow()
        text = self.glyphSetList.takeItem(i).text()
        del self.glyphSets[text]
        if self.glyphSetList.count() < 2:
            self.removeGlyphSetButton.setEnabled(False)

    def renameGlyphSet(self):
        newKey = self.glyphSetList.currentItem()
        if newKey is None:
            return
        newKey = newKey.text()
        self.glyphSets[newKey] = self.glyphSets[self._cachedName]
        del self.glyphSets[self._cachedName]

    def importFromCurrentFont(self):
        currentMainWindow = QApplication.instance().currentMainWindow()
        glyphs = currentMainWindow.getGlyphs()
        info = currentMainWindow.font.info
        name = "%s %s" % (info.familyName, info.styleName)
        self.addGlyphSet([glyph.name for glyph in glyphs], name)

    def toggleGlyphSetDrop(self):
        sender = self.sender()
        self.defaultGlyphSetDrop.setEnabled(sender.isChecked())

    def updateGlyphSetContents(self, current, previous):
        # store content of the textEdit in the glyphSet dict
        if previous is not None:
            glyphNames = self.glyphSetContents.toPlainText().split()
            self.glyphSets[previous.text()] = glyphNames
        # now update the text edit to current glyphSet
        glyphSetName = current.text()
        text = " ".join(self.glyphSets[glyphSetName])
        self.glyphSetContents.setText(text)
        # cache current name for renames
        self._cachedName = glyphSetName

    def writeGlyphSets(self, settings):
        # technically we're already enforcing that this doesn't happen
        if not len(self.glyphSets):
            return
        settings.beginWriteArray("glyphSets", len(self.glyphSets))
        index = 0
        for name, cset in self.glyphSets.items():
            settings.setArrayIndex(index)
            settings.setValue("name", name)
            settings.setValue("glyphNames", cset)
            index += 1
        settings.endArray()

    def getGlyphList(self):
        fileFormats = (
            self.tr("Text file {}").format("(*.txt)"),
            self.tr("All files {}").format("(*.*)"),
        )
        path, _ = QFileDialog.getOpenFileName(
            self, self.tr("Open File"), '', ";;".join(fileFormats)
        )
        if path:
            self.glyphListEdit.setText(path)

    def writeValues(self):
        # store content of the textEdit in the glyphSet dict
        glyphNames = self.glyphSetContents.toPlainText().split()
        currentGlyphSet = self.glyphSetList.currentItem().text()
        self.glyphSets[currentGlyphSet] = glyphNames

        settings = QSettings()
        self.writeGlyphSets(settings)
        if not self.defaultGlyphSetBox.isChecked():
            settings.setValue("settings/defaultGlyphSet", "")
        else:
            defaultGlyphSet = self.defaultGlyphSetDrop.currentText()
            if defaultGlyphSet != latinDefault.name:
                settings.setValue("settings/defaultGlyphSet", defaultGlyphSet)
        if not self.glyphListBox.isChecked():
            settings.setValue("settings/glyphListPath", "")
        else:
            glyphListPath = self.glyphListEdit.text()
            if glyphListPath:
                settings.setValue("settings/glyphListPath", glyphListPath)
                app = QApplication.instance()
                app.loadGlyphList()


class MetricsWindowTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        settings = QSettings()
        self.inputTextLabel = QLabel(self.tr("Default text:"), self)
        self.inputTextList = QListWidget(self)
        self.inputTextList.setDragDropMode(QAbstractItemView.InternalMove)
        entries = settings.value("metricsWindow/comboBoxItems", comboBoxItems,
                                 str)
        for entry in entries:
            item = QListWidgetItem(entry, self.inputTextList)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
        self.addItemButton = QPushButton("+", self)
        self.addItemButton.clicked.connect(self.addItem)
        self.removeItemButton = QPushButton("−", self)
        self.removeItemButton.clicked.connect(self.removeItem)
        if not len(entries):
            self.removeItemButton.setEnabled(False)

        layout = QGridLayout(self)
        l = 0
        layout.addWidget(self.inputTextLabel, l, 0, 1, 3)
        l += 1
        layout.addWidget(self.inputTextList, l, 0, 1, 3)
        l += 1
        layout.addWidget(self.addItemButton, l, 0)
        layout.addWidget(self.removeItemButton, l, 1)
        self.setLayout(layout)

    def addItem(self):
        item = QListWidgetItem(self.inputTextList)
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        self.inputTextList.setCurrentItem(item)
        self.inputTextList.editItem(item)
        self.removeItemButton.setEnabled(True)

    def removeItem(self):
        i = self.inputTextList.currentRow()
        self.inputTextList.takeItem(i)
        if not self.inputTextList.count():
            self.removeItemButton.setEnabled(False)

    def writeValues(self):
        entries = []
        for i in range(self.inputTextList.count()):
            item = self.inputTextList.item(i)
            entries.append(item.text())
        settings = QSettings()
        settings.setValue("metricsWindow/comboBoxItems", entries)


def readMarkColors(settings=None):

    def toQColor(color):
        return QColor.fromRgbF(*Color(color))

    if settings is None:
        settings = QSettings()
    size = settings.beginReadArray("misc/markColors")
    # TODO: maybe cache this in qApp
    markColors = OrderedDict()
    if not size:
        # serialized in UFO form
        markColors["Red"] = toQColor("1,0,0,1")
        markColors["Yellow"] = toQColor("1,1,0,1")
        markColors["Green"] = toQColor("0,1,0,1")
    for i in range(size):
        settings.setArrayIndex(i)
        markColorName = settings.value("name", type=str)
        markColor = settings.value("color", type=str)
        markColors[markColorName] = toQColor(markColor)
    settings.endArray()
    return markColors


class MiscTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        settings = QSettings()
        loadRecentFile = settings.value("misc/loadRecentFile", False, bool)
        self.loadRecentFileBox = QCheckBox(
            self.tr("Load most recent file on start"), self)
        self.loadRecentFileBox.setChecked(loadRecentFile)

        self.markColorLabel = QLabel(self.tr("Default flag colors:"), self)
        # TODO: enforce duplicate names avoidance
        self.markColorWidget = QTreeWidget(self)
        self.markColorWidget.setHeaderLabels((self.tr("Color"),
                                              self.tr("Name")))
        self.markColorWidget.setRootIsDecorated(False)
        self.markColorWidget.setSelectionBehavior(
            QAbstractItemView.SelectRows)
        # TODO: make this work correctly, top-level items only
        # self.markColorWidget.setDragDropMode(QAbstractItemView.InternalMove)
        entries = readMarkColors(settings)
        for name, color in entries.items():
            item = QTreeWidgetItem(self.markColorWidget)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
            widget = ColorVignette(self)
            widget.setColor(color)
            widget.setMargins(2, 2, 2, 2)
            widget.setMayClearColor(False)
            self.markColorWidget.setItemWidget(item, 0, widget)
            item.setText(1, name)
        self.addItemButton = QPushButton("+", self)
        self.addItemButton.clicked.connect(self.addItem)
        self.removeItemButton = QPushButton("−", self)
        self.removeItemButton.clicked.connect(self.removeItem)
        if not len(entries):
            self.removeItemButton.setEnabled(False)

        layout = QGridLayout(self)
        l = 0
        layout.addWidget(self.loadRecentFileBox, l, 0, 1, 3)
        l += 1
        layout.addWidget(self.markColorLabel, l, 0, 1, 3)
        l += 1
        layout.addWidget(self.markColorWidget, l, 0, 1, 3)
        l += 1
        layout.addWidget(self.addItemButton, l, 0)
        layout.addWidget(self.removeItemButton, l, 1)
        self.setLayout(layout)

    def addItem(self):

        def mangleNewName():
            name = self.tr("New")
            index = 0
            while self.markColorWidget.findItems(name, Qt.MatchExactly, 1):
                index += 1
                name = "{0} ({1})".format(name, index)
            return name

        # TODO: not DRY with ctor
        item = QTreeWidgetItem(self.markColorWidget)
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        widget = ColorVignette(self)
        widget.setColor(QColor(Qt.white))
        widget.setMargins(2, 2, 2, 2)
        widget.setMayClearColor(False)
        self.markColorWidget.setItemWidget(item, 0, widget)
        item.setText(1, mangleNewName())

        self.markColorWidget.setCurrentItem(item)
        self.markColorWidget.editItem(item, 1)
        self.removeItemButton.setEnabled(True)

    def removeItem(self):
        i = self.markColorWidget.selectionModel().currentIndex().row()
        self.markColorWidget.takeTopLevelItem(i)
        if not self.markColorWidget.topLevelItemCount():
            self.removeItemButton.setEnabled(False)

    def writeMarkColors(self, settings=None):
        if settings is None:
            settings = QSettings()
        settings.beginWriteArray("misc/markColors")
        # serialized in UFO form
        for i in range(self.markColorWidget.topLevelItemCount()):
            settings.setArrayIndex(i)
            item = self.markColorWidget.topLevelItem(i)
            color = self.markColorWidget.itemWidget(item, 0).color()
            settings.setValue("name", item.text(1))
            settings.setValue("color", str(Color(color.getRgbF())))
        settings.endArray()

    def writeValues(self):
        settings = QSettings()
        loadRecentFile = self.loadRecentFileBox.isChecked()
        settings.setValue("misc/loadRecentFile", loadRecentFile)
        self.writeMarkColors()
