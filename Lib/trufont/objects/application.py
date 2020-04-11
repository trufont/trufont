import os

from defcon.tools.notifications import NotificationCenter
from PyQt5.QtCore import QEvent, QStandardPaths, Qt, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QAction, QApplication, QFileDialog

from trufont.controls.aboutDialog import AboutDialog
from trufont.drawingTools.knifeTool import KnifeTool
from trufont.drawingTools.penTool import PenTool
from trufont.drawingTools.rulerTool import RulerTool
from trufont.drawingTools.selectionTool import SelectionTool
from trufont.drawingTools.shapesTool import ShapesTool
from trufont.drawingTools.textTool import TextTool
from trufont.objects import settings
from trufont.objects.defcon import TFont
from trufont.objects.extension import TExtension
from trufont.objects.menu import MAX_RECENT_FILES, Entries, MenuBar, globalMenuBar
from trufont.tools import errorReports, glyphList, platformSpecific
from trufont.windows.extensionBuilderWindow import ExtensionBuilderWindow
from trufont.windows.fontWindow import FontWindow
from trufont.windows.scriptingWindow import ScriptingWindow
from trufont.windows.settingsWindow import SettingsWindow


class Application(QApplication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._currentGlyph = None
        self._currentFontWindow = None
        self._launched = False
        self._drawingTools = [
            SelectionTool,
            PenTool,
            KnifeTool,
            RulerTool,
            ShapesTool,
            TextTool,
        ]
        self._extensions = []
        self.dispatcher = NotificationCenter()
        self.dispatcher.addObserver(self, "_fontWindowClosed", "fontWillClose")
        self.focusWindowChanged.connect(self._focusWindowChanged)
        self.GL2UV = None
        self.outputWindow = None

    # --------------
    # Event handling
    # --------------

    def _focusWindowChanged(self):
        # update menu bar
        self.updateMenuBar()
        # update main window
        window = self.activeWindow()
        if window is None:
            return
        while True:
            parent = window.parent()
            if parent is None:
                break
            window = parent
        if isinstance(window, FontWindow):
            self.setCurrentFontWindow(window)

    def _fontWindowClosed(self, notification):
        font = notification.data["font"]
        # cleanup CurrentFont/CurrentGlyph when closing the corresponding
        # window
        if self._currentFontWindow is not None:
            if self._currentFontWindow.font == font:
                self.setCurrentFontWindow(None)
        if self._currentGlyph is not None:
            if self._currentGlyph.font == font:
                self.setCurrentGlyph(None)

    def event(self, event):
        eventType = event.type()
        # respond to OSX open events
        if eventType == QEvent.FileOpen:
            filePath = event.file()
            self.openFile(filePath)
            return True
        elif eventType == QEvent.ApplicationStateChange:
            applicationState = self.applicationState()
            if applicationState == Qt.ApplicationActive:
                if not self._launched:
                    notification = "applicationLaunched"
                    self.loadGlyphList()
                    self._launched = True
                else:
                    notification = "applicationActivated"
                    # XXX: do it
                    # self.lookupExternalChanges()
                self.postNotification(notification)
            elif applicationState == Qt.ApplicationInactive:
                self.postNotification("applicationWillIdle")
        return super().event(event)

    def postNotification(self, notification, data=None):
        dispatcher = self.dispatcher
        dispatcher.postNotification(
            notification=notification, observable=self, data=data
        )

    # ---------------
    # File management
    # ---------------

    def loadGlyphList(self):
        glyphListPath = settings.glyphListPath()
        if glyphListPath and os.path.exists(glyphListPath):
            try:
                glyphList_ = glyphList.parseGlyphList(glyphListPath)
            except Exception as e:
                msg = self.tr(
                    "The glyph list at {0} cannot " "be parsed and will be dropped."
                ).format(glyphListPath)
                errorReports.showWarningException(e, msg)
                settings.removeGlyphListPath()
            else:
                self.GL2UV = glyphList_

    def lookupExternalChanges(self):
        for font in self.allFonts():
            if not font.path:
                continue
            changed = font.testForExternalChanges()
            for attr in ("info", "kerning", "groups", "features", "lib"):
                if changed[attr]:
                    data = dict(font=font)
                    self.postNotification("fontChangedExternally", data)
                    return
            # XXX: do more

    # -----------------
    # Window management
    # -----------------

    def currentFontWindow(self):
        return self._currentFontWindow

    def setCurrentFontWindow(self, fontWindow):
        if fontWindow == self._currentFontWindow:
            return
        self._currentFontWindow = fontWindow
        self.postNotification("currentFontChanged")

    # --------
    # Menu Bar
    # --------

    def fetchMenuBar(self, window=None):
        if platformSpecific.useGlobalMenuBar():
            try:
                self._menuBar
            except Exception:
                self._menuBar = globalMenuBar()
            self._menuBar.resetState()
            return self._menuBar
        menuBar = window.menuBar()
        if not isinstance(menuBar, MenuBar):
            menuBar = MenuBar(window)
            window.setMenuBar(menuBar)
        return menuBar

    def setupMenuBar(self, menuBar=None):
        if menuBar is None:
            try:
                menuBar = self._menuBar
            except Exception:
                return
            menuBar.resetState()
        activeWindow = self.activeWindow()
        fileMenu = menuBar.fetchMenu(Entries.File)
        # HACK: scripting window has its own New/Open;
        # figure out how to do this without explicit blacklist.
        if not isinstance(activeWindow, ScriptingWindow):
            fileMenu.fetchAction(Entries.File_New, self.newFile)
            fileMenu.fetchAction(Entries.File_Open, self.openFile)
        recentFilesMenu = fileMenu.fetchMenu(Entries.File_Open_Recent)
        self.updateRecentFiles(recentFilesMenu)
        if not platformSpecific.mergeOpenAndImport():
            fileMenu.fetchAction(Entries.File_Import, self.importFile)
        fileMenu.fetchAction(Entries.File_Save_All, self.saveAll)
        fileMenu.fetchAction(Entries.File_Exit, self.closeAll)

        editMenu = menuBar.fetchMenu(Entries.Edit)
        editMenu.fetchAction(Entries.Edit_Settings, self.settings)

        viewMenu = menuBar.fetchMenu(Entries.View)
        self.updateDrawingAttributes(viewMenu)

        coordinatesSubmenu = viewMenu.fetchMenu(Entries.View_Show_Coordinates)
        self.updateDrawingAttributes(coordinatesSubmenu)

        scriptsMenu = menuBar.fetchMenu(Entries.Scripts)
        self.updateExtensions(scriptsMenu)

        windowMenu = menuBar.fetchMenu(Entries.Window)
        if platformSpecific.windowCommandsInMenu() and activeWindow is not None:
            windowMenu.fetchAction(Entries.Window_Minimize, activeWindow.showMinimized)
            windowMenu.fetchAction(Entries.Window_Minimize_All, self.minimizeAll)
            windowMenu.fetchAction(Entries.Window_Zoom, lambda: self.zoom(activeWindow))
        windowMenu.fetchAction(Entries.Window_Scripting, self.scripting)
        if self.outputWindow is not None:
            windowMenu.fetchAction(Entries.Window_Output, self.output)
        # TODO: add a list of open windows in window menu, check active window
        # maybe add helper function that filters topLevelWidgets into windows
        # bc we need this in a few places

        helpMenu = menuBar.fetchMenu(Entries.Help)
        helpMenu.fetchAction(
            Entries.Help_Documentation,
            lambda: QDesktopServices.openUrl(QUrl("http://trufont.github.io/")),
        )
        helpMenu.fetchAction(
            Entries.Help_Report_An_Issue,
            lambda: QDesktopServices.openUrl(
                QUrl("https://github.com/trufont/trufont/issues/new")
            ),
        )
        helpMenu.addSeparator()
        helpMenu.fetchAction(Entries.Help_About, self.about)

    def updateMenuBar(self):
        window = self.activeWindow()
        if window is not None and hasattr(window, "setupMenu"):
            menuBar = self.fetchMenuBar(window)
            window.setupMenu(menuBar)
            menuBar.setSpawnElementsHint(False)
            self.setupMenuBar(menuBar)
            menuBar.setSpawnElementsHint(True)
        else:
            self.setupMenuBar()

    # ---------
    # Scripting
    # ---------

    def allFonts(self):
        fonts = []
        for widget in self.topLevelWidgets():
            if isinstance(widget, FontWindow):
                font = widget.font_()
                fonts.append(font)
        return fonts

    def currentFont(self):
        # might be None when closing all windows with scripting window open
        if self._currentFontWindow is None:
            return None
        return self._currentFontWindow.font_()

    def currentGlyph(self):
        return self._currentGlyph

    def setCurrentGlyph(self, glyph):
        if glyph == self._currentGlyph:
            return
        self._currentGlyph = glyph
        self.postNotification("currentGlyphChanged")

    def globals(self):
        global_vars = {
            "__builtins__": __builtins__,
            "AllFonts": self.allFonts,
            "CurrentFont": self.currentFont,
            "CurrentGlyph": self.currentGlyph,
            "events": self.dispatcher,
            "registerExtension": self.registerExtension,
            "unregisterExtension": self.unregisterExtension,
            "registerTool": self.registerTool,
            "unregisterTool": self.unregisterTool,
            "qApp": self,
        }
        return global_vars

    # directory getters

    def _getLocalDirectory(self, key, name):
        userPath = settings.value(key, type=str)
        if userPath and os.path.isdir(userPath):
            return userPath

        appDataFolder = QStandardPaths.standardLocations(
            QStandardPaths.AppLocalDataLocation
        )[0]
        subFolder = os.path.normpath(os.path.join(appDataFolder, name))

        if not os.path.exists(subFolder):
            try:
                os.makedirs(subFolder)
            except OSError:
                subFolder = os.path.expanduser("~")

        settings.setValue(key, subFolder)
        return subFolder

    def getExtensionsDirectory(self):
        return self._getLocalDirectory("scripting/extensionsPath", "Extensions")

    def getScriptsDirectory(self):
        return self._getLocalDirectory("scripting/scriptsPath", "Scripts")

    # -------------
    # Drawing tools
    # -------------

    def drawingTools(self):
        return self._drawingTools

    def registerTool(self, tool):
        self._drawingTools.append(tool)
        data = dict(tool=tool)
        self.postNotification("drawingToolRegistered", data)

    def unregisterTool(self, tool):
        self._drawingTools.remove(tool)
        data = dict(tool=tool)
        self.postNotification("drawingToolUnregistered", data)

    # ----------
    # Extensions
    # ----------

    def extensions(self):
        return self._extensions

    def registerExtension(self, extension):
        self._extensions.append(extension)
        self.updateMenuBar()
        data = dict(extension=extension)
        self.postNotification("extensionRegistered", data)

    def unregisterExtension(self, extension):
        self._extensions.remove(extension)
        self.updateMenuBar()
        data = dict(extension=extension)
        self.postNotification("extensionUnregistered", data)

    def updateExtensions(self, menu):
        def getFunc(ext, path):
            # need a stack frame here to return a unique lambda for each run
            return lambda: ext.run(path)

        menu.clear()
        # also clear submenus
        for child in menu.children():
            if isinstance(child, menu.__class__):
                child.setParent(None)
                child.deleteLater()

        for extension in self._extensions:
            addToMenu = extension.addToMenu
            if addToMenu:
                if isinstance(addToMenu, list):
                    parentMenu = menu.addMenu(extension.name or "")
                else:
                    addToMenu = [addToMenu]
                    parentMenu = menu
                for entry in addToMenu:
                    menuName = entry.get("name")
                    menuPath = entry.get("path")
                    shortcut = entry.get("shortcut")
                    parentMenu.addAction(
                        menuName, getFunc(extension, menuPath), shortcut
                    )
        menu.addSeparator()
        menu.addAction(self.tr(Entries.Scripts_Build_Extension), self.extensionBuilder)

    # ----------------
    # Menu Bar entries
    # ----------------

    def newFile(self):
        font = TFont.new()
        window = FontWindow(font)
        window.show()

    def openFile(self, path=None):
        self._openFile(path, importFile=platformSpecific.mergeOpenAndImport())

    def importFile(self):
        self._openFile(openFile=False, importFile=True)

    def _openFile(self, path=None, openFile=True, importFile=False):
        if not path:
            # formats
            fileFormats = []
            supportedFiles = ""
            if openFile:
                packageAsFile = platformSpecific.treatPackageAsFile()
                if packageAsFile:
                    ufoFormat = "*.ufo"
                    tfExtFormat = "*.tfExt"
                else:
                    ufoFormat = "metainfo.plist"
                    tfExtFormat = "info.plist"
                fileFormats.extend(
                    [
                        self.tr("UFO Fonts {}").format("(%s)" % ufoFormat),
                        self.tr("TruFont Extension {}").format("(%s)" % tfExtFormat),
                    ]
                )
                supportedFiles += f"{ufoFormat} {tfExtFormat} "
            if importFile:
                # TODO: systematize this
                fileFormats.extend(
                    [
                        self.tr("OpenType Font file {}").format("(*.otf *.ttf)"),
                        self.tr("Type1 Font file {}").format("(*.pfa *.pfb)"),
                        self.tr("ttx Font file {}").format("(*.ttx)"),
                        self.tr("WOFF Font file {}").format("(*.woff *.woff2)"),
                    ]
                )
                supportedFiles += "*.otf *.pfa *.pfb *.ttf *.ttx *.woff"
            all_supported_types_filter = self.tr("All supported files {}").format(
                "({})".format(supportedFiles.rstrip())
            )
            fileFormats.extend(
                [all_supported_types_filter, self.tr("All files {}").format("(*.*)")]
            )
            # dialog
            importKey = importFile and not openFile
            state = (
                settings.openFileDialogState()
                if not importKey
                else settings.importFileDialogState()
            )
            directory = (
                None
                if state
                else QStandardPaths.standardLocations(QStandardPaths.DocumentsLocation)[
                    0
                ]
            )
            title = self.tr("Open File") if openFile else self.tr("Import File")
            dialog = QFileDialog(
                self.activeWindow(), title, directory, ";;".join(fileFormats)
            )
            if state:
                dialog.restoreState(state)
            dialog.setAcceptMode(QFileDialog.AcceptOpen)
            dialog.setFileMode(QFileDialog.ExistingFile)
            dialog.selectNameFilter(all_supported_types_filter)
            ret = dialog.exec_()
            # save current directory
            # TODO: should open w/o file chooser also update current dir?
            state = dialog.saveState()
            if importKey:
                settings.setImportFileDialogState(directory)
            else:
                settings.setOpenFileDialogState(directory)
            # cancelled?
            if not ret:
                return
            path = dialog.selectedFiles()[0]
        # sanitize
        path = os.path.normpath(path)
        if ".plist" in os.path.basename(path):
            path = os.path.dirname(path)
        ext = os.path.splitext(path)[1]
        if ext == ".ufo":
            self._loadUFO(path)
        elif ext == ".tfExt":
            self._loadExt(path)
        else:
            self._loadBinary(path)

    def _loadBinary(self, path):
        for widget in self.topLevelWidgets():
            if isinstance(widget, FontWindow):
                font = widget.font_()
                if font is not None and font.binaryPath == path:
                    widget.raise_()
                    return
        font = TFont()
        try:
            font.extract(path)
            self._loadFont(font)
        except Exception as e:
            errorReports.showCriticalException(e)
            return
        self.setCurrentFile(font.binaryPath)

    def _loadExt(self, path):
        # TODO: put version check in place
        e = TExtension(path)
        e.install()

    def _loadUFO(self, path):
        for widget in self.topLevelWidgets():
            if isinstance(widget, FontWindow):
                font = widget.font_()
                if font is not None and font.path == path:
                    widget.raise_()
                    return
        try:
            font = TFont(path)
            self._loadFont(font)
        except Exception as e:
            msg = self.tr("There was an issue opening the font at {}.").format(path)
            errorReports.showCriticalException(e, msg)
            return
        self.setCurrentFile(font.path)

    def _loadFont(self, font):
        currentFont = self.currentFont()
        # Open new font in current font window if it contains an unmodified
        # empty font (e.g. after startup).
        if (
            currentFont is not None
            and currentFont.path is None
            and currentFont.binaryPath is None
            and currentFont.dirty is False
        ):
            window = self._currentFontWindow
            window.setFont_(font)
        else:
            window = FontWindow(font)
        window.show()

    def openRecentFile(self):
        fontPath = self.sender().toolTip()
        self.openFile(fontPath)

    def clearRecentFiles(self):
        settings.setRecentFiles([])

    def saveAll(self):
        for widget in self.topLevelWidgets():
            if isinstance(widget, FontWindow):
                widget.saveFile()

    def closeAll(self):
        for widget in self.topLevelWidgets():
            if isinstance(widget, FontWindow):
                widget.close()
        # loop again to see if user kept font windows open
        for widget in self.topLevelWidgets():
            if isinstance(widget, FontWindow):
                return
        self.quit()

    # Edit

    def settings(self):
        if hasattr(self, "_settingsWindow") and self._settingsWindow.isVisible():
            self._settingsWindow.raise_()
        else:
            self._settingsWindow = SettingsWindow()
            self._settingsWindow.show()

    # Scripts

    def extensionBuilder(self):
        # TODO: don't store, spawn window each time instead
        # or have tabs?
        if not hasattr(self, "_extensionBuilderWindow"):
            self._extensionBuilderWindow = ExtensionBuilderWindow()
        if self._extensionBuilderWindow.isVisible():
            self._extensionBuilderWindow.raise_()
        else:
            self._extensionBuilderWindow.show()

    # Window

    def minimizeAll(self):
        for widget in self.topLevelWidgets():
            if widget.isVisible():
                # additional guard, shouldnt be needed
                # if isinstance(widget, (QMenu, QMenuBar)):
                #     continue
                widget.showMinimized()

    def zoom(self, window):
        if window.isMaximized():
            window.showNormal()
        else:
            window.showMaximized()

    def scripting(self):
        # TODO: don't store, spawn window each time instead
        # or have tabs?
        if not hasattr(self, "_scriptingWindow"):
            self._scriptingWindow = ScriptingWindow()
        if self._scriptingWindow.isVisible():
            self._scriptingWindow.raise_()
        else:
            self._scriptingWindow.show()

    def output(self):
        self.outputWindow.setVisible(not self.outputWindow.isVisible())

    # Help

    def about(self):
        AboutDialog(self.activeWindow()).exec_()

    # ------------
    # Recent files
    # ------------

    def setCurrentFile(self, path):
        if path is None:
            return
        path = os.path.abspath(path)
        recentFiles = settings.recentFiles()
        if path in recentFiles:
            recentFiles.remove(path)
        recentFiles.insert(0, path)
        while len(recentFiles) > MAX_RECENT_FILES:
            del recentFiles[-1]
        settings.setRecentFiles(recentFiles)

    def updateRecentFiles(self, menu):
        # bootstrap
        actions = menu.actions()
        for i in range(MAX_RECENT_FILES):
            try:
                action = actions[i]
            except IndexError:
                action = QAction(menu)
                menu.addAction(action)
            action.setVisible(False)
            action.triggered.connect(self.openRecentFile)
        try:
            actions[MAX_RECENT_FILES]
        except IndexError:
            menu.addSeparator()
            action = QAction(menu)
            action.setText(self.tr("Clear Menu"))
            action.triggered.connect(self.clearRecentFiles)
            menu.addAction(action)

        # fill
        actions = menu.actions()
        recentFiles = settings.recentFiles()
        count = min(len(recentFiles), MAX_RECENT_FILES)
        for index, recentFile in enumerate(recentFiles[:count]):
            action = actions[index]
            shortName = os.path.basename(recentFile.rstrip(os.sep))

            action.setText(shortName)
            action.setToolTip(recentFile)
            action.setVisible(True)
        for index in range(count, MAX_RECENT_FILES):
            actions[index].setVisible(False)

        menu.setEnabled(len(recentFiles))
        # TODO: put recent files in dock on OSX
        # import sys
        # if sys.platform == "darwin":
        #     menu.setAsDockMenu()

    # ------------------
    # Drawing attributes
    # ------------------

    def setDrawingAttribute(self):
        sender = self.sender()
        drawingAttributes = settings.drawingAttributes()
        checked = sender.isChecked()
        for attr in sender.data():
            drawingAttributes[attr] = checked
        settings.setDrawingAttributes(drawingAttributes)
        self.postNotification("preferencesChanged")

    def updateDrawingAttributes(self, menu):
        drawingAttributes = settings.drawingAttributes()
        elements = [
            (
                Entries.View_Show_Points,
                ("showGlyphOnCurvePoints", "showGlyphOffCurvePoints"),
                True,
            ),
            (
                Entries.View_Show_Coordinates_When_Selected,
                ("showGlyphCoordinatesWhenSelected",),
                False,
            ),
            (
                Entries.View_Show_Point_Coordinates,
                ("showGlyphPointCoordinates",),
                False,
            ),
            (
                Entries.View_Show_Bezier_Handles_Coordinates,
                ("showGlyphBezierHandlesCoordinates",),
                False,
            ),
            (
                Entries.View_Show_Metrics,
                (
                    "showGlyphMetrics",
                    "showFontVerticalMetrics",
                    "showFontPostscriptBlues",
                ),
                True,
            ),
            (Entries.View_Show_Images, ("showGlyphImage",), True,),
            (
                Entries.View_Show_Guidelines,
                ("showGlyphGuidelines", "showFontGuidelines"),
                True,
            ),
        ]
        for entry, attrs, checked in elements:
            action = menu.fetchAction(entry)
            action.setCheckable(True)
            action.setChecked(drawingAttributes.get(attrs[0], checked))
            action.setData(attrs)
            action.triggered.connect(self.setDrawingAttribute)
