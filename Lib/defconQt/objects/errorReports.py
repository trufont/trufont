from PyQt5.QtWidgets import QMessageBox
import traceback

def showCriticalException(e):
    title = e.__class__.__name__
    messageBox = QMessageBox(
        QMessageBox.Critical, title, str(e).capitalize())
    messageBox.setDetailedText(traceback.format_exc())
    messageBox.exec_()
