from defconQt.controls.baseCodeEditor import (
    BaseCodeEditor, BaseCodeHighlighter, GotoLineDialog)
from keyword import kwlist
from PyQt5.QtCore import (
    pyqtSignal, QDir, QSettings, QSize, QStandardPaths, Qt, QUrl)
from PyQt5.QtGui import (
    QColor, QDesktopServices, QKeySequence, QTextCharFormat, QTextCursor)
from PyQt5.QtWidgets import (
    QApplication, QComboBox, QFileDialog, QFileSystemModel, QMainWindow, QMenu,
    QMessageBox, QPushButton, QSplitter, QStatusBar, QTreeView, QWidget,
    QVBoxLayout)
from trufont.controls.clickLabel import ClickLabel
from trufont.objects import settings
from trufont.tools import platformSpecific
from trufont.windows.outputWindow import OutputEdit, OutputStream
import os
import tokenize
import traceback


class ScriptingWindow(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)

        fileMenu = QMenu(self.tr("&File"), self)
        fileMenu.addAction(self.tr("&New…"), self.newFile, QKeySequence.New)
        fileMenu.addAction(
            self.tr("&Open…"), self.openFile, QKeySequence.Open)
        fileMenu.addAction(self.tr("&Save"), self.saveFile, QKeySequence.Save)
        fileMenu.addAction(
            self.tr("Save &As…"), self.saveFileAs, QKeySequence.SaveAs)
        fileMenu.addSeparator()
        fileMenu.addAction(self.tr("&Run…"), self.runScript, "Ctrl+R")
        fileMenu.addSeparator()
        fileMenu.addAction(
            self.tr("&Close"), self.close, platformSpecific.closeKeySequence())
        self.menuBar().addMenu(fileMenu)

        self.editor = PythonEditor(self)
        self.fileChooser = FileChooser(self)
        self.fileChooser.fileOpened.connect(self.openFile)
        self.outputEdit = OutputEdit(self)

        splitter = QSplitter(self)
        self.vSplitter = QSplitter(Qt.Vertical, splitter)
        self.vSplitter.addWidget(self.editor)
        self.vSplitter.addWidget(self.outputEdit)
        self.vSplitter.setStretchFactor(0, 1)
        self.vSplitter.setStretchFactor(1, 0)
        splitter.addWidget(self.fileChooser)
        splitter.addWidget(self.vSplitter)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        statusBar = ScriptingStatusBar(self)
        self.setCentralWidget(splitter)
        self.setStatusBar(statusBar)
        self.newFile()
        self.editor.modificationChanged.connect(self.setWindowModified)
        statusBar.setPosition(self.editor.textCursor())
        self.editor.cursorPositionChanged.connect(
            lambda: statusBar.setPosition(self.sender().textCursor()))
        statusBar.setIndent(self.editor.indent())
        self.editor.indentChanged.connect(statusBar.setIndent)
        splitter.splitterMoved.connect(self.writeSettings)
        self.vSplitter.splitterMoved.connect(self.writeSettings)
        statusBar.indentModified.connect(self.editor.setIndent)
        statusBar.positionClicked.connect(self.gotoLine)
        statusBar.clearButtonClicked.connect(self.outputEdit.clear)
        statusBar.runButtonClicked.connect(self.runScript)

        self.readSettings()

    def readSettings(self):
        geometry = settings.scriptingWindowGeometry()
        if geometry:
            self.restoreGeometry(geometry)
        sizes = settings.scriptingWindowHSplitterSizes()
        if sizes:
            splitter = self.centralWidget()
            splitter.setSizes(sizes)
        sizes = settings.scriptingWindowVSplitterSizes()
        if sizes:
            self.vSplitter.setSizes(sizes)

    def writeSettings(self):
        settings.setScriptingWindowGeometry(self.saveGeometry())
        splitter = self.centralWidget()
        settings.setScriptingWindowHSplitterSizes(splitter.sizes())
        settings.setScriptingWindowVSplitterSizes(self.vSplitter.sizes())

    @property
    def currentPath(self):
        return self._currentPath

    @currentPath.setter
    def currentPath(self, currentPath):
        self._currentPath = currentPath
        if self._currentPath is None:
            self.setWindowTitle(self.tr("Untitled.py"))
        else:
            self.setWindowTitle(os.path.basename(self._currentPath))

    def newFile(self):
        if not self._maybeSaveBeforeExit():
            return
        self.editor.setPlainText(None)
        self.currentPath = None

    def openFile(self, path=None):
        if not self._maybeSaveBeforeExit():
            return
        if path is None:
            path = self._ioDialog(QFileDialog.AcceptOpen)
            if path is None:
                return
            self.fileChooser.setCurrentFolder(os.path.dirname(path))
        with tokenize.open(path) as inputFile:
            self.editor.setPlainText(inputFile.read())
        self.currentPath = path

    def saveFile(self):
        if self.currentPath is None:
            self.saveFileAs()
        else:
            self.editor.write(self.currentPath)

    def saveFileAs(self):
        path = self._ioDialog(QFileDialog.AcceptSave)
        if path is not None:
            self.currentPath = path
            self.saveFile()

    # TODO: why not use simple dialogs?
    def _ioDialog(self, mode):
        if mode == QFileDialog.AcceptOpen:
            title = self.tr("Open File")
        else:
            title = self.tr("Save File")
        dialog = QFileDialog(self, title, None, self.tr("Python file (*.py)"))
        dialog.setAcceptMode(mode)
        dialog.setDirectory(self.fileChooser.currentFolder())
        dialog.setFileMode(QFileDialog.ExistingFile)
        ok = dialog.exec_()
        if ok:
            return dialog.selectedFiles()[0]
        return None

    def gotoLine(self):
        newLine, newColumn, ret = GotoLineDialog.getLineColumnNumber(self)
        if ret and newLine:
            self.editor.scrollToLine(newLine, newColumn)

    def runScript(self):
        app = QApplication.instance()
        script = self.editor.toPlainText()
        global_vars = {
            "__builtins__": __builtins__,
            "AllFonts": app.allFonts,
            "CurrentFont": app.currentFont,
            "CurrentGlyph": app.currentGlyph,
            "events": app.dispatcher,
            "installTool": app.installTool,
            "OpenMetricsWindow": app.openMetricsWindow,
            "qApp": app,
        }
        streams = []
        for channel in ("stdout", "stderr"):
            stream = OutputStream(channel, self)
            stream.forward = True
            stream.messagePassed.connect(self.outputEdit.write)
            streams.append(stream)
        try:
            code = compile(script, "<string>", "exec")
            exec(code, global_vars)
        except:
            traceback.print_exc()
        for stream in streams:
            stream.unregisterStream()

    # ----------
    # Qt methods
    # ----------

    def setWindowTitle(self, title):
        super().setWindowTitle("[*]{}".format(title))

    def sizeHint(self):
        return QSize(650, 700)

    def moveEvent(self, event):
        self.writeSettings()

    resizeEvent = moveEvent

    def closeEvent(self, event):
        ok = self._maybeSaveBeforeExit()
        if ok:
            event.accept()
        else:
            event.ignore()

    # TODO: somehow duplicates fontView
    def _maybeSaveBeforeExit(self):
        if self.isWindowModified():
            currentFile = self.windowTitle()[3:]
            body = self.tr("Do you want to save the changes you made "
                           "to “{}”?").format(currentFile)
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


class FileTreeView(QTreeView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.doubleClickCallback = None

    def _showInExplorer(self, path):
        if os.path.isfile(path):
            path = os.path.dirname(path)
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.RightButton:
            model = self.model()
            modelIndex = self.indexAt(event.pos())
            if modelIndex.isValid():
                path = model.filePath(modelIndex)
            else:
                path = model.rootPath()
            menu = QMenu(self)
            menu.addAction(
                self.tr("Open In Explorer"),
                lambda: self._showInExplorer(path))
            menu.exec_(event.globalPos())

    def mouseDoubleClickEvent(self, event):
        if self.doubleClickCallback is not None:
            modelIndex = self.indexAt(event.pos())
            if modelIndex.isValid():
                self.doubleClickCallback(modelIndex)
        super().mouseDoubleClickEvent(event)


class FileChooser(QWidget):
    fileOpened = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.folderBox = QComboBox(self)
        self.explorerTree = FileTreeView(self)
        self.explorerTree.doubleClickCallback = self._fileOpened
        self.explorerModel = QFileSystemModel(self)
        self.explorerModel.setFilter(
            QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot)
        self.explorerModel.setNameFilters(["*.py"])
        self.explorerModel.setNameFilterDisables(False)
        self.explorerTree.setModel(self.explorerModel)
        for index in range(1, self.explorerModel.columnCount()):
            self.explorerTree.hideColumn(index)
        self.setCurrentFolder()
        self.folderBox.currentIndexChanged[int].connect(
            self.updateCurrentFolder)

        layout = QVBoxLayout(self)
        layout.addWidget(self.folderBox)
        layout.addWidget(self.explorerTree)
        layout.setContentsMargins(5, 5, 0, 5)

    def _fileOpened(self, modelIndex):
        path = self.explorerModel.filePath(modelIndex)
        if os.path.isfile(path):
            self.fileOpened.emit(path)

    def getScriptsDirectory(self):
        userPath = QSettings().value("scripting/path")
        if userPath and os.path.exists(userPath):
            return userPath

        appDataFolder = QStandardPaths.standardLocations(
            QStandardPaths.AppLocalDataLocation)[0]
        scriptsFolder = os.path.normpath(os.path.join(
            appDataFolder, "Scripts"))

        if not os.path.exists(scriptsFolder):
            try:
                os.makedirs(scriptsFolder)
            except OSError:
                return os.path.expanduser("~")

        return scriptsFolder

    def currentFolder(self):
        return self.explorerModel.rootPath()

    def setCurrentFolder(self, path=None):
        if path is None:
            path = self.getScriptsDirectory()
        else:
            assert os.path.isdir(path)
        self.explorerModel.setRootPath(path)
        self.explorerTree.setRootIndex(self.explorerModel.index(path))
        self.folderBox.blockSignals(True)
        self.folderBox.clear()
        style = self.style()
        dirIcon = style.standardIcon(style.SP_DirIcon)
        self.folderBox.addItem(dirIcon, os.path.basename(path))
        self.folderBox.insertSeparator(1)
        self.folderBox.addItem(self.tr("Browse…"))
        self.folderBox.setCurrentIndex(0)
        self.folderBox.blockSignals(False)

    def updateCurrentFolder(self, index):
        if index < self.folderBox.count() - 1:
            return
        path = QFileDialog.getExistingDirectory(
            self, self.tr("Choose Directory"), self.currentFolder(),
            QFileDialog.ShowDirsOnly)
        if path:
            QSettings().setValue("scripting/path", path)
            self.setCurrentFolder(path)


class PythonEditor(BaseCodeEditor):
    openBlockDelimiter = ":"
    autocomplete = {
        Qt.Key_ParenLeft: ")",
        Qt.Key_BracketLeft: "]",
        Qt.Key_BraceLeft: "}",
        Qt.Key_Apostrophe: "",
        Qt.Key_QuoteDbl: "",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighter = PythonHighlighter(self.document())

    def write(self, path):
        with open(path, "wt", encoding="utf-8") as outputFile:
            outputFile.write(self.toPlainText())
        self.document().setModified(False)

    def keyPressEvent(self, event):
        key = event.key()
        if key in self.autocomplete.keys():
            super().keyPressEvent(event)
            cursor = self.textCursor()
            cursor.insertText(self.autocomplete[key] or chr(key))
            cursor.movePosition(QTextCursor.PreviousCharacter)
            self.setTextCursor(cursor)
            return
        elif key == Qt.Key_Return:
            cursor = self.textCursor()
            ok = cursor.movePosition(QTextCursor.NextCharacter)
            if ok:
                cursor.movePosition(
                    QTextCursor.PreviousCharacter, QTextCursor.KeepAnchor, 2)
                combo = ["{}{}".format(chr(
                    k), v) for k, v in self.autocomplete.items() if v]
                if not cursor.selectedText() in combo:
                    ok = False
            if ok:
                for _ in range(2):
                    super().keyPressEvent(event)
                cursor = self.textCursor()
                cursor.movePosition(QTextCursor.Up)
                cursor.insertText(self._indent)
                cursor.movePosition(QTextCursor.EndOfLine)
                self.setTextCursor(cursor)
                return
        elif key == Qt.Key_Backspace:
            cursor = self.textCursor()
            ok = cursor.movePosition(QTextCursor.PreviousCharacter)
            if ok:
                ok = cursor.movePosition(
                    QTextCursor.NextCharacter, QTextCursor.KeepAnchor, 2)
                tags = ["{}{}".format(chr(k), v if v else chr(
                    k)) for k, v in self.autocomplete.items()]
                if ok and cursor.selectedText() in tags:
                    cursor.removeSelectedText()
                    event.accept()
                    return
        super().keyPressEvent(event)

    def dragEnterEvent(self, event):
        if event.source() != self:
            mimeData = event.mimeData()
            if mimeData.hasUrls():
                urls = mimeData.urls()
                for url in urls:
                    if url.isLocalFile():
                        event.acceptProposedAction()
                        break
                return
        super().dragEnterEvent(event)

    def dropEvent(self, event):
        if event.source() != self:
            mimeData = event.mimeData()
            if mimeData.hasUrls():
                urls = mimeData.urls()
                paths = [
                    url.toLocalFile() for url in urls if url.isLocalFile()]
                text = ", ".join(paths)
                if len(paths) > 1:
                    text = "[%s]" % text
                textCursor = self.cursorForPosition(event.pos())
                textCursor.insertText(text)
                self.setTextCursor(textCursor)
                # HACK: Qt uses cleanup routines in a private namespace
                # called by the superclass. Ugh. We have no choice but to make
                # up an empty event if we want to exit drag state.
                mimeData = mimeData.__class__()
                event = event.__class__(
                    event.posF(), event.possibleActions(), mimeData,
                    event.mouseButtons(), event.keyboardModifiers())
        super().dropEvent(event)

    def setPlainText(self, text):
        super().setPlainText(text)
        self.document().setModified(False)


class PythonHighlighter(BaseCodeHighlighter):

    def __init__(self, parent=None):
        super().__init__(parent)

        quotationFormat = QTextCharFormat()
        quotationFormat.setForeground(QColor(255, 27, 147))
        self.addBlockRule('u?r?"""', '"""', quotationFormat)
        self.addBlockRule("u?r?'''", "'''", quotationFormat)

        singleLineCommentFormat = QTextCharFormat()
        singleLineCommentFormat.setForeground(QColor(112, 128, 144))
        self.addRule("#[^\n]*", singleLineCommentFormat)

        quotationTemplate = "{0}[^{0}\\\\]*(\\\\.[^{0}\\\\]*)*{0}"
        self.addRule(
            "|".join(quotationTemplate.format(char) for char in ("'", "\"")),
            quotationFormat)

        classOrFnNameFormat = QTextCharFormat()
        classOrFnNameFormat.setForeground(QColor(96, 106, 161))
        self.addRule(
            "(?<=\\bclass\\s|def\\s\\b)\\s*(\\w+)", classOrFnNameFormat)

        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(QColor(45, 95, 235))
        self.addRule("\\b(%s)\\b" % ("|".join(kwlist)), keywordFormat)


class ScriptingStatusBar(QStatusBar):

    def __init__(self, parent=None):
        super().__init__(parent)
        if platformSpecific.needsTighterMargins():
            self.setContentsMargins(6, -10, 9, -12)
        self.setSizeGripEnabled(False)
        self.positionLabel = ClickLabel(self)
        self.indentLabel = IndentLabel(self)
        self.clearButton = QPushButton(self.tr("Clear"), self)
        self.runButton = QPushButton(self.tr("Run"), self)

        self.addWidget(self.positionLabel)
        self.addPermanentWidget(self.indentLabel)
        self.addPermanentWidget(self.clearButton)
        self.addPermanentWidget(self.runButton)

        self.indentModified = self.indentLabel.indentModified
        self.positionClicked = self.positionLabel.clicked
        self.clearButtonClicked = self.clearButton.clicked
        self.runButtonClicked = self.runButton.clicked

    def setIndent(self, indent):
        # TODO: this could be in a label widget subclass for better
        # encapsulation
        space = tab = 0
        for char in indent:
            if char == " ":
                space += 1
            elif char == "\t":
                tab += 1
        if space and not tab:
            if space < 2:
                text = self.tr("Space")
            else:
                text = self.tr("{}-Spaces").format(space)
        elif tab and not space:
            if tab < 2:
                text = self.tr("Tab")
            else:
                text = self.tr("Tabs")
        else:
            text = self.tr("Other")
        self.indentLabel.setText(text)

    def setPosition(self, textCursor):
        blockNumber, blockPosition = textCursor.blockNumber(
            ), textCursor.positionInBlock()
        # TODO: display selection information?
        self.positionLabel.setText("%d:%d" % (blockNumber+1, blockPosition+1))


class IndentLabel(ClickLabel):
    indentModified = pyqtSignal(str)

    def contextMenu(self):
        menu = QMenu(self)
        menu.addAction(
            self.tr("2-Spaces"), lambda: self.indentModified.emit("  "))
        menu.addAction(
            self.tr("4-Spaces"), lambda: self.indentModified.emit("    "))
        menu.addAction(
            self.tr("Tab"), lambda: self.indentModified.emit("\t"))
        return menu
