from defconQt.featureTextEditor import MainEditWindow
from defconQt.fontInfo import TabDialog
from defconQt.glyphCollectionView import GlyphCollectionWidget
from defconQt.glyphView import MainGfxWindow
from defconQt.groupsView import GroupsWindow
from defconQt.objects.defcon import CharacterSet, TFont, TGlyph
from defcon import Component
from defconQt.spaceCenter import MainSpaceWindow
from fontTools.agl import AGL2UV
# TODO: remove globs when things start to stabilize
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import os, pickle, unicodedata

cannedDesign = [
    dict(type="cannedDesign", allowPseudoUnicode=True)
]
sortItems = ["alphabetical", "category", "unicode", "script", "suffix",
    "decompositionBase", "weightedSuffix", "ligature"]
latin1 = CharacterSet(
["space","exclam","quotesingle","quotedbl","numbersign","dollar",
"percent","ampersand","parenleft","parenright","asterisk","plus","comma",
"hyphen","period","slash","zero","one","two","three","four","five",
"six","seven","eight","nine","colon","semicolon","less","equal",
"greater","question","at","A","B","C","D","E","F","G","H","I","J",
"K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z",
"bracketleft","backslash","bracketright","asciicircum","underscore","grave",
"a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t",
"u","v","w","x","y","z","braceleft","bar","braceright","asciitilde","exclamdown",
"cent","sterling","currency","yen","brokenbar","section","dieresis","copyright",
"ordfeminine","guillemotleft","logicalnot","registered","macron","degree",
"plusminus","twosuperior","threesuperior","acute","mu","paragraph",
"periodcentered","cedilla","onesuperior","ordmasculine","guillemotright",
"onequarter","onehalf","threequarters","questiondown","Agrave","Aacute",
"Acircumflex","Atilde","Adieresis","Aring","AE","Ccedilla","Egrave","Eacute",
"Ecircumflex","Edieresis","Igrave","Iacute","Icircumflex","Idieresis","Eth",
"Ntilde","Ograve","Oacute","Ocircumflex","Otilde","Odieresis","multiply",
"Oslash","Ugrave","Uacute","Ucircumflex","Udieresis","Yacute","Thorn",
"germandbls","agrave","aacute","acircumflex","atilde","adieresis","aring","ae",
"ccedilla","egrave","eacute","ecircumflex","edieresis","igrave","iacute",
"icircumflex","idieresis","eth","ntilde","ograve","oacute","ocircumflex",
"otilde","odieresis","divide","oslash","ugrave","uacute","ucircumflex",
"udieresis","yacute","thorn","ydieresis","dotlessi","circumflex","caron",
"breve","dotaccent","ring","ogonek","tilde","hungarumlaut","quoteleft",
"quoteright","minus"], "Latin-1")

# TODO: implement Frederik's Glyph Construction Builder
class AddGlyphDialog(QDialog):
    def __init__(self, currentGlyphs=None, parent=None):
        super(AddGlyphDialog, self).__init__(parent)
        self.setWindowModality(Qt.WindowModal)
        self.setWindowTitle("Add glyphs…")
        self.currentGlyphs = currentGlyphs
        self.currentGlyphNames = [glyph.name for glyph in currentGlyphs]

        layout = QGridLayout(self)
        self.importCharDrop = QComboBox(self)
        self.importCharDrop.addItem("Import glyphnames…")
        self.importCharDrop.addItem("Latin-1", latin1)
        self.importCharDrop.currentIndexChanged[int].connect(self.importCharacters)
        self.addGlyphEdit = QPlainTextEdit(self)
        self.addGlyphEdit.setFocus(True)

        self.sortFontBox = QCheckBox("Sort font", self)
        self.overwriteBox = QCheckBox("Override", self)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        l = 0
        layout.addWidget(self.importCharDrop, l, 3)
        l += 1
        layout.addWidget(self.addGlyphEdit, l, 0, 1, 4)
        l += 1
        layout.addWidget(self.sortFontBox, l, 0)
        layout.addWidget(self.overwriteBox, l, 1)
        layout.addWidget(buttonBox, l, 3)
        self.setLayout(layout)

    @staticmethod
    def getNewGlyphNames(parent, currentGlyphs=None):
        dialog = AddGlyphDialog(currentGlyphs, parent)
        result = dialog.exec_()
        sortFont = False
        newGlyphNames = []
        for name in dialog.addGlyphEdit.toPlainText().split():
            if name not in dialog.currentGlyphNames:
                newGlyphNames.append(name)
        if dialog.sortFontBox.isChecked():
            # XXX: if we get here with previous sort being by character set,
            # should it just stick?
            sortFont = True
        return (newGlyphNames, sortFont, result)

    def importCharacters(self, index):
        if index == 0: return
        charset = self.importCharDrop.currentData()
        editorNames = self.addGlyphEdit.toPlainText().split()
        currentNames = set(self.currentGlyphNames) ^ set(editorNames)
        changed = False
        for name in charset.glyphNames:
            if name not in currentNames:
                changed = True
                editorNames.append(name)
        if changed:
            self.addGlyphEdit.setPlainText(" ".join(editorNames))
            cursor = self.addGlyphEdit.textCursor()
            cursor.movePosition(QTextCursor.End, QTextCursor.MoveAnchor)
            self.addGlyphEdit.setTextCursor(cursor)
        self.importCharDrop.setCurrentIndex(0)
        self.addGlyphEdit.setFocus(True)

class SortDialog(QDialog):
    def __init__(self, desc=None, parent=None):
        super(SortDialog, self).__init__(parent)
        self.setWindowModality(Qt.WindowModal)
        self.setWindowTitle("Sort…")

        self.smartSortBox = QRadioButton("Smart sort", self)
        self.characterSetBox = QRadioButton("Character set", self)
        self.characterSetBox.toggled.connect(self.characterSetToggle)
        self.characterSetDrop = QComboBox(self)
        self.characterSetDrop.setEnabled(False)
        # XXX: fetch from settings
        self.characterSetDrop.insertItem(0, "Latin 1")
        self.customSortBox = QRadioButton("Custom…", self)
        self.customSortBox.toggled.connect(self.customSortToggle)

        self.customSortGroup = QGroupBox(parent=self)
        self.customSortGroup.setEnabled(False)
        descriptorsCount = 6
        if desc is None:
            # sort fetched from public.glyphOrder. no-op
            pass
        elif isinstance(desc, CharacterSet):
            self.characterSetBox.setChecked(True)
            self.characterSetDrop.setEnabled(True)
            # TODO: match cset name when QSettings support lands
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
            line.append(QCheckBox("Ascending", self))
            line.append(QCheckBox("Allow pseudo-unicode", self))
            if self.customSortBox.isChecked():
                line[0].setCurrentIndex(self.indexFromItemName(desc[i]["type"]))
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
                btn.pressed.connect(self._addRow)
                self.addLineButton = btn
            else:
                btn.setText("−")
                btn.pressed.connect(self._deleteRow)
        self.customSortGroup.setLayout(self.customSortLayout)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self.smartSortBox)
        layout.addWidget(self.characterSetBox)
        layout.addWidget(self.characterSetDrop)
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
        btn.pressed.connect(self._deleteRow)
        line.append(btn)
        self.customDescriptors.append(line)
        self.customSortLayout.addWidget(line[0], i, 0)
        self.customSortLayout.addWidget(line[1], i, 1)
        self.customSortLayout.addWidget(line[2], i, 2)
        self.customSortLayout.addWidget(line[3], i, 3)
        if i == 7: self.sender().setEnabled(False)

    def _deleteRow(self):
        rel = self.sender().property("index")
        desc = self.customDescriptors
        for i in range(rel+1, len(desc)-1):
            desc[i][0].setCurrentIndex(desc[i+1][0].currentIndex())
            desc[i][1].setChecked(desc[i+1][1].isChecked())
            desc[i][2].setChecked(desc[i+1][2].isChecked())
        for elem in desc[-1]:
            elem.setParent(None)
        del self.customDescriptors[-1]
        self.addLineButton.setEnabled(True)
        self.adjustSize()

    def indexFromItemName(self, name):
        for index, item in enumerate(sortItems):
            if name == item: return index
        print("Unknown descriptor name: %s", name)
        return 0

    @staticmethod
    def getDescriptor(parent, sortDescriptor=None):
        dialog = SortDialog(sortDescriptor, parent)
        result = dialog.exec_()
        if dialog.characterSetBox.isChecked():
            # TODO: dispatch csets when QSettings support lands
            ret = latin1
        elif dialog.customSortBox.isChecked():
            descriptors = []
            for line in dialog.customDescriptors:
                descriptors.append(dict(type=line[0].currentText(), ascending=line[1].isChecked(),
                    allowPseudoUnicode=line[2].isChecked()))
            ret = descriptors
        else:
            ret = cannedDesign
        return (ret, result)

    def characterSetToggle(self):
        checkBox = self.sender()
        self.characterSetDrop.setEnabled(checkBox.isChecked())

    def customSortToggle(self):
        checkBox = self.sender()
        self.customSortGroup.setEnabled(checkBox.isChecked())

class MainWindow(QMainWindow):
    def __init__(self, font):
        super(MainWindow, self).__init__()
        squareSize = 56
        self.collectionWidget = GlyphCollectionWidget(self)
        self._font = None
        self._sortDescriptor = None
        self.font = font
        self.collectionWidget.characterSelectedCallback = self._selectionChanged
        self.collectionWidget.doubleClickCallback = self._glyphOpened
        self.collectionWidget.setFocus()

        menuBar = self.menuBar()
        # TODO: make shortcuts platform-independent
        fileMenu = QMenu("&File", self)
        fileMenu.addAction("&New…", self.newFile, QKeySequence.New)
        fileMenu.addAction("&Open…", self.openFile, QKeySequence.Open)
        # TODO: add functionality
        #fileMenu.addMenu(QMenu("Open &Recent...", self))
        fileMenu.addSeparator()
        fileMenu.addAction("&Save", self.saveFile, QKeySequence.Save)
        fileMenu.addAction("Save &As…", self.saveFileAs, QKeySequence.SaveAs)
        fileMenu.addAction("Reload from disk", self.reload)
        fileMenu.addAction("E&xit", self.close, QKeySequence.Quit)
        menuBar.addMenu(fileMenu)

        editMenu = QMenu("&Edit", self)
        markColorMenu = QMenu("Mark color", self)
        pixmap = QPixmap(24, 24)
        none = markColorMenu.addAction("None", self.markColor)
        none.setData(None)
        red = markColorMenu.addAction("Red", self.markColor)
        pixmap.fill(Qt.red)
        red.setIcon(QIcon(pixmap))
        red.setData(QColor(Qt.red))
        yellow = markColorMenu.addAction("Yellow", self.markColor)
        pixmap.fill(Qt.yellow)
        yellow.setIcon(QIcon(pixmap))
        yellow.setData(QColor(Qt.yellow))
        green = markColorMenu.addAction("Green", self.markColor)
        pixmap.fill(Qt.green)
        green.setIcon(QIcon(pixmap))
        green.setData(QColor(Qt.green))
        editMenu.addMenu(markColorMenu)
        editMenu.addAction("Copy", self.copy, QKeySequence.Copy)
        editMenu.addAction("Copy as Component", self.copyAsComponent, "Ctrl+Alt+c")
        editMenu.addAction("Paste", self.paste, QKeySequence.Paste)
        menuBar.addMenu(editMenu)

        fontMenu = QMenu("&Font", self)
        # TODO: work out sensible shortcuts and make sure they're cross-platform
        # ready - consider extracting them into separate file?
        fontMenu.addAction("&Add glyph", self.addGlyph, "Ctrl+U")
        fontMenu.addAction("Font &info", self.fontInfo, "Ctrl+M")
        fontMenu.addAction("Font &features", self.fontFeatures, "Ctrl+F")
        fontMenu.addSeparator()
        fontMenu.addAction("Sort…", self.sortCharacters)
        menuBar.addMenu(fontMenu)

        windowMenu = QMenu("&Windows", self)
        windowMenu.addAction("&Space center", self.spaceCenter, "Ctrl+Y")
        windowMenu.addAction("&Groups window", self.fontGroups, "Ctrl+G")
        menuBar.addMenu(windowMenu)

        helpMenu = QMenu("&Help", self)
        helpMenu.addAction("&About", self.about)
        helpMenu.addAction("About &Qt", QApplication.instance().aboutQt)
        menuBar.addMenu(helpMenu)

        self.sqSizeSlider = QSlider(Qt.Horizontal, self)
        self.sqSizeSlider.setMinimum(36)
        self.sqSizeSlider.setMaximum(96)
        self.sqSizeSlider.setFixedWidth(.9*self.sqSizeSlider.width())
        self.sqSizeSlider.setValue(squareSize)
        self.sqSizeSlider.valueChanged.connect(self._squareSizeChanged)
        self.selectionLabel = QLabel(self)
        statusBar = self.statusBar()
        statusBar.addPermanentWidget(self.sqSizeSlider)
        statusBar.addWidget(self.selectionLabel)

        self.setCentralWidget(self.collectionWidget.scrollArea())
        self.resize(605, 430)
        self.setWindowTitle()

    def newFile(self):
        ok = self.maybeSaveBeforeExit()
        if not ok: return
        self.font = TFont()
        self.font.info.unitsPerEm = 1000
        self.font.info.ascender = 750
        self.font.info.descender = -250
        self.font.info.capHeight = 750
        self.font.info.xHeight = 500
        self.setWindowTitle("Untitled.ufo")
        self.sortDescriptor = latin1

    def openFile(self, path=None):
        if not path:
            path, ok = QFileDialog.getOpenFileName(self, "Open File", '',
                    "UFO Fonts (metainfo.plist)")
            if not ok: return
        if path:
            # TODO: error handling
            path = os.path.dirname(path)
            # TODO: I note that a change of self.font often goes with setWindowTitle().
            # Be more DRY.
            self.font = TFont(path)
            self.setWindowTitle()

    def saveFile(self, path=None):
        if path is None and self.font.path is None:
            self.saveFileAs()
        else:
            glyphs = self.collectionWidget.glyphs
            # TODO: save sortDescriptor somewhere in lib as well
            glyphNames = []
            for glyph in glyphs:
                glyphNames.append(glyph.name)
            self.font.lib["public.glyphOrder"] = glyphNames
            self.font.save(path=path)
            self.font.dirty = False
            for glyph in self.font:
                glyph.dirty = False
            self.setWindowModified(False)

    def saveFileAs(self):
        path, ok = QFileDialog.getSaveFileName(self, "Save File", '',
                "UFO Fonts (*.ufo)")
        if ok:
            self.saveFile(path)
            self.setWindowTitle()
        #return ok

    def closeEvent(self, event):
        ok = self.maybeSaveBeforeExit()
        if ok:
            self.font.removeObserver(self, "Font.Changed")
            event.accept()
        else:
            event.ignore()

    def maybeSaveBeforeExit(self):
        if self.font.dirty:
            title = "Me"
            if self.font.path is not None:
                # TODO: maybe cache this font name in the Font
                currentFont = os.path.basename(self.font.path.rstrip(os.sep))
            else:
                currentFont = "Untitled.ufo"
            body = "Do you want to save the changes you made to “%s”?" % currentFont
            closeDialog = QMessageBox(QMessageBox.Question, title, body,
                  QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel, self)
            closeDialog.setInformativeText("Your changes will be lost if you don’t save them.")
            closeDialog.setModal(True)
            ret = closeDialog.exec_()
            if ret == QMessageBox.Save:
                self.saveFile()
                return True
            elif ret == QMessageBox.Discard:
                return True
            return False
        return True

    def reload(self):
        font = self._font
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
        self._font = font
        self._font.addObserver(self, "_fontChanged", "Font.Changed")
        if "public.glyphOrder" in self._font.lib:
            self.sortDescriptor = CharacterSet(
                self._font.lib["public.glyphOrder"])
        else:
            # TODO: cannedDesign or carry sortDescriptor from previous font?
            self.sortDescriptor = cannedDesign

    font = property(_get_font, _set_font, doc="The fontView font. Subscribes \
        to the new font, updates the sorting order and cells widget when set.")

    def _get_sortDescriptor(self):
        return self._sortDescriptor

    def _set_sortDescriptor(self, desc):
        if isinstance(desc, CharacterSet):
            cnt = 0
            glyphs = []
            for glyphName in desc.glyphNames:
                if not glyphName in self._font:
                    # create a template glyph
                    self.newStandardGlyph(glyphName)
                    self._font[glyphName].template = True
                else:
                    cnt += 1
                glyphs.append(self._font[glyphName])
            if cnt < len(self._font):
                # somehow some glyphs in the font are not present in the glyph
                # order, loop again to add these at the end
                for glyph in self._font:
                    if not glyph in glyphs:
                     glyphs.append(glyph)
        else:
            glyphs = [self._font[k] for k in self._font.unicodeData
                .sortGlyphNames(self._font.keys(), desc)]
        self.collectionWidget.glyphs = glyphs
        self._sortDescriptor = desc

    sortDescriptor = property(_get_sortDescriptor, _set_sortDescriptor,
        doc="The sortDescriptor. Takes glyphs from the font and sorts them \
        when set.")

    def copy(self):
        glyphs = self.collectionWidget.glyphs
        selection = self.collectionWidget.selection
        pickled = []
        for index in sorted(self.collectionWidget.selection):
            pickled.append(glyphs[index].serializeForUndo(False))
        clipboard = QApplication.clipboard()
        mimeData = QMimeData()
        mimeData.setData("application/x-defconQt-glyph-data", pickle.dumps(pickled))
        clipboard.setMimeData(mimeData)

    def copyAsComponent(self):
        glyphs = self.collectionWidget.glyphs
        selection = self.collectionWidget.selection
        pickled = []
        for index in sorted(self.collectionWidget.selection):
            glyph = glyphs[index]
            componentGlyph = TGlyph()
            componentGlyph.width = glyph.width
            component = Component()
            component.baseGlyph = glyph.name
            componentGlyph.appendComponent(component)
            pickled.append(componentGlyph.serializeForUndo(False))
        clipboard = QApplication.clipboard()
        mimeData = QMimeData()
        mimeData.setData("application/x-defconQt-glyph-data", pickle.dumps(pickled))
        clipboard.setMimeData(mimeData)

    def paste(self):
        clipboard = QApplication.clipboard()
        mimeData = clipboard.mimeData()
        if mimeData.hasFormat("application/x-defconQt-glyph-data"):
            data = pickle.loads(mimeData.data("application/x-defconQt-glyph-data"))
            glyphs = self.collectionWidget.getSelectedGlyphs()
            if len(data) == len(glyphs):
                for pickled, glyph in zip(data, glyphs):
                    name = glyph.name
                    uni = glyph.unicode
                    glyph.deserializeFromUndo(pickled)
                    # XXX: after upgrade to ufo3, write a more flexible
                    # serialization system
                    glyph.name = name
                    glyph.unicode = uni

    def markColor(self):
        color = self.sender().data()
        glyphs = self.collectionWidget.glyphs
        for key in self.collectionWidget.selection:
            glyph = glyphs[key]
            if color is None:
                if "public.markColor" in glyph.lib:
                    del glyph.lib["public.markColor"]
            else:
                glyph.lib["public.markColor"] = ",".join(str(c) for c in color.getRgbF())

    # TODO: maybe store this in TFont
    def newStandardGlyph(self, name):
        self.font.newGlyph(name)
        self.font[name].width = 500
        # TODO: we should not force-add unicode, also list ought to be
        # changeable from AGL2UV
        if name in AGL2UV: self.font[name].unicode = AGL2UV[name]

    def _fontChanged(self, notification):
        self.collectionWidget.update()
        self.setWindowModified(True)

    def _glyphOpened(self, glyph):
        glyphViewWindow = MainGfxWindow(glyph, self)
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
                text = "%s(%d selected)" % (text, count)
        else: text = ""
        self.selectionLabel.setText(text)

    def _squareSizeChanged(self):
        val = self.sqSizeSlider.value()
        self.collectionWidget._sizeEvent(self.width(), val)
        QToolTip.showText(QCursor.pos(), str(val), self)

    def resizeEvent(self, event):
        if self.isVisible(): self.collectionWidget._sizeEvent(event.size().width())
        super(MainWindow, self).resizeEvent(event)

    def setWindowTitle(self, title=None):
        if title is None: title = os.path.basename(self.font.path.rstrip(os.sep))
        super(MainWindow, self).setWindowTitle("[*]{}".format(title))

    def fontInfo(self):
        # If a window is already opened, bring it to the front, else spawn one.
        # TODO: see about using widget.setAttribute(Qt.WA_DeleteOnClose) otherwise
        # it seems we're just leaking memory after each close... (both raise_ and
        # show allocate memory instead of using the hidden widget it seems)
        if not (hasattr(self, 'fontInfoWindow') and self.fontInfoWindow.isVisible()):
            self.fontInfoWindow = TabDialog(self.font, self)
            self.fontInfoWindow.show()
        else:
            # Should data be rewind if user calls font info while one is open?
            # I'd say no, but this has yet to be settled.
            self.fontInfoWindow.raise_()

    def fontFeatures(self):
        # TODO: see up here
        if not (hasattr(self, 'fontFeaturesWindow') and self.fontFeaturesWindow.isVisible()):
            self.fontFeaturesWindow = MainEditWindow(self.font, self)
            self.fontFeaturesWindow.show()
        else:
            self.fontFeaturesWindow.raise_()

    def spaceCenter(self):
        # TODO: see up here
        # TODO: show selection in a space center, rewind selection if we raise window (rf)
        if not (hasattr(self, 'spaceCenterWindow') and self.spaceCenterWindow.isVisible()):
            self.spaceCenterWindow = MainSpaceWindow(self.font, parent=self)
            self.spaceCenterWindow.show()
        else:
            self.spaceCenterWindow.raise_()
        selection = self.collectionWidget.selection
        if selection:
            glyphs = []
            for item in sorted(selection):
                glyph = self.collectionWidget.glyphs[item]
                glyphs.append(glyph)
            self.spaceCenterWindow.setGlyphs(glyphs)

    def fontGroups(self):
        # TODO: see up here
        if not (hasattr(self, 'fontGroupsWindow') and self.fontGroupsWindow.isVisible()):
            self.fontGroupsWindow = GroupsWindow(self.font, self)
            self.fontGroupsWindow.show()
        else:
            self.fontGroupsWindow.raise_()

    def sortCharacters(self):
        sortDescriptor, ok = SortDialog.getDescriptor(self, self.sortDescriptor)
        if ok:
            self.sortDescriptor = sortDescriptor

    def addGlyph(self):
        glyphs = self.collectionWidget.glyphs
        newGlyphNames, sortFont, ok = AddGlyphDialog.getNewGlyphNames(self, glyphs)
        if ok:
            for name in newGlyphNames:
                self.newStandardGlyph(name)
                glyph = self.font[name]
                # XXX: consider making this parametrizable in the dialog
                glyph.template = True
                glyphs.append(glyph)
            self.collectionWidget.glyphs = glyphs
            if sortFont:
                # kick-in the sort mechanism
                self.sortDescriptor = self.sortDescriptor

    def about(self):
        QMessageBox.about(self, "About Me",
                "<h3>About Me</h3>" \
                "<p>I am a new UFO-centric font editor and I aim to bring the <b>robofab</b> " \
                "ecosystem to all main operating systems, in a fast and dependency-free " \
                "package.</p>")
