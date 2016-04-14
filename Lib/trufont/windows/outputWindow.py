from defconQt.tools import platformSpecific
from PyQt5.QtCore import pyqtSignal, QObject, Qt
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QMainWindow, QPushButton, QTextEdit
import sys


class OutputWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Tool)
        self.outputEdit = QTextEdit(self)
        self.outputEdit.setFont(platformSpecific.fixedFont())
        self.outputEdit.setAcceptRichText(False)
        palette = self.outputEdit.palette()
        palette.setColor(QPalette.Base, Qt.black)
        self.outputEdit.setPalette(palette)
        self.outputEdit.viewport().setCursor(Qt.ArrowCursor)
        self.outputEdit.setReadOnly(True)
        clearOutputButton = QPushButton("Clear", self)
        clearOutputButton.clicked.connect(self.outputEdit.clear)

        self.setCentralWidget(self.outputEdit)
        self.setWindowTitle(self.tr("Output Window"))
        statusBar = self.statusBar()
        statusBar.addPermanentWidget(clearOutputButton)
        statusBar.setSizeGripEnabled(False)

        for channel in ("stdout", "stderr"):
            stream = OutputStream(channel, self)
            stream.messagePassed.connect(self.write)

    def write(self, message, stream=None):
        self.outputEdit.setTextColor(
            Qt.red if stream == "stderr" else Qt.white)
        self.outputEdit.insertPlainText(message)


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
