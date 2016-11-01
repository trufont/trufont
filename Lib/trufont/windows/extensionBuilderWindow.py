from defconQt.controls.listView import ListView
from PyQt5.QtCore import QRegularExpression, QSize
from PyQt5.QtGui import QRegularExpressionValidator
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
    QFrame, QLabel, QLineEdit, QVBoxLayout)
from trufont.controls.folderComboBox import FolderComboBox
from trufont.objects.extension import TExtension
import os


def VersionValidator(parent):
    validator = QRegularExpressionValidator(parent)
    validator.setRegularExpression(
        QRegularExpression("([0-9]+\\.[0-9]+\\.[0-9]+)?"))
    return validator


def HLine(parent):
    widget = QFrame(parent)
    widget.setFrameShape(QFrame.HLine)
    widget.setFrameShadow(QFrame.Sunken)
    return widget


class ExtensionBuilderWindow(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Extension Builder"))

        layout = QFormLayout(self)
        layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        self.nameEdit = QLineEdit(self)
        self.versionEdit = QLineEdit(self)
        self.versionEdit.setValidator(VersionValidator(self))
        self.developerEdit = QLineEdit(self)
        self.developerURLEdit = QLineEdit(self)
        layout.addRow(self.tr("Name:"), self.nameEdit)
        layout.addRow(self.tr("Version:"), self.versionEdit)
        layout.addRow(self.tr("Developer:"), self.developerEdit)
        layout.addRow(self.tr("Developer URL:"), self.developerURLEdit)
        layout.addRow(HLine(self))

        self.resourcesRootBox = FolderComboBox(self)
        self.scriptRootBox = FolderComboBox(self)
        self.scriptRootBox.currentFolderModified.connect(self.updateView)
        layout.addRow(self.tr("Resources root:"), self.resourcesRootBox)
        layout.addRow(self.tr("Script root:"), self.scriptRootBox)

        self.launchAtStartupBox = QCheckBox(self.tr("Launch At Startup"), self)
        self.mainScriptDrop = QComboBox(self)
        addScriptsLabel = QLabel(self.tr("Add script to main menu:"), self)
        self.addScriptsView = ListView(self)
        self.addScriptsView.setList([["", "", "", ""]])
        self.addScriptsView.setHeaderLabels(
            ["", "Script", "Menu name", "Shortcut"])
        scriptLayout = QVBoxLayout()
        scriptLayout.addWidget(self.launchAtStartupBox)
        scriptLayout.addWidget(self.mainScriptDrop)
        scriptLayout.addWidget(addScriptsLabel)
        scriptLayout.addWidget(self.addScriptsView)
        layout.addRow("", scriptLayout)
        layout.addRow(HLine(self))

        self.tfVersionEdit = QLineEdit(self)
        self.tfVersionEdit.setValidator(VersionValidator(self))
        layout.addRow(self.tr("Requires TruFont:"), self.tfVersionEdit)

        buttonBox = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Close, self)
        buttonBox.accepted.connect(self.saveFile)
        buttonBox.rejected.connect(self.close)
        layout.addRow(buttonBox)

        self.setLayout(layout)
        self.updateView()

    def saveFile(self):
        e = TExtension()
        e.name = self.nameEdit.text() or None
        e.version = self.versionEdit.text() or None
        e.developer = self.developerEdit.text() or None
        e.developerURL = self.developerURLEdit.text() or None

        e.resourcesPath = self.resourcesRootBox.currentFolder()
        e.libPath = self.scriptRootBox.currentFolder()

        e.launchAtStartup = self.launchAtStartupBox.isChecked()
        e.mainScript = self.mainScriptDrop.currentText()
        # Note. for now we always do a list.
        addToMenu = []
        for ok, path, name, shortcut in self.addScriptsView.list():
            if not ok:
                continue
            data = dict(path=path, name=name, shortcut=shortcut)
            for k, v in data.items():
                if v is None:
                    del data[k]
            addToMenu.append(data)
        if addToMenu:
            e.addToMenu = addToMenu
        e.tfVersion = self.tfVersionEdit.text() or None

        # TODO: switch to directory on platforms that need it
        dialog = QFileDialog(
            self, self.tr("Save File"), None, "TruFont Extension (*.tfExt)")
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        ok = dialog.exec_()
        if ok:
            path = dialog.selectedFiles()[0]
            e.save(path)

    def updateView(self):
        path = self.scriptRootBox.currentFolder()
        widgets = (
            self.launchAtStartupBox,
            self.mainScriptDrop,
            self.addScriptsView,
        )
        for widget in widgets:
            widget.setEnabled(path is not None)
        if path is None:
            return
        elements = []
        for root, dirs, files in os.walk(path):
            for file in files:
                if os.path.splitext(file)[1] != ".py":
                    continue
                name = os.path.join(root[len(path)+1:], file)
                self.mainScriptDrop.addItem(name)
                elements.append(
                    [False, name, None, ""])
        self.addScriptsView.setList(elements)
        # TODO: should be done in the widget
        model = self.addScriptsView.model()
        for i in range(len(elements)):
            self.addScriptsView.openPersistentEditor(model.index(i, 0))

    # ----------
    # Qt methods
    # ----------

    def sizeHint(self):
        return QSize(580, 480)
