from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtWidgets import (
    QDialog, QDialogButtonBox, QGridLayout, QLabel, QLineEdit, QListWidget,
    QRadioButton)


class GotoDialog(QDialog):
    alphabetical = [
        dict(type="alphabetical", allowPseudoUnicode=True)
    ]

    def __init__(self, currentGlyph, parent=None):
        super(GotoDialog, self).__init__(parent)
        self.setWindowModality(Qt.WindowModal)
        self.setWindowTitle("Go to…")
        self.font = currentGlyph.getParent()
        self._sortedGlyphs = self.font.unicodeData.sortGlyphNames(
            self.font.keys(), self.alphabetical)

        layout = QGridLayout(self)
        self.glyphLabel = QLabel("Glyph:", self)
        self.glyphEdit = QLineEdit(self)
        self.glyphEdit.textChanged.connect(self.updateGlyphList)
        self.glyphEdit.event = self.lineEvent
        self.glyphEdit.keyPressEvent = self.lineKeyPressEvent

        self.beginsWithBox = QRadioButton("Begins with", self)
        self.containsBox = QRadioButton("Contains", self)
        self.beginsWithBox.setChecked(True)
        self.beginsWithBox.toggled.connect(self.updateGlyphList)

        self.glyphList = QListWidget(self)
        self.glyphList.itemDoubleClicked.connect(self.accept)

        buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        l = 0
        layout.addWidget(self.glyphLabel, l, 0, 1, 2)
        layout.addWidget(self.glyphEdit, l, 2, 1, 4)
        l += 1
        layout.addWidget(self.beginsWithBox, l, 0, 1, 3)
        layout.addWidget(self.containsBox, l, 3, 1, 3)
        l += 1
        layout.addWidget(self.glyphList, l, 0, 1, 6)
        l += 1
        layout.addWidget(buttonBox, l, 0, 1, 6)
        self.setLayout(layout)
        self.updateGlyphList(True)

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

    def updateGlyphList(self, select):
        self.glyphList.clear()
        if not self.glyphEdit.isModified():
            self.glyphList.addItems(self._sortedGlyphs)
        text = self.glyphEdit.text()
        if select:
            glyphs = [glyph for glyph in self._sortedGlyphs
                      if glyph.startswith(text)]
        else:
            glyphs = [glyph for glyph in self._sortedGlyphs if text in glyph]
        self.glyphList.addItems(glyphs)
        if select:
            self.glyphList.setCurrentRow(0)

    @classmethod
    def getNewGlyph(cls, parent, currentGlyph):
        dialog = cls(currentGlyph, parent)
        result = dialog.exec_()
        currentItem = dialog.glyphList.currentItem()
        newGlyph = None
        if currentItem is not None:
            newGlyphName = currentItem.text()
            if newGlyphName in dialog.font:
                newGlyph = dialog.font[newGlyphName]
        return (newGlyph, result)


class AddAnchorDialog(QDialog):

    def __init__(self, pos=None, parent=None):
        super(AddAnchorDialog, self).__init__(parent)
        self.setWindowModality(Qt.WindowModal)
        if pos is not None:
            self.setWindowTitle("Add anchor…")
        else:
            self.setWindowTitle("Rename anchor…")

        layout = QGridLayout(self)

        anchorNameLabel = QLabel("Anchor name:", self)
        self.anchorNameEdit = QLineEdit(self)
        self.anchorNameEdit.setFocus(True)
        if pos is not None:
            anchorPositionLabel = QLabel(
                "The anchor will be added at ({}, {})."
                .format(pos.x(), pos.y()), self)

        buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        l = 0
        layout.addWidget(anchorNameLabel, l, 0)
        layout.addWidget(self.anchorNameEdit, l, 1, 1, 3)
        if pos is not None:
            l += 1
            layout.addWidget(anchorPositionLabel, l, 0, 1, 4)
        l += 1
        layout.addWidget(buttonBox, l, 3)
        self.setLayout(layout)

    @classmethod
    def getNewAnchorName(cls, parent, pos=None):
        dialog = cls(pos, parent)
        result = dialog.exec_()
        name = dialog.anchorNameEdit.text()
        return (name, result)


class AddComponentDialog(GotoDialog):

    def __init__(self, *args, **kwargs):
        super(AddComponentDialog, self).__init__(*args, **kwargs)
        self.setWindowTitle("Add component…")
        self._sortedGlyphs.remove(args[0].name)
        self.updateGlyphList(False)


class AddLayerDialog(QDialog):

    def __init__(self, parent=None):
        super(AddLayerDialog, self).__init__(parent)
        self.setWindowModality(Qt.WindowModal)
        self.setWindowTitle("Add layer…")

        layout = QGridLayout(self)

        layerNameLabel = QLabel("Layer name:", self)
        self.layerNameEdit = QLineEdit(self)
        self.layerNameEdit.setFocus(True)

        buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        l = 0
        layout.addWidget(layerNameLabel, l, 0)
        layout.addWidget(self.layerNameEdit, l, 1)
        l += 1
        layout.addWidget(buttonBox, l, 0, 1, 2)
        self.setLayout(layout)

    @classmethod
    def getNewLayerName(cls, parent):
        dialog = cls(parent)
        result = dialog.exec_()
        name = dialog.layerNameEdit.text()
        return (name, result)


class LayerActionsDialog(QDialog):

    def __init__(self, currentGlyph, parent=None):
        super().__init__(parent)
        self.setWindowModality(Qt.WindowModal)
        self.setWindowTitle("Layer actions…")
        self._workableLayers = []
        for layer in currentGlyph.layerSet:
            if layer != currentGlyph.layer:
                self._workableLayers.append(layer)

        layout = QGridLayout(self)

        copyBox = QRadioButton("Copy", self)
        moveBox = QRadioButton("Move", self)
        swapBox = QRadioButton("Swap", self)
        self.otherCheckBoxes = (moveBox, swapBox)
        copyBox.setChecked(True)

        self.layersList = QListWidget(self)
        self.layersList.addItems(
            layer.name for layer in self._workableLayers)
        if self.layersList.count():
            self.layersList.setCurrentRow(0)
        self.layersList.itemDoubleClicked.connect(self.accept)

        buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        l = 0
        layout.addWidget(copyBox, l, 0, 1, 2)
        layout.addWidget(moveBox, l, 2, 1, 2)
        layout.addWidget(swapBox, l, 4, 1, 2)
        l += 1
        layout.addWidget(self.layersList, l, 0, 1, 6)
        l += 1
        layout.addWidget(buttonBox, l, 0, 1, 6)
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
