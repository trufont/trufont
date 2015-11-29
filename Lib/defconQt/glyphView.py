from PyQt5.QtCore import Qt
from PyQt5.QtGui import (
    QBrush, QColor, QPainter, QPen)
from PyQt5.QtWidgets import (
    QAction, QGraphicsItem, QGraphicsPathItem, QGraphicsView)

from defcon import Anchor, Component
from defconQt import icons_db  # noqa
from defconQt.objects.defcon import TGlyph
from defconQt.objects.sizeGripItem import ResizeHandleItem
from defconQt.util.roundPosition import roundPosition
from defconQt.dialogs.addAnchorDialog import AddAnchorDialog
from defconQt.dialogs.addComponentDialog import AddComponentDialog
from defconQt.dialogs.layerActionsDialog import LayerActionsDialog
from defconQt.items.anchorItem import AnchorItem
from defconQt.items.componentItem import ComponentItem
from defconQt.items.handleLineItem import HandleLineItem
from defconQt.items.offCurvePointItem import OffCurvePointItem
from defconQt.items.onCurvePointItem import OnCurvePointItem
from defconQt.items.startPointItem import StartPointItem
from defconQt.items.vGuidelinesTextItem import VGuidelinesTextItem
from defconQt.glyphScene import GlyphScene, SceneTools

backgroundColor = Qt.white
bluesColor = QColor.fromRgbF(.5, .7, 1, .3)
fillColor = QColor(200, 200, 200, 120)
componentFillColor = QColor.fromRgbF(0, 0, 0, .4)
metricsColor = QColor(70, 70, 70)
bluesAttrs = ["postscriptBlueValues", "postscriptOtherBlues"]


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

        self._drawStroke = True
        self._showOffCurvePoints = True
        self._showOnCurvePoints = True
        self._showMetricsTitles = True

        self.setBackgroundBrush(QBrush(Qt.lightGray))
        self.setScene(GlyphScene(
            self, self._getSceneItems('scene-added-items')))
        font = self.font()
        font.setFamily("Roboto Mono")
        font.setFixedPitch(True)
        self.setFont(font)

        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        # self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
        self.horizontalScrollBar().valueChanged.connect(self.scaleElements)

        self.setSceneSelection()

        self.setRenderHint(QPainter.Antialiasing)
        self.scale(1, -1)
        self.addBackground()
        self.addBlues()
        self.addHorizontalMetrics()

        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        createAnchorAction = QAction("Add Anchor…", self)
        createAnchorAction.triggered.connect(self.createAnchor)
        self.addAction(createAnchorAction)
        createComponentAction = QAction("Add Component…", self)
        createComponentAction.triggered.connect(self.createComponent)
        self.addAction(createComponentAction)

        font = glyph.getParent()
        font.info.addObserver(self, "_fontInfoChanged", "Info.ValueChanged")
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
        self._layerSet.addObserver(
            self, '_layerDeleted', 'LayerSet.LayerWillBeDeleted')
        self._layerSet.addObserver(
            self, '_layerGenericVisualChange', 'LayerSet.LayerOrderChanged')

    def _listenToLayer(self, layer, remove=False):
        if remove:
            layer.removeObserver(self, 'Layer.GlyphAdded')
        else:
            layer.addObserver(self, '_layerGlyphAdded', 'Layer.GlyphAdded')

    def _layerGenericVisualChange(self, notification):
        self.redraw()

    def _listenToGlyph(self, layer):
        layer[self._name].addObserver(self, "_glyphChanged", "Glyph.Changed")
        layer.addObserver(self, '_layerGenericVisualChange',
                          'Layer.ColorChanged')

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

    def _fontInfoChanged(self, notification):
        if notification.data["attribute"] in bluesAttrs:
            self.addBlues()

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
        # For now, we'll assume that scene._blocked == moving UI points
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
        if width is None:
            width = 0
        item = scene.addRect(-1000, -1000, 3000, 3000,
                             QPen(Qt.black), QBrush(Qt.gray))
        item.setZValue(-1000)
        scene._widthItem = scene.addRect(
            0, -1000, width, 3000, QPen(Qt.NoPen), QBrush(backgroundColor))
        scene._widthItem.setZValue(-999)
        descender = font.info.descender
        if descender is None:
            descender = -250
        unitsPerEm = font.info.unitsPerEm
        if unitsPerEm is None:
            unitsPerEm = 1000
        self.centerOn(width / 2, descender + unitsPerEm / 2)

    def addBlues(self):
        scene = self.scene()
        font = self._glyph.getParent()
        blues = self._getSceneItems('blues', clear=True)
        if font is None:
            return
        for attr in bluesAttrs:
            values = getattr(font.info, attr)
            if not values:
                continue
            yMins = [i for index, i in enumerate(values) if not index % 2]
            yMaxs = [i for index, i in enumerate(values) if index % 2]
            for yMin, yMax in zip(yMins, yMaxs):
                if yMin == yMax:
                    item = scene.addLine(-1000, yMin, 3000,
                                         yMax, QPen(bluesColor))
                    item.setZValue(-998)
                else:
                    item = scene.addRect(-1000, yMin, 3000, yMax - yMin,
                                         QPen(Qt.NoPen), QBrush(bluesColor))
                    item.setZValue(-998)
                blues.append(item)

    def addHorizontalMetrics(self):
        scene = self.scene()
        font = self._glyph.getParent()
        width = self._glyph.width  # * self._inverseScale
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
        if self._showMetricsTitles:  # and self._impliedPointSize > 150:
            fontSize = 9  # * self._inverseScale
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
            if kind != 'component':
                brushcolor = fillColor
            else:
                brushcolor = componentFillColor
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
            if isOutlined:
                brush = None  # like Qt.NoBrush
            else:
                pen = None  # like Qt.black
        return (pen, brush)

    @property
    def _activeLayerZValue(self):
        return -995 if not self._settings.activeLayerOnTop else -993

    def drawAllLayers(self):
        activeLayer = self._layer
        # all layers before the active layer are -996
        # the active layer is -995 or -993 if
        # self._settings.activeLayerOnTop == True
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
        if pen:
            item.setPen(pen)
        if brush:
            item.setBrush(brush)

        item.setZValue(zValue)

        self._sceneItems[layer] = item
        scene.addItem(item)
        if isActiveLayer:
            # FIXME: don't like this
            scene._outlineItem = item
            self.addComponents()
            self.addStartPoints()
        return item

    def updateActiveLayerPath(self):
        self.updateLayerPath(
            self._layer, representationKey="defconQt.NoComponentsQPainterPath")
        self.addStartPoints()

    def updateLayerPath(self, layer,
                        representationKey="defconQt.QPainterPath"):
        glyph = layer[self._name]
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
            if pen:
                item.setPen(pen)
            if brush:
                item.setBrush(brush)
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

    def addStartPoints(self):
        scene = self.scene()
        startPointItems = self._getSceneItems('startPoints', clear=True)
        startPointsData = self._glyph.getRepresentation(
            "defconQt.StartPointsInformation")
        # path = QPainterPath()  # unused
        for point, angle in startPointsData:
            x, y = point
            if angle is not None:
                item = StartPointItem(x, y, angle, self.transform().m11())
                startPointItems.append(item)
                scene.addItem(item)

    def addPoints(self):
        scene = self.scene()
        pointItems = self._getSceneItems('points', clear=True)
        # use the data from the outline representation
        outlineData = self._glyph.getRepresentation(
            "defconQt.OutlineInformation")
        scale = self.transform().m11()
        for onCurve in outlineData:
            # on curve
            x, y = onCurve.x, onCurve.y
            item = OnCurvePointItem(
                x, y, onCurve.isSmooth,
                self._glyph[onCurve.contourIndex],
                self._glyph[onCurve.contourIndex][onCurve.pointIndex],
                scale)
            pointItems.append(item)
            scene.addItem(item)
            # off curve
            for CP in [onCurve.prevCP, onCurve.nextCP]:
                if CP:
                    cx, cy = CP
                    # line
                    HandleLineItem(0, 0, cx - x, cy - y, item)
                    # point
                    CPObject = OffCurvePointItem(cx - x, cy - y, item)
                else:
                    HandleLineItem(0, 0, 0, 0, item)
                    CPObject = OffCurvePointItem(0, 0, item)
                    CPObject.setVisible(False)
        '''
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

    def layerActions(self):
        newLayer, action, ok = LayerActionsDialog.getLayerAndAction(
            self, self._glyph)
        if ok and newLayer is not None:
            # TODO: whole glyph for now, but consider selection too
            if not self._glyph.name in newLayer:
                newLayer.newGlyph(self._glyph.name)
            otherGlyph = newLayer[self._glyph.name]
            otherGlyph.disableNotifications()
            if action == "Swap":
                tempGlyph = TGlyph()
                otherGlyph.drawPoints(tempGlyph.getPointPen())
                tempGlyph.width = otherGlyph.width
                otherGlyph.clearContours()
            self._glyph.drawPoints(otherGlyph.getPointPen())
            otherGlyph.width = self._glyph.width
            if action != "Copy":
                self._glyph.disableNotifications()
                self._glyph.clearContours()
                # XXX: we shouldn't have to do this manually but it seems there
                # is a timing problem
                self._glyph.destroyAllRepresentations()
                if action == "Swap":
                    tempGlyph.drawPoints(self._glyph.getPointPen())
                    self._glyph.width = tempGlyph.width
                self._glyph.enableNotifications()
            otherGlyph.enableNotifications()

    def _makeLayerGlyph(self, layer):
        name = self._name
        glyph = layer.newGlyph(name)
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
        if descender is None:
            descender = -250
        unitsPerEm = font.info.unitsPerEm
        if unitsPerEm is None:
            unitsPerEm = 1000
        self.fitInView(0, descender, self._glyph.width,
                       unitsPerEm, Qt.KeepAspectRatio)

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
        if event.modifiers() & Qt.ControlModifier:
            factor = pow(1.2, event.angleDelta().y() / 120.0)
            self.scale(factor, factor)
            event.accept()
        else:
            super().wheelEvent(event)

    def scaleElements(self):
        # TODO: stop displaying SimpleTextItems at certains sizes, maybe anchor
        # them differently as well
        scale = self.transform().m11()
        if scale < 4:
            for item in self.scene().items():
                if isinstance(item, (OnCurvePointItem, OffCurvePointItem,
                                     ResizeHandleItem, AnchorItem,
                                     StartPointItem)):
                    item.setPointPath(scale)
