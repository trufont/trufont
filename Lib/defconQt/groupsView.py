from defconQt.glyphCollectionView import GlyphCollectionWidget
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class GroupListWidget(QListWidget):
    def __init__(self, groupNames, parent=None):
        super(GroupListWidget, self).__init__(parent)
        #self.setAlternatingRowColors(True)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSortingEnabled(True)

        for groupName in groupNames:
            item = QListWidgetItem(groupName, self)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
        #if len(groupNames): self.setCurrentRow(0)

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Delete:
            self.parent()._groupDelete()
            event.accept()
        elif key == Qt.Key_Left:
            self.parent().alignLeftBox.setChecked(True)
        elif key == Qt.Key_Right:
            self.parent().alignRightBox.setChecked(True)
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

    def setAlignment(self, alignRight):
        self.alignRight = alignRight
        self.update()

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

class GroupCollectionWidget(GlyphCollectionWidget):
    def __init__(self, parent=None):
        super(GroupCollectionWidget, self).__init__(parent)
        self._columns = 9
        self._scrollArea.setAcceptDrops(True)
        self._scrollArea.dragEnterEvent = self.pipeDragEnterEvent
        self._scrollArea.dropEvent = self.pipeDropEvent

        # TODO: upstream this, somehow
        self.characterDeletionCallback = None
        self.characterDropCallback = None
        self.resize(self.width(), 200)

    # TODO: The standard QListWidget has scrollbar and does not need three times parent call.
    # Find out how to handle that properly.
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            if self.characterDeletionCallback is not None:
                self.characterDeletionCallback(self.selection)
            event.accept()
        else:
            super(GroupCollectionWidget, self).keyPressEvent(event)

    def pipeDragEnterEvent(self, event):
        # TODO: the problem with text/plain is that any sort of text can get here.
        # (It allows direct compatibility with featureTextEditor though.)
        if (event.mimeData().hasText()):
            event.acceptProposedAction()

    def pipeDropEvent(self, event):
        if self.characterDropCallback is not None:
            self.characterDropCallback(event)

class GroupsWindow(QWidget):
    leftGroups = ["@MMK_L", "public.kern1"]
    rightGroups = ["@MMK_R", "public.kern2"]

    def __init__(self, font, parent=None):
        super(GroupsWindow, self).__init__(parent, Qt.Window)
        self.font = font

        groups = self.font.groups.keys()
        self.groupsList = GroupListWidget(groups, self)
        self.groupsList.currentItemChanged.connect(self._groupChanged)
        self.groupsList.itemChanged.connect(self._groupRenamed)
        self.groupsList.setFocus(True)

        self.stackWidget = GroupStackWidget(self.font, parent=self)

        self.addGroupButton = QPushButton("+", self)
        self.addGroupButton.clicked.connect(self._groupAdd)
        self.removeGroupButton = QPushButton("−", self)
        self.removeGroupButton.clicked.connect(self._groupDelete)
        if not groups: self.removeGroupButton.setEnabled(False)

        self.alignLeftBox = QRadioButton("Align left", self)
        self.alignRightBox = QRadioButton("Align right", self)
        self.alignLeftBox.setChecked(True)
        self.alignLeftBox.toggled.connect(self._alignmentChanged)
        self._autoDirection = True

        self.collectionWidget = GroupCollectionWidget(parent=self)
        self.collectionWidget.characterDeletionCallback = self.characterDeleteEvent
        self.collectionWidget.characterDropCallback = self.characterDropEvent
        self._cachedName = None

        layout = QGridLayout(self)
        layout.addWidget(self.groupsList, 0, 0, 5, 4)
        layout.addWidget(self.stackWidget, 0, 4, 5, 4)
        layout.addWidget(self.addGroupButton, 5, 0)
        layout.addWidget(self.removeGroupButton, 5, 3)
        layout.addWidget(self.alignLeftBox, 5, 4)
        layout.addWidget(self.alignRightBox, 5, 7)
        layout.addWidget(self.collectionWidget.scrollArea(), 6, 0, 4, 8)
        # TODO: calib this more
        layout.setColumnStretch(4, 1)
        self.setLayout(layout)

        self.setWindowTitle("Groups window – %s %s" % (self.font.info.familyName, self.font.info.styleName))

    def _alignmentChanged(self):
        alignRight = self.alignRightBox.isChecked()
        self.stackWidget.setAlignment(alignRight)

    def _groupAdd(self):
        groupName = "New group"
        if groupName in self.font.groups:
            index = 1
            while "%s %d" % (groupName, index) in self.font.groups:
                index += 1
            groupName = "%s %d" % (groupName, index)
        self.font.groups[groupName] = []
        item = QListWidgetItem(groupName, self.groupsList)
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        self.groupsList.setCurrentItem(item)
        self.groupsList.editItem(item)
        self.removeGroupButton.setEnabled(True)

    def _groupChanged(self):
        self._cachedName = self.groupsList.currentItem().text()
        if self._autoDirection:
            for name in self.leftGroups:
                if self._cachedName.startswith(name):
                    self.alignRightBox.setChecked(True)
                    break
            for name in self.rightGroups:
                if self._cachedName.startswith(name):
                    self.alignLeftBox.setChecked(True)
                    break
        glyphs = []
        for gName in self.font.groups[self._cachedName]:
            if gName in self.font:
                glyphs.append(self.font[gName])
        self.stackWidget.setGlyphs(glyphs)
        self.collectionWidget.glyphs = glyphs

    def _groupRenamed(self):
        newKey = self.groupsList.currentItem()
        if newKey is None: return
        newKey = newKey.text()
        self.font.groups[newKey] = self.font.groups[self._cachedName]
        del self.font.groups[self._cachedName]

    def _groupDelete(self):
        newKey = self.groupsList.currentItem().text()
        del self.font.groups[newKey]
        self.groupsList.takeItem(self.groupsList.currentRow())
        if not self.font.groups.keys(): self.removeGroupButton.setEnabled(False)
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
        currentGroup = self.groupsList.currentItem()
        if currentGroup is None: return
        currentGroup = currentGroup.text()
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
            self.collectionWidget._sizeEvent(width)
            self.stackWidget.update()
        super(GroupsWindow, self).resizeEvent(event)
