from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtGui import QIcon, QColor, QPixmap, QKeySequence
from PyQt5.QtWidgets import (
    QMainWindow, QMenu, QToolBar, QWidget, QComboBox,
    QActionGroup, QApplication, QColorDialog, QSizePolicy)

from defconQt.addLayerDialog import AddLayerDialog
from defconQt.displayStyleSettings import DisplayStyleSettings
from defconQt.glyphView import GlyphView
from defconQt.gotoDialog import GotoDialog
from functools import partial

class MainGfxWindow(QMainWindow):

    def __init__(self, glyph, parent=None):
        super(MainGfxWindow, self).__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setAttribute(Qt.WA_KeyCompression)

        self.view = None

        self._layerSet = layerSet = glyph.layerSet

        self._layerSetNotifications = []

        layerSet.addObserver(self, '_layerSetLayerAdded',
                             'LayerSet.LayerAdded')
        layerSet.addObserver(self, '_layerSetLayerDeleted',
                             'LayerSet.LayerDeleted')
        self._layerSetNotifications.append('LayerSet.LayerAdded')
        self._layerSetNotifications.append('LayerSet.LayerDeleted')

        for event in ('LayerSet.LayerChanged', 'LayerSet.DefaultLayerChanged',
                      'LayerSet.LayerOrderChanged'):
            self._layerSetNotifications.append(event)
            layerSet.addObserver(self, '_layerSetEvents', event)

        menuBar = self.menuBar()

        fileMenu = QMenu("&File", self)
        fileMenu.addAction("E&xit", self.close, QKeySequence.Quit)
        menuBar.addMenu(fileMenu)

        glyphMenu = QMenu("&Glyph", self)
        glyphMenu.addAction("&Next Glyph",
                            lambda: self._glyphOffset(1), "Ctrl+)")
        glyphMenu.addAction("&Previous Glyph",
                            lambda: self._glyphOffset(-1), "Ctrl+(")
        glyphMenu.addAction("&Go To…", self.changeGlyph, "G")
        glyphMenu.addAction("&Layer Actions…",
                            self._redirect('view', 'layerActions'), "L")
        menuBar.addMenu(glyphMenu)

        self._displaySettings = DisplayStyleSettings(
            "&Display", self, self._displayChanged)
        menuBar.addMenu(self._displaySettings.menuWidget)

        self._toolBar = toolBar = QToolBar(self)
        toolBar.setMovable(False)
        toolBar.setContentsMargins(2, 0, 2, 0)
        selectionToolButton = toolBar.addAction(
            "Selection", self._redirect('view', 'setSceneSelection'))
        selectionToolButton.setCheckable(True)
        selectionToolButton.setChecked(True)
        selectionToolButton.setIcon(QIcon(":/resources/cursor.svg"))
        penToolButton = toolBar.addAction(
            "Pen", self._redirect('view', 'setSceneDrawing'))
        penToolButton.setCheckable(True)
        penToolButton.setIcon(QIcon(":/resources/curve.svg"))
        rulerToolButton = toolBar.addAction(
            "Ruler", self._redirect('view', 'setSceneRuler'))
        rulerToolButton.setCheckable(True)
        rulerToolButton.setIcon(QIcon(":/resources/ruler.svg"))
        knifeToolButton = toolBar.addAction(
            "Knife", self._redirect('view', 'setSceneKnife'))
        knifeToolButton.setCheckable(True)
        knifeToolButton.setIcon(QIcon(":/resources/cut.svg"))

        # http://www.setnode.com/blog/right-aligning-a-button-in-a-qtoolbar/
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        toolBar.addWidget(spacer)
        self._currentLayerBox = QComboBox(self)
        self._currentLayerBox.currentIndexChanged.connect(
            self._changeLayerHandler)
        toolBar.addWidget(self._currentLayerBox)

        self._layerColorButton = toolBar.addAction(
            "Layer Color (shift + click to remove the color)",
            self._chooseLayerColor)

        toolsGroup = QActionGroup(self)
        toolsGroup.addAction(selectionToolButton)
        toolsGroup.addAction(penToolButton)
        toolsGroup.addAction(rulerToolButton)
        toolsGroup.addAction(knifeToolButton)
        self.addToolBar(toolBar)

        for layer in self._layerSet:
            self._listenToLayer(layer)

        self._changeGlyph(glyph)
        self._updateComboBox()

        self.setWindowTitle(glyph.name, glyph.getParent())
        self.adjustSize()

    def _changeGlyph(self, glyph):
        oldView = self.view
        # Preserve the selected layer (by setting the glyph from that layer)
        # Todo: If that layer is already in the glyph, it would be a little bit
        # harder to create it here and may be better or worse. Worse because
        # we'd alter the data without being explicitly asked to do so.
        # Ask someone who does UX.
        if oldView:
            if (oldView.layer is not glyph.layer and
                    glyph.name in oldView.layer):
                glyph = oldView.layer[glyph.name]
            oldView.hide()
            oldView.deleteLater()

        self.view = GlyphView(glyph, self._displaySettings, self)
        # Preserve the zoom level of the oldView.
        # TODO: is there more state that we need to carry over to the next
        # GlyphView? If yes, we should make an interface for a
        # predecessor -> successor transformation
        if oldView:
            self.view._currentTool = oldView._currentTool
            self.view.setTransform(oldView.transform())

        self._setlayerColorButtonColor()

        app = QApplication.instance()
        app.setCurrentGlyph(glyph)
        self.setWindowTitle(glyph.name, glyph.getParent())

        # switch
        self.setCentralWidget(self.view)

    def _glyphOffset(self, offset):
        if not self.view:
            return
        currentGlyph = self.view._glyph
        font = currentGlyph.getParent()
        # should be enforced in fontView already
        if not (font.glyphOrder and len(font.glyphOrder)):
            return
        index = font.glyphOrder.index(currentGlyph.name)
        newIndex = (index + offset) % len(font.glyphOrder)
        glyph = font[font.glyphOrder[newIndex]]
        self._changeGlyph(glyph)

    def _executeRemoteCommand(self, targetName, commandName, *args, **kwds):
        """
        Execute a method named `commandName` on the attribute named
        `targetName`.
        This strongly suggest that there is always a known interface at
        self.{targetName}
        See MainGfxWindow._redirect
        """
        target = getattr(self, targetName)
        command = getattr(target, commandName)
        command(*args, **kwds)

    def _redirect(self, target, command):
        """
        This creates an indirection to permanently connect an event to a
        property that may (will) change its identity.
        """
        return partial(self._executeRemoteCommand, target, command)

    def _layerSetEvents(self, notification):
        layerSet = notification.object
        assert layerSet is self._layerSet
        self._updateComboBox()

    def _layerSetLayerDeleted(self, notification):
        self._layerSetEvents(notification)
        self._changeLayerHandler(0)

    def _layerSetLayerAdded(self, notification):
        self._layerSetEvents(notification)
        layerName = notification.data['name']
        layer = self._layerSet[layerName]
        self.view.layerAdded(layer)
        self._listenToLayer(layer)

    def _listenToLayer(self, layer, remove=False):
        if remove:
            layer.removeObserver(self, 'Layer.ColorChanged')
        else:
            layer.addObserver(self, '_layerColorChange', 'Layer.ColorChanged')

    def _chooseLayerColor(self):
        if QApplication.keyboardModifiers() & Qt.ShiftModifier:
            # reset to default color, i.e. delete the layer color
            color = None
        else:
            startColor = self.view.getLayerColor() or QColor('limegreen')
            qColor = QColorDialog.getColor(
                startColor, self, options=QColorDialog.ShowAlphaChannel)
            if not qColor.isValid():
                # cancelled
                return
            color = qColor.getRgbF()
        # will trigger Layer.ColorChanged
        self.view.layer.color = color

    def _layerColorChange(self, notification):
        layer = notification.object
        if layer is self.view.layer:
            self._setlayerColorButtonColor()

    def _setlayerColorButtonColor(self):
        color = self.view.getLayerColor()
        if color is None:
            icon = QIcon(":/resources/defaultColor.svg")
        else:
            # set the layer color to the button
            pixmap = QPixmap(100, 100)
            pixmap.fill(color)
            icon = QIcon(pixmap)
        self._layerColorButton.setIcon(icon)

    def _updateComboBox(self):
        comboBox = self._currentLayerBox
        comboBox.blockSignals(True)
        comboBox.clear()
        for layer in self._layerSet:
            comboBox.addItem(layer.name, layer)
            if layer == self.view.layer:
                comboBox.setCurrentText(layer.name)
                continue
        comboBox.addItem("New layer...", None)
        comboBox.blockSignals(False)

    def _setComboboxIndex(self, index):
        comboBox = self._currentLayerBox
        comboBox.blockSignals(True)
        comboBox.setCurrentIndex(index)
        comboBox.blockSignals(False)

    def _makeNewLayerViaDialog(self):
        newLayerName, ok = AddLayerDialog.getNewLayerName(self)
        if ok:
            # this should cause self._layerSetLayerAdded to be executed
            self._layerSet.newLayer(newLayerName)
            return self._layerSet[newLayerName]
        else:
            return None

    def _changeLayerHandler(self, newLayerIndex):
        comboBox = self._currentLayerBox
        layer = comboBox.itemData(newLayerIndex)
        if layer is None:
            layer = self._makeNewLayerViaDialog()
            if layer is None:
                # restore comboBox to active index
                index = self._layerSet.layerOrder.index(self.view.layer.name)
                self._setComboboxIndex(index)
                return

        self.view.changeCurrentLayer(layer)
        self._updateComboBox()
        self._setlayerColorButtonColor()

        app = QApplication.instance()
        # setting the layer-glyph here
        app.setCurrentGlyph(self.view._glyph)

    def changeGlyph(self):
        glyph = self.view._glyph
        newGlyph, ok = GotoDialog.getNewGlyph(self, glyph)
        if ok and newGlyph is not None:
            self._changeGlyph(newGlyph)
            self._updateComboBox()

    def _displayChanged(self, *args):
        # redraw the view
        self.view.redraw()

    def event(self, event):
        if event.type() == QEvent.WindowActivate:
            app = QApplication.instance()
            app.setCurrentGlyph(self.view._glyph)
        return super(MainGfxWindow, self).event(event)

    def closeEvent(self, event):
        for name in self._layerSetNotifications:
            self._layerSet.removeObserver(self, name)

        for layer in self._layerSet:
            self._listenToLayer(layer, remove=True)

        self.view = None

        event.accept()

    def setWindowTitle(self, title, font=None):
        if font is not None:
            title = "%s – %s %s" % (
                title, font.info.familyName, font.info.styleName)
        super(MainGfxWindow, self).setWindowTitle(title)
