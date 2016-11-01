from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import QApplication, QMessageBox, QStyle
from trufont.tools import platformSpecific


class MessageBox(QMessageBox):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIcon(QMessageBox.Question)
        self.setWindowTitle(QApplication.applicationName())
        self.setWindowModality(Qt.WindowModal)
        if platformSpecific.showAppIconInDialog():
            iconSize = self.style().pixelMetric(
                QStyle.PM_MessageBoxIconSize, None, self)
            icon = self.windowIcon()
            size = icon.actualSize(QSize(iconSize, iconSize))
            self.setIconPixmap(icon.pixmap(size))


class ReloadMessageBox(MessageBox):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText(self.tr("Do you want to reload the document?"))
        self.setInformativeText(
            self.tr("Your current changes will be lost."))
        self.setStandardButtons(
            QMessageBox.Yes | QMessageBox.No)
        self.setDefaultButton(QMessageBox.Yes)

    @classmethod
    def getReloadDocument(cls, parent, documentName=None):
        dialog = cls(parent)
        if documentName is not None:
            dialog.setText(
                dialog.tr("Do you want to reload “{}”?").format(documentName))
        return dialog.exec_()


class CloseMessageBox(MessageBox):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText(self.tr("Do you want to save your changes?"))
        self.setInformativeText(
            self.tr("Your changes will be lost if you don’t save them."))
        self.setStandardButtons(
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        self.setDefaultButton(QMessageBox.Save)

    @classmethod
    def getCloseDocument(cls, parent, documentName=None):
        dialog = cls(parent)
        if documentName is not None:
            dialog.setText(
                dialog.tr("Do you want to save the changes you made "
                          "to “{}”?").format(documentName))
        return dialog.exec_()
