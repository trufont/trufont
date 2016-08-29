from defconQt.controls.glyphCellView import GlyphCellView, GlyphCellWidget
from defconQt.controls.listView import ListView
from defconQt.tools.glyphsMimeData import GlyphsMimeData
from trufont.controls.glyphStackWidget import GlyphStackWidget
from trufont.objects import settings
from trufont.tools import platformSpecific
from PyQt5.QtCore import pyqtSignal, QSize, Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QGridLayout, QPushButton, QRadioButton, QWidget)
import bisect

_leftGroupPrefix = "public.kern1"
_rightGroupPrefix = "public.kern2"


class GroupsWindow(QWidget):

    def __init__(self, font, parent=None):
        super().__init__(parent, Qt.Window)
        self._autoDirection = True
        self._font = font
        self._font.groups.addObserver(self, "_groupsChanged", "Groups.Changed")
        self._font.info.addObserver(self, "_fontInfoChanged", "Info.Changed")

        groups = self._font.groups
        self.groupsListView = GroupListView(self)
        self.groupsListView.setList(sorted(groups.keys()))
        self.groupsListView.setHeaderLabels(["Name"])
        self.groupsListView.alignmentChanged.connect(self._alignmentChanged)
        # self.groupsListView.groupDeleted.connect(self._groupDeleted)
        self.groupsListView.currentItemChanged.connect(self._groupChanged)
        self.groupsListView.valueChanged.connect(self._groupRenamed)

        self.stackWidget = GlyphStackWidget(self)

        self.addGroupButton = QPushButton("+", self)
        self.addGroupButton.clicked.connect(self._groupAdd)
        self.removeGroupButton = QPushButton("−", self)
        self.removeGroupButton.clicked.connect(self._groupDeleted)
        if not groups:
            self.removeGroupButton.setEnabled(False)

        self.alignLeftBox = QRadioButton(self.tr("Align left"), self)
        self.alignRightBox = QRadioButton(self.tr("Align right"), self)
        self.alignRightBox.toggled.connect(self._alignmentChanged)
        self.alignLeftBox.setChecked(True)

        self.groupCellView = GroupCellView(font, self)
        self.groupCellView.glyphsDropped.connect(self._glyphsDropped)
        self.groupCellView.selectionDeleted.connect(self._selectionDeleted)

        layout = QGridLayout(self)
        layout.addWidget(self.groupsListView, 0, 0, 5, 4)
        layout.addWidget(self.stackWidget, 0, 4, 5, 4)
        layout.addWidget(self.addGroupButton, 5, 0)
        layout.addWidget(self.removeGroupButton, 5, 3)
        layout.addWidget(self.alignLeftBox, 5, 4)
        layout.addWidget(self.alignRightBox, 5, 7)
        layout.addWidget(self.groupCellView, 6, 0, 4, 8)
        # TODO: calib this more
        layout.setColumnStretch(4, 1)
        self.setLayout(layout)

        self.updateWindowTitle(font=self._font)
        self.readSettings()

    def readSettings(self):
        geometry = settings.groupsWindowGeometry()
        if geometry:
            self.restoreGeometry(geometry)

    def writeSettings(self):
        settings.setGroupsWindowGeometry(self.saveGeometry())

    def updateWindowTitle(self, title=None, font=None):
        if title is None:
            title = self.tr("Groups")
        if font is not None:
            title = "%s – %s %s" % (
                title, font.info.familyName, font.info.styleName)
        self.setWindowTitle(title)

    # -------------
    # Notifications
    # -------------

    # font

    def _groupsChanged(self, notification):
        groups = notification.object
        self.groupsListView.setList(sorted(groups.keys()))
        name = self.groupsListView.currentValue()
        groupIsValid = name is not None and name in groups
        if groupIsValid:
            glyphs = [self._font[gName] for gName in groups[
                name] if gName in self._font]
        else:
            glyphs = []
        self.groupCellView.setAcceptDrops(groupIsValid)
        self.stackWidget.setGlyphs(list(glyphs))
        self.groupCellView.setGlyphs(list(glyphs))

    def _fontInfoChanged(self, notification):
        self.updateWindowTitle(font=self._font)

    # widgets

    def _alignmentChanged(self, alignRight):
        self.stackWidget.setAlignment(
            "right" if alignRight else "left")
        if alignRight:
            self.alignRightBox.blockSignals(True)
            self.alignRightBox.setChecked(True)
            self.alignRightBox.blockSignals(False)
        else:
            self.alignLeftBox.setChecked(True)

    def _groupAdd(self):
        groupName = self.tr("New group")
        groups = self._font.groups
        if groupName in groups:
            index = 1
            while "%s %d" % (groupName, index) in groups:
                index += 1
            groupName = "%s %d" % (groupName, index)
        groups.disableNotifications(observer=self)
        groups[groupName] = []
        # TODO; make this a listView method
        lst = self.groupsListView.list()
        index = bisect.bisect_left(lst, groupName)
        lst.insert(index, groupName)
        self.groupsListView.setList(lst)
        self.groupsListView.editRow(index)
        self.removeGroupButton.setEnabled(True)
        groups.enableNotifications(observer=self)

    def _groupChanged(self, name):
        if name is None:
            self.groupCellView.setAcceptDrops(False)
            return
        if self._autoDirection:
            if name.startswith(_leftGroupPrefix):
                self.alignRightBox.setChecked(True)
            if name.startswith(_rightGroupPrefix):
                self.alignLeftBox.setChecked(True)
        glyphs = []
        for gName in self._font.groups[name]:
            if gName in self._font:
                glyphs.append(self._font[gName])
        self.groupCellView.setAcceptDrops(True)
        self.stackWidget.setGlyphs(list(glyphs))
        self.groupCellView.setGlyphs(glyphs)

    def _groupRenamed(self, index, previous, current):
        if current == previous:
            return
        groups = self._font.groups
        groups.holdNotifications()
        groups[current] = groups[previous]
        del groups[previous]
        groups.releaseHeldNotifications()

    def _groupDeleted(self):
        name = self.groupsListView.currentValue()
        if name is None:
            return
        del self._font.groups[name]

    def _selectionDeleted(self, selection):
        name = self.groupsListView.currentValue()
        if name is None:
            return
        groups = self._font.groups
        currentGroup = groups[name]
        # relying on ordered group elements
        # reverse to not change index of smaller elements
        for key in sorted(selection, reverse=True):
            del currentGroup[key]
        groups[name] = currentGroup
        groups.dirty = True

    def _glyphsDropped(self):
        name = self.groupsListView.currentValue()
        if name is None:
            return
        glyphs = self.groupCellView.glyphs()
        self._font.groups[name] = [glyph.name for glyph in glyphs]

    # ----------
    # Qt methods
    # ----------

    def sizeHint(self):
        return QSize(650, 650)

    def moveEvent(self, event):
        self.writeSettings()

    resizeEvent = moveEvent

    def closeEvent(self, event):
        super().closeEvent(event)
        if event.isAccepted():
            self._font.groups.removeObserver(self, "Groups.Changed")
            self._font.info.removeObserver(self, "Info.Changed")


class GroupListView(ListView):
    alignmentChanged = pyqtSignal(bool)
    groupDeleted = pyqtSignal(object)

    def currentValue(self):
        index = self.currentIndex()
        model = self.model()
        if model is None:
            return None
        return model.data(index)

    def editRow(self, index):
        self.editItem(index, 0)

    def keyPressEvent(self, event):
        key = event.key()
        if platformSpecific.isDeleteEvent(event):
            indexes = self.selectedIndexes()
            if indexes:
                data = self.model().data(indexes[0])
                self.groupDeleted.emit(data)
        elif key == Qt.Key_Left:
            self.alignmentChanged.emit(False)
        elif key == Qt.Key_Right:
            self.alignmentChanged.emit(True)
        else:
            super().keyPressEvent(event)


class GroupCellWidget(GlyphCellWidget):
    selectionDeleted = pyqtSignal(set)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._font = None

    def font_(self):
        return self._font

    def setFont_(self, font):
        self._font = font

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Delete):
            selection = self._selection
            if selection:
                self.selectionDeleted.emit(selection)
        else:
            super().keyPressEvent(event)

    def dragEnterEvent(self, event):
        mimeData = event.mimeData()
        if isinstance(mimeData, GlyphsMimeData):
            glyphs = mimeData.glyphs()
            for glyph in glyphs:
                if glyph.font == self._font:
                    event.acceptProposedAction()
                    return

    def dropEvent(self, event):
        mimeData = event.mimeData()
        # remove glyphs that aren't from our font or are already there
        glyphs = mimeData.glyphs()
        for index, glyph in enumerate(glyphs):
            if glyph.font != self._font or glyph in self._glyphs:
                del glyphs[index]
        mimeData.setGlyphs(glyphs)
        # now proceed
        super().dropEvent(event)


class GroupCellView(GlyphCellView):
    glyphCellWidgetClass = GroupCellWidget

    def __init__(self, font, parent=None):
        super().__init__(parent)
        self._glyphCellWidget.setFont_(font)
        # re-export signals
        self.selectionDeleted = self._glyphCellWidget.selectionDeleted

    def sizeHint(self):
        cellHeight = self._glyphCellWidget.cellSize()[1]
        size = super().sizeHint()
        size.setHeight(cellHeight * 2)
        return size
