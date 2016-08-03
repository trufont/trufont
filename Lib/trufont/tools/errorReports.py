from PyQt5.QtWidgets import QMessageBox
import sys
import traceback

_showMessages = True


def exceptionCallback(etype, value, tb):
    global _showMessages
    text = "TruFont has encountered a problem and must shutdown."
    exc = traceback.format_exception(etype, value, tb)
    exc_text = "".join(exc)
    print(exc_text, file=sys.stderr)

    if _showMessages:
        messageBox = QMessageBox(QMessageBox.Critical, ":(", text)
        messageBox.setStandardButtons(
            QMessageBox.Ok | QMessageBox.Close | QMessageBox.Ignore)
        messageBox.setDetailedText(exc_text)
        messageBox.setInformativeText(str(value))
        result = messageBox.exec_()
        if result == QMessageBox.Close:
            sys.exit(1)
        elif result == QMessageBox.Ignore:
            _showMessages = False


def _showException(e, kind, message):
    traceback.print_exc()
    title = e.__class__.__name__
    messageBox = QMessageBox(
        kind, title, str(e).capitalize())
    if kind == QMessageBox.Critical:
        messageBox.setStandardButtons(
            QMessageBox.Ok | QMessageBox.Close)
    messageBox.setDetailedText(traceback.format_exc())
    messageBox.setInformativeText(message)
    ret = messageBox.exec_()
    if ret == QMessageBox.Close:
        sys.exit(1)

def showCriticalException(e, message=None):
    _showException(e, QMessageBox.Critical, message)


def showWarningException(e, message=None):
    _showException(e, QMessageBox.Warning, message)
