from PyQt5.QtCore import QEvent, QLocale, Qt
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QRadioButton,
)


class FindDialog(QDialog):
    alphabetical = [dict(type="alphabetical", allowPseudoUnicode=True)]

    def __init__(self, currentGlyph, parent=None):
        super().__init__(parent)
        self.setWindowModality(Qt.WindowModal)
        self.setWindowTitle(self.tr("Find…"))
        self._sortedGlyphNames = currentGlyph.font.unicodeData.sortGlyphNames(
            currentGlyph.layer.keys(), self.alphabetical
        )

        layout = QGridLayout(self)
        self.glyphLabel = QLabel(self.tr("Glyph:"), self)
        self.glyphEdit = QLineEdit(self)
        self.glyphEdit.textChanged.connect(self.updateGlyphList)
        self.glyphEdit.event = self.lineEvent
        self.glyphEdit.keyPressEvent = self.lineKeyPressEvent

        self.beginsWithBox = QRadioButton(self.tr("Begins with"), self)
        self.containsBox = QRadioButton(self.tr("Contains"), self)
        self.beginsWithBox.setChecked(True)
        self.beginsWithBox.toggled.connect(self.updateGlyphList)

        self.glyphList = QListWidget(self)
        self.glyphList.itemDoubleClicked.connect(self.accept)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        line = 0
        layout.addWidget(self.glyphLabel, line, 0, 1, 2)
        layout.addWidget(self.glyphEdit, line, 2, 1, 4)
        line += 1
        layout.addWidget(self.beginsWithBox, line, 0, 1, 3)
        layout.addWidget(self.containsBox, line, 3, 1, 3)
        line += 1
        layout.addWidget(self.glyphList, line, 0, 1, 6)
        line += 1
        layout.addWidget(buttonBox, line, 0, 1, 6)
        self.setLayout(layout)
        self.updateGlyphList()

    def lineEvent(self, event):
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Tab:
            if self.beginsWithBox.isChecked():
                self.containsBox.toggle()
            else:
                self.beginsWithBox.toggle()
            return True
        else:
            return QLineEdit.event(self.glyphEdit, event)

    def lineKeyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Up or key == Qt.Key_Down:
            self.glyphList.keyPressEvent(event)
        else:
            QLineEdit.keyPressEvent(self.glyphEdit, event)

    def updateGlyphList(self):
        beginsWith = self.beginsWithBox.isChecked()
        self.glyphList.clear()
        if not self.glyphEdit.isModified():
            self.glyphList.addItems(self._sortedGlyphNames)
        else:
            text = self.glyphEdit.text()
            if beginsWith:
                glyphs = [
                    glyphName
                    for glyphName in self._sortedGlyphNames
                    if glyphName and glyphName.startswith(text)
                ]
            else:
                glyphs = [
                    glyphName
                    for glyphName in self._sortedGlyphNames
                    if glyphName and text in glyphName
                ]
            self.glyphList.addItems(glyphs)
        self.glyphList.setCurrentRow(0)

    @classmethod
    def getNewGlyph(cls, parent, currentGlyph):
        dialog = cls(currentGlyph, parent)
        result = dialog.exec_()
        currentItem = dialog.glyphList.currentItem()
        newGlyph = None
        if currentItem is not None:
            newGlyphName = currentItem.text()
            if newGlyphName in currentGlyph.layer:
                newGlyph = currentGlyph.layer[newGlyphName]
        return (newGlyph, result)


class AddComponentDialog(FindDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle(self.tr("Add component…"))
        self._sortedGlyphNames.remove(args[0].name)
        self.updateGlyphList()


class LayerActionsDialog(QDialog):
    def __init__(self, currentGlyph, parent=None):
        super().__init__(parent)
        self.setWindowModality(Qt.WindowModal)
        self.setWindowTitle(self.tr("Layer actions…"))
        self._workableLayers = []
        for layer in currentGlyph.layerSet:
            if layer != currentGlyph.layer:
                self._workableLayers.append(layer)

        copyBox = QRadioButton(self.tr("Copy"), self)
        moveBox = QRadioButton(self.tr("Move"), self)
        swapBox = QRadioButton(self.tr("Swap"), self)
        self.otherCheckBoxes = (moveBox, swapBox)
        copyBox.setChecked(True)

        self.layersList = QListWidget(self)
        self.layersList.addItems(layer.name for layer in self._workableLayers)
        if self.layersList.count():
            self.layersList.setCurrentRow(0)
        self.layersList.itemDoubleClicked.connect(self.accept)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QGridLayout(self)
        line = 0
        layout.addWidget(copyBox, line, 0, 1, 2)
        layout.addWidget(moveBox, line, 2, 1, 2)
        layout.addWidget(swapBox, line, 4, 1, 2)
        line += 1
        layout.addWidget(self.layersList, line, 0, 1, 6)
        line += 1
        layout.addWidget(buttonBox, line, 0, 1, 6)
        self.setLayout(layout)

    @classmethod
    def getLayerAndAction(cls, parent, currentGlyph):
        dialog = cls(currentGlyph, parent)
        result = dialog.exec_()
        currentItem = dialog.layersList.currentItem()
        newLayer = None
        if currentItem is not None:
            newLayerName = currentItem.text()
            for layer in dialog._workableLayers:
                if layer.name == newLayerName:
                    newLayer = layer
        action = "Copy"
        for checkBox in dialog.otherCheckBoxes:
            if checkBox.isChecked():
                action = checkBox.text()
        return (newLayer, action, result)


class EditDialog(QDialog):
    def __init__(self, parent=None, item=None):
        super().__init__(parent)
        self.setWindowModality(Qt.WindowModal)
        self.setWindowTitle(self.tr("Edit…"))

        nameLabel = QLabel(self.tr("Name:"), self)
        self.nameEdit = QLineEdit(self)
        self.nameEdit.setFocus(Qt.OtherFocusReason)

        validator = QDoubleValidator(self)
        validator.setLocale(QLocale.c())
        xLabel = QLabel(self.tr("X:"), self)
        self.xEdit = QLineEdit(self)
        self.xEdit.setValidator(validator)
        yLabel = QLabel(self.tr("Y:"), self)
        self.yEdit = QLineEdit(self)
        self.yEdit.setValidator(validator)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QGridLayout(self)
        line = 0
        layout.addWidget(nameLabel, line, 0)
        layout.addWidget(self.nameEdit, line, 1, 1, 3)
        line += 1
        layout.addWidget(xLabel, line, 0)
        layout.addWidget(self.xEdit, line, 1)
        layout.addWidget(yLabel, line, 2)
        layout.addWidget(self.yEdit, line, 3)
        line += 1
        layout.addWidget(buttonBox, line, 3)
        self.setLayout(layout)

    @classmethod
    def getNewProperties(cls, parent, item):
        dialog = cls(parent, item)
        dialog.nameEdit.setText(item.name)
        dialog.nameEdit.selectAll()
        dialog.xEdit.setText(str(item.x))
        dialog.xEdit.selectAll()
        dialog.yEdit.setText(str(item.y))
        dialog.yEdit.selectAll()
        result = dialog.exec_()
        name = dialog.nameEdit.text()
        x = float(dialog.xEdit.text())
        y = float(dialog.yEdit.text())
        return (name, x, y, result)
