from fontView import CharacterWidget
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class GroupCharacterWidget(CharacterWidget):
    def __init__(self, font, squareSize=56, scrollArea=None, parent=None):
        super(GroupCharacterWidget, self).__init__(font, squareSize, scrollArea, parent)
        self.columns = 8
        self.scrollArea.setAcceptDrops(True)
        self.scrollArea.dragEnterEvent = self.pipeDragEnterEvent
        self.scrollArea.dropEvent = self.pipeDropEvent
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self.parent().parent().parent().characterDeleteEvent(self._selection)
            event.accept()
        else:
            super(GroupCharacterWidget, self).keyPressEvent(event)
    
    def pipeDragEnterEvent(self, event):
        # TODO: the problem with text/plain is that any sort of text can get here.
        # (It allows direct compatibility with featureTextEditor though.)
        if (event.mimeData().hasFormat("text/plain")):
            event.acceptProposedAction()
    
    def pipeDropEvent(self, event):
        self.parent().parent().parent().characterDropEvent(event)

class GroupsWindow(QWidget):
    def __init__(self, font, parent=None):
        super(GroupsWindow, self).__init__(parent, Qt.Window)
        self.font = font

        self.groupsList = QListWidget(self)
        self.groupsList.setSelectionMode(QAbstractItemView.SingleSelection)
        self.groupsList.setSortingEnabled(True)
        for groupName in self.font.groups.keys():
            item = QListWidgetItem(groupName, self.groupsList)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
        self.groupsList.itemChanged.connect(self._groupRenamed)
        
        self.scrollArea = QScrollArea(self)
        self.characterWidget = GroupCharacterWidget(self.font, scrollArea=self.scrollArea, parent=self)
        self.scrollArea.setWidget(self.characterWidget)
        self.groupsList.currentItemChanged.connect(self._groupChanged)
        
        layout = QHBoxLayout(self)
        layout.addWidget(self.groupsList)
        layout.addWidget(self.scrollArea)
        self.setLayout(layout)
        
        self.setWindowTitle("%s%s%s%s" % ("Groups window – ", self.font.info.familyName, " ", self.font.info.styleName))
    
    def _groupChanged(self):
        currentGroup = self.groupsList.currentItem().text()
        glyphs = []
        for gName in self.font.groups[currentGroup]:
            glyphs.append(self.font[gName])
        self.characterWidget.setGlyphs(glyphs)
    
    def _groupRenamed(self):
        cur = self.groupsList.currentItem()
        # XXX: perf?
        index = self.groupsList.indexFromItem(cur)
        newKey = cur.text()
        self.font.groups[newKey] = self.font.groups[self.groups[index]]
        del self.font.groups[self.groups[index]]
        #print(self.groupsList.currentItem().text())
    
    def characterDeleteEvent(self, selection):
        currentGroup = self.groupsList.currentItem().text()
        currentGroupList = self.font.groups[currentGroup]
        # relying on ordered group elements
        # reverse to not change index of smaller elements
        for key in sorted(selection, reverse=True):
            del currentGroupList[key]
        self.font.groups[currentGroup] = currentGroupList
        self.characterWidget.update()
    
    def characterDropEvent(self, event):
        currentGroup = self.groupsList.currentItem().text()
        glyphNames = event.mimeData().text().split(" ")
        for gName in glyphNames:
            # Due to defcon limitations, we must fetch and update for the
            # notification to pass through
            currentGroupList = self.font.groups[currentGroup]
            currentGroupList.append(gName)
            self.font.groups[currentGroup] = currentGroupList
        event.acceptProposedAction()
        self._groupChanged()