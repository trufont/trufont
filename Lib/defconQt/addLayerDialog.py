from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QGridLayout, QLabel,
    QLineEdit, QDialogButtonBox)

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
