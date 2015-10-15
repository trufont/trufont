from enum import Enum
from math import copysign
from functools import partial
import pickle
from defcon import Anchor, Component
from defconQt import icons_db
from defconQt.objects.defcon import TContour, TGlyph
from defconQt.pens.copySelectionPen import CopySelectionPen
from defconQt.util import platformSpecific
from fontTools.misc import bezierTools
from PyQt5.QtCore import *#QFile, QLineF, QObject, QPointF, QRectF, QSize, Qt
from PyQt5.QtGui import *#QBrush, QColor, QImage, QKeySequence, QPainter, QPainterPath, QPixmap, QPen, QColorDialog
from PyQt5.QtWidgets import *#(QAction, QActionGroup, QApplication, QFileDialog,
        #QGraphicsItem, QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsPathItem, QGraphicsRectItem, QGraphicsScene, QGraphicsView,
        #QMainWindow, QMenu, QMessageBox, QStyle, QStyleOptionGraphicsItem, QWidget)

class GotoDialog(QDialog):
    alphabetical = [
        dict(type="alphabetical", allowPseudoUnicode=True)
    ]

    def __init__(self, currentGlyph, parent=None):
        super(GotoDialog, self).__init__(parent)
        self.setWindowModality(Qt.WindowModal)
        self.setWindowTitle("Go to…")
        self.font = currentGlyph.getParent()
        self._sortedGlyphs = self.font.unicodeData.sortGlyphNames(self.font.keys(), self.alphabetical)

        layout = QGridLayout(self)
        self.glyphLabel = QLabel("Glyph:", self)
        self.glyphEdit = QLineEdit(self)
        self.glyphEdit.textChanged.connect(self.updateGlyphList)
        self.glyphEdit.event = self.lineEvent
        self.glyphEdit.keyPressEvent = self.lineKeyPressEvent

        self.beginsWithBox = QRadioButton("Begins with", self)
        self.containsBox = QRadioButton("Contains", self)
        self.beginsWithBox.setChecked(True)
        self.beginsWithBox.toggled.connect(self.updateGlyphList)

        self.glyphList = QListWidget(self)
        self.glyphList.itemDoubleClicked.connect(self.accept)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        l = 0
        layout.addWidget(self.glyphLabel, l, 0, 1, 2)
        layout.addWidget(self.glyphEdit, l, 2, 1, 4)
        l += 1
        layout.addWidget(self.beginsWithBox, l, 0, 1, 3)
        layout.addWidget(self.containsBox, l, 3, 1, 3)
        l += 1
        layout.addWidget(self.glyphList, l, 0, 1, 6)
        l += 1
        layout.addWidget(buttonBox, l, 0, 1, 6)
        self.setLayout(layout)
        self.updateGlyphList(True)

    def lineEvent(self, event):
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Tab:
            if self.beginsWithBox.isChecked():
                self.containsBox.toggle()
            else:
                self.beginsWithBox.toggle()
            return True
        else:
            return QLineEdit.event(self.glyphEdit, event)

    def lineKeyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Up or key == Qt.Key_Down:
            self.glyphList.keyPressEvent(event)
        else:
            QLineEdit.keyPressEvent(self.glyphEdit, event)

    def updateGlyphList(self, select):
        self.glyphList.clear()
        if not self.glyphEdit.isModified():
            self.glyphList.addItems(self._sortedGlyphs)
        text = self.glyphEdit.text()
        if select:
            glyphs = [glyph for glyph in self._sortedGlyphs if glyph.startswith(text)]
        else:
            glyphs = [glyph for glyph in self._sortedGlyphs if text in glyph]
        self.glyphList.addItems(glyphs)
        if select: self.glyphList.setCurrentRow(0)

    @classmethod
    def getNewGlyph(cls, parent, currentGlyph):
        dialog = cls(currentGlyph, parent)
        result = dialog.exec_()
        currentItem = dialog.glyphList.currentItem()
        newGlyph = None
        if currentItem is not None:
            newGlyphName = currentItem.text()
            if newGlyphName in dialog.font:
                newGlyph = dialog.font[newGlyphName]
        return (newGlyph, result)

class AddAnchorDialog(QDialog):
    def __init__(self, pos=None, parent=None):
        super(AddAnchorDialog, self).__init__(parent)
        self.setWindowModality(Qt.WindowModal)
        self.setWindowTitle("Add anchor…")

        layout = QGridLayout(self)

        anchorNameLabel = QLabel("Anchor name:", self)
        self.anchorNameEdit = QLineEdit(self)
        self.anchorNameEdit.setFocus(True)
        if pos is not None:
            anchorPositionLabel = QLabel("The anchor will be added at ({}, {})."
              .format(pos.x(), pos.y()), self)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        l = 0
        layout.addWidget(anchorNameLabel, l, 0)
        layout.addWidget(self.anchorNameEdit, l, 1, 1, 3)
        l += 1
        layout.addWidget(anchorPositionLabel, l, 0, 1, 4)
        l += 1
        layout.addWidget(buttonBox, l, 3)
        self.setLayout(layout)

    @classmethod
    def getNewAnchorName(cls, parent, pos=None):
        dialog = cls(pos, parent)
        result = dialog.exec_()
        name = dialog.anchorNameEdit.text()
        return (name, result)

class AddComponentDialog(GotoDialog):
    def __init__(self, *args, **kwargs):
        super(AddComponentDialog, self).__init__(*args, **kwargs)
        self.setWindowTitle("Add component…")
        self._sortedGlyphs.remove(args[0].name)
        self.updateGlyphList(False)

class AddLayerDialog(QDialog):
    def __init__(self, parent=None):
        super(AddLayerDialog, self).__init__(parent)
        self.setWindowModality(Qt.WindowModal)
        self.setWindowTitle("Add layer…")

        layout = QGridLayout(self)

        layerNameLabel = QLabel("Layer name:", self)
        self.layerNameEdit = QLineEdit(self)
        self.layerNameEdit.setFocus(True)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        l = 0
        layout.addWidget(layerNameLabel, l, 0)
        layout.addWidget(self.layerNameEdit, l, 1)
        l += 1
        layout.addWidget(buttonBox, l, 2)
        self.setLayout(layout)

    @classmethod
    def getNewLayerName(cls, parent):
        dialog = cls(parent)
        result = dialog.exec_()
        name = dialog.layerNameEdit.text()
        return (name, result)


class GenericSettings(object):
    def __init__(self, title, parent, callback):
        #super().__init__()
        self._menuWidget = QMenu(title, parent)
        self._actions = {}
        self._callback = callback
        for key, item in self._items:
            self._addAction(key, *item)

        if(self._presets):
            self._menuWidget.addSeparator()
            for i, presets in enumerate(self._presets):
                self._addPresetAction(i, *presets)

    _items = {}
    _presets = tuple()

    @property
    def menuWidget(self):
        return self._menuWidget

    def _addAction(self, key, label, checked):
        action = self._menuWidget.addAction(label, partial(self._callback, key))
        action.setCheckable(True)
        action.setChecked(checked)
        self._actions[key] = action

    def _addPresetAction(self, index, label, presets, **args):
        self._menuWidget.addAction(label, partial(self._setPreset, index))

    def _setPreset(self, index):
        _, data = self._presets[index]
        for key, value in data.items():
            action = self._actions[key]
            action.blockSignals(True)
            action.setChecked(value)
            action.blockSignals(False)
        self._callback()

    def __setattr__(self, name, value):
        if name.startswith('_'):
            self.__dict__[name] = value
            return
        raise AttributeError('It\'s not allowed to set attributes here.', name)

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        if name not in self._actions:
            raise AttributeError(name)
        return self._actions[name].isChecked()



class DisplayStyleSettings(GenericSettings):
    _presets = (
        ('TruFont Default', dict(
            activeLayerOnTop = True
          , activeLayerFilled = True
          , otherLayersFilled = False
          , activeLayerUseLayerColor = False
          , otherLayerUseLayerColor = True
          , drawOtherLayers = True
        ))
      , ('Layer Fonts', dict(
            activeLayerOnTop = False
          , activeLayerFilled = True
          , otherLayersFilled = True
          , activeLayerUseLayerColor = True
          , otherLayerUseLayerColor = True
          , drawOtherLayers = True
        ))
    )

    _items = (
        ('activeLayerOnTop', ('Active Layer on Top', True))
      , ('activeLayerFilled', ('Active Layer Filled', True))
      , ('activeLayerUseLayerColor', ('Active Layer use Custom Color', False))
      , ('otherLayersFilled', ('Other Layers Filled', False))
      , ('otherLayerUseLayerColor', ('Other Layers use Custom Color', True))
      , ('drawOtherLayers', ('Show Other Layers', True))
    )


class MainGfxWindow(QMainWindow):
    def __init__(self, glyph, parent=None):
        super(MainGfxWindow, self).__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setAttribute(Qt.WA_KeyCompression)

        self.view = None

        self._layerSet = layerSet = glyph.layerSet

        self._layerSetNotifications = []

        layerSet.addObserver(self, '_layerSetLayerAdded', 'LayerSet.LayerAdded')
        layerSet.addObserver(self, '_layerSetLayerDeleted', 'LayerSet.LayerDeleted')
        self._layerSetNotifications.append('LayerSet.LayerAdded')
        self._layerSetNotifications.append('LayerSet.LayerDeleted')


        for event in ('LayerSet.LayerChanged', 'LayerSet.DefaultLayerChanged'
                                            , 'LayerSet.LayerOrderChanged'):
            self._layerSetNotifications.append(event)
            layerSet.addObserver(self, '_layerSetEvents',  event)



        menuBar = self.menuBar()

        fileMenu = QMenu("&File", self)
        fileMenu.addAction("E&xit", self.close, QKeySequence.Quit)
        menuBar.addMenu(fileMenu)

        glyphMenu = QMenu("&Glyph", self)
        glyphMenu.addAction("&Jump", self.changeGlyph, "J")
        menuBar.addMenu(glyphMenu)


        self._displaySettings = DisplayStyleSettings("&Display", self, self._displayChanged)
        menuBar.addMenu(self._displaySettings.menuWidget)

        self._toolBar = toolBar = QToolBar(self)
        toolBar.setMovable(False)
        toolBar.setContentsMargins(2, 0, 2, 0)
        selectionToolButton = toolBar.addAction("Selection", self._redirect('view', 'setSceneSelection'))
        selectionToolButton.setCheckable(True)
        selectionToolButton.setChecked(True)
        selectionToolButton.setIcon(QIcon(":/resources/cursor.svg"))
        penToolButton = toolBar.addAction("Pen", self._redirect('view', 'setSceneDrawing'))
        penToolButton.setCheckable(True)
        penToolButton.setIcon(QIcon(":/resources/curve.svg"))
        rulerToolButton = toolBar.addAction("Ruler", self._redirect('view', 'setSceneRuler'))
        rulerToolButton.setCheckable(True)
        rulerToolButton.setIcon(QIcon(":/resources/ruler.svg"))
        knifeToolButton = toolBar.addAction("Knife", self._redirect('view', 'setSceneKnife'))
        knifeToolButton.setCheckable(True)
        knifeToolButton.setIcon(QIcon(":/resources/cut.svg"))

        # http://www.setnode.com/blog/right-aligning-a-button-in-a-qtoolbar/
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        toolBar.addWidget(spacer)
        self._currentLayerBox = QComboBox(self)
        self._currentLayerBox.currentIndexChanged.connect(self._changeLayerHandler)
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

        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        createAnchorAction = QAction("Add Anchor…", self)
        createAnchorAction.triggered.connect(self._redirect('view', 'createAnchor'))
        self.addAction(createAnchorAction)
        createComponentAction = QAction("Add Component…", self)
        createComponentAction.triggered.connect(self._redirect('view', 'createComponent'))
        self.addAction(createComponentAction)

        for layer in self._layerSet:
            self._listenToLayer(layer)

        self._changeGlyph(glyph)
        self._updateComboBox()

        self.setWindowTitle(glyph.name, glyph.getParent())
        self.adjustSize()

    def _changeGlyph(self, glyph):
        oldView = self.view
        if oldView:
            # Preserve the selected layer (by setting the glyph from that layer)
            # Todo: If that layer is already in the glyph, it would be a little bit
            # harder to create it here and may be better or worse. Worse becaue
            # we'd alter the data without being explicitly asked to do so.
            # Ask someone who does UX.
            if oldView.layer is not glyph.layer and glyph.name in oldView.layer:
                glyph = oldView.layer[glyph.name]
            oldView.hide()
            oldView.deleteLater()

        self.view = GlyphView(glyph, self._displaySettings, self)
        # Preserve the zoom level of the oldView.
        # TODO: is there more state that we need to carry over to the next
        # GlyphView? If yes, we should make an interface for a
        # predecessor -> successor transformation
        if oldView:
            self.view.setTransform(oldView.transform())

        self._setlayerColorButtonColor()

        app = QApplication.instance()
        app.setCurrentGlyph(glyph)
        self.setWindowTitle(glyph.name, glyph.getParent())

        # switch
        self.setCentralWidget(self.view)

    def _executeRemoteCommand(self, targetName, commandName, *args, **kwds):
        """
        Execute a method named `commandName` on the attribute named `targetName`.
        This strongly suggest that there is always a known interface at self.{targetName}
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
            qColor = QColorDialog.getColor(startColor, self, options=QColorDialog.ShowAlphaChannel)
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
        if font is not None: title = "%s – %s %s" % (title, font.info.familyName, font.info.styleName)
        super(MainGfxWindow, self).setWindowTitle(title)

def roundPosition(value):
    value = value * 10#self._scale
    value = round(value) - .5
    value = value * .1#self._inverseScale
    return value

offCurvePointSize = 8#5
onCurvePointSize = 9#6
onCurveSmoothPointSize = 10#7
offWidth = offHeight = roundPosition(offCurvePointSize)# * self._inverseScale)
offHalf = offWidth / 2.0
onWidth = onHeight = roundPosition(onCurvePointSize)# * self._inverseScale)
onHalf = onWidth / 2.0
smoothWidth = smoothHeight = roundPosition(onCurveSmoothPointSize)# * self._inverseScale)
smoothHalf = smoothWidth / 2.0
onCurvePenWidth = 1.5
offCurvePenWidth = 1.0

anchorSize = 11
anchorWidth = anchorHeight = roundPosition(anchorSize)
anchorHalf = anchorWidth / 2.0

bezierHandleColor = QColor.fromRgbF(0, 0, 0, .2)
startPointColor = QColor.fromRgbF(0, 0, 0, .2)
backgroundColor = Qt.white
offCurvePointColor = QColor.fromRgbF(1, 1, 1, 1)
offCurvePointStrokeColor = QColor.fromRgbF(.6, .6, .6, 1)
onCurvePointColor = offCurvePointStrokeColor
onCurvePointStrokeColor = offCurvePointColor
anchorColor = QColor(120, 120, 255)
anchorSelectionColor = Qt.blue
bluesColor = QColor.fromRgbF(.5, .7, 1, .3)
fillColor = QColor(200, 200, 200, 120)#QColor.fromRgbF(0, 0, 0, .4)
componentFillColor = QColor.fromRgbF(0, 0, 0, .4)#QColor.fromRgbF(.2, .2, .3, .4)
metricsColor = QColor(70, 70, 70)
pointSelectionColor = Qt.red

class SceneTools(Enum):
    SelectionTool = 0
    DrawingTool = 1
    RulerTool = 2
    KnifeTool = 3

class HandleLineItem(QGraphicsLineItem):
    def __init__(self, x1, y1, x2, y2, parent):
        super(HandleLineItem, self).__init__(x1, y1, x2, y2, parent)
        self.setPen(QPen(bezierHandleColor, 1.0))
        self.setFlag(QGraphicsItem.ItemStacksBehindParent)

class OffCurvePointItem(QGraphicsEllipseItem):
    def __init__(self, x, y, parent=None):
        super(OffCurvePointItem, self).__init__(parent)
        # since we have a parent, setPos must be relative to it
        self.setPointPath()
        self.setPos(x, y) # TODO: abstract and use pointX-self.parent().pos().x()
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setFlag(QGraphicsItem.ItemStacksBehindParent)

        self.setBrush(QBrush(offCurvePointColor))
        self._needsUngrab = False

    def delete(self):
        self.parentItem()._CPDeleted()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            if self.scene()._integerPlane:
                value.setX(round(value.x()))
                value.setY(round(value.y()))
            if QApplication.keyboardModifiers() & Qt.ShiftModifier \
                  and len(self.scene().selectedItems()) == 1:
                ax = abs(value.x())
                ay = abs(value.y())
                if ay >= ax * 2:
                    value.setX(0)
                elif ay > ax / 2:
                    avg = (ax + ay) / 2
                    value.setX(copysign(avg, value.x()))
                    value.setY(copysign(avg, value.y()))
                else:
                    value.setY(0)
        elif change == QGraphicsItem.ItemPositionHasChanged:
            self.parentItem()._CPMoved(value)
        # TODO: consider what to do w offCurves
        #elif change == QGraphicsItem.ItemSelectedHasChanged:
        #    pass#self.parentItem()._CPSelChanged(value)
        return value

    def mousePressEvent(self, event):
        if not self._needsUngrab and self.x() == 0 and self.y() == 0:
            event.ignore()
        super(OffCurvePointItem, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super(OffCurvePointItem, self).mouseReleaseEvent(event)
        if self._needsUngrab:
            self.ungrabMouse()
            self._needsUngrab = False

    # http://www.qtfr.org/viewtopic.php?pid=21045#p21045
    def paint(self, painter, option, widget):
        #if self.x() == 0 and self.y() == 0: return
        newOption = QStyleOptionGraphicsItem(option)
        newOption.state = QStyle.State_None
        pen = self.pen()
        if option.state & QStyle.State_Selected:
            pen.setColor(pointSelectionColor)
        else:
            pen.setColor(offCurvePointStrokeColor)
        self.setPen(pen)
        super(OffCurvePointItem, self).paint(painter, newOption, widget)

    def setPointPath(self, scale=None):
        if scale is None:
            scene = self.scene()
            if scene is not None:
                scale = scene.getViewScale()
            else:
                scale = 1
        if scale > 4: scale = 4
        elif scale < .4: scale = .4
        self.prepareGeometryChange()
        self.setRect(-offHalf/scale, -offHalf/scale, offWidth/scale, offHeight/scale)
        self.setPen(QPen(offCurvePointStrokeColor, offCurvePenWidth/scale))

class OnCurvePointItem(QGraphicsPathItem):
    def __init__(self, x, y, isSmooth, contour, point, scale=1, parent=None):
        super(OnCurvePointItem, self).__init__(parent)
        self._contour = contour
        self._point = point
        self._isSmooth = isSmooth
        self._posBeforeMove = None

        self.setPointPath(scale)
        self.setPos(x, y)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setBrush(QBrush(onCurvePointColor))

    def delete(self, preserveShape=True):
        def findNextOnCurve(self, index=0):
            for _ in self._contour:
                if self._contour[index].segmentType is not None:
                    break
                index = (index+1) % len(self._contour)
            return index

        scene = self.scene()
        glyph = scene._glyphObject
        if len(self._contour.segments) < 2:
            glyph.removeContour(self._contour)
        else:
            ptIndex = self.getPointIndex()
            if self._contour.open and ptIndex == 0:
                nextOnCurveIndex = findNextOnCurve(self, 1)
                self._contour._points = self._contour[nextOnCurveIndex:]
                self._contour[0].segmentType = "move"
                self._contour.dirty = True
            else:
                # Using preserveShape at the edge of an open contour will traceback
                if ptIndex == len(self._contour): preserveShape = False
                self._contour.removeSegment(self.getSegmentIndex(), preserveShape)
                nextOnCurveIndex = findNextOnCurve(self)
                self._contour.setStartPoint(nextOnCurveIndex)
        # This object will be removed from scene by notification mechanism

    def setPointPath(self, scale=None):
        path = QPainterPath()
        if scale is None:
            scene = self.scene()
            if scene is not None:
                scale = scene.getViewScale()
            else:
                scale = 1
        if scale > 4: scale = 4
        elif scale < .4: scale = .4
        if self._isSmooth:
            path.addEllipse(-smoothHalf/scale, -smoothHalf/scale, smoothWidth/scale, smoothHeight/scale)
        else:
            path.addRect(-onHalf/scale, -onHalf/scale, onWidth/scale, onHeight/scale)
        self.prepareGeometryChange()
        self.setPath(path)
        self.setPen(QPen(onCurvePointStrokeColor, onCurvePenWidth/scale))

    def getPointIndex(self):
        return self._contour.index(self._point)

    def getSegmentIndex(self):
        # closed contour cycles and so the "previous" segment goes to current point
        index = 0 if self._contour.open else -1
        for pt in self._contour:
            if pt == self._point: break
            if pt.segmentType is not None: index += 1
        return index % len(self._contour.segments)

    def _CPDeleted(self):
        pointIndex = self.getPointIndex()
        children = self.childItems()
        selected = 1
        if not (children[1].isVisible() and children[1].isSelected()):
            selected = 3

        firstSibling = self._contour[pointIndex+selected-2]
        secondSibling = self._contour[pointIndex+(selected-2)*2]
        if firstSibling.segmentType is None and secondSibling.segmentType is None:
            # we have two offCurves, wipe them
            self._contour.removePoint(firstSibling)
            self._contour.removePoint(secondSibling)

    def _CPMoved(self, newValue):
        pointIndex = self.getPointIndex()
        children = self.childItems()
        # nodes are stored after lines (for stacking order)
        if children[1].isSelected():
            selected = 1
            propagate = 3
        else:
            selected = 3
            propagate = 1
        curValue = children[selected].pos()
        line = children[selected-1].line()
        children[selected-1].setLine(line.x1(), line.y1(), newValue.x(), newValue.y())

        if not len(children) > 4:
            elemIndex = pointIndex-2+selected
            self._contour[elemIndex].x = self.pos().x()+newValue.x()
            self._contour[elemIndex].y = self.pos().y()+newValue.y()
        if not (self._isSmooth and children[propagate].isVisible()):
            self.setShallowDirty()
            return
        if children[selected]._needsUngrab:
            targetLen = children[selected-1].line().length()*2
        else:
            targetLen = children[selected-1].line().length()+children[propagate-1].line().length()
        if not newValue.isNull():
            tmpLine = QLineF(newValue, QPointF())
            tmpLine.setLength(targetLen)
        else:
            # if newValue is null, we’d construct a zero-length line and collapse
            # both offCurves
            tmpLine = QLineF(QPointF(), children[propagate].pos())
        children[propagate].setFlag(QGraphicsItem.ItemSendsGeometryChanges, False)
        children[propagate].setPos(tmpLine.x2(), tmpLine.y2())
        children[propagate].setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        children[propagate-1].setLine(line.x1(), line.y1(), tmpLine.x2(), tmpLine.y2())
        propagateInContour = pointIndex-2+propagate
        self._contour[propagateInContour].x = self.pos().x()+tmpLine.x2()
        self._contour[propagateInContour].y = self.pos().y()+tmpLine.y2()
        self.setShallowDirty()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            if self.scene()._integerPlane:
                value.setX(round(value.x()))
                value.setY(round(value.y()))
        elif change == QGraphicsItem.ItemPositionHasChanged:
            # have a look at defcon FuzzyNumber as well
            pointIndex = self.getPointIndex()
            self._contour[pointIndex].x = self.pos().x()
            self._contour[pointIndex].y = self.pos().y()

            children = self.childItems()
            if children[1].isVisible():
                prevPos = children[1].pos()
                self._contour[pointIndex-1].x = self.pos().x()+prevPos.x()
                self._contour[pointIndex-1].y = self.pos().y()+prevPos.y()
            if children[3].isVisible():
                nextPos = children[3].pos()
                self._contour[pointIndex+1].x = self.pos().x()+nextPos.x()
                self._contour[pointIndex+1].y = self.pos().y()+nextPos.y()
            self.setShallowDirty()
        elif change == QGraphicsItem.ItemSelectedHasChanged:
            self._point.selected = value
        return value

    def setShallowDirty(self):
        scene = self.scene()
        scene._blocked = True
        self._contour.dirty = True
        scene._blocked = False

    def mouseMoveEvent(self, event):
        modifiers = event.modifiers()
        children = self.childItems()
        # Ctrl: get and move prevCP, Alt: nextCP
        if modifiers & Qt.ControlModifier and children[1].x() == 0 and children[1].y() == 0:
            i, o = 1, 3
        elif modifiers & Qt.AltModifier and children[3].x() == 0 and children[3].y() == 0:
            i, o = 3, 1
        elif not (modifiers & Qt.ControlModifier or modifiers & Qt.AltModifier):
            super(OnCurvePointItem, self).mouseMoveEvent(event)
            return
        else: # eat the event if we are not going to yield an offCP
            event.accept()
            return
        ptIndex = self.getPointIndex()
        scene = self.scene()
        scene._blocked = True
        # if we have line segment, insert offCurve points
        insertIndex = (ptIndex+(i-1)//2) % len(self._contour)
        if self._contour[insertIndex].segmentType == "line":
            nextToCP = self._contour[(ptIndex-2+i) % len(self._contour)]
            assert(nextToCP.segmentType is not None)
            self._contour[insertIndex].segmentType = "curve"
            if i == 1:
                first, second = (self._point.x, self._point.y), (nextToCP.x, nextToCP.y)
            else:
                first, second = (nextToCP.x, nextToCP.y), (self._point.x, self._point.y)
            self._contour.insertPoint(insertIndex, self._contour._pointClass(first))
            self._contour.insertPoint(insertIndex, self._contour._pointClass(second))
            children[i].setVisible(True)
            # TODO: need a list of items to make this efficient
            scene.getItemForPoint(nextToCP).childItems()[o].setVisible(True)
        # release current onCurve
        scene.sendEvent(self, QEvent(QEvent.MouseButtonRelease))
        scene.mouseGrabberItem().ungrabMouse()
        self.setSelected(False)
        self.setIsSmooth(False)
        children[i]._needsUngrab = True
        scene.sendEvent(children[i], QEvent(QEvent.MouseButtonPress))
        children[i].setSelected(True)
        children[i].grabMouse()
        scene._blocked = False
        event.accept()

    def mouseDoubleClickEvent(self, event):
        view = self.scene().views()[0] # XXX: meh, maybe refactor doubleClick event into the scene?
        if view._currentTool == SceneTools.RulerTool or view._currentTool == SceneTools.KnifeTool:
            return
        self.setIsSmooth(not self._isSmooth)

    def setIsSmooth(self, isSmooth):
        self._isSmooth = isSmooth
        self._point.smooth = self._isSmooth
        self.setShallowDirty()
        self.setPointPath()

    # http://www.qtfr.org/viewtopic.php?pid=21045#p21045
    def paint(self, painter, option, widget):
        newOption = QStyleOptionGraphicsItem(option)
        newOption.state = QStyle.State_None
        pen = self.pen()
        if option.state & QStyle.State_Selected:
            pen.setColor(pointSelectionColor)
        else:
            pen.setColor(onCurvePointStrokeColor)
        self.setPen(pen)
        super(OnCurvePointItem, self).paint(painter, newOption, widget)

class AnchorItem(QGraphicsPathItem):
    def __init__(self, anchor, scale=1, parent=None):
        super(AnchorItem, self).__init__(parent)
        self._anchor = anchor

        textItem = QGraphicsSimpleTextItem(self._anchor.name, parent=self)
        font = QFont()
        font.setPointSize(9)
        textItem.setFont(font)
        textItem.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        self.setPointPath(scale)
        self.setPos(self._anchor.x, self._anchor.y)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setBrush(QBrush(anchorColor))
        self.setPen(QPen(Qt.NoPen))

    def delete(self):
        glyph = self._anchor.getParent()
        glyph.removeAnchor(self._anchor)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            if self.scene()._integerPlane:
                value.setX(round(value.x()))
                value.setY(round(value.y()))
        elif change == QGraphicsItem.ItemPositionHasChanged:
            x = self.pos().x()
            y = self.pos().y()
            scene = self.scene()
            scene._blocked = True
            self._anchor.x = x
            self._anchor.y = y
            scene._blocked = False
        return value

    def setPointPath(self, scale=None):
        path = QPainterPath()
        if scale is None:
            scene = self.scene()
            if scene is not None:
                scale = scene.getViewScale()
            else:
                scale = 1
        if scale > 4: scale = 4
        elif scale < .4: scale = .4

        path.moveTo(-anchorHalf/scale, 0)
        path.lineTo(0, anchorHalf/scale)
        path.lineTo(anchorHalf/scale, 0)
        path.lineTo(0, -anchorHalf/scale)
        path.closeSubpath()

        self.prepareGeometryChange()
        self.setPath(path)
        textItem = self.childItems()[0]
        textItem.setPos(anchorHalf/scale, textItem.boundingRect().height()/2)

    # http://www.qtfr.org/viewtopic.php?pid=21045#p21045
    def paint(self, painter, option, widget):
        newOption = QStyleOptionGraphicsItem(option)
        newOption.state = QStyle.State_None
        pen = self.pen()
        if option.state & QStyle.State_Selected:
            self.setBrush(anchorSelectionColor)
        else:
            self.setBrush(anchorColor)
        super(AnchorItem, self).paint(painter, newOption, widget)

class ComponentItem(QGraphicsPathItem):
    def __init__(self, path, component, parent=None):
        super(ComponentItem, self).__init__(path, parent)
        self._component = component
        self.setTransform(QTransform(*component.transformation))
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)

    def delete(self):
        glyph = self._component.getParent()
        glyph.removeComponent(self._component)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            if self.scene()._integerPlane:
                value.setX(round(value.x()))
                value.setY(round(value.y()))
        elif change == QGraphicsItem.ItemPositionHasChanged:
            t = self._component.transformation
            x = self.pos().x()
            y = self.pos().y()
            scene = self.scene()
            scene._blocked = True
            self._component.transformation = (t[0], t[1], t[2], t[3], x, y)
            scene._blocked = False
        return value

class VGuidelinesTextItem(QGraphicsSimpleTextItem):
    def __init__(self, text, font, parent=None):
        super(VGuidelinesTextItem, self).__init__(text, parent)
        self.setBrush(metricsColor)
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        self.setFont(font)

class ResizeHandleItem(QGraphicsRectItem):
    def __init__(self, parent=None):
        super(QGraphicsRectItem, self).__init__(parent)
        self.setPointPath()
        self.setBrush(QBrush(QColor(60, 60, 60)))
        self.setPen(QPen(Qt.NoPen))
        self.setFlag(QGraphicsItem.ItemIgnoresParentOpacity)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        #self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setCursor(Qt.SizeFDiagCursor)

        rect = self.parentItem().boundingRect()
        self.setPos(rect.width(), rect.height())

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            if not value: self.setVisible(value)
        return value

    def mouseMoveEvent(self, event):
        self.parentItem()._pixmapGeometryChanged(event)

    def setPointPath(self, scale=None):
        if scale is None:
            scene = self.scene()
            if scene is not None:
                scale = scene.getViewScale()
            else:
                scale = 1
        if scale > 4: scale = 4
        self.prepareGeometryChange()
        self.setRect(-onHalf/scale, -onHalf/scale, onWidth/scale, onHeight/scale)

class PixmapItem(QGraphicsPixmapItem):
    def __init__(self, x, y, pixmap, parent=None):
        super(QGraphicsPixmapItem, self).__init__(pixmap, parent)
        self.setPos(x, y)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setTransform(QTransform().fromScale(1, -1))
        self.setOpacity(.5)
        self.setZValue(-1)

        rect = self.boundingRect()
        self._rWidth = rect.width()
        self._rHeight = rect.height()
        handle = ResizeHandleItem(self)
        handle.setVisible(False)

    def _pixmapGeometryChanged(self, event):
        modifiers = event.modifiers()
        pos = event.scenePos()
        if modifiers & Qt.ControlModifier:
            # rotate
            refLine = QLineF(self.x(), self.y(), self.x()+self._rWidth, self.y()-self._rHeight)
            curLine = QLineF(self.x(), self.y(), pos.x(), pos.y())
            self.setRotation(refLine.angleTo(curLine))
        else:
            # scale
            dy = (pos.y() - self.y()) / self._rHeight
            if modifiers & Qt.ShiftModifier:
                # keep original aspect ratio
                dx = -dy
            else:
                dx = (pos.x() - self.x()) / self._rWidth
            self.setTransform(QTransform().fromScale(dx, dy))
        event.accept()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            children = self.childItems()
            if not children[0].isUnderMouse():
                children[0].setVisible(value)
        return value

class GlyphScene(QGraphicsScene):
    def __init__(self, parent, sceneAddedItems=None):
        super(GlyphScene, self).__init__(parent)
        self._editing = False
        self._integerPlane = True
        self._cachedRuler = None
        self._rulerObject = None
        self._cachedIntersections = []
        self._knifeDots = []
        self._knifeLine = None
        self._dataForUndo = []
        self._dataForRedo = []

        # if this is an array, the Glyphview will clean up all contents
        # when redrawing the active layer
        self._sceneAddedItems = sceneAddedItems

        font = self.font()
        font.setFamily("Roboto Mono")
        font.setFixedPitch(True)
        self.setFont(font)

        self._blocked = False

    def _get_glyphObject(self):
        view = self.views()[0]
        return view._glyph

    _glyphObject = property(_get_glyphObject, doc="Get the current glyph in the view.")

    def _addRegisterItem(self, item):
        """The parent object will take care of removing these again"""
        if self._sceneAddedItems is not None:
            self._sceneAddedItems.append(item)
        self.addItem(item)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super(GlyphScene, self).dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super(GlyphScene, self).dragMoveEvent(event)

    def dropEvent(self, event):
        mimeData = event.mimeData()
        if mimeData.hasUrls():
            paths = mimeData.urls()
            # only support the drop of one image for now
            dragPix = QPixmap(paths[0].toLocalFile())
            event.setAccepted(not dragPix.isNull())
        else:
            return
        pos = event.scenePos()
        newPix = PixmapItem(pos.x(), pos.y(), dragPix)
        self._addRegisterItem(newPix)
        event.acceptProposedAction()

    def getItemForPoint(self, point):
        for item in self.items():
            if isinstance(item, OnCurvePointItem) and item._point == point:
                return item
        return None

    def getViewScale(self):
        return self.views()[0].transform().m11()

    # TODO: implement key multiplex in a set()
    # http://stackoverflow.com/a/10568233/2037879
    def keyPressEvent(self, event):
        key = event.key()
        count = event.count()
        modifiers = event.modifiers()
        # XXX: clean this up, prioritize key dispatching before processing things
        # TODO: this is not DRY w space center, put this in a function
        if modifiers & Qt.ShiftModifier:
            count *= 10
            if modifiers & Qt.ControlModifier:
                count *= 10
        if key == Qt.Key_Left:
            x,y = -count,0
        elif key == Qt.Key_Up:
            x,y = 0,count
        elif key == Qt.Key_Right:
            x,y = count,0
        elif key == Qt.Key_Down:
            x,y = 0,-count
        elif key == platformSpecific.deleteKey:
            self._blocked = True
            for item in self.selectedItems():
                if isinstance(item, OnCurvePointItem):
                    item.delete(not event.modifiers() & Qt.ShiftModifier)
                elif isinstance(item, (AnchorItem, ComponentItem, OffCurvePointItem)):
                    item.delete()
                elif isinstance(item, PixmapItem):
                    self.removeItem(item)
            self._blocked = False
            self._glyphObject.dirty = True
            event.accept()
            return
        elif event.matches(QKeySequence.Undo):
            if len(self._dataForUndo) > 0:
                undo = self._dataForUndo.pop()
                redo = self._glyphObject.serialize()
                self._glyphObject.deserialize(undo)
                self._dataForRedo.append(redo)
            event.accept()
            return
        elif event.matches(QKeySequence.Redo):
            if len(self._dataForRedo) > 0:
                undo = self._glyphObject.serialize()
                redo = self._dataForRedo.pop()
                self._dataForUndo.append(undo)
                self._glyphObject.deserialize(redo)
            event.accept()
            return
        elif event.matches(QKeySequence.SelectAll):
            path = QPainterPath()
            path.addRect(self.sceneRect())
            view = self.views()[0]
            self.setSelectionArea(path, view.transform())
            event.accept()
            return
        elif modifiers & Qt.ControlModifier and key == Qt.Key_D:
            view = self.views()[0]
            self.setSelectionArea(QPainterPath(), view.transform())
            event.accept()
            return
        elif event.matches(QKeySequence.Copy):
            clipboard = QApplication.clipboard()
            mimeData = QMimeData()
            pen = CopySelectionPen()
            self._glyphObject.drawPoints(pen)
            copyGlyph = pen.getGlyph()
            # TODO: somehow try to do this in the pen
            # pass the glyph to a controller object that holds a self._pen
            copyGlyph.width = self._glyphObject.width
            mimeData.setData("application/x-defconQt-glyph-data", pickle.dumps([copyGlyph.serialize()]))
            clipboard.setMimeData(mimeData)
            event.accept()
            return
        elif event.matches(QKeySequence.Paste):
            clipboard = QApplication.clipboard()
            mimeData = clipboard.mimeData()
            if mimeData.hasFormat("application/x-defconQt-glyph-data"):
                data = pickle.loads(mimeData.data("application/x-defconQt-glyph-data"))
                if len(data) == 1:
                    undo = self._glyphObject.serialize()
                    self._dataForUndo.append(undo)
                    pen = self._glyphObject.getPointPen()
                    pasteGlyph = TGlyph()
                    pasteGlyph.deserialize(data[0])
                    pasteGlyph.drawPoints(pen)
            event.accept()
            return
        else:
            sel = self.selectedItems()
            if len(sel) == 1 and isinstance(sel[0], OffCurvePointItem) and \
              sel[0].parentItem().getPointIndex() == len(sel[0].parentItem()._contour)-2 and \
              key == Qt.Key_Alt and self._editing is not False:
                sel[0].parentItem().setIsSmooth(False)
            super(GlyphScene, self).keyPressEvent(event)
            return
        if len(self.selectedItems()) == 0:
            super(GlyphScene, self).keyPressEvent(event)
            return
        for item in self.selectedItems():
            # TODO: if isinstance turns out to be slow, we might want to make a selectedMoveBy
            # function in items that calls moveBy for onCurve, noops for offCurve
            if isinstance(item, OffCurvePointItem) and item.parentItem().isSelected(): continue
            item.moveBy(x,y)
        event.accept()

    def keyReleaseEvent(self, event):
        sel = self.selectedItems()
        if len(sel) == 1 and isinstance(sel[0], OffCurvePointItem) and \
          sel[0].parentItem().getPointIndex() == len(sel[0].parentItem()._contour)-2 and \
          event.key() == Qt.Key_Alt and self._editing is not False:
            sel[0].parentItem().setIsSmooth(True)
        super(GlyphScene, self).keyReleaseEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self._rightClickPos = event.scenePos()
        view = self.views()[0]
        touched = self.itemAt(event.scenePos(), view.transform())
        if view._currentTool == SceneTools.RulerTool:
            self.rulerMousePress(event)
            return
        else:
            data = self._glyphObject.serialize()
            self._dataForUndo.append(data)
            self._dataForRedo = []
            if view._currentTool == SceneTools.KnifeTool:
                self.knifeMousePress(event)
                return
            elif view._currentTool == SceneTools.SelectionTool:
                super(GlyphScene, self).mousePressEvent(event)
                return
        self._blocked = True
        forceSelect = False
        sel = self.selectedItems()
        x, y = event.scenePos().x(), event.scenePos().y()
        if self._integerPlane:
            x, y = round(x), round(y)
        # XXX: not sure why isinstance does not work here
        if len(sel) == 1:
            isLastOnCurve = type(sel[0]) is OnCurvePointItem and sel[0]._contour.open and \
                sel[0].getPointIndex() == len(sel[0]._contour)-1
            # TODO: reimplement convenience methods in OffCurvePointItem
            isLastOffCurve = type(sel[0]) is OffCurvePointItem and sel[0].parentItem()._contour.open and \
                sel[0].parentItem().getPointIndex()+1 == len(sel[0].parentItem()._contour)-1
        if len(sel) == 1 and (isLastOffCurve or isLastOnCurve):
            if isLastOnCurve:
                lastContour = sel[0]._contour
            else:
                lastContour = sel[0].parentItem()._contour
            if (touched and isinstance(touched, OnCurvePointItem)) and touched.getPointIndex() == 0 \
                  and lastContour == touched._contour and len(lastContour) > 1:
                # Changing the first point from move to line/curve will cycle and so close the contour
                if isLastOffCurve:
                    lastContour.addPoint((x,y))
                    lastContour[0].segmentType = "curve"
                    touched.childItems()[1].setVisible(True)
                else:
                    lastContour[0].segmentType = "line"
            elif touched and isinstance(touched, OnCurvePointItem):
                super(GlyphScene, self).mousePressEvent(event)
                return
            else:
                if QApplication.keyboardModifiers() & Qt.ShiftModifier:
                    forceSelect = True
                    if isLastOnCurve:
                        refx = sel[0].x()
                        refy = sel[0].y()
                    else:
                        refx = sel[0].parentItem().x()
                        refy = sel[0].parentItem().y()
                    if abs(x-refx) > abs(y-refy): y = copysign(refy, y)
                    else: x = copysign(refx, x)
                if isLastOffCurve:
                    lastContour.addPoint((x,y))
                    lastContour.addPoint((x,y), "curve")
                else:
                    lastContour.addPoint((x,y), "line")
                item = OnCurvePointItem(x, y, False, lastContour, lastContour[-1], self.getViewScale())
                self._addRegisterItem(item)
                for _ in range(2):
                    lineObj = HandleLineItem(0, 0, 0, 0, item)
                    CPObject = OffCurvePointItem(0, 0, item)
                    CPObject.setVisible(False)
                if isLastOffCurve:
                    item.childItems()[1].setVisible(True)
            lastContour.dirty = True
            self._editing = True
        elif not (touched and isinstance(touched, OnCurvePointItem)):
            nextC = TContour()
            self._glyphObject.appendContour(nextC)
            nextC.addPoint((x,y), "move")

            item = OnCurvePointItem(x, y, False, self._glyphObject[-1], self._glyphObject[-1][-1], self.getViewScale())
            self._addRegisterItem(item)
            for _ in range(2):
                lineObj = HandleLineItem(0, 0, 0, 0, item)
                CPObject = OffCurvePointItem(0, 0, item)
                CPObject.setVisible(False)
            self._editing = True
        self._blocked = False
        super(GlyphScene, self).mousePressEvent(event)
        # Since shift clamps, we might be missing the point in mousePressEvent
        if forceSelect: item.setSelected(True)

    def mouseMoveEvent(self, event):
        if self._editing is True:
            sel = self.selectedItems()
            if len(sel) == 1:
                if isinstance(sel[0], OnCurvePointItem) and (event.scenePos() - sel[0].pos()).manhattanLength() >= 2:
                    mouseGrabberItem = self.mouseGrabberItem()
                    # If we drawn an onCurve w Shift and we're not touching the item, we wont have
                    # a mouse grabber (anyways), return early here.
                    if mouseGrabberItem is None:
                        event.accept()
                        return
                    self._blocked = True
                    if len(sel[0]._contour) < 2:
                        # release current onCurve
                        self.sendEvent(sel[0], QEvent(QEvent.MouseButtonRelease))
                        mouseGrabberItem.ungrabMouse()
                        sel[0].setSelected(False)
                        # append an offCurve point and start moving it
                        sel[0]._contour.addPoint((event.scenePos().x(), event.scenePos().y()))
                        nextCP = sel[0].childItems()[3]
                        nextCP.setVisible(True)
                        nextCP._needsUngrab = True
                        #nextCP.setSelected(True)
                        self.sendEvent(nextCP, QEvent(QEvent.MouseButtonPress))
                        nextCP.grabMouse()
                    else:
                        # release current onCurve, delete from contour
                        self.sendEvent(sel[0], QEvent(QEvent.MouseButtonRelease))
                        mouseGrabberItem.ungrabMouse()
                        sel[0].setSelected(False)

                        # construct a curve segment to the current point if there is not one
                        onCurve = sel[0]._point
                        if not onCurve.segmentType == "curve":
                            # remove the last onCurve
                            sel[0]._contour.removePoint(onCurve)
                            prev = sel[0]._contour[-1]
                            self.getItemForPoint(prev).childItems()[3].setVisible(True)
                            # add a zero-length offCurve to the previous point
                            sel[0]._contour.addPoint((prev.x, prev.y))
                            # add prevOffCurve and activate
                            sel[0]._contour.addPoint((sel[0].x(), sel[0].y()))
                            sel[0].childItems()[1].setVisible(True)
                            # add back current onCurve as a curve point
                            sel[0]._contour.addPoint((onCurve.x, onCurve.y), "curve")
                            sel[0]._point = sel[0]._contour[-1]
                        if not QApplication.keyboardModifiers() & Qt.AltModifier:
                            sel[0]._point.smooth = True
                            sel[0]._isSmooth = True
                            sel[0].setPointPath()
                        if sel[0].getPointIndex() == 0:
                            # we're probably dealing with the first point that we looped.
                            # preserve nextCP whatsoever.
                            lineObj = HandleLineItem(0, 0, 0, 0, sel[0])
                            nextCP = OffCurvePointItem(0, 0, sel[0])
                            # now we have l1, p1, l2, p2, l3, p3
                            l2 = sel[0].childItems()[2]
                            lineObj.stackBefore(l2)
                            nextCP.stackBefore(l2)
                        else:
                            # add last offCurve
                            sel[0]._contour.addPoint((sel[0].x(), sel[0].y()))
                            nextCP = sel[0].childItems()[3]
                        nextCP._needsUngrab = True
                        nextCP.setVisible(True)
                        #nextCP.setSelected(True)
                        self.sendEvent(nextCP, QEvent(QEvent.MouseButtonPress))
                        nextCP.grabMouse()
                    self._blocked = False
                    self._editing = None
                    super(GlyphScene, self).mouseMoveEvent(event)
                else:
                    # eat the event
                    event.accept()
        else:
            currentTool = self.views()[0]._currentTool
            if currentTool == SceneTools.RulerTool:
                self.rulerMouseMove(event)
                return
            elif currentTool == SceneTools.KnifeTool:
                self.knifeMouseMove(event)
                return
            items = self.items(event.scenePos())
            # XXX: we must cater w mouse tracking
            # we dont need isSelected() once its rid
            if len(items) > 1 and isinstance(items[0], OnCurvePointItem) and \
                  isinstance(items[1], OffCurvePointItem) and items[1].isSelected():
                items[1].setPos(0, 0)
            else:
                super(GlyphScene, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._editing = False
        currentTool = self.views()[0]._currentTool
        if currentTool == SceneTools.DrawingTool:
            # cleanup extra point elements if we dealt w curved first point
            touched = self.itemAt(event.scenePos(), self.views()[0].transform())
            if touched and isinstance(touched, OffCurvePointItem):
                onCurve = touched.parentItem()
                children = onCurve.childItems()
                if len(children) > 4:
                    # l1, p1, l3, p3, l2, p2
                    children[3].prepareGeometryChange()
                    self.removeItem(children[3])
                    children[2].prepareGeometryChange()
                    self.removeItem(children[2])

                    onCurve._isSmooth = False
                    onCurve.setPointPath()
                    onCurve._point.smooth = False
        elif currentTool == SceneTools.RulerTool:
            self.rulerMouseRelease(event)
        elif currentTool == SceneTools.KnifeTool:
            self.knifeMouseRelease(event)
        super(GlyphScene, self).mouseReleaseEvent(event)

    def rulerMousePress(self, event):
        touched = self.itemAt(event.scenePos(), self.views()[0].transform())
        if touched is not None and isinstance(touched, OnCurvePointItem) or \
            isinstance(touched, OffCurvePointItem):
            x, y = touched.scenePos().x(), touched.scenePos().y()
        else:
            x, y = event.scenePos().x(), event.scenePos().y()
        if self._integerPlane:
            x, y = round(x), round(y)
        if self._cachedRuler is not None:
            self.removeItem(self._cachedRuler)
            self._cachedRuler = None
        path = QPainterPath()
        path.moveTo(x, y)
        path.lineTo(x+1, y)
        path.lineTo(x+1, y+1)
        path.closeSubpath()
        self._rulerObject = self.addPath(path)
        textItem = QGraphicsSimpleTextItem("0", self._rulerObject)
        font = self.font()
        font.setPointSize(9)
        textItem.setFont(font)
        textItem.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        textItem.setPos(x, y + textItem.boundingRect().height())
        event.accept()

    def rulerMouseMove(self, event):
        # XXX: shouldnt have to do this, it seems mouseTracking is wrongly activated
        if self._rulerObject is None: return
        touched = self.itemAt(event.scenePos(), self.views()[0].transform())
        if touched is not None and isinstance(touched, OnCurvePointItem) or \
            isinstance(touched, OffCurvePointItem):
            x, y = touched.scenePos().x(), touched.scenePos().y()
        else:
            # TODO: 45deg clamp w ShiftModifier
            # maybe make a function for that + other occurences...
            x, y = event.scenePos().x(), event.scenePos().y()
        if self._integerPlane:
            x, y = round(x), round(y)
        path = self._rulerObject.path()
        baseElem = path.elementAt(0)
        path.setElementPositionAt(1, x, baseElem.y)
        path.setElementPositionAt(2, x, y)
        path.setElementPositionAt(3, baseElem.x, baseElem.y)
        self._rulerObject.setPath(path)
        textItem = self._rulerObject.childItems()[0]
        line = QLineF(baseElem.x, baseElem.y, x, y)
        l = line.length()
        # XXX: angle() doesnt go by trigonometric direction. Weird.
        # TODO: maybe split in positive/negative 180s (ff)
        a = 360 - line.angle()
        line.setP2(QPointF(x, baseElem.y))
        h = line.length()
        line.setP1(QPointF(x, y))
        v = line.length()
        text = "%d\n↔ %d\n↕ %d\nα %dº" % (l, h, v, a)
        textItem.setText(text)
        dx = x - baseElem.x
        if dx >= 0: px = x
        else: px = x - textItem.boundingRect().width()
        dy = y - baseElem.y
        if dy > 0: py = baseElem.y
        else: py = baseElem.y + textItem.boundingRect().height()
        textItem.setPos(px, py)
        event.accept()

    def rulerMouseRelease(self, event):
        textItem = self._rulerObject.childItems()[0]
        if textItem.text() == "0":
            # delete no-op ruler
            self.removeItem(self._rulerObject)
            self._rulerObject = None
        else:
            self._cachedRuler = self._rulerObject
            self._rulerObject = None
        event.accept()

    def knifeMousePress(self, event):
        scenePos = event.scenePos()
        x, y = scenePos.x(), scenePos.y()
        self._knifeLine = self.addLine(x, y, x, y)
        event.accept()

    """
    Computes intersection between a cubic spline and a line segment.
    Adapted from: https://www.particleincell.com/2013/cubic-line-intersection/

    Takes four defcon points describing curve and four scalars describing line
    parameters.
    """
    def computeIntersections(self, p1, p2, p3, p4, x1, y1, x2, y2):
        bx, by = x1 - x2, y2 - y1
        m = x1*(y1-y2) + y1*(x2-x1)
        a, b, c, d = bezierTools.calcCubicParameters((p1.x, p1.y), (p2.x, p2.y),
            (p3.x, p3.y), (p4.x, p4.y))

        pc0 = by*a[0] + bx*a[1]
        pc1 = by*b[0] + bx*b[1]
        pc2 = by*c[0] + bx*c[1]
        pc3 = by*d[0] + bx*d[1] + m
        r = bezierTools.solveCubic(pc0, pc1, pc2, pc3)

        sol = []
        for t in r:
            s0 = a[0]*t**3 + b[0]*t**2 + c[0]*t + d[0]
            s1 = a[1]*t**3 + b[1]*t**2 + c[1]*t + d[1]
            if (x2-x1) != 0:
                s = (s0-x1) / (x2-x1)
            else:
                s = (s1-y1) / (y2-y1)
            if not (t < 0 or t > 1 or s < 0 or s > 1):
                sol.append((s0, s1, t))
        return sol

    """
    G. Bach, http://stackoverflow.com/a/1968345
    """
    def lineIntersection(self, x1, y1, x2, y2, x3, y3, x4, y4):
        Bx_Ax = x2 - x1
        By_Ay = y2 - y1
        Dx_Cx = x4 - x3
        Dy_Cy = y4 - y3
        determinant = (-Dx_Cx * By_Ay + Bx_Ax * Dy_Cy)
        if abs(determinant) < 1e-20: return []
        s = (-By_Ay * (x1 - x3) + Bx_Ax * (y1 - y3)) / determinant
        t = ( Dx_Cx * (y1 - y3) - Dy_Cy * (x1 - x3)) / determinant
        if s >= 0 and s <= 1 and t >= 0 and t <= 1:
            return [(x1 + (t * Bx_Ax), y1 + (t * By_Ay), t)]
        return []

    def knifeMouseMove(self, event):
        # XXX: shouldnt have to do this, it seems mouseTracking is wrongly activated
        if self._knifeLine is None: return
        for dot in self._knifeDots:
            self.removeItem(dot)
        self._knifeDots = []
        scenePos = event.scenePos()
        x, y = scenePos.x(), scenePos.y()
        line = self._knifeLine.line()
        line.setP2(QPointF(x, y))
        # XXX: not nice
        glyph = self.views()[0]._glyph
        self._cachedIntersections = []
        for contour in glyph:
            segments = contour.segments
            for index, seg in enumerate(segments):
                prev = segments[index-1][-1]
                if len(seg) == 3:
                    i = self.computeIntersections(prev, seg[0], seg[1], seg[2], line.x1(), line.y1(), x, y)
                else:
                    i = self.lineIntersection(prev.x, prev.y, seg[0].x, seg[0].y, line.x1(), line.y1(), x, y)
                for pt in i:
                    scale = self.getViewScale()
                    item = self.addEllipse(-offHalf/scale, -offHalf/scale, offWidth/scale, offHeight/scale)
                    item.setPos(pt[0], pt[1])
                    self._cachedIntersections.append((contour, index, pt[2]))
                    self._knifeDots.append(item)
        self._knifeLine.setLine(line)
        event.accept()

    def knifeMouseRelease(self, event):
        self.removeItem(self._knifeLine)
        self._knifeLine = None
        for dot in self._knifeDots:
            self.removeItem(dot)
        self._knifeDots = []
        # reverse so as to not invalidate our cached segment indexes
        # XXX: multiple cuts on one segment don't work reliably
        self._cachedIntersections.reverse()
        if len(self._cachedIntersections):
            for intersect in self._cachedIntersections:
                contour, index, t = intersect
                contour.splitAndInsertPointAtSegmentAndT(index, t)
        self._cachedIntersections = []
        event.accept()


class GlyphView(QGraphicsView):
    def __init__(self, glyph, settings, parent=None):
        super(GlyphView, self).__init__(parent)

        # wont change during lifetime
        self._layerSet = layerSet = glyph.layerSet
        self._name = glyph.name
        self._settings = settings

        # we got the individual layers as keys => pathItem
        # we got string keys => [list of scene items] like 'components'
        self._sceneItems = {}

        # will change during lifetime
        self._layer = glyph.layer

        self._impliedPointSize = 1000
        self._pointSize = None

        # apparently unused code
        self._inverseScale = 0.1
        self._scale = 10

        self._noPointSizePadding = 200
        self._drawStroke = True
        self._showOffCurvePoints = True
        self._showOnCurvePoints = True
        self._showMetricsTitles = True

        self.setBackgroundBrush(QBrush(Qt.lightGray))
        self.setScene(GlyphScene(self, self._getSceneItems('scene-added-items')))
        font = self.font()
        font.setFamily("Roboto Mono")
        font.setFixedPitch(True)
        self.setFont(font)

        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        #self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        self.horizontalScrollBar().valueChanged.connect(self.scaleElements)

        self.setSceneSelection()

        self.setRenderHint(QPainter.Antialiasing)
        self.scale(1, -1)
        self.addBackground()
        self.addBlues()
        self.addHorizontalMetrics()

        for layer in layerSet:
            if self._name not in layer:
                self._listenToLayer(layer)
            else:
                self._listenToGlyph(layer)
        self._listenToLayerSet()

        self.changeCurrentLayer(self._layer)


    @property
    def _glyph(self):
        # instead of a getter we could change the glyph each time
        # self._layer is changed. However, it might be that the glyph
        # is not ready when the layer is set
        return self._layer[self._name]

    @property
    def name(self):
        return self._name

    @property
    def layer(self):
        return self._layer

    @property
    def defaultWidth(self):
        defaultLayer = self._layerSet[None]
        return defaultLayer[self._name].width \
                                    if self._name in defaultLayer else 0

    def _listenToLayerSet(self):
        self._layerSet.addObserver(self, '_layerDeleted', 'LayerSet.LayerWillBeDeleted')
        self._layerSet.addObserver(self, '_layerGenericVisualChange', 'LayerSet.LayerOrderChanged')

    def _listenToLayer(self, layer, remove=False):
        if remove:
            layer.removeObserver(self, 'Layer.GlyphAdded')
        else:
            layer.addObserver(self, '_layerGlyphAdded', 'Layer.GlyphAdded')

    def _layerGenericVisualChange(self, notification):
        self.redraw()

    def _listenToGlyph(self, layer):
        layer[self._name].addObserver(self, "_glyphChanged", "Glyph.Changed")
        layer.addObserver(self, '_layerGenericVisualChange', 'Layer.ColorChanged')

    def layerAdded(self, layer):
        self._listenToLayer(layer)

    def _layerGlyphAdded(self, notification):
        glyphName = notification.data['name']
        # the layer will emit this for each new glyph
        if glyphName != self._name:
            return
        layer = notification.object
        self._listenToLayer(layer, remove=True)
        self._listenToGlyph(layer)
        self.redraw()

    def _layerDeleted(self, notification):
        layerName = notification.data['name']
        layer = self._layerSet[layerName]
        self._removeLayerPath(layer)

    def _glyphChanged(self, notification):
        # TODO: maybe detect sidebearing changes (space center) and then only
        # translate elements rather than reconstructing them.
        # Also we lose selection when reconstructing, rf does not when changing
        # sp.center values.
        glyph = notification.object
        layer = glyph.layer
        if layer is self._layer:
            self.activeGlyphChanged()
        else:
            self.updateLayerPath(layer)

    def redraw(self):
        self._getSceneItems('scene-added-items', clear=True)
        self.updateLayerAssets()
        self.drawAllLayers()
        self.addAnchors()
        self.addPoints()

    def updateLayerAssets(self):
        for item in self._getSceneItems('hMetricLabels'):
            item.setPos(self._glyph.width, item.y())

    def activeGlyphChanged(self):
        # For now, we'll assume not scene._blocked == moving UI points
        # this will not be the case anymore when drag sidebearings pops up
        scene = self.scene()
        if scene._blocked:
            self.updateActiveLayerPath()
            return
        self.updateActiveLayer()

    def updateActiveLayer(self):
        self._getSceneItems('scene-added-items', clear=True)
        self.updateLayerAssets()

        self.updateActiveLayerPath()
        self.addComponents()
        self.addAnchors()
        self.addPoints()

        # this is related to addBackground
        scene = self.scene()
        scene._widthItem.setRect(0, -1000, self._glyph.width, 3000)

    def addBackground(self):
        scene = self.scene()
        font = self._glyph.getParent()
        width = self._glyph.width
        if width is None: width = 0
        item = scene.addRect(-1000, -1000, 3000, 3000, QPen(Qt.black), QBrush(Qt.gray))
        item.setZValue(-1000)
        scene._widthItem = scene.addRect(0, -1000, width, 3000, QPen(Qt.NoPen), QBrush(backgroundColor))
        scene._widthItem.setZValue(-999)
        descender = font.info.descender
        if descender is None: descender = -250
        unitsPerEm = font.info.unitsPerEm
        if unitsPerEm is None: unitsPerEm = 1000
        self.centerOn(width/2, descender+unitsPerEm/2)

    def addBlues(self):
        scene = self.scene()
        font = self._glyph.getParent()
        if font is None:
            return
        attrs = ["postscriptBlueValues", "postscriptOtherBlues"]
        for attr in attrs:
            values = getattr(font.info, attr)
            if not values:
                continue
            yMins = [i for index, i in enumerate(values) if not index % 2]
            yMaxs = [i for index, i in enumerate(values) if index % 2]
            for yMin, yMax in zip(yMins, yMaxs):
                if yMin == yMax:
                    item = scene.addLine(-1000, yMin, 3000, yMax, QPen(bluesColor))
                    item.setZValue(-998)
                else:
                    item = scene.addRect(-1000, yMin, 3000, yMax - yMin, QPen(Qt.NoPen), QBrush(bluesColor))
                    item.setZValue(-998)

    def addHorizontalMetrics(self):
        scene = self.scene()
        font = self._glyph.getParent()
        width = self._glyph.width# * self._inverseScale
        toDraw = [
            ("Descender", font.info.descender),
            ("Baseline", 0),
            ("x-height", font.info.xHeight),
            ("Cap height", font.info.capHeight),
            ("Ascender", font.info.ascender),
        ]
        positions = {}
        for name, position in toDraw:
            if position is None:
                continue
            if position not in positions:
                positions[position] = []
            positions[position].append(name)
        # lines
        for position, names in sorted(positions.items()):
            y = roundPosition(position)
            item = scene.addLine(-1000, y, 2000, y, QPen(metricsColor))
            item.setZValue(-997)


        labels = self._getSceneItems('hMetricLabels', clear=True)
        # text
        if self._showMetricsTitles:# and self._impliedPointSize > 150:
            fontSize = 9# * self._inverseScale
            font = self.font()
            font.setPointSize(fontSize)
            for position, names in sorted(positions.items()):
                y = position - (fontSize / 2)
                text = ", ".join(names)
                text = " %s " % text
                item = VGuidelinesTextItem(text, font)
                item.setBrush(metricsColor)
                item.setFlag(QGraphicsItem.ItemIgnoresTransformations)
                item.setPos(width, y)
                item.setZValue(-997)
                labels.append(item)
                scene.addItem(item)

    def getLayerColor(self, layer=None):
        if layer is None:
            layer = self._layer
        if layer.color is not None:
            return QColor.fromRgbF(*layer.color)
        return None


    def _getDrawingStyleForLayer(self, layer, kind=None):
        isActive = layer is self._layer
        isFilled = self._settings.activeLayerFilled \
                    if isActive else self._settings.otherLayersFilled
        isOutlined = not isFilled
        useLayerColor = self._settings.activeLayerUseLayerColor \
                    if isActive else self._settings.otherLayerUseLayerColor

        if useLayerColor:
            brushcolor = self.getLayerColor(layer) or Qt.black
            pencolor = brushcolor
        else:
            # default app colors
            brushcolor = fillColor if kind != 'component' else componentFillColor
            pencolor = Qt.black

        if isOutlined:
            pen = QPen(pencolor)
            brush = QBrush(Qt.NoBrush)
        else:
            pen = QPen(Qt.NoPen)
            brush = QBrush(brushcolor)

        if isActive and not useLayerColor:
            # The originally released app did fall back to QT's default
            #  behavior i.e. no pen defined, so I preserve this here
            if isOutlined: brush = None # like Qt.NoBrush
            else: pen = None # like Qt.black
        return (pen, brush)



    @property
    def _activeLayerZValue(self):
        return -995 if not self._settings.activeLayerOnTop else -993

    def drawAllLayers(self):
        activeLayer = self._layer
        # all layers before the active layer are -996
        # the active layer is -995 or -993 if self._settings.activeLayerOnTop == True
        # all layers after the active layer are -996
        zValue = -996
        for layer in reversed(list(self._layerSet)):
            if self._name not in layer:
                continue
            isActiveLayer = layer is activeLayer
            if isActiveLayer:
                zValue = self._activeLayerZValue
            elif not self._settings.drawOtherLayers:
                self._removeLayerPath(layer)
                continue
            self.drawLayer(layer, zValue)
            if isActiveLayer:
                zValue = -994

    def _removeLayerPath(self, layer):
        scene = self.scene()
        item = self._sceneItems.get(layer, None)
        if item is not None:
            scene.removeItem(item)
        if layer in self._sceneItems:
            del self._sceneItems[layer]

    def drawLayer(self, layer, zValue):
        scene = self.scene()
        glyph = layer[self._name]
        self._removeLayerPath(layer)

        isActiveLayer = layer is self._layer
        if isActiveLayer:
            representationKey = "defconQt.NoComponentsQPainterPath"
        else:
            representationKey = "defconQt.QPainterPath"

        path = glyph.getRepresentation(representationKey)
        item = QGraphicsPathItem()
        item.setPath(path)

        pen, brush = self._getDrawingStyleForLayer(layer)
        if pen: item.setPen(pen)
        if brush: item.setBrush(brush)

        item.setZValue(zValue)

        self._sceneItems[layer] = item
        scene.addItem(item)
        if isActiveLayer:
            # FIXME: don't like this
            scene._outlineItem = item
            self.addComponents()
        return item

    def updateActiveLayerPath(self):
        self.updateLayerPath(self._layer, representationKey="defconQt.NoComponentsQPainterPath")

    def updateLayerPath(self, layer, representationKey="defconQt.QPainterPath"):
        glyph = layer[self._name]
        scene = self.scene()
        path = glyph.getRepresentation(representationKey)
        self._sceneItems[layer].setPath(path)

    def _getSceneItems(self, key, clear=False):
        items = self._sceneItems.get(key, None)
        if items is None:
            items = []
            self._sceneItems[key] = items
        elif clear:
            scene = self.scene()
            for item in items:
                scene.removeItem(item)
            del items[:]
        return items

    def addComponents(self):
        scene = self.scene()
        layer = self._layer
        glyph = self._glyph

        pen, brush = self._getDrawingStyleForLayer(layer, kind='component')
        components = self._getSceneItems('components', clear=True)
        for component in glyph.components:
            if component.baseGlyph not in layer:
                continue
            componentGlyph = layer[component.baseGlyph]
            path = componentGlyph.getRepresentation("defconQt.QPainterPath")
            item = ComponentItem(path, component)
            if pen: item.setPen(pen)
            if brush: item.setBrush(brush)
            item.setZValue(self._activeLayerZValue)
            components.append(item)
            scene.addItem(item)

    def addAnchors(self):
        scene = self.scene()
        anchors = self._getSceneItems('anchors', clear=True)

        for anchor in self._glyph.anchors:
            item = AnchorItem(anchor, self.transform().m11())
            item.setZValue(-992)
            anchors.append(item)
            scene.addItem(item)

    def addPoints(self):
        scene = self.scene()

        pointItems = self._getSceneItems('points', clear=True)

        # work out appropriate sizes and
        # skip if the glyph is too small
        pointSize = self._impliedPointSize
        if pointSize > 550:
            startPointSize = 21
            offCurvePointSize = 5
            onCurvePointSize = 6
            onCurveSmoothPointSize = 7
        elif pointSize > 250:
            startPointSize = 15
            offCurvePointSize = 3
            onCurvePointSize = 4
            onCurveSmoothPointSize = 5
        elif pointSize > 175:
            startPointSize = 9
            offCurvePointSize = 1
            onCurvePointSize = 2
            onCurveSmoothPointSize = 3
        else:
            return
        # use the data from the outline representation
        outlineData = self._glyph.getRepresentation("defconQt.OutlineInformation")
        points = [] # TODO: remove this unless we need it # useful for text drawing, add it
        startObjects = []
        scale = self.transform().m11()
        if outlineData["onCurvePoints"]:
            for onCurve in outlineData["onCurvePoints"]:
                # on curve
                x, y = onCurve.x, onCurve.y
                points.append((x, y))
                item = OnCurvePointItem(x, y, onCurve.isSmooth, self._glyph[onCurve.contourIndex],
                    self._glyph[onCurve.contourIndex][onCurve.pointIndex], scale)
                pointItems.append(item)
                scene.addItem(item)
                # off curve
                for CP in [onCurve.prevCP, onCurve.nextCP]:
                    if CP:
                        cx, cy = CP
                        # line
                        lineObj = HandleLineItem(0, 0, cx-x, cy-y, item)
                        # point
                        points.append((cx, cy))
                        CPObject = OffCurvePointItem(cx-x, cy-y, item)
                    else:
                        lineObj = HandleLineItem(0, 0, 0, 0, item)
                        #lineObj.setVisible(False)
                        CPObject = OffCurvePointItem(0, 0, item)
                        CPObject.setVisible(False)
        '''
        # start point
        if self._showOnCurvePoints and outlineData["startPoints"]:
            startWidth = startHeight = roundPosition(startPointSize)# * self._inverseScale)
            startHalf = startWidth / 2.0
            for point, angle in outlineData["startPoints"]:
                x, y = point
                # TODO: do we really need to special-case with Qt?
                if angle is not None:
                    path = QPainterPath()
                    path.moveTo(x, y)
                    path.arcTo(x-startHalf, y-startHalf, 2*startHalf, 2*startHalf, angle-90, -180)
                    item = scene.addPath(path, QPen(Qt.NoPen), QBrush(self._startPointColor))
                    startObjects.append(item)
                    #path.closeSubpath()
                else:
                    item = scene.addEllipse(x-startHalf, y-startHalf, startWidth, startHeight,
                        QPen(Qt.NoPen), QBrush(self._startPointColor))
                    startObjects.append(item)
            #s.addPath(path, QPen(Qt.NoPen), brush=QBrush(self._startPointColor))
        # text
        if self._showPointCoordinates and coordinateSize:
            fontSize = 9 * self._inverseScale
            attributes = {
                NSFontAttributeName : NSFont.systemFontOfSize_(fontSize),
                NSForegroundColorAttributeName : self._pointCoordinateColor
            }
            for x, y in points:
                posX = x
                posY = y
                x = round(x, 1)
                if int(x) == x:
                    x = int(x)
                y = round(y, 1)
                if int(y) == y:
                    y = int(y)
                text = "%d  %d" % (x, y)
                self._drawTextAtPoint(text, attributes, (posX, posY), 3)
        '''

    def createAnchor(self, *args):
        scene = self.scene()
        pos = scene._rightClickPos
        if scene._integerPlane:
            pos.setX(int(pos.x()))
            pos.setY(int(pos.y()))
        newAnchorName, ok = AddAnchorDialog.getNewAnchorName(self, pos)
        if ok:
            anchor = Anchor()
            anchor.x = pos.x()
            anchor.y = pos.y()
            anchor.name = newAnchorName
            self._glyph.appendAnchor(anchor)

    def createComponent(self, *args):
        newGlyph, ok = AddComponentDialog.getNewGlyph(self, self._glyph)
        if ok and newGlyph is not None:
            component = Component()
            component.baseGlyph = newGlyph.name
            self._glyph.appendComponent(component)

    def _makeLayerGlyph(self, layer):
        name = self._name
        layer.newGlyph(name)
        glyph = layer[name]
        # TODO: generalize this out, can’t use newStandardGlyph unfortunately
        glyph.width = self.defaultWidth

        # This prevents the empty glyph from being saved.
        # TGlyph sets it to False when the glyph is marked as dirty
        glyph.template = True
        return glyph

    def changeCurrentLayer(self, layer):
        name = self._name

        # set current layer
        self._layer = layer

        if name in layer:
            # please redraw
            self.redraw()
        else:
            # no need to redraw, will happen within _layerGlyphAdded
            self._makeLayerGlyph(layer)

        # TODO: Undo data does not keep track of different layers
        scene = self.scene()
        scene._dataForUndo = []
        scene._dataForRedo = []

    def showEvent(self, event):
        super(GlyphView, self).showEvent(event)
        font = self._glyph.getParent()
        # TODO: we should have an app-wide mechanism to handle default metrics
        # values (that are applied to new fonts as well)
        descender = font.info.descender
        if descender is None: descender = -250
        unitsPerEm = font.info.unitsPerEm
        if unitsPerEm is None: unitsPerEm = 1000
        self.fitInView(0, descender, self._glyph.width, unitsPerEm, Qt.KeepAspectRatio)

    def mousePressEvent(self, event):
        if (event.button() == Qt.MidButton):
            dragMode = self.dragMode()
            if dragMode == QGraphicsView.RubberBandDrag:
                self.setDragMode(QGraphicsView.ScrollHandDrag)
            elif dragMode == QGraphicsView.ScrollHandDrag:
                self.setDragMode(QGraphicsView.RubberBandDrag)
        super(GlyphView, self).mousePressEvent(event)

    def setSceneDrawing(self):
        self._currentTool = SceneTools.DrawingTool
        self.setDragMode(QGraphicsView.NoDrag)

    def setSceneRuler(self):
        self._currentTool = SceneTools.RulerTool
        self.setDragMode(QGraphicsView.NoDrag)

    def setSceneSelection(self):
        self._currentTool = SceneTools.SelectionTool
        self.setDragMode(QGraphicsView.RubberBandDrag)

    def setSceneKnife(self):
        self._currentTool = SceneTools.KnifeTool
        self.setDragMode(QGraphicsView.NoDrag)

    # Lock/release handdrag does not seem to work…
    '''
    def mouseReleaseEvent(self, event):
        if (event.button() == Qt.MidButton):
            self.setDragMode(QGraphicsView.RubberBandDrag)
        super(GlyphView, self).mouseReleaseEvent(event)
    '''

    def wheelEvent(self, event):
        factor = pow(1.2, event.angleDelta().y() / 120.0)
        event.accept()

        self.scale(factor, factor)

    def scaleElements(self):
        # TODO: stop displaying SimpleTextItems at certains sizes, maybe anchor them differently as well
        scale = self.transform().m11()
        if scale < 4:
            for item in self.scene().items():
                if isinstance(item, (OnCurvePointItem, OffCurvePointItem, \
                  ResizeHandleItem, AnchorItem)):
                    item.setPointPath(scale)
