from defconQt.tools import platformSpecific as basePlatformSpecific
from PyQt5.QtCore import pyqtSignal, QObject, QSize, Qt
from PyQt5.QtGui import QPalette, QTextCursor, QTextOption
from PyQt5.QtWidgets import QCheckBox, QMainWindow, QPushButton, QPlainTextEdit
from trufont.objects import settings
from trufont.tools import platformSpecific
import sys


class OutputWindow(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Tool)
        self.outputEdit = OutputEdit(self)
        palette = self.outputEdit.palette()
        palette.setColor(QPalette.Base, Qt.black)
        palette.setColor(QPalette.Text, Qt.white)
        self.outputEdit.setPalette(palette)
        self.outputEdit.viewport().setCursor(Qt.ArrowCursor)
        self.wrapLinesBox = QCheckBox(self.tr("Wrap Lines"), self)
        self.wrapLinesBox.toggled.connect(self.setWordWrapEnabled)
        clearOutputButton = QPushButton(self.tr("Clear"), self)
        clearOutputButton.clicked.connect(self.outputEdit.clear)

        self.setCentralWidget(self.outputEdit)
        self.setWindowTitle(self.tr("Output"))
        statusBar = self.statusBar()
        statusBar.addWidget(self.wrapLinesBox)
        statusBar.addPermanentWidget(clearOutputButton)
        statusBar.setSizeGripEnabled(False)
        if platformSpecific.needsTighterMargins():
            margins = (7, -10, 9, -12)
        else:
            margins = (4, -1, 5, 0)
        statusBar.setContentsMargins(*margins)

        for channel in ("stdout", "stderr"):
            stream = OutputStream(channel, self)
            stream.messagePassed.connect(self.outputEdit.write)

        self.readSettings()

    def readSettings(self):
        geometry = settings.outputWindowGeometry()
        if geometry:
            self.restoreGeometry(geometry)
        checked = settings.outputWindowWrapLines()
        self.wrapLinesBox.setChecked(checked)

    def writeSettings(self):
        settings.setOutputWindowGeometry(self.saveGeometry())
        settings.setOutputWindowWrapLines(self.wrapLinesBox.isChecked())

    def setWordWrapEnabled(self, value):
        if value:
            wrapMode = QTextOption.WrapAtWordBoundaryOrAnywhere
        else:
            wrapMode = QTextOption.NoWrap
        self.outputEdit.setWordWrapMode(wrapMode)
        self.writeSettings()

    # ----------
    # Qt methods
    # ----------

    def moveEvent(self, event):
        self.writeSettings()

    resizeEvent = moveEvent

    def sizeHint(self):
        return QSize(465, 400)


class OutputEdit(QPlainTextEdit):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(basePlatformSpecific.fixedFont())
        self.setReadOnly(True)
        self.setUndoRedoEnabled(False)

    def isScrollBarAtBottom(self):
        scrollBar = self.verticalScrollBar()
        return scrollBar.value() == scrollBar.maximum()

    def scrollToBottom(self):
        scrollBar = self.verticalScrollBar()
        scrollBar.setValue(scrollBar.maximum())
        # QPlainTextEdit destroys the first calls value in case of multiline
        # text, so make sure that the scroll bar actually gets the value set.
        # Is a noop if the first call succeeded.
        scrollBar.setValue(scrollBar.maximum())

    def write(self, message, stream=None):
        atBottom = self.isScrollBarAtBottom()
        textCursor = self.textCursor()
        if not textCursor.atEnd():
            self.moveCursor(QTextCursor.End)
        charFormat = self.currentCharFormat()
        if stream == "stderr":
            color = Qt.red
        else:
            color = self.palette().color(QPalette.Text)
        charFormat.setForeground(color)
        self.setCurrentCharFormat(charFormat)
        self.insertPlainText(message)
        if atBottom:
            self.scrollToBottom()


class OutputStream(QObject):
    messagePassed = pyqtSignal(str, str)

    def __init__(self, stream=None, parent=None):
        super().__init__(parent)
        self.forward = False
        self.stream = None
        self.oldStream = None
        self.registerStream(stream)

    def registerStream(self, stream):
        self.stream = stream
        if self.stream is None:
            return
        assert self.stream in ("stdout", "stderr")
        self.oldStream = getattr(sys, self.stream)
        setattr(sys, self.stream, self)

    def unregisterStream(self):
        if self.oldStream is None:
            return
        setattr(sys, self.stream, self.oldStream)
        self.stream = None
        self.oldStream = None

    def flush(self):
        pass

    def write(self, message):
        self.messagePassed.emit(message, self.stream)
        if self.forward:
            self.oldStream.write(message)
