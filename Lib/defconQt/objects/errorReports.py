from PyQt5.QtWidgets import QMessageBox
import traceback

def _showException(e, kind, message):
    traceback.print_exc()
    title = e.__class__.__name__
    messageBox = QMessageBox(
        kind, title, str(e).capitalize())
    messageBox.setDetailedText(traceback.format_exc())
    messageBox.setInformativeText(message)
    messageBox.exec_()

def showCriticalException(e, message=None):
    _showException(e, QMessageBox.Critical, message)

def showWarningException(e, message=None):
    _showException(e, QMessageBox.Warning, message)
