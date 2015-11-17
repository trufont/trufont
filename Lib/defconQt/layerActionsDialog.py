from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QGridLayout, QListWidget,
    QDialogButtonBox, QRadioButton)

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
