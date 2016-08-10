from PyQt5.QtWidgets import QMessageBox
import sys
import traceback

_showMessages = True


def showCriticalException(e, message=None):
    _prepareException(e, QMessageBox.Critical, message)


def showWarningException(e, message=None):
    _prepareException(e, QMessageBox.Warning, message)


def exceptionCallback(etype, value, tb):
    title = ":("
    message = "TruFont has encountered a problem and must shutdown."
    _displayException(etype, value, tb, QMessageBox.Critical, title, message)


def _displayException(etype, value, tb, kind, title, message):
    global _showMessages
    exc = traceback.format_exception(etype, value, tb)
    exc_text = "".join(exc)
    print(exc_text, file=sys.stderr)

    if _showMessages:
        messageBox = QMessageBox(kind, title, message)
        standardButtons = QMessageBox.Ok | QMessageBox.Close
        if kind == QMessageBox.Critical:
            standardButtons |= QMessageBox.Ignore
        messageBox.setStandardButtons(standardButtons)
        messageBox.setDetailedText(exc_text)
        messageBox.setInformativeText(str(value))
        result = messageBox.exec_()
        if result == QMessageBox.Close:
            sys.exit(1)
        elif result == QMessageBox.Ignore:
            _showMessages = False


def _prepareException(e, kind, message):
    title = e.__class__.__name__
    _displayException(e.__class__, e, e.__traceback__, kind, title, message)
