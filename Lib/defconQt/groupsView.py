from fontView import CharacterWidget
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class GroupListWidget(QListWidget):
    def __init__(self, groupNames, parent=None):
        super(GroupListWidget, self).__init__(parent)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSortingEnabled(True)
        
        for groupName in groupNames:
            item = QListWidgetItem(groupName, self)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self.parent()._groupDelete()
            event.accept()
        else:
            super(GroupListWidget, self).keyPressEvent(event)

class GroupStackWidget(QWidget):
    def __init__(self, font, glyphs=[], parent=None):
        super(GroupStackWidget, self).__init__(parent)
        self.ascender = font.info.ascender
        self.glyphs = glyphs
        self.maxWidth = max(glyph.width for glyph in self.glyphs) if len(self.glyphs) else 300
        self.upm = font.info.unitsPerEm
        self.padding = 10
        self.alignRight = False
    
    def setGlyphs(self, glyphs):
        self.glyphs = glyphs
        self.maxWidth = max(glyph.width for glyph in self.glyphs) if len(self.glyphs) else 300
        self.update()
    
    def sizeHint(self):
        return QSize(self.maxWidth+2*self.padding, 400)
    
    def paintEvent(self, event):
        # TODO: maybe use self.upm*(1+2*BufferHeight) for the denominator as in fontView
        scale = self.height() / (self.upm*1.2)
        x_offset = (self.width()-self.maxWidth*scale-self.padding*2)/2
        if x_offset < 0:
            scale *= 1+2*x_offset/(self.maxWidth*scale)
            x_offset = 0
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(self.padding, self.padding+(self.ascender*1.2)*scale)
        painter.scale(scale, -scale)
            
        col = QColor(Qt.black)
        col.setAlphaF(.2)
        for glyph in self.glyphs:
            if self.alignRight: dist = self.maxWidth - glyph.width
            else: dist = 0
            glyphPath = glyph.getRepresentation("defconQt.QPainterPath")
            painter.save()
            painter.translate(x_offset+dist, 0)
            painter.fillPath(glyphPath, col)
            painter.restore()

class GroupCharacterWidget(CharacterWidget):
    def __init__(self, font, squareSize=56, scrollArea=None, parent=None):
        super(GroupCharacterWidget, self).__init__(font, squareSize, scrollArea, parent)
        self.columns = 9
        self.scrollArea.setAcceptDrops(True)
        self.scrollArea.dragEnterEvent = self.pipeDragEnterEvent
        self.scrollArea.dropEvent = self.pipeDropEvent
        self.resize(self.width(), 200)
    
    # TODO: The standard QListWidget has scrollbar and does not need three times parent call.
    # Find out how to handle that properly.
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

        self.groupsList = GroupListWidget(self.font.groups.keys(), self)
        self.groupsList.itemChanged.connect(self._groupRenamed)
        # TODO: it seems grid layout extends the column regardless of this
        self.groupsList.setMaximumWidth(4*56+1)
        
        self.stackWidget = GroupStackWidget(self.font, parent=self)
        
        self.scrollArea = QScrollArea(self)
        self.characterWidget = GroupCharacterWidget(self.font, scrollArea=self.scrollArea, parent=self)
        self.scrollArea.setWidget(self.characterWidget)
        self.groupsList.currentItemChanged.connect(self._groupChanged)
        
        layout = QGridLayout(self)
        layout.addWidget(self.groupsList, 0, 0, 5, 4)
        layout.addWidget(self.stackWidget, 0, 4, 5, 4)
        layout.addWidget(self.scrollArea, 5, 0, 4, 8)
        self.setLayout(layout)
        
        self.setWindowTitle("%s%s%s%s" % ("Groups window – ", self.font.info.familyName, " ", self.font.info.styleName))
    
    def _groupChanged(self):
        currentGroup = self.groupsList.currentItem().text()
        glyphs = []
        for gName in self.font.groups[currentGroup]:
            glyphs.append(self.font[gName])
        self.stackWidget.setGlyphs(glyphs)
        self.characterWidget.setGlyphs(glyphs)
    
    def _groupRenamed(self):
        cur = self.groupsList.currentItem()
        # XXX: perf?
        index = self.groupsList.indexFromItem(cur)
        newKey = cur.text()
        self.font.groups[newKey] = self.font.groups[self.groups[index]]
        del self.font.groups[self.groups[index]]
    
    def _groupDelete(self):
        cur = self.groupsList.currentItem()
        del self.font.groups[cur.text()]
        self.groupsList.takeItem(self.groupsList.currentRow())
        self._groupChanged()
    
    def characterDeleteEvent(self, selection):
        currentGroup = self.groupsList.currentItem().text()
        currentGroupList = self.font.groups[currentGroup]
        # relying on ordered group elements
        # reverse to not change index of smaller elements
        for key in sorted(selection, reverse=True):
            del currentGroupList[key]
        self.font.groups[currentGroup] = currentGroupList
        self._groupChanged()
    
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
        
    def resizeEvent(self, event):
        if self.isVisible():
            margins = self.layout().contentsMargins()
            width = event.size().width() - (margins.left() + margins.right())
            self.characterWidget._sizeEvent(width)
            self.stackWidget.update()
        super(GroupsWindow, self).resizeEvent(event)