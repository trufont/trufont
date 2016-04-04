"""
ToolBar is exclusive and displays only icons.
"""
from trufont.tools import platformSpecific
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QAction, QTabBar, QToolBar

__all__ = ["ButtonToolBar"]


if platformSpecific.useTabBar():
    class ButtonToolBar(QToolBar):

        def __init__(self, title, parent=None):
            super().__init__(title, parent)
            self._tabBar = ButtonTabBar(self)
            self.currentChanged = self._tabBar.currentChanged
            # self.setMovable(False)

        def addButton(self, icon, text):
            self._tabBar.addButton(icon, text)

        def insertButton(self, index, icon, text):
            self._tabBar.insertButton(index, icon, text)

        def removeButton(self, index):
            self._tabBar.removeButton(index)

        def count(self):
            return self._tabBar.count()

        def currentIndex(self):
            return self._tabBar.currentIndex()

        def setCurrentIndex(self, index):
            self._tabBar.setCurrentIndex(index)

    class ButtonTabBar(QTabBar):

        def addButton(self, icon, text):
            self.insertButton(self.count(), icon, text)

        def insertButton(self, index, icon, text):
            # don't display the text, but put it in the tooltip
            index = self.insertTab(index, icon, None)
            self.setTabToolTip(index, text)

        def removeButton(self, index):
            self.removeTab(index)
else:
    class ButtonToolBar(QToolBar):
        currentChanged = pyqtSignal(int)

        def __init__(self, title, parent=None):
            super().__init__(title, parent)
            self.actionTriggered.connect(self._actionTriggered)
            # self.setMovable(False)

        # notifications

        def _actionTriggered(self, action):
            actions = self.actions()
            self.currentChanged.emit(actions.index(action))

        # methods

        def addButton(self, icon, text):
            self.addAction(icon, text)

        def insertButton(self, index, icon, text):
            actions = self.actions()
            if index >= len(actions):
                return
            before = actions[index]
            after = QAction(icon, text, self)
            self.insertAction(before, after)

        def removeButton(self, index):
            actions = self.actions()
            if index >= len(actions):
                return
            action = actions[index]
            self.removeAction(action)

        def count(self):
            return len(self.actions())

        def currentIndex(self):
            for index, action in enumerate(self.actions()):
                if action.isChecked():
                    return index
            return -1

        def setCurrentIndex(self, index):
            actions = self.actions()
            for action in actions:
                action.setChecked(False)
            if index < 0 or index >= len(actions):
                return
            actions[index].setChecked(True)
