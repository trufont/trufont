from defconQt.controls.colorVignette import ColorVignette
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QGridLayout,
    QGroupBox, QPlainTextEdit, QPushButton, QRadioButton, QVBoxLayout)
from trufont.objects import settings

sortItems = ["alphabetical", "category", "unicode", "script", "suffix",
             "decompositionBase", "weightedSuffix", "ligature"]


class AddGlyphsDialog(QDialog):

    # TODO: implement Frederik's Glyph Construction Builder
    def __init__(self, currentGlyphs=None, parent=None):
        super().__init__(parent)
        self.setWindowModality(Qt.WindowModal)
        self.setWindowTitle(self.tr("Add Glyphs…"))
        self.currentGlyphs = currentGlyphs
        self.currentGlyphNames = [glyph.name for glyph in currentGlyphs]

        layout = QGridLayout(self)
        self.markColorWidget = ColorVignette(self)
        self.markColorWidget.setFixedWidth(56)
        self.importCharDrop = QComboBox(self)
        self.importCharDrop.addItem(self.tr("Import glyph names…"))
        glyphSets = settings.readGlyphSets()
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
        super().__init__(parent)
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
        glyphSets = settings.readGlyphSets()
        for name, glyphNames in glyphSets.items():
            self.glyphSetDrop.addItem(name, glyphNames)
        self.customSortBox = QRadioButton(self.tr("Custom…"), self)
        self.customSortBox.toggled.connect(self.customSortToggle)

        self.customSortGroup = QGroupBox(parent=self)
        self.customSortGroup.setEnabled(False)
        descriptorsCount = 6
        if desc is None:
            pass
        elif desc[0]["type"] == "glyphSet":
            self.glyphSetBox.setChecked(True)
            self.glyphSetDrop.setEnabled(True)
            # XXX: we must handle unknown glyphSets... or glyphSets with
            # the same name but different
            self.glyphSetDrop.setCurrentText(desc[0]["name"])
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
            ret = [
                dict(type="glyphSet", glyphs=data, name=name)
            ]
        elif dialog.customSortBox.isChecked():
            descriptors = []
            for line in dialog.customDescriptors:
                descriptors.append(dict(
                    type=line[0].currentText(),
                    ascending=line[1].isChecked(),
                    allowPseudoUnicode=line[2].isChecked()))
            ret = descriptors
        else:
            ret = [
                dict(type="cannedDesign", allowPseudoUnicode=True)
            ]
        return (ret, result)

    def glyphSetToggle(self):
        checkBox = self.sender()
        self.glyphSetDrop.setEnabled(checkBox.isChecked())

    def customSortToggle(self):
        checkBox = self.sender()
        self.customSortGroup.setEnabled(checkBox.isChecked())
