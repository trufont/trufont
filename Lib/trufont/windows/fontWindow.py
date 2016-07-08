from defconQt.controls.glyphCellView import GlyphCellView, GlyphCellWidget
from defconQt.windows.baseWindows import BaseMainWindow
from trufont import __version__
from trufont.controls.fontDialogs import AddGlyphsDialog, SortDialog
from trufont.objects import settings
from trufont.objects.defcon import TFont
from trufont.tools import errorReports, platformSpecific
from trufont.windows.fontFeaturesWindow import FontFeaturesWindow
from trufont.windows.fontInfoWindow import FontInfoWindow
from trufont.windows.glyphWindow import GlyphWindow
from trufont.windows.groupsWindow import GroupsWindow
from trufont.windows.metricsWindow import MetricsWindow
from trufont.windows.inspectorWindow import InspectorWindow
from trufont.windows.scriptingWindow import ScriptingWindow
from trufont.windows.settingsWindow import SettingsWindow
from PyQt5.QtCore import QEvent, QMimeData, QSize, Qt
from PyQt5.QtGui import QCursor, QIcon, QKeySequence, QPixmap
from PyQt5.QtWidgets import (
    QAction, QApplication, QDialogButtonBox, QFileDialog, QLabel, QMenu,
    QMessageBox, QSlider, QToolTip)
from collections import OrderedDict
import os
import pickle
import platform
import subprocess

try:
    gitShortHash = subprocess.check_output(
        ['git', 'rev-parse', '--short', 'HEAD'], stderr=subprocess.DEVNULL
    ).decode()
except:
    gitShortHash = ""

MAX_RECENT_FILES = 6


class FontWindow(BaseMainWindow):

    def __init__(self, font, parent=None):
        super().__init__(parent)
        self._font = None

        self._settingsWindow = None
        self._infoWindow = None
        self._featuresWindow = None
        self._metricsWindow = None
        self._groupsWindow = None

        menuBar = self.menuBar()
        fileMenu = QMenu(self.tr("&File"), self)
        fileMenu.addAction(self.tr("&New…"), self.newFile, QKeySequence.New)
        fileMenu.addAction(
            self.tr("&Open…"), self.openFile, QKeySequence.Open)
        # recent files
        self.recentFilesMenu = QMenu(self.tr("Open &Recent"), self)
        for i in range(MAX_RECENT_FILES):
            action = QAction(self.recentFilesMenu)
            action.setVisible(False)
            action.triggered.connect(self.openRecentFile)
            self.recentFilesMenu.addAction(action)
        self.updateRecentFiles()
        fileMenu.addMenu(self.recentFilesMenu)
        fileMenu.addAction(self.tr("&Import…"), self.importFile)
        fileMenu.addSeparator()
        fileMenu.addAction(self.tr("&Save"), self.saveFile, QKeySequence.Save)
        fileMenu.addAction(
            self.tr("Save &As…"), self.saveFileAs, QKeySequence.SaveAs)
        fileMenu.addAction(self.tr("&Export…"), self.exportFile)
        fileMenu.addAction(self.tr("&Reload From Disk"), self.reloadFile)
        fileMenu.addAction(self.tr("E&xit"), self.close, QKeySequence.Quit)
        menuBar.addMenu(fileMenu)

        editMenu = QMenu(self.tr("&Edit"), self)
        self._undoAction = editMenu.addAction(
            self.tr("&Undo"), self.undo, QKeySequence.Undo)
        self._redoAction = editMenu.addAction(
            self.tr("&Redo"), self.redo, QKeySequence.Redo)
        editMenu.addSeparator()
        self.markColorMenu = QMenu(self.tr("&Flag Color"), self)
        self.updateMarkColors()
        editMenu.addMenu(self.markColorMenu)
        cut = editMenu.addAction(self.tr("C&ut"), self.cut, QKeySequence.Cut)
        copy = editMenu.addAction(
            self.tr("&Copy"), self.copy, QKeySequence.Copy)
        copyComponent = editMenu.addAction(
            self.tr("Copy &As Component"), self.copyAsComponent, "Ctrl+Alt+C")
        paste = editMenu.addAction(
            self.tr("&Paste"), self.paste, QKeySequence.Paste)
        self._clipboardActions = (cut, copy, copyComponent, paste)
        editMenu.addSeparator()
        editMenu.addAction(self.tr("&Settings…"), self.settings)
        menuBar.addMenu(editMenu)

        fontMenu = QMenu(self.tr("&Font"), self)
        fontMenu.addAction(
            self.tr("&Add Glyphs…"), self.addGlyphs, "Ctrl+G")
        fontMenu.addAction(
            self.tr("Font &Info"), self.fontInfo, "Ctrl+Alt+I")
        fontMenu.addAction(
            self.tr("Font &Features"), self.fontFeatures, "Ctrl+Alt+F")
        fontMenu.addSeparator()
        fontMenu.addAction(self.tr("&Sort…"), self.sortGlyphs)
        menuBar.addMenu(fontMenu)

        pythonMenu = QMenu(self.tr("&Python"), self)
        pythonMenu.addAction(
            self.tr("&Scripting Window"), self.scripting, "Ctrl+Alt+R")
        pythonMenu.addAction(
            self.tr("&Output Window"), self.outputWindow, "Ctrl+Alt+O")
        menuBar.addMenu(pythonMenu)

        windowMenu = QMenu(self.tr("&Windows"), self)
        action = windowMenu.addAction(
            self.tr("&Inspector"), self.inspector, "Ctrl+I")
        # XXX: we're getting duplicate shortcut when we spawn a new window...
        action.setShortcutContext(Qt.ApplicationShortcut)
        windowMenu.addAction(
            self.tr("&Metrics Window"), self.metrics, "Ctrl+Alt+S")
        windowMenu.addAction(
            self.tr("&Groups Window"), self.groups, "Ctrl+Alt+G")
        menuBar.addMenu(windowMenu)

        helpMenu = QMenu(self.tr("&Help"), self)
        helpMenu.addAction(self.tr("&About"), self.about)
        helpMenu.addAction(
            self.tr("About &Qt"), QApplication.instance().aboutQt)
        menuBar.addMenu(helpMenu)

        cellSize = 56
        self.glyphCellView = FontCellView(self)
        self.glyphCellView.glyphActivated.connect(self._glyphActivated)
        self.glyphCellView.glyphsDropped.connect(self._orderChanged)
        self.glyphCellView.selectionChanged.connect(self._selectionChanged)
        self.glyphCellView.setAcceptDrops(True)
        self.glyphCellView.setCellRepresentationName("TruFont.GlyphCell")
        self.glyphCellView.setCellSize(cellSize)
        self.glyphCellView.setFocus()

        self.cellSizeSlider = QSlider(Qt.Horizontal, self)
        self.cellSizeSlider.setMinimum(32)
        self.cellSizeSlider.setMaximum(116)
        self.cellSizeSlider.setFixedWidth(.9 * self.cellSizeSlider.width())
        self.cellSizeSlider.setValue(cellSize)
        self.cellSizeSlider.valueChanged.connect(self._sliderCellSizeChanged)
        self.selectionLabel = QLabel(self)
        statusBar = self.statusBar()
        statusBar.addPermanentWidget(self.cellSizeSlider)
        statusBar.addWidget(self.selectionLabel)

        self.setFont_(font)
        if font is not None:
            self.setCurrentFile(font.path)

        app = QApplication.instance()
        app.dispatcher.addObserver(
            self, "_preferencesChanged", "preferencesChanged")
        app.dispatcher.addObserver(self, "_fontSaved", "fontSaved")
        self._updateGlyphActions()

        self.setCentralWidget(self.glyphCellView)
        self.setWindowTitle()
        self.resize(605, 430)

    # --------------
    # Custom methods
    # --------------

    def font_(self):
        return self._font

    def setFont_(self, font):
        if self._font is not None:
            self._font.removeObserver(self, "Font.Changed")
            self._font.removeObserver(self, "Font.GlyphOrderChanged")
            self._font.removeObserver(self, "Font.SortDescriptorChanged")
        self._font = font
        if font is None:
            return
        self._updateGlyphsFromGlyphOrder()
        font.addObserver(self, "_fontChanged", "Font.Changed")
        font.addObserver(
            self, "_glyphOrderChanged", "Font.GlyphOrderChanged")
        font.addObserver(
            self, "_sortDescriptorChanged", "Font.SortDescriptorChanged")

    def maybeSaveBeforeExit(self):
        if self._font.dirty:
            currentFont = self.windowTitle()[3:]
            body = self.tr("Do you want to save the changes you made "
                           "to “{}”?").format(currentFont)
            closeDialog = QMessageBox(
                QMessageBox.Question, None, body,
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                self)
            closeDialog.setInformativeText(
                self.tr("Your changes will be lost if you don’t save them."))
            closeDialog.setModal(True)
            ret = closeDialog.exec_()
            if ret == QMessageBox.Save:
                self.saveFile()
                return True
            elif ret == QMessageBox.Discard:
                return True
            return False
        return True

    # -------------
    # Notifications
    # -------------

    # app

    def _fontSaved(self, notification):
        if notification.data["font"] != self._font:
            return
        path = notification.data["path"]
        self.setCurrentFile(path)
        self.setWindowModified(False)

    def _preferencesChanged(self, notification):
        self.updateMarkColors()

    # widgets

    def _sliderCellSizeChanged(self):
        cellSize = self.cellSizeSlider.value()
        self.glyphCellView.setCellSize(cellSize)
        QToolTip.showText(QCursor.pos(), str(cellSize), self)

    def _glyphActivated(self, glyph):
        glyphWindow = GlyphWindow(glyph, self)
        glyphWindow.show()

    def _orderChanged(self):
        # TODO: reimplement when we start showing glyph subsets
        glyphs = self.glyphCellView.glyphs()
        self._font.glyphOrder = [glyph.name for glyph in glyphs]

    def _selectionChanged(self):
        # currentGlyph
        lastSelectedGlyph = self.glyphCellView.lastSelectedGlyph()
        app = QApplication.instance()
        app.setCurrentGlyph(lastSelectedGlyph)
        # selection text
        # TODO: this should probably be internal to the label
        selection = self.glyphCellView.selection()
        if selection is not None:
            count = len(selection)
            if count == 1:
                glyph = self.glyphCellView.glyphsForIndexes(selection)[0]
                text = "%s " % glyph.name
            else:
                text = ""
            if count:
                text = self.tr("{0}(%n selected)".format(text), n=count)
        else:
            text = ""
        self.selectionLabel.setText(text)
        # actions
        self._updateGlyphActions()

    # defcon

    def _fontChanged(self, notification):
        font = notification.object
        self.setWindowModified(font.dirty)

    def _glyphOrderChanged(self, notification):
        self._updateGlyphsFromGlyphOrder()

    def _updateGlyphsFromGlyphOrder(self):
        font = self._font
        glyphOrder = font.glyphOrder
        if glyphOrder:
            glyphs = []
            for glyphName in glyphOrder:
                if glyphName in font:
                    glyphs.append(font[glyphName])
            if len(glyphs) < len(font):
                # if some glyphs in the font are not present in the glyph
                # order, loop again to add them at the end
                for glyph in font:
                    if glyph not in glyphs:
                        glyphs.append(glyph)
                font.disableNotifications(observer=self)
                font.glyphOrder = [glyph.name for glyph in glyphs]
                font.enableNotifications(observer=self)
        else:
            glyphs = list(font)
            font.disableNotifications(observer=self)
            font.glyphOrder = [glyph.name for glyph in glyphs]
            font.enableNotifications(observer=self)
        self.glyphCellView.setGlyphs(glyphs)

    def _sortDescriptorChanged(self, notification):
        font = notification.object
        descriptors = notification.data["newValue"]
        if descriptors[0]["type"] == "glyphSet":
            glyphNames = descriptors[0]["glyphs"]
        else:
            glyphNames = font.unicodeData.sortGlyphNames(
                font.keys(), descriptors)
        font.glyphOrder = glyphNames

    # ------------
    # Menu methods
    # ------------

    # File

    def newFile(self):
        QApplication.instance().newFile()

    def openFile(self):
        path, _ = QFileDialog.getOpenFileName(
            self, self.tr("Open File"), '',
            platformSpecific.fileFormat
        )
        if path:
            QApplication.instance().openFile(path)

    def openRecentFile(self):
        fontPath = self.sender().toolTip()
        QApplication.instance().openFile(fontPath)

    def saveFile(self, path=None, ufoFormatVersion=3):
        if path is None and self._font.path is None:
            self.saveFileAs()
        else:
            if path is None:
                path = self._font.path
            self._font.save(path, ufoFormatVersion)

    def saveFileAs(self):
        fileFormats = OrderedDict([
            (self.tr("UFO Font version 3 {}").format("(*.ufo)"), 3),
            (self.tr("UFO Font version 2 {}").format("(*.ufo)"), 2),
        ])
        # TODO: switch to directory on platforms that need it
        dialog = QFileDialog(
            self, self.tr("Save File"), None, ";;".join(fileFormats.keys()))
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        ok = dialog.exec_()
        if ok:
            nameFilter = dialog.selectedNameFilter()
            path = dialog.selectedFiles()[0]
            self.saveFile(path, fileFormats[nameFilter])
            self.setWindowTitle()
        # return ok

    def importFile(self):
        # TODO: systematize this
        fileFormats = (
            self.tr("OpenType Font file {}").format("(*.otf *.ttf)"),
            self.tr("Type1 Font file {}").format("(*.pfa *.pfb)"),
            self.tr("ttx Font file {}").format("(*.ttx)"),
            self.tr("WOFF Font file {}").format("(*.woff)"),
            self.tr("All supported files {}").format(
                "(*.otf *.pfa *.pfb *.ttf *.ttx *.woff)"),
            self.tr("All files {}").format("(*.*)"),
        )

        path, _ = QFileDialog.getOpenFileName(
            self, self.tr("Import File"), None,
            ";;".join(fileFormats), fileFormats[-2])

        if path:
            font = TFont()
            try:
                font.extract(path)
            except Exception as e:
                errorReports.showCriticalException(e)
                return
            window = FontWindow(font)
            window.show()

    def exportFile(self):
        path, _ = QFileDialog.getSaveFileName(
            self, self.tr("Export File"), None,
            self.tr("OpenType PS font {}").format("(*.otf)"))
        if path:
            try:
                self._font.export(path)
            except Exception as e:
                errorReports.showCriticalException(e)

    def reloadFile(self):
        font = self._font
        if font.path is None:
            return
        font.reloadInfo()
        font.reloadKerning()
        font.reloadGroups()
        font.reloadFeatures()
        font.reloadLib()
        font.reloadGlyphs(font.keys())
        self.setWindowModified(False)

    # Edit

    def undo(self):
        glyph = self.glyphCellView.lastSelectedGlyph()
        glyph.undo()

    def redo(self):
        glyph = self.glyphCellView.lastSelectedGlyph()
        glyph.redo()

    def markColor(self):
        color = self.sender().data()
        if color is not None:
            color = color.getRgbF()
        glyphs = self.glyphCellView.glyphs()
        for index in self.glyphCellView.selection():
            glyph = glyphs[index]
            glyph.markColor = color

    def cut(self):
        self.copy()
        glyphs = self.glyphCellView.glyphs()
        for index in self.glyphCellView.selection():
            glyph = glyphs[index]
            glyph.clear()

    def copy(self):
        glyphs = self.glyphCellView.glyphs()
        pickled = []
        for index in sorted(self.glyphCellView.selection()):
            pickled.append(glyphs[index].serialize(
                blacklist=("name", "unicode")
            ))
        clipboard = QApplication.clipboard()
        mimeData = QMimeData()
        mimeData.setData("application/x-trufont-glyph-data",
                         pickle.dumps(pickled))
        clipboard.setMimeData(mimeData)

    def copyAsComponent(self):
        glyphs = self.glyphCellView.glyphs()
        pickled = []
        for index in self.glyphCellView.selection():
            glyph = glyphs[index]
            componentGlyph = glyph.__class__()
            componentGlyph.width = glyph.width
            component = componentGlyph.instantiateComponent()
            component.baseGlyph = glyph.name
            pickled.append(componentGlyph.serialize())
        clipboard = QApplication.clipboard()
        mimeData = QMimeData()
        mimeData.setData("application/x-trufont-glyph-data",
                         pickle.dumps(pickled))
        clipboard.setMimeData(mimeData)

    def paste(self):
        clipboard = QApplication.clipboard()
        mimeData = clipboard.mimeData()
        if mimeData.hasFormat("application/x-trufont-glyph-data"):
            data = pickle.loads(mimeData.data(
                "application/x-trufont-glyph-data"))
            selection = self.glyphCellView.selection()
            glyphs = self.glyphCellView.glyphsForIndexes(selection)
            if len(data) == len(glyphs):
                for pickled, glyph in zip(data, glyphs):
                    # XXX: prune
                    glyph.prepareUndo()
                    glyph.deserialize(pickled)

    def settings(self):
        if self._settingsWindow is not None and \
                self._settingsWindow.isVisible():
            self._settingsWindow.raise_()
        else:
            self._settingsWindow = SettingsWindow(self)
            self._settingsWindow.show()

    # Font

    def fontInfo(self):
        # If a window is already opened, bring it to the front, else spawn one.
        # TODO: see about using widget.setAttribute(Qt.WA_DeleteOnClose)
        # otherwise it seems we're just leaking memory after each close...
        # (both raise_ and show allocate memory instead of using the hidden
        # widget it seems)
        if self._infoWindow is not None and self._infoWindow.isVisible():
            self._infoWindow.raise_()
        else:
            self._infoWindow = FontInfoWindow(self._font, self)
            self._infoWindow.show()

    def fontFeatures(self):
        # TODO: see up here
        if self._featuresWindow is not None and self._featuresWindow.isVisible(
                ):
            self._featuresWindow.raise_()
        else:
            self._featuresWindow = FontFeaturesWindow(self._font, self)
            self._featuresWindow.show()

    def addGlyphs(self):
        glyphs = self.glyphCellView.glyphs()
        newGlyphNames, params, ok = AddGlyphsDialog.getNewGlyphNames(
            self, glyphs)
        if ok:
            sortFont = params.pop("sortFont")
            for name in newGlyphNames:
                glyph = self._font.newStandardGlyph(name, **params)
                if glyph is not None:
                    glyphs.append(glyph)
            self.glyphCellView.setGlyphs(glyphs)
            if sortFont:
                # TODO: when the user add chars from a glyphSet and no others,
                # should we try to sort according to that glyphSet?
                # The above would probably warrant some rearchitecturing.
                # kick-in the sort mechanism
                self._font.sortDescriptor = self._font.sortDescriptor

    def sortGlyphs(self):
        sortDescriptor, ok = SortDialog.getDescriptor(
            self, self._font.sortDescriptor)
        if ok:
            self._font.sortDescriptor = sortDescriptor

    # Python

    def scripting(self):
        app = QApplication.instance()
        if not hasattr(app, 'scriptingWindow'):
            app.scriptingWindow = ScriptingWindow()
            app.scriptingWindow.show()
        elif app.scriptingWindow.isVisible():
            app.scriptingWindow.raise_()
        else:
            app.scriptingWindow.show()

    def outputWindow(self):
        app = QApplication.instance()
        if app.outputWindow.isVisible():
            app.outputWindow.raise_()
        else:
            app.outputWindow.show()

    # Windows

    def inspector(self):
        app = QApplication.instance()
        if app.inspectorWindow is None:
            app.inspectorWindow = InspectorWindow()
            app.inspectorWindow.show()
        elif app.inspectorWindow.isVisible():
            # TODO: do this only if the widget is user-visible, otherwise the
            # key press feels as if it did nothing
            # toggle
            app.inspectorWindow.close()
        else:
            app.inspectorWindow.show()

    def metrics(self):
        # TODO: see up here
        if self._metricsWindow is not None and self._metricsWindow.isVisible():
            self._metricsWindow.raise_()
        else:
            self._metricsWindow = MetricsWindow(self._font, parent=self)
            self._metricsWindow.show()
        # TODO: default string kicks-in on the window before this. Figure out
        # how to make a clean interface
        selection = self.glyphCellView.selection()
        if selection:
            glyphs = self.glyphCellView.glyphsForIndexes(selection)
            self._metricsWindow.setGlyphs(glyphs)

    def groups(self):
        # TODO: see up here
        if self._groupsWindow is not None and self._groupsWindow.isVisible():
            self._groupsWindow.raise_()
        else:
            self._groupsWindow = GroupsWindow(self._font, self)
            self._groupsWindow.show()

    # About

    def about(self):
        name = QApplication.applicationName()
        domain = QApplication.organizationDomain()
        caption = self.tr(
            "<h3>About {n}</h3>"
            "<p>{n} is a cross-platform, modular typeface design "
            "application.</p>").format(n=name)
        text = self.tr(
            "<p>{} is built on top of "
            "<a href='http://ts-defcon.readthedocs.org/en/ufo3/'>defcon</a> "
            "and includes scripting support "
            "with a <a href='http://robofab.com/'>robofab</a>-like API.</p>"
            "<p>Version {} {} – Python {}.").format(
            name, __version__, gitShortHash, platform.python_version())
        if domain:
            text += self.tr("<br>See <a href='http://{d}'>{d}</a> for more "
                            "information.</p>").format(d=domain)
        else:
            text += "</p>"
        # This duplicates much of QMessageBox.about(), but it has no way to
        # setInformativeText()...
        msgBox = QMessageBox(self)
        msgBox.setAttribute(Qt.WA_DeleteOnClose)
        icon = msgBox.windowIcon()
        size = icon.actualSize(QSize(64, 64))
        msgBox.setIconPixmap(icon.pixmap(size))
        msgBox.setWindowTitle(self.tr("About {}").format(name))
        msgBox.setText(caption)
        msgBox.setInformativeText(text)
        if platformSpecific.useCenteredButtons():
            buttonBox = msgBox.findChild(QDialogButtonBox)
            buttonBox.setCenterButtons(True)
        msgBox.show()

    # update methods

    def setCurrentFile(self, path):
        if path is None:
            return
        recentFiles = settings.recentFiles()
        if path in recentFiles:
            recentFiles.remove(path)
        recentFiles.insert(0, path)
        while len(recentFiles) > MAX_RECENT_FILES:
            del recentFiles[-1]
        settings.setRecentFiles(recentFiles)
        for window in QApplication.topLevelWidgets():
            if isinstance(window, FontWindow):
                window.updateRecentFiles()

    def updateRecentFiles(self):
        recentFiles = settings.recentFiles()
        count = min(len(recentFiles), MAX_RECENT_FILES)
        actions = self.recentFilesMenu.actions()
        for index, recentFile in enumerate(recentFiles[:count]):
            action = actions[index]
            shortName = os.path.basename(recentFile.rstrip(os.sep))

            action.setText(shortName)
            action.setToolTip(recentFile)
            action.setVisible(True)
        for index in range(count, MAX_RECENT_FILES):
            actions[index].setVisible(False)

        self.recentFilesMenu.setEnabled(len(recentFiles))

    def updateMarkColors(self):
        entries = settings.readMarkColors()
        self.markColorMenu.clear()
        pixmap = QPixmap(24, 24)
        none = self.markColorMenu.addAction("None", self.markColor)
        none.setData(None)
        for color, name in entries:
            action = self.markColorMenu.addAction(name, self.markColor)
            pixmap.fill(color)
            action.setIcon(QIcon(pixmap))
            action.setData(color)

    def _updateGlyphActions(self):
        currentGlyph = self.glyphCellView.lastSelectedGlyph()
        # disconnect eventual signal of previous glyph
        self._undoAction.disconnect()
        self._undoAction.triggered.connect(self.undo)
        self._redoAction.disconnect()
        self._redoAction.triggered.connect(self.redo)
        # now update status
        if currentGlyph is None:
            self._undoAction.setEnabled(False)
            self._redoAction.setEnabled(False)
        else:
            undoManager = currentGlyph.undoManager
            self._undoAction.setEnabled(currentGlyph.canUndo())
            undoManager.canUndoChanged.connect(self._undoAction.setEnabled)
            self._redoAction.setEnabled(currentGlyph.canRedo())
            undoManager.canRedoChanged.connect(self._redoAction.setEnabled)
        # and other actions
        for action in self._clipboardActions:
            action.setEnabled(currentGlyph is not None)
        self.markColorMenu.setEnabled(currentGlyph is not None)

    # ----------
    # Qt methods
    # ----------

    def showEvent(self, event):
        app = QApplication.instance()
        data = dict(
            font=self._font,
            window=self,
        )
        app.postNotification("fontWindowWillOpen", data)
        super().showEvent(event)
        app.postNotification("fontWindowOpened", data)

    def closeEvent(self, event):
        ok = self.maybeSaveBeforeExit()
        if ok:
            app = QApplication.instance()
            data = dict(
                font=self._font,
                window=self,
            )
            app.postNotification("fontWindowWillClose", data)
            self._font.removeObserver(self, "Font.Changed")
            app = QApplication.instance()
            app.dispatcher.removeObserver(self, "preferencesChanged")
            app.dispatcher.removeObserver(self, "fontSaved")
            event.accept()
        else:
            event.ignore()

    def event(self, event):
        if event.type() == QEvent.WindowActivate:
            app = QApplication.instance()
            app.setCurrentMainWindow(self)
            inspector = app.inspectorWindow
            if inspector is not None and inspector.isVisible():
                inspector.raise_()
            lastSelectedGlyph = self.glyphCellView.lastSelectedGlyph()
            if lastSelectedGlyph is not None:
                app.setCurrentGlyph(lastSelectedGlyph)
        return super().event(event)

    def setWindowTitle(self, title=None):
        if title is None:
            if self._font.path is not None:
                title = os.path.basename(self._font.path.rstrip(os.sep))
            else:
                title = self.tr("Untitled.ufo")
        super().setWindowTitle("[*]{}".format(title))


class FontCellWidget(GlyphCellWidget):

    def _proceedWithDeletion(self, erase=False):
        if not self._selection:
            return
        tr = self.tr("Delete") if erase else self.tr("Clear")
        text = self.tr("Do you want to %s selected glyphs?") % tr.lower()
        closeDialog = QMessageBox(
            QMessageBox.Question, "",
            self.tr("%s glyphs") % tr,
            QMessageBox.Yes | QMessageBox.No, self)
        closeDialog.setInformativeText(text)
        closeDialog.setModal(True)
        ret = closeDialog.exec_()
        if ret == QMessageBox.Yes:
            return True
        return False

    def keyPressEvent(self, event):
        modifiers = event.modifiers()
        if platformSpecific.isDeleteEvent(event):
            erase = modifiers & Qt.ShiftModifier
            if self._proceedWithDeletion(erase):
                glyphs = self.glyphsForIndexes(self._selection)
                for glyph in glyphs:
                    font = glyph.font
                    if erase:
                        del font[glyph.name]
                    else:
                        # TODO: consider doing that in glyph template setter
                        glyph.clear()
                        glyph.template = True
        elif event.matches(QKeySequence.SelectAll):
            self.selectAll()
        elif event.key() == Qt.Key_D and modifiers & Qt.ControlModifier:
            self.setSelection(set())
        else:
            super().keyPressEvent(event)


class FontCellView(GlyphCellView):
    glyphCellWidgetClass = FontCellWidget
