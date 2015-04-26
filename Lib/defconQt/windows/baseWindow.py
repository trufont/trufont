from PyQt5.QtCore import QDir
from PyQt5.QtWidgets import (QFileDialog, QMessageBox)

'''
Base Window is a rather abstract object containing the common methods of
all widgets.
As such, it does not have an init function and is meant to be inherited
by subsequent classes.
'''
class BaseWindowController(object):

    '''
    def setUpBaseWindowBehavior(self):
        self.w.bind("close", self.windowCloseCallback)
        if isinstance(self.w, vanilla.Sheet):
            self.w.bind("became key", self.windowSelectCallback)
            self.w.bind("resigned key", self.windowDeselectCallback)
        else:
            self.w.bind("became main", self.windowSelectCallback)
            self.w.bind("resigned main", self.windowDeselectCallback)

    def windowCloseCallback(self, sender):
        self.w.unbind("close", self.windowCloseCallback)
        if isinstance(self.w, vanilla.Sheet):
            self.w.unbind("became key", self.windowSelectCallback)
            self.w.unbind("resigned key", self.windowDeselectCallback)
        else:
            self.w.unbind("became main", self.windowSelectCallback)
            self.w.unbind("resigned main", self.windowDeselectCallback)

    def windowSelectCallback(self, sender):
        pass

    def windowDeselectCallback(self, sender):
        pass
    '''

    def startProgress(self, text="", tickCount=None):
        try:
            from defconQt.windows.progressWindow import ProgressWindow
        except:
            from progressWindow import ProgressWindow
        return ProgressWindow(text, tickCount, self.w)

    def showMessage(self, messageText, informativeText, callback=None):
        QMessageBox.information(self.w.activeWindow(), messageText, informativeText)
        #if callback is None:
        #    return 1
        #vanilla.dialogs.message(parentWindow=self.w.getNSWindow(), messageText=messageText, informativeText=informativeText, resultCallback=callback)

    def showAskYesNo(self, messageText, informativeText, callback=None):#
        result = QMessageBox.question(self.w.activeWindow(), messageText, informativeText, QMessageBox.Yes | QMessageBox.No)
        #vanilla.dialogs.askYesNo(parentWindow=self.w.getNSWindow(), messageText=messageText, informativeText=informativeText, resultCallback=callback)
        if callback is None:
            if result == QMessageBox.Yes:
                return 1
            else:
                return 0
        #    return alert._value

    def showGetFolder(self, callback=None):#
        directory = QFileDialog.getExistingDirectory(parent=self.w.activeWindow(), directory=QDir.currentPath())
        if callback is None:
            return directory
        #vanilla.dialogs.getFolder(parentWindow=self.w.getNSWindow(), resultCallback=callback)

    def showGetFile(self, fileTypes, callback, allowsMultipleSelection=False):
        # TODO: Mac OS sees UFO as file, make sure that this accepts it eveywhere
        # Note: fileTypes must follow QT convention e.g. "All Files (*);;Text Files (*.txt)"
        # Note#2: getOpenFileNames may pack in an array while getOpenFileName does not
        if allowsMultipleSelection: # why would you do this in a Font Editor?
            files = QFileDialog.getOpenFileNames(parent=self.w.activeWindow(), directory=QDir.currentPath(), filter=fileTypes)
        else:
            files = QFileDialog.getOpenFileName(parent=self.w.activeWindow(), directory=QDir.currentPath(), filter=fileTypes)
        #vanilla.dialogs.getFile(fileTypes=fileTypes, allowsMultipleSelection=allowsMultipleSelection,
        #    parentWindow=self.w.getNSWindow(), resultCallback=callback)

    def showPutFile(self, fileTypes, callback=None, fileName=None, directory=None, accessoryView=None):#
        # ! fileTypes

        # basic instance cannot put a default file name, use the base class
        #result = QFileDialog.getSaveFileName(parent=self.w, directory=directory, filter=fileTypes)
        # https://github.com/qtproject/qt/blob/98530cbc3a0bbb633bab96eebb535d7f92ecb1fa/src/gui/dialogs/qfiledialog.cpp#L1965
        dlg = QFileDialog(parent=self.w.activeWindow(), filter=fileTypes)
        dlg.setFileMode(QFileDialog.AnyFile)
        dlg.setAcceptMode(QFileDialog.AcceptSave)
        if directory: dlg.setDirectory(directory)
        if fileName: dlg.selectFile(fileName)
        if (dlg.exec_() == QDialog.Accepted):
            result = dialog.selectedFiles().value(0)
        if callback is None:
            return result
        '''
        if accessoryView is not None:
            w, h = accessoryView._posSize[2:]
            accessoryView._nsObject.setFrame_(((0, 0), (w, h)))
            accessoryView = accessoryView._nsObject
        vanilla.dialogs.putFile(fileTypes=fileTypes,
            parentWindow=self.w.getNSWindow(), resultCallback=callback, fileName=fileName, directory=directory, accessoryView=accessoryView)
        '''

