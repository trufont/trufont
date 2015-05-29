from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class GroupsWindow(QWidget):
    def __init__(self, font, parent=None):
        super(GroupsWindow, self).__init__(parent, Qt.Window)
        self.font = font
        self.groups = sorted(font.groups.keys(), key=lambda t: t[0])

        self.groupsList = QListWidget(self)
        #self.groupsList.addItems(self.font.groups.keys())
        #self.groupsList.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        for groupName in self.font.groups.keys():
            item = QListWidgetItem(groupName, self.groupsList)
            #item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsEditable)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
        self.groupsList.itemChanged.connect(self._groupRenamed)
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.groupsList)
        self.setLayout(layout)
        
        self.setWindowTitle("%s%s%s%s" % ("Groups window – ", self.font.info.familyName, " ", self.font.info.styleName))
    
    def _groupRenamed(self):
        cur = self.groupsList.currentItem()
        # XXX: perf?
        index = self.groupsList.indexFromItem(cur)
        newKey = cur.text()
        self.font.groups[newKey] = self.font.groups[self.groups[index]]
        del self.font.groups[self.groups[index]]
        self.groups[index] = newKey
        #print(self.groupsList.currentItem().text())