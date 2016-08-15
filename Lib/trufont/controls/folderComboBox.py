from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QComboBox, QFileDialog, QStyle
import os


class FolderComboBox(QComboBox):
    currentFolderModified = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._currentFolder = None
        # TODO: could be done in showEvent only if currentFolder is
        # None/untouched
        self._updateContents()

        self.currentIndexChanged[int].connect(self._updateCurrentFolder)

    def currentFolder(self):
        return self._currentFolder

    def setCurrentFolder(self, path):
        if path == self._currentFolder:
            return
        if path is not None:
            assert os.path.isdir(path)
        self._currentFolder = path
        self._updateContents()
        self.currentFolderModified.emit(self._currentFolder)

    def _updateContents(self):
        self.blockSignals(True)
        self.clear()
        path = self._currentFolder
        if path is not None:
            dirIcon = self.style().standardIcon(QStyle.SP_DirIcon)
            self.addItem(dirIcon, os.path.basename(path))
        else:
            self.addItem("<None>")
        self.insertSeparator(1)
        self.addItem(self.tr("Browse…"))
        self.setCurrentIndex(0)
        self.blockSignals(False)

    def _updateCurrentFolder(self, index):
        if index < self.count() - 1:
            return
        # TODO: use app.activeWindow()?
        path = QFileDialog.getExistingDirectory(
            self, self.tr("Choose Directory"), self._currentFolder,
            QFileDialog.ShowDirsOnly)
        if path:
            self.setCurrentFolder(path)
        else:
            self.setCurrentIndex(0)
