from defconQt.tools import platformSpecific as basePlatformSpecific
from PyQt5.QtCore import pyqtSignal, QObject, QSize, Qt
from PyQt5.QtGui import QPalette, QTextCursor, QTextOption
from PyQt5.QtWidgets import QCheckBox, QMainWindow, QPushButton, QPlainTextEdit
from trufont.tools import platformSpecific
import sys


class OutputWindow(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Tool)
        self.outputEdit = QPlainTextEdit(self)
        self.outputEdit.setFont(basePlatformSpecific.fixedFont())
        self.outputEdit.setUndoRedoEnabled(False)
        palette = self.outputEdit.palette()
        palette.setColor(QPalette.Base, Qt.black)
        self.outputEdit.setPalette(palette)
        self.outputEdit.viewport().setCursor(Qt.ArrowCursor)
        self.outputEdit.setReadOnly(True)
        wrapLinesBox = QCheckBox(self.tr("Wrap Lines"), self)
        wrapLinesBox.toggled.connect(self.setWordWrapEnabled)
        clearOutputButton = QPushButton(self.tr("Clear"), self)
        clearOutputButton.clicked.connect(self.outputEdit.clear)

        self.setCentralWidget(self.outputEdit)
        self.setWindowTitle(self.tr("Output Window"))
        statusBar = self.statusBar()
        statusBar.addWidget(wrapLinesBox)
        statusBar.addPermanentWidget(clearOutputButton)
        statusBar.setSizeGripEnabled(False)
        if platformSpecific.needsTighterMargins():
            statusBar.setContentsMargins(7, -10, 9, -12)

        for channel in ("stdout", "stderr"):
            stream = OutputStream(channel, self)
            stream.messagePassed.connect(self.write)

    def isScrollBarAtBottom(self):
        scrollBar = self.outputEdit.verticalScrollBar()
        return scrollBar.value() == scrollBar.maximum()

    def scrollToBottom(self):
        scrollBar = self.outputEdit.verticalScrollBar()
        scrollBar.setValue(scrollBar.maximum())
        # QPlainTextEdit destroys the first calls value in case of multiline
        # text, so make sure that the scroll bar actually gets the value set.
        # Is a noop if the first call succeeded.
        scrollBar.setValue(scrollBar.maximum())

    def setWordWrapEnabled(self, value):
        if value:
            wrapMode = QTextOption.WrapAtWordBoundaryOrAnywhere
        else:
            wrapMode = QTextOption.NoWrap
        self.outputEdit.setWordWrapMode(wrapMode)

    def write(self, message, stream=None):
        atBottom = self.isScrollBarAtBottom()
        textCursor = self.outputEdit.textCursor()
        if not textCursor.atEnd():
            textCursor.movePosition(QTextCursor.End)
        charFormat = self.outputEdit.currentCharFormat()
        charFormat.setForeground(Qt.red if stream == "stderr" else Qt.white)
        self.outputEdit.setCurrentCharFormat(charFormat)
        self.outputEdit.insertPlainText(message)
        if atBottom:
            self.scrollToBottom()

    # ----------
    # Qt methods
    # ----------

    def moveEvent(self, event):
        self.writeSettings()

    resizeEvent = moveEvent

    def sizeHint(self):
        return QSize(465, 400)


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
