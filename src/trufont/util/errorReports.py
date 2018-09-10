import sys
import traceback
import wx


def showExceptionError(parent, exc, message=None):
    _displayException(
        parent, exc.__class__, exc, exc.__traceback__, wx.ICON_ERROR, message)


def _displayException(parent, etype, value, tb, icon, message):
    info = traceback.format_exception(etype, value, tb)
    info_text = "".join(info)
    print(info_text, file=sys.stderr)

    if message is None:
        message = str(etype)
    with wx.MessageDialog(parent, message, style=icon) as dialog:
        dialog.SetExtendedMessage(info_text)
        dialog.ShowModal()

    """
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
    """
