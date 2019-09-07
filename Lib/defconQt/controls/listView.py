"""
The *listView* submodule
------------------------

The *listView* submodule provides a widget that can conveniently display Python
lists_.

.. _lists: https://docs.python.org/3/tutorial/introduction.html#lists
"""

import collections.abc

from defcon import Font, Glyph
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QColorDialog,
    QProxyStyle,
    QStyle,
    QStyledItemDelegate,
    QStyleOption,
    QTreeView,
)

from defconQt.tools import drawing

__all__ = ["ListView"]


class AbstractListModel(QAbstractTableModel):
    valueChanged = pyqtSignal(QModelIndex, object, object)

    def __init__(self, lst, parent=None):
        super().__init__(parent)
        self._headerLabels = []
        self._inDrop = False

        self.setList(lst)

    # implementation-specific methods

    def _data(self, row, column):
        raise NotImplementedError

    def _setData(self, row, column, value):
        raise NotImplementedError

    def _columnCount(self):
        raise NotImplementedError

    def _rowCount(self):
        raise NotImplementedError

    def _insertRows(self):
        raise NotImplementedError

    def _removeRows(self):
        raise NotImplementedError

    # other methods

    def list(self):
        return list(self._list)

    def setList(self, lst):
        self.layoutAboutToBeChanged.emit()
        self._list = lst
        self.layoutChanged.emit()

    def headerLabels(self):
        return list(self._headerLabels)

    def setHeaderLabels(self, labels):
        self._headerLabels = labels

    def sorted(self):
        return self._sorted

    def setSorted(self, value):
        self._sorted = value
        if value:
            self._list = sorted(self._list)

    # builtins

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid() and role in (Qt.DisplayRole, Qt.EditRole):
            row, column = index.row(), index.column()
            return self._data(row, column)
        return None

    def setData(self, index, value, role=Qt.EditRole):
        if index.isValid() and role in (Qt.DisplayRole, Qt.EditRole):
            row, column = index.row(), index.column()
            oldValue = self._data(row, column)
            self._setData(row, column, value)
            if not self._inDrop:
                self.valueChanged.emit(index, oldValue, value)
            self.dataChanged.emit(index, index, [role])
            return True
        return super().setData(index, value, role)

    def columnCount(self, parent=QModelIndex()):
        # flat table
        # http://stackoverflow.com/a/27333368/2037879
        if parent.isValid():
            return 0
        return self._columnCount()

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return self._rowCount()

    def insertRows(self, row, count, parent=QModelIndex()):
        if parent.isValid():
            return False
        self.beginInsertRows(parent, row, row + count - 1)
        self._insertRows(row, count)
        self.endInsertRows()
        return True

    def removeRows(self, row, count, parent=QModelIndex()):
        if parent.isValid():
            return False
        self.beginRemoveRows(parent, row, row + count - 1)
        self._removeRows(row, count)
        self.endRemoveRows()
        return True

    def dropMimeData(self, data, action, row, column, parent):
        if parent.isValid():
            return False
        # force column 0, we want to drag column onto the start of the
        # drop spot, otherwise it will be split between two new columns
        self._inDrop = True
        result = super().dropMimeData(data, action, row, 0, parent)
        self._inDrop = False
        return result

    def flags(self, index):
        flags = (
            Qt.ItemIsEnabled
            | Qt.ItemIsSelectable
            | Qt.ItemIsDragEnabled
            | Qt.ItemIsDropEnabled
            | Qt.ItemNeverHasChildren
        )
        if not isinstance(self.data(index), (Font, Glyph)):
            flags |= Qt.ItemIsEditable
        return flags

    def supportedDropActions(self):
        return Qt.CopyAction | Qt.MoveAction

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if section >= len(self._headerLabels):
                return None
            else:
                return self._headerLabels[section]
        return super().headerData(section, orientation, role)


class FlatListModel(AbstractListModel):
    def __init__(self, lst, columnCount=1, parent=None):
        super().__init__(lst, parent)
        self._columns = columnCount

    def _data(self, row, column):
        return self._list[row * self._columns + column]

    def _setData(self, row, column, value):
        self._list[row * self._columns + column] = value

    def _columnCount(self):
        return self._columns

    def _rowCount(self):
        return len(self._list) // self._columns

    def _insertRows(self, row, count):
        # XXX: test this!
        for index in range(row, row + count):
            for _ in self._columns:
                self._list.insert(index, 0)

    def _removeRows(self, row, count):
        # XXX: test this!
        for index in range(row, row + count):
            for _ in self._columns:
                del self._list[index * self._columns]


class OneTwoListModel(AbstractListModel):
    def _data(self, row, column):
        if self._is2D:
            return self._list[row][column]
        else:
            assert column == 0
            return self._list[row]

    def _setData(self, row, column, value):
        if self._is2D:
            self._list[row][column] = value
        else:
            assert column == 0
            self._list[row] = value

    def _columnCount(self):
        if self._is2D:
            if self._list:
                return len(self._list[0])
            return 0
        else:
            return 1

    def _rowCount(self):
        return len(self._list)

    def _insertRows(self, row, count):
        for index in range(row, row + count):
            elem = [0] * self._columnCount() if self._is2D else 0
            self._list.insert(index, elem)

    def _removeRows(self, row, count):
        for index in range(row, row + count):
            del self._list[index]

    def setList(self, lst):
        self.layoutAboutToBeChanged.emit()
        self._list = lst
        if self._list and isinstance(self._list[0], collections.abc.MutableSequence):
            self._is2D = True
        else:
            self._is2D = False
        self.layoutChanged.emit()


class ListItemDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        data = index.data(Qt.EditRole)
        if isinstance(data, bool):
            checkBox = QCheckBox(parent)
            checkBox.setChecked(data)
            checkBox.toggled.connect(
                lambda: self.setModelData(checkBox, index.model(), index)
            )
            return checkBox
        elif isinstance(data, QColor):
            # we have our own ways
            return None
        return super().createEditor(parent, option, index)

    def displayText(self, value, locale):
        if isinstance(value, Font):
            info = value.info
            return f"{info.familyName} {info.styleName}"
        elif isinstance(value, Glyph):
            return value.name
        elif isinstance(value, (QColor, bool)):
            # we'll paint those instead
            return None
        return super().displayText(value, locale)

    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        data = index.data(Qt.DisplayRole)
        if isinstance(data, QColor):
            rect = option.rect.adjusted(2, 1, -2, -1)
            if data.isValid():
                painter.fillRect(rect, data)
            else:
                backgroundColor = QColor(214, 214, 214)
                color = QColor(170, 170, 170)
                tileSize = round(rect.height() / 3)
                drawing.drawTiles(
                    painter,
                    rect,
                    tileSize=tileSize,
                    color=color,
                    backgroundColor=backgroundColor,
                )

    def setModelData(self, editor, model, index):
        data = index.data(Qt.EditRole)
        if isinstance(data, bool):
            value = editor.isChecked()
            model.setData(index, value)
        else:
            super().setModelData(editor, model, index)


class ListProxy(QProxyStyle):
    def drawPrimitive(self, element, option, painter, widget):
        # http://stackoverflow.com/a/9611137/2037879
        if element == QStyle.PE_IndicatorItemViewItemDrop and not option.rect.isNull():
            # we don't drag over items
            # XXX: possible to forbid this in the model instead?
            if option.rect.height():
                return
            option_ = QStyleOption(option)
            option_.rect.setLeft(0)
            if widget is not None:
                option_.rect.setRight(widget.width())
            super().drawPrimitive(element, option_, painter, widget)
        else:
            super().drawPrimitive(element, option, painter, widget)


class ListView(QTreeView):
    """
    A QTreeView_ widget that displays a Python list, whether 1D or 2D.

    Besides standard types, this widget can display Font_ or Glyph_.

    Use *setDragEnabled(True)* to allow reordering drag and drop.

    Emits *listChanged* when data changes inside the widget (when performing
    drag and drop, mostly).

    # TODO: cleanup API and compare w QTreeWidget
    # TODO: maybe clear widgets on setList() and try to do without setIndexWidget
    # TODO: make it possible to up/down selected row w shortcut
    # e.g. Alt+Up/Down

    .. _Font: http://ts-defcon.readthedocs.org/en/ufo3/objects/font.html
    .. _Glyph: http://ts-defcon.readthedocs.org/en/ufo3/objects/glyph.html
    .. _QTreeView: http://doc.qt.io/qt-5/qtreeview.html
    """

    currentItemChanged = pyqtSignal(object)
    selectionChanged_ = pyqtSignal()

    flatListModelClass = FlatListModel
    oneTwoListModelClass = OneTwoListModel

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDragEnabled(False)
        self.setItemDelegate(ListItemDelegate())
        self.setRootIsDecorated(False)
        self.setStyle(ListProxy())
        self.header().setVisible(False)
        self.doubleClicked.connect(self._doubleClicked)
        self._flatListInput = False
        self._triggers = None

    def _doubleClicked(self, index):
        model = self.model()
        if model is None:
            return
        data = model.data(index)
        if isinstance(data, QColor):
            if QApplication.keyboardModifiers() & Qt.AltModifier:
                model.setData(index, QColor())
            else:
                dialog = QColorDialog(self)
                dialog.setCurrentColor(data)
                dialog.setOption(QColorDialog.ShowAlphaChannel)
                ret = dialog.exec_()
                if ret:
                    color = dialog.currentColor()
                    model.setData(index, color)

    # -------------------
    # Convenience methods
    # -------------------

    def currentRow(self):
        index = self.currentIndex()
        data = self.model().list()
        return data[index.row()]

    def removeCurrentRow(self):
        index = self.currentIndex()
        model = self.model()
        model.removeRow(index.row())

    def editItem(self, row, column):
        model = self.model()
        if model is None:
            return
        self.edit(model.index(row, column))

    def setCurrentItem(self, row, column):
        model = self.model()
        if model is None:
            return
        index = model.index(row, column)
        super().setCurrentIndex(index)

    def selectedRows(self):
        selectionModel = self.selectionModel()
        if selectionModel is None:
            return []
        selectedRows = selectionModel.selectedRows()
        return [index.row() for index in selectedRows]

    def setEditable(self, value):
        """
        Sets whether the list’s elements can be edited.
        """
        if value:
            if self._triggers is None:
                return
            # default actions vary depending on platform
            self.setEditTriggers(self._triggers)
        else:
            self._triggers = self.editTriggers()
            self.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def headerLabels(self):
        """
        Returns this widget’s current header labels.
        """
        model = self.model()
        if model is None:
            return None
        return model.headerLabels()

    def setHeaderLabels(self, labels):
        """
        Sets the header labels to *labels* (should be a list of strings).
        """
        model = self.model()
        if model is None:
            return
        model.setHeaderLabels(labels)
        self.header().setVisible(bool(labels))

    def list(self):
        """
        Returns the list as displayed by this widget, or None if no list was
        specified.
        """
        model = self.model()
        if model is None:
            return None
        return model.list()

    def setList(self, lst, **kwargs):
        """
        Sets the widget to display list *lst*.

        Additional keyword arguments may be provided and forwarded to the
        model.

        The default is None.

        # TODO: we should maybe clear indexWidgets here
        """
        model = self.model()
        if model is None:
            if self._flatListInput:
                modelClass = self.flatListModelClass
            else:
                modelClass = self.oneTwoListModelClass
            model = modelClass(lst, **kwargs)
            self.dataDropped = model.rowsRemoved
            self.valueChanged = model.valueChanged
            self.setModel(model)
        else:
            index = self.currentIndex()
            # reset the selection model to avoid selected row out of range
            # http://stackoverflow.com/a/15878679/2037879
            self.selectionModel().reset()
            model.setList(lst)
            if index.row() < model.rowCount() and index.column() < model.columnCount():
                self.setCurrentIndex(index)

    def flatListInput(self):
        """
        Returns whether this widget takes a flat list as input.
        """
        return self._flatListInput

    def setFlatListInput(self, value):
        """
        Sets whether :func:`setList` should consider its input list as flat,
        i.e. as a 2D structure.
        In that case, pass the *columnCount* argument to specify how many
        columns should be considered, e.g.:

        >>> from defconQt.controls.listView import ListView
        >>> view = ListView()
        >>> view.setList(
        ...     [
        ...         [1, 2, 3],
        ...         [4, 5, 6]
        ...     ])

        is equivalent to:

        >>> view = ListView()
        >>> view.setFlatList(True)
        >>> view.setList([1, 2, 3, 4, 5, 6], columnCount=3)

        """
        self._flatListInput = value

    # ----------
    # Qt methods
    # ----------

    def currentChanged(self, current, previous):
        super().currentChanged(current, previous)
        model = self.model()
        self.currentItemChanged.emit(model.data(current))

    def selectionChanged(self, selected, deselected):
        super().selectionChanged(selected, deselected)
        self.selectionChanged_.emit()

    def dropEvent(self, event):
        if event.source() == self:
            # widgets bookkeeping
            cachedWidgets = []
            # figure out the indexes
            dragRow = self.currentIndex().row()
            dropRow = self.indexAt(event.pos()).row()
            if self.dropIndicatorPosition() == QAbstractItemView.BelowItem:
                dropRow += 1
            # extract
            model = self.model()
            for col in range(model.columnCount()):
                widget = self.indexWidget(model.index(dragRow, 0))
                if widget:
                    # release the widget
                    self.editorDestroyed(widget)
                    # store it
                    cachedWidgets.append((col, widget))
            super().dropEvent(event)
            for col, widget in cachedWidgets:
                index = model.index(dropRow, col)
                self.setIndexWidget(index, widget)
        else:
            super().dropEvent(event)
