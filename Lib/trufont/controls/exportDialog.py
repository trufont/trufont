import os

from PyQt5.QtCore import QDir, QFileSystemWatcher, QSize, QStandardPaths, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStyle,
    QVBoxLayout,
    QWidget,
)
from ufo2ft.fontInfoData import getAttrWithFallback

from defconQt.controls.roundedButtonSet import RoundedButtonSet as ButtonSet
from trufont.objects import icons, settings


class ExportDialog(QDialog):
    def __init__(self, font, parent=None):
        super().__init__(parent, Qt.MSWindowsFixedSizeDialogHint)
        self.setWindowModality(Qt.WindowModal)
        self.setWindowTitle(self.tr("Export…"))

        self._exportDirectory = QDir.toNativeSeparators(
            QStandardPaths.standardLocations(QStandardPaths.DocumentsLocation)[0]
        )
        self.baseName = getAttrWithFallback(font.info, "postscriptFontName")

        self.formatBtnSet = ButtonSet(self)
        self.formatBtnSet.setOptions(["OTF", "TTF"])
        self.formatBtnSet.setSelectionMode(ButtonSet.OneOrMoreSelection)
        self.compressionBtnSet = ButtonSet(self)
        self.compressionBtnSet.setOptions(["None", "WOFF", "WOFF2"])
        self.compressionBtnSet.setSelectionMode(ButtonSet.OneOrMoreSelection)
        self.numberLabel = QLabel(self)
        self.formatBtnSet.clicked.connect(self.updateNumbers)
        self.compressionBtnSet.clicked.connect(self.updateNumbers)

        self.removeOverlapBox = QCheckBox(self.tr("Remove Overlap"), self)
        # self.removeOverlapBox.setChecked(True)  # XXX: implement
        self.removeOverlapBox.setEnabled(False)
        self.autohintBox = QCheckBox(self.tr("Autohint"), self)
        # self.autohintBox.setChecked(True)  # XXX: implement
        self.autohintBox.setEnabled(False)

        self.exportBox = QCheckBox(self)
        boxSize = self.exportBox.sizeHint()
        self.exportBox.setText(self.tr("Use Export Directory"))
        self.exportBox.setChecked(True)
        self.exportIcon = QLabel(self)
        icon = self.style().standardIcon(QStyle.SP_DirClosedIcon)
        iconSize = QSize(24, 24)
        self.exportIcon.setPixmap(icon.pixmap(icon.actualSize(iconSize)))
        self.exportIcon.setBaseSize(iconSize)
        self.exportDirLabel = QLabel(self)
        self.exportDirLabel.setText(self.exportDirectory)
        self.exportDirButton = QPushButton(self)
        self.exportDirButton.setText(self.tr("Choose…"))
        self.exportDirButton.clicked.connect(
            lambda: self.chooseExportDir(self.exportDirectory)
        )

        # if files are to be overwritten, put up a warning
        # + use a file system watcher to avoid TOCTOU
        self.warningIcon = QLabel(self)
        icon = icons.i_warning()
        iconSize = QSize(20, 20)
        self.warningIcon.setPixmap(icon.pixmap(icon.actualSize(iconSize)))
        self.warningIcon.setBaseSize(iconSize)
        # XXX: not sure why this is needed
        self.warningIcon.setFixedWidth(iconSize.width())
        sp = self.warningIcon.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        self.warningIcon.setSizePolicy(sp)
        self.warningLabel = QLabel(self)
        palette = self.warningLabel.palette()
        role, color = self.warningLabel.foregroundRole(), QColor(230, 20, 20)
        palette.setColor(palette.Active, role, color)
        palette.setColor(palette.Inactive, role, color)
        self.warningLabel.setPalette(palette)
        sp = self.warningLabel.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        self.warningLabel.setSizePolicy(sp)

        self.updateExportStatus()
        self.exportBox.toggled.connect(self.updateExportStatus)

        self.watcher = QFileSystemWatcher(self)
        self.watcher.addPath(self.exportDirectory)
        self.updateNumbers()
        self.watcher.directoryChanged.connect(self.updateNumbers)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Cancel)
        buttonBox.addButton(self.tr("Generate…"), QDialogButtonBox.AcceptRole)
        buttonBox.accepted.connect(self.finish)
        buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        formLayout = QFormLayout()
        formLayout.addRow(self.tr("Format"), self.formatBtnSet)
        formLayout.addRow(self.tr("Compression"), self.compressionBtnSet)
        formLayout.setHorizontalSpacing(16)
        formLayout.setContentsMargins(0, 0, 0, 4)
        layout.addLayout(formLayout)
        layout.addWidget(self.numberLabel)
        layout.addWidget(self.removeOverlapBox)
        layout.addWidget(self.autohintBox)
        layout.addWidget(self.exportBox)
        exportLayout = QHBoxLayout()
        exportLayout.addWidget(self.exportIcon)
        exportLayout.addWidget(self.exportDirLabel)
        exportLayout.addWidget(self.exportDirButton)
        exportLayout.addWidget(QWidget())
        margins = exportLayout.contentsMargins()
        margins.setLeft(margins.left() + boxSize.width() + 4)
        exportLayout.setContentsMargins(margins)
        exportLayout.setStretch(3, 1)
        layout.addLayout(exportLayout)
        warningLayout = QHBoxLayout()
        warningLayout.addWidget(self.warningIcon)
        warningLayout.addWidget(self.warningLabel)
        warningLayout.addWidget(QWidget())
        margins.setBottom(margins.bottom() + 4)
        warningLayout.setContentsMargins(margins)
        warningLayout.setStretch(3, 1)
        layout.addLayout(warningLayout)
        layout.addWidget(buttonBox)
        # XXX: check this on non-Windows platforms
        layout.setContentsMargins(16, 16, 16, 16)

        self.readSettings()

    def readSettings(self):
        attrs = [
            (settings.exportFileFormats, self.formatBtnSet.setSelectedOptions),
            (
                settings.exportCompressionFormats,
                self.compressionBtnSet.setSelectedOptions,
            ),
            (settings.exportRemoveOverlap, self.removeOverlapBox.setChecked),
            (settings.exportAutohint, self.autohintBox.setChecked),
            (settings.exportUseDirectory, self.exportBox.setChecked),
            (
                settings.exportDirectory,
                lambda attr: setattr(self, "exportDirectory", attr),
            ),
        ]
        for getValue, setter in attrs:
            value = getValue()
            if value != "":
                setter(value)
        self.exportDirLabel.setText(self.exportDirectory)
        self.updateNumbers()

    def writeSettings(self):
        attrs = [
            (settings.setExportFileFormats, self.formatBtnSet.selectedOptions),
            (
                settings.setExportCompressionFormats,
                self.compressionBtnSet.selectedOptions,
            ),
            (settings.setExportRemoveOverlap, self.removeOverlapBox.isChecked),
            (settings.setExportAutohint, self.autohintBox.isChecked),
            (settings.setExportUseDirectory, self.exportBox.isChecked),
            (settings.setExportDirectory, lambda: getattr(self, "exportDirectory")),
        ]
        for setValue, getter in attrs:
            value = getter()
            setValue(value)

    @property
    def exportDirectory(self):
        return self._exportDirectory

    @exportDirectory.setter
    def exportDirectory(self, path):
        oldValue = self._exportDirectory
        if oldValue == path:
            return
        if oldValue is not None:
            self.watcher.removePath(oldValue)
        self._exportDirectory = path
        self.watcher.addPath(self.exportDirectory)
        self.exportDirLabel.setText(self._exportDirectory)
        self.updateNumbers()

    def chooseExportDir(self, givenDir=None):
        state = settings.exportFileDialogState()
        dialog = QFileDialog(self)
        if state:
            dialog.restoreState(state)
        dialogDir = dialog.directory()
        if givenDir is not None:
            dialog.setDirectory(givenDir)
        elif dialogDir is None:
            dialog.setDirectory(
                QStandardPaths.standardLocations(QStandardPaths.DocumentsLocation)[0]
            )
        dialog.setAcceptMode(QFileDialog.AcceptOpen)
        dialog.setFileMode(QFileDialog.Directory)
        ok = dialog.exec_()
        exportDir = QDir.toNativeSeparators(dialog.directory().absolutePath())
        if givenDir is not None:
            dialog.setDirectory(dialogDir)
        settings.setExportFileDialogState(dialog.saveState())
        if ok:
            self.exportDirectory = exportDir

    def updateExportStatus(self):
        value = self.exportBox.isChecked()
        for w in (
            self.exportIcon,
            self.exportDirLabel,
            self.exportDirButton,
            self.warningIcon,
            self.warningLabel,
        ):
            w.setEnabled(value)

    def updateNumbers(self):
        formatOptions = self.formatBtnSet.selectedOptions()
        compressionOptions = self.compressionBtnSet.selectedOptions()
        # number label
        count = len(formatOptions) * len(compressionOptions)
        self.numberLabel.setText(
            self.tr(f"×%n font(s) with base name: {self.baseName}*", n=count)
        )
        # overwrite status
        # XXX: not DRY with the TFont.export logic
        count = 0
        # make a list out of this, otherwise we'll consume the iterator
        compressions = list(map(str.lower, compressionOptions))
        for format in map(str.lower, formatOptions):
            filePath = os.path.join(self.exportDirectory, f"{self.baseName}.{format}")
            for compression in compressions:
                fullPath = filePath
                if compression != "none":
                    fullPath += f".{compression}"
                count += os.path.exists(fullPath)
        visible = bool(count)
        self.warningIcon.setVisible(visible)
        self.warningLabel.setVisible(visible)
        if visible:
            self.warningLabel.setText(
                self.tr("%n file(s) will be overwritten.", n=count)
            )

    def finish(self):
        self.accept()
        export = self.exportBox.isChecked()
        # here we pick a directory, but it won't become the default export dir
        if not export:
            self.chooseExportDir()

    @classmethod
    def getExportParameters(cls, parent, font):
        dialog = cls(font, parent)
        result = dialog.exec_()
        params = dict(
            baseName=dialog.baseName,
            formats=dialog.formatBtnSet.selectedOptions(),
            compression=dialog.compressionBtnSet.selectedOptions(),
            exportDirectory=dialog.exportDirectory,
            removeOverlap=dialog.removeOverlapBox.isChecked(),
            autohint=dialog.autohintBox.isChecked(),
        )
        return (params, result)

    # ----------
    # Qt methods
    # ----------

    def accept(self):
        self.writeSettings()
        super().accept()

    def reject(self):
        self.writeSettings()
        super().reject()

    def closeEvent(self, event):
        super().closeEvent(event)
        if event.isAccepted():
            self.writeSettings()
