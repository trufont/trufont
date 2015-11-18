from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QGridLayout, QLabel,
    QLineEdit, QDialogButtonBox)

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
