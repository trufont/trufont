from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from defconQt.controls.listView import ListView
from trufont.controls.nameTabWidget import NameTabWidget
from trufont.objects import icons, settings


class SettingsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Settings"))

        self.tabWidget = NameTabWidget(self)
        self.tabWidget.addNamedTab(GlyphSetTab(self))
        self.tabWidget.addNamedTab(MetricsWindowTab(self))
        self.tabWidget.addNamedTab(MiscTab(self))

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.tabWidget)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

        self.readSettings()

    def readSettings(self):
        geometry = settings.settingsWindowGeometry()
        if geometry:
            self.restoreGeometry(geometry)

    def writeSettings(self):
        settings.setSettingsWindowGeometry(self.saveGeometry())

    def moveEvent(self, event):
        self.writeSettings()

    resizeEvent = moveEvent

    def sizeHint(self):
        return QSize(625, 450)

    def accept(self):
        for i in range(self.tabWidget.count()):
            self.tabWidget.widget(i).writeSettings()
        app = QApplication.instance()
        app.postNotification("preferencesChanged")
        super().accept()


class GlyphSetTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.name = self.tr("Glyph sets")

        self.defaultGlyphSetBox = QCheckBox(self.tr("Default glyph set:"), self)
        self.defaultGlyphSetDrop = QComboBox(self)
        self.defaultGlyphSetBox.toggled.connect(self.toggleGlyphSetDrop)

        self.glyphSetList = QListWidget(self)
        self.glyphSetList.setSortingEnabled(True)
        self.glyphSetContents = QPlainTextEdit(self)
        self.glyphSetList.currentItemChanged.connect(self.updateGlyphSetContents)
        self.glyphSetList.itemChanged.connect(self.renameGlyphSet)
        self._cachedName = None
        splitter = QSplitter(self)
        splitter.addWidget(self.glyphSetList)
        splitter.addWidget(self.glyphSetContents)
        self.addGlyphSetButton = QPushButton(self)
        self.addGlyphSetButton.setIcon(icons.i_plus())
        self.addGlyphSetButton.clicked.connect(lambda: self.addGlyphSet())
        self.removeGlyphSetButton = QPushButton(self)
        self.removeGlyphSetButton.setIcon(icons.i_minus())
        self.removeGlyphSetButton.clicked.connect(self.removeGlyphSet)
        self.importButton = QPushButton(self.tr("Import"), self)
        importMenu = QMenu(self)
        importMenu.addAction(
            self.tr("Import from Current Font"), self.importFromCurrentFont
        )
        self.importButton.setMenu(importMenu)
        self.glyphListBox = QCheckBox(self.tr("Glyph list path:"), self)
        self.glyphListEdit = QLineEdit(self)
        self.glyphListEdit.setReadOnly(True)
        self.glyphListButton = QPushButton(self.tr("Browse…"), self)
        self.glyphListButton.clicked.connect(self.getGlyphList)
        self.glyphListBox.toggled.connect(self.glyphListEdit.setEnabled)
        self.glyphListBox.toggled.connect(self.glyphListButton.setEnabled)

        buttonsLayout = QHBoxLayout()
        buttonsLayout.addWidget(self.addGlyphSetButton)
        buttonsLayout.addWidget(self.removeGlyphSetButton)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        buttonsLayout.addWidget(spacer)
        buttonsLayout.addWidget(self.importButton)

        firstLayout = QGridLayout()
        line = 0
        firstLayout.addWidget(self.defaultGlyphSetBox, line, 0, 1, 2)
        firstLayout.addWidget(self.defaultGlyphSetDrop, line, 3, 1, 3)
        line += 1
        firstLayout.addWidget(splitter, line, 0, 1, 6)
        line += 1
        firstLayout.addLayout(buttonsLayout, line, 0, 1, 3)
        secondLayout = QHBoxLayout()
        secondLayout.addWidget(self.glyphListBox)
        secondLayout.addWidget(self.glyphListEdit)
        secondLayout.addWidget(self.glyphListButton)
        mainLayout = QVBoxLayout(self)
        mainLayout.addLayout(firstLayout)
        mainLayout.addLayout(secondLayout)
        self.setLayout(mainLayout)

        self.readSettings()

    def addGlyphSet(self, glyphNames=[], glyphSetName=None):
        if glyphSetName is None:
            glyphSetName = self.tr("New glyph set")
        if glyphSetName in self.glyphSets:
            index = 1
            while "%s %d" % (glyphSetName, index) in self.glyphSets:
                index += 1
            glyphSetName = "%s %d" % (glyphSetName, index)
        self.glyphSets[glyphSetName] = glyphNames
        item = QListWidgetItem(glyphSetName, self.glyphSetList)
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        self.glyphSetList.setCurrentItem(item)
        self.glyphSetList.editItem(item)
        self.removeGlyphSetButton.setEnabled(True)

    def removeGlyphSet(self):
        i = self.glyphSetList.currentRow()
        text = self.glyphSetList.takeItem(i).text()
        del self.glyphSets[text]
        if self.glyphSetList.count() < 2:
            self.removeGlyphSetButton.setEnabled(False)

    def renameGlyphSet(self):
        newKey = self.glyphSetList.currentItem()
        if newKey is None:
            return
        newKey = newKey.text()
        self.glyphSets[newKey] = self.glyphSets[self._cachedName]
        del self.glyphSets[self._cachedName]

    def importFromCurrentFont(self):
        font = QApplication.instance().currentFont()
        name = f"{font.info.familyName} {font.info.styleName}"
        self.addGlyphSet(font.glyphOrder, name)

    def toggleGlyphSetDrop(self):
        sender = self.sender()
        self.defaultGlyphSetDrop.setEnabled(sender.isChecked())

    def updateGlyphSetContents(self, current, previous):
        # store content of the textEdit in the glyphSet dict
        if previous is not None:
            glyphNames = self.glyphSetContents.toPlainText().split()
            self.glyphSets[previous.text()] = glyphNames
        # now update the text edit to current glyphSet
        glyphSetName = current.text()
        text = " ".join(self.glyphSets[glyphSetName])
        self.glyphSetContents.setPlainText(text)
        # cache current name for renames
        self._cachedName = glyphSetName

    def getGlyphList(self):
        fileFormats = (
            self.tr("Text file {}").format("(*.txt)"),
            self.tr("All files {}").format("(*.*)"),
        )
        path, _ = QFileDialog.getOpenFileName(
            self, self.tr("Open File"), "", ";;".join(fileFormats)
        )
        if path:
            self.glyphListEdit.setText(path)

    def readSettings(self):
        defaultGlyphSet = settings.defaultGlyphSet()
        self.defaultGlyphSetBox.setChecked(len(defaultGlyphSet))

        self.glyphSets = settings.readGlyphSets()
        self.defaultGlyphSetDrop.clear()
        self.defaultGlyphSetDrop.addItems(self.glyphSets.keys())

        self.glyphSetList.clear()
        glyphSetNames = self.glyphSets.keys()
        # Normally we should be enforcing this rather decently in the interface
        # already
        if glyphSetNames:
            for glyphSetName in glyphSetNames:
                item = QListWidgetItem(glyphSetName, self.glyphSetList)
                item.setFlags(item.flags() | Qt.ItemIsEditable)
            self.glyphSetList.setCurrentRow(0)
        self.removeGlyphSetButton.setEnabled(len(self.glyphSets) > 1)

        glyphListPath = settings.glyphListPath()
        self.glyphListBox.setChecked(bool(glyphListPath))
        self.glyphListEdit.setEnabled(bool(glyphListPath))
        self.glyphListEdit.setText(glyphListPath)
        self.glyphListButton.setEnabled(bool(glyphListPath))

    def writeSettings(self):
        # store content of the textEdit in the glyphSet dict
        glyphNames = self.glyphSetContents.toPlainText().split()
        currentGlyphSet = self.glyphSetList.currentItem().text()
        self.glyphSets[currentGlyphSet] = glyphNames

        settings.writeGlyphSets(self.glyphSets)
        if not self.defaultGlyphSetBox.isChecked():
            settings.setDefaultGlyphSet(None)
        else:
            defaultGlyphSet = self.defaultGlyphSetDrop.currentText()
            settings.setDefaultGlyphSet(defaultGlyphSet)
        if not self.glyphListBox.isChecked():
            settings.setGlyphListPath(None)
        else:
            glyphListPath = self.glyphListEdit.text()
            if glyphListPath:
                settings.setGlyphListPath(glyphListPath)
                QApplication.instance().loadGlyphList()


class MetricsWindowTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.name = self.tr("Metrics Window")

        self.inputTextLabel = QLabel(self.tr("Default text:"), self)
        self.inputTextList = QListWidget(self)
        self.inputTextList.setDragDropMode(QAbstractItemView.InternalMove)
        self.addItemButton = QPushButton(self)
        self.addItemButton.setIcon(icons.i_plus())
        self.addItemButton.clicked.connect(self.addItem)
        self.removeItemButton = QPushButton(self)
        self.removeItemButton.setIcon(icons.i_minus())
        self.removeItemButton.clicked.connect(self.removeItem)

        buttonsLayout = QHBoxLayout()
        buttonsLayout.addWidget(self.addItemButton)
        buttonsLayout.addWidget(self.removeItemButton)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        buttonsLayout.addWidget(spacer)

        layout = QVBoxLayout(self)
        layout.addWidget(self.inputTextLabel)
        layout.addWidget(self.inputTextList)
        layout.addLayout(buttonsLayout)
        self.setLayout(layout)

        self.readSettings()

    def addItem(self):
        item = QListWidgetItem(self.inputTextList)
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        self.inputTextList.setCurrentItem(item)
        self.inputTextList.editItem(item)
        self.removeItemButton.setEnabled(True)

    def removeItem(self):
        i = self.inputTextList.currentRow()
        self.inputTextList.takeItem(i)
        if not self.inputTextList.count():
            self.removeItemButton.setEnabled(False)

    def readSettings(self):
        self.inputTextList.clear()
        entries = settings.metricsWindowComboBoxItems()
        for entry in entries:
            item = QListWidgetItem(entry, self.inputTextList)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
        if not len(entries):
            self.removeItemButton.setEnabled(False)

    def writeSettings(self):
        entries = []
        for i in range(self.inputTextList.count()):
            item = self.inputTextList.item(i)
            entries.append(item.text())
        settings.setMetricsWindowComboBoxItems(entries)


class MiscTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.name = self.tr("Misc")

        self.markColorLabel = QLabel(self.tr("Default flag colors:"), self)
        self.markColorView = ListView(self)
        self.markColorView.setDragEnabled(True)
        # HACK: we need a model before declaring headers
        self.markColorView.setList([])
        self.markColorView.setHeaderLabels((self.tr("Color"), self.tr("Name")))
        self.addItemButton = QPushButton(self)
        self.addItemButton.setIcon(icons.i_plus())
        self.addItemButton.clicked.connect(self.addItem)
        self.removeItemButton = QPushButton(self)
        self.removeItemButton.setIcon(icons.i_minus())
        self.removeItemButton.clicked.connect(self.removeItem)

        self.loadRecentFileBox = QCheckBox(
            self.tr("Load most recent file on start"), self
        )

        buttonsLayout = QHBoxLayout()
        buttonsLayout.setSizeConstraint(QHBoxLayout.SetMinimumSize)
        buttonsLayout.addWidget(self.addItemButton)
        buttonsLayout.addWidget(self.removeItemButton)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        buttonsLayout.addWidget(spacer)

        layout = QVBoxLayout(self)
        layout.addWidget(self.markColorLabel)
        layout.addWidget(self.markColorView)
        layout.addLayout(buttonsLayout)
        layout.addWidget(self.loadRecentFileBox)
        self.setLayout(layout)

        self.readSettings()

    def addItem(self):
        lst = self.markColorView.list()
        lst.append([QColor(170, 255, 255), self.tr("New!")])
        self.markColorView.setList(lst)
        self.markColorView.editIndex(len(lst) - 1, 1)
        self.removeItemButton.setEnabled(True)

    def removeItem(self):
        self.markColorView.removeCurrentRow()
        if not len(self.markColorView.list()):
            self.removeItemButton.setEnabled(False)

    def readSettings(self):
        entries = settings.readMarkColors()
        self.markColorView.setList(entries)
        if not len(entries):
            self.removeItemButton.setEnabled(False)

        loadRecentFile = settings.loadRecentFile()
        self.loadRecentFileBox.setChecked(loadRecentFile)

    def writeSettings(self):
        markColors = self.markColorView.list()
        settings.writeMarkColors(markColors)

        loadRecentFile = self.loadRecentFileBox.isChecked()
        settings.setLoadRecentFile(loadRecentFile)
