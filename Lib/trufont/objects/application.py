from defcon.tools.notifications import NotificationCenter
from PyQt5.QtCore import QEvent, QStandardPaths, Qt
from PyQt5.QtWidgets import QApplication
from trufont.drawingTools.selectionTool import SelectionTool
from trufont.drawingTools.penTool import PenTool
from trufont.drawingTools.rulerTool import RulerTool
from trufont.drawingTools.knifeTool import KnifeTool
from trufont.windows.fontWindow import FontWindow
from trufont.objects import settings
from trufont.objects.defcon import TFont
from trufont.tools import errorReports, glyphList
import os


class Application(QApplication):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._currentGlyph = None
        self._currentMainWindow = None
        self._launched = False
        self._drawingTools = [SelectionTool, PenTool, RulerTool, KnifeTool]
        self._extensions = []
        self.dispatcher = NotificationCenter()
        self.dispatcher.addObserver(self, "_mainWindowClosed", "fontWillClose")
        self.focusChanged.connect(self.updateCurrentMainWindow)
        self.GL2UV = None
        self.inspectorWindow = None
        self.outputWindow = None

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
                self.updateCurrentMainWindow()
            elif applicationState == Qt.ApplicationInactive:
                self.postNotification("applicationWillIdle")
        return super().event(event)

    def postNotification(self, notification, data=None):
        dispatcher = self.dispatcher
        dispatcher.postNotification(
            notification=notification, observable=self, data=data)

    def loadGlyphList(self):
        glyphListPath = settings.glyphListPath()
        if glyphListPath and os.path.exists(glyphListPath):
            try:
                glyphList_ = glyphList.parseGlyphList(glyphListPath)
            except Exception as e:
                msg = self.tr(
                    "The glyph list at {0} cannot "
                    "be parsed and will be dropped.").format(glyphListPath)
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

    def _mainWindowClosed(self, notification):
        font = notification.data["font"]
        # cleanup CurrentFont/CurrentGlyph when closing the corresponding
        # window
        if self._currentMainWindow is not None:
            if self._currentMainWindow.font == font:
                self.setCurrentMainWindow(None)
        if self._currentGlyph is not None:
            if self._currentGlyph.font == font:
                self.setCurrentGlyph(None)

    def _getLocalDirectory(self, key, name):
        userPath = settings.value(key, type=str)
        if userPath and os.path.isdir(userPath):
            return userPath

        appDataFolder = QStandardPaths.standardLocations(
            QStandardPaths.AppLocalDataLocation)[0]
        subFolder = os.path.normpath(os.path.join(
            appDataFolder, name))

        if not os.path.exists(subFolder):
            try:
                os.makedirs(subFolder)
            except OSError:
                subFolder = os.path.expanduser("~")

        settings.setValue(key, subFolder)
        return subFolder

    def getExtensionsDirectory(self):
        return self._getLocalDirectory(
            "scripting/extensionsPath", "Extensions")

    def getScriptsDirectory(self):
        return self._getLocalDirectory("scripting/scriptsPath", "Scripts")

    def newFile(self):
        font = TFont.newStandardFont()
        window = FontWindow(font)
        window.show()

    def openFile(self, path):
        if ".plist" in path:
            path = os.path.dirname(path)
        path = os.path.normpath(path)
        for window in self.topLevelWidgets():
            if isinstance(window, FontWindow):
                font = window.font_()
                if font is not None and font.path == path:
                    window.raise_()
                    return
        try:
            font = TFont(path)
            window = FontWindow(font)
        except Exception as e:
            errorReports.showCriticalException(e)
            return
        window.show()

    def allFonts(self):
        fonts = []
        for window in QApplication.topLevelWidgets():
            if isinstance(window, FontWindow):
                font = window.font_()
                fonts.append(font)
        return fonts

    def currentFont(self):
        # might be None when closing all windows with scripting window open
        if self._currentMainWindow is None:
            return None
        return self._currentMainWindow.font_()

    def currentGlyph(self):
        return self._currentGlyph

    def setCurrentGlyph(self, glyph):
        if glyph == self._currentGlyph:
            return
        self._currentGlyph = glyph
        self.postNotification("currentGlyphChanged")

    def currentMainWindow(self):
        return self._currentMainWindow

    def setCurrentMainWindow(self, mainWindow):
        if mainWindow == self._currentMainWindow:
            return
        self._currentMainWindow = mainWindow
        self.postNotification("currentFontChanged")

    def updateCurrentMainWindow(self):
        window = self.activeWindow()
        if window is None:
            return
        while True:
            parent = window.parent()
            if parent is None:
                break
            window = parent
        if isinstance(window, FontWindow):
            self.setCurrentMainWindow(window)

    def openMetricsWindow(self, font):
        for window in QApplication.topLevelWidgets():
            if isinstance(window, FontWindow) and window.font_() == font:
                window.metrics()
                return window._metricsWindow
        return None

    def globals(self):
        global_vars = {
            "__builtins__": __builtins__,
            "AllFonts": self.allFonts,
            "CurrentFont": self.currentFont,
            "CurrentGlyph": self.currentGlyph,
            "events": self.dispatcher,
            "registerTool": self.registerTool,
            "OpenMetricsWindow": self.openMetricsWindow,
            "qApp": self,
        }
        return global_vars

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
        data = dict(extension=extension)
        self.postNotification("extensionRegistered", data)

    def unregisterExtension(self, extension):
        self._extensions.remove(extension)
        data = dict(extension=extension)
        self.postNotification("extensionUnregistered", data)
