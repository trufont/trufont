from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence, QColor, QPixmap, QIcon
from PyQt5.QtWidgets import QWidget, QMenu, QListWidget, QListWidgetItem, \
                            QAbstractItemView, QVBoxLayout, QAction, QColorDialog
from defconQt import icons_db
from defconQt.glyphView import AddLayerDialog

class LayerSetList(QListWidget):
    def __init__(self, font, parent=None, *args, **kwds):
        super().__init__(parent, *args, **kwds)

        self._layerSet = font.layers

        self.setDragDropMode(QAbstractItemView.InternalMove)

        model = self.model()
        model.rowsMoved.connect(self._reordered)
        self.itemChanged.connect(self._itemChanged)

        self.setContextMenuPolicy(Qt.ActionsContextMenu)

        action = QAction("Add Layer…", self)
        action.setShortcuts(QKeySequence.New)
        action.triggered.connect(self._addLayer)
        self.addAction(action)

        action = QAction("Change &Name", self)
        action.setShortcuts(QKeySequence('n'))
        action.triggered.connect(lambda : self.editItem(self.currentItem()))
        self.addAction(action)

        action = QAction("Change &Color", self)
        action.setShortcuts(QKeySequence('c'))
        action.triggered.connect(self._changeColor)
        self.addAction(action)

        action = QAction("Reset Color to &Default", self)
        action.setShortcuts(QKeySequence('d'))
        action.triggered.connect(self._resetColor)
        self.addAction(action)

        action = QAction("Delete", self)
        action.setShortcuts(QKeySequence.Delete)
        action.triggered.connect(self._deleteLayer)
        self.addAction(action)

        self._layerSet.addObserver(self, '_update', 'LayerSet.Changed')

        self._update()

    def _update(self, *args):
        index = self.currentRow()
        while self.count():
            self.takeItem(self.count()-1)
        for i, layer in enumerate(self._layerSet):
            item = self._makeItem(layer)
            self.addItem(item)
            if i == index:
                self.setCurrentItem(item)

    def _makeItem(self, layer):
        isDefault = layer is self._layerSet.defaultLayer
        name = layer.name
        color = layer.color
        item = QListWidgetItem()
        item.setText(name)
        if color:
            pixmap = QPixmap(100, 100)
            # change color
            pixmap.fill(QColor.fromRgbF(*color))
            icon = QIcon(pixmap)
        else:
            icon = QIcon(":/resources/defaultColor.svg")
        item.setIcon(icon)

        if isDefault:
            font = item.font()
            font.setBold(True)
            item.setFont(font)

        item.setFlags(item.flags() | Qt.ItemIsEditable)

        return item;

    def _getCurrentLayer(self):
        item = self.currentItem()
        if not item:
            return
        name = item.text()
        return self._layerSet[name] if name in self._layerSet else None

    def _deleteLayer(self):
        layer = self._getCurrentLayer()
        if not layer:
            return

        if layer is self._layerSet.defaultLayer:
            # because I think we can't handle a font without a default layer
            # TODO: try this
            return
        del self._layerSet[layer.name];

    def _reordered(self, *args):
        # get a new layer order
        newOrder = [self.item(index).text() for index in range(self.count())]
        self._layerSet.layerOrder = newOrder

    def _itemChanged(self, item):
        index = self.indexFromItem(item).row()
        layerName = self._layerSet.layerOrder[index]
        self._layerSet[layerName].name = item.text()

    def _addLayer(self):
        newLayerName, ok = AddLayerDialog.getNewLayerName(self)
        if ok:
            # this should cause self._layerSetLayerAdded to be executed
            self._layerSet.newLayer(newLayerName)

    def _changeColor(self):
        layer = self._getCurrentLayer()
        if not layer:
            return

        startColor = layer.color and QColor.fromRgbF(*layer.color) or QColor('limegreen')
        qcolor = QColorDialog.getColor(startColor, self, options=QColorDialog.ShowAlphaChannel)
        if not qcolor.isValid():
            # cancelled
            return
        layer.color = qcolor.getRgbF()

    def _resetColor(self):
        layer = self._getCurrentLayer()
        if not layer:
            return
        layer.color = None
