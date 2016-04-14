from defconQt.controls.featureCodeEditor import FeatureCodeEditor
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QMessageBox
from trufont.tools import platformSpecific


class FontFeaturesWindow(QMainWindow):

    def __init__(self, font=None, parent=None):
        super().__init__(parent)

        self.font = font
        self.font.info.addObserver(self, "_fontInfoChanged", "Info.Changed")
        self.editor = FeatureCodeEditor(self)
        self.editor.setPlainText(self.font.features.text)
        self.editor.modificationChanged.connect(self.setWindowModified)

        fileMenu = QMenu(self.tr("&File"), self)
        fileMenu.addAction(self.tr("&Save…"), self.save, QKeySequence.Save)
        fileMenu.addSeparator()
        fileMenu.addAction(self.tr("&Reload From Disk"), self.reload)
        fileMenu.addAction(
            self.tr("&Close"), self.close, platformSpecific.closeKeySequence())
        self.menuBar().addMenu(fileMenu)

        self.updateWindowTitle()
        self.setCentralWidget(self.editor)
        self.resize(600, 500)

    def updateWindowTitle(self, title=None, font=None):
        if title is None:
            title = self.tr("Font Features")
        if font is None:
            font = self.font
        text = self.tr("{0} - {1} {2}").format(
            title, font.info.familyName, font.info.styleName)
        self.setWindowTitle("[*]" + text)

    # -------------
    # Notifications
    # -------------

    def _fontInfoChanged(self, notification):
        self.updateWindowTitle()

    # ------------
    # Menu methods
    # ------------

    def save(self):
        self.editor.write(self.font.features)

    def reload(self):
        self.font.reloadFeatures()
        self.editor.setPlainText(self.font.features.text)

    # ----------
    # Qt methods
    # ----------

    # TODO: maybe bring up to the code editor widget?
    def closeEvent(self, event):
        if self.editor.document().isModified():
            name = QApplication.applicationName()
            closeDialog = QMessageBox(
                QMessageBox.Question,
                name,
                self.tr("Save your changes?"),
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                self
            )
            closeDialog.setInformativeText(
                self.tr("Your changes will be lost if you don’t save them.")
            )
            closeDialog.setModal(True)
            ret = closeDialog.exec_()
            if ret == QMessageBox.Save:
                self.save()
                event.accept()
            elif ret == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
                return
            self.font.info.removeObserver(self, "Info.Changed")
