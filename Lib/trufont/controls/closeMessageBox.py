from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import QApplication, QMessageBox, QStyle
from trufont.tools import platformSpecific


class CloseMessageBox(QMessageBox):

    def __init__(self, parent=None):
        super().__init__(parent)
        # TODO: make sure we need this on Windows
        self.setWindowTitle(QApplication.applicationName())
        self.setText(self.tr("Do you want to save your changes?"))
        self.setInformativeText(
            self.tr("Your changes will be lost if you don’t save them."))
        self.setWindowModality(Qt.WindowModal)
        self.setStandardButtons(
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        self.setDefaultButton(QMessageBox.Save)
        self.setIcon(QMessageBox.Question)
        if platformSpecific.showAppIconInDialog():
            iconSize = self.style().pixelMetric(
                QStyle.PM_MessageBoxIconSize, None, self)
            icon = self.windowIcon()
            size = icon.actualSize(QSize(iconSize, iconSize))
            self.setIconPixmap(icon.pixmap(size))

    @classmethod
    def getCloseDocument(cls, parent, documentName=None):
        dialog = cls(parent)
        if documentName is not None:
            dialog.setText(
                dialog.tr("Do you want to save the changes you made "
                          "to “{}”?").format(documentName))
        return dialog.exec_()
