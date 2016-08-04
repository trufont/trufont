from defconQt.controls.featureCodeEditor import FeatureCodeEditor
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from trufont.objects import settings
from trufont.objects.menu import Entries


class FontFeaturesWindow(QMainWindow):

    def __init__(self, font=None, parent=None):
        super().__init__(parent)

        self.font = font
        self.font.info.addObserver(self, "_fontInfoChanged", "Info.Changed")
        self.editor = FeatureCodeEditor(self)
        self.editor.setPlainText(self.font.features.text)
        self.editor.modificationChanged.connect(self.setWindowModified)

        self.updateWindowTitle()
        self.setCentralWidget(self.editor)

        self.readSettings()

    def readSettings(self):
        geometry = settings.fontFeaturesWindowGeometry()
        if geometry:
            self.restoreGeometry(geometry)

    def writeSettings(self):
        settings.setFontFeaturesWindowGeometry(self.saveGeometry())

    def setupMenu(self, menuBar):
        fileMenu = menuBar.fetchMenu(Entries.File)
        fileMenu.fetchAction(Entries.File_Save, self.save)
        fileMenu.addSeparator()
        fileMenu.fetchAction(Entries.File_Reload, self.reload)
        fileMenu.fetchAction(Entries.File_Close, self.close)

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

    def sizeHint(self):
        return QSize(650, 500)

    def moveEvent(self, event):
        self.writeSettings()

    resizeEvent = moveEvent

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
