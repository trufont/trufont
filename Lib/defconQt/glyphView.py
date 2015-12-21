from defconQt.glyphCollectionView import headerFont
from defconQt.objects.defcon import TGlyph
from defconQt.objects.glyphDialogs import (
    GotoDialog, AddLayerDialog, LayerActionsDialog)
# TODO: make stdTools reexport?
from defconQt.tools.baseTool import BaseTool
from defconQt.tools.selectionTool import SelectionTool
from defconQt.tools.penTool import PenTool
from defconQt.tools.rulerTool import RulerTool
from defconQt.tools.knifeTool import KnifeTool
from defconQt.tools.removeOverlapButton import RemoveOverlapButton
from defconQt.util import drawing
from PyQt5.QtCore import QEvent, QMimeData, QPointF, QSize, Qt
from PyQt5.QtGui import (
    QIcon, QKeySequence, QMouseEvent, QPainter, QPainterPath)
from PyQt5.QtWidgets import (
    QActionGroup, QApplication, QComboBox, QMainWindow, QMenu, QScrollArea,
    QSizePolicy, QToolBar, QWidget)
import pickle


class MainGlyphWindow(QMainWindow):

    def __init__(self, glyph, parent=None):
        super().__init__(parent)

        menuBar = self.menuBar()
        fileMenu = QMenu("&File", self)
        fileMenu.addAction("E&xit", self.close, QKeySequence.Quit)
        menuBar.addMenu(fileMenu)
        editMenu = QMenu("&Edit", self)
        self._undoAction = editMenu.addAction(
            "&Undo", self.undo, QKeySequence.Undo)
        self._redoAction = editMenu.addAction(
            "&Redo", self.redo, QKeySequence.Redo)
        editMenu.addSeparator()
        # XXX
        action = editMenu.addAction("C&ut", self.cutOutlines, QKeySequence.Cut)
        action.setEnabled(False)
        self._copyAction = editMenu.addAction(
            "&Copy", self.copyOutlines, QKeySequence.Copy)
        editMenu.addAction("&Paste", self.pasteOutlines, QKeySequence.Paste)
        editMenu.addAction(
            "Select &All", self.selectAll, QKeySequence.SelectAll)
        editMenu.addAction("&Deselect", self.deselect, "Ctrl+D")
        menuBar.addMenu(editMenu)
        glyphMenu = QMenu("&Glyph", self)
        glyphMenu.addAction("&Next Glyph", lambda: self.glyphOffset(1), "End")
        glyphMenu.addAction(
            "&Previous Glyph", lambda: self.glyphOffset(-1), "Home")
        glyphMenu.addAction("&Go To…", self.changeGlyph, "G")
        glyphMenu.addSeparator()
        # TODO: enable only when len(layerSet) > 1
        glyphMenu.addAction(
            "&Layer Actions…", self.layerActions, "L")
        menuBar.addMenu(glyphMenu)

        # create tools and buttons toolBars
        self._tools = []
        self._toolsActionGroup = QActionGroup(self)
        self._toolsToolBar = QToolBar("Tools", self)
        self._toolsToolBar.setMovable(False)
        self._buttons = []
        self._buttonsToolBar = QToolBar("Buttons", self)
        self._buttonsToolBar.setMovable(False)
        self.addToolBar(self._toolsToolBar)
        self.addToolBar(self._buttonsToolBar)

        # http://www.setnode.com/blog/right-aligning-a-button-in-a-qtoolbar/
        self._layersToolBar = QToolBar("Layers", self)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._currentLayerBox = QComboBox(self)
        self._currentLayerBox.currentIndexChanged.connect(
            self._layerChanged)
        self._layersToolBar.addWidget(spacer)
        self._layersToolBar.addWidget(self._currentLayerBox)
        self._layersToolBar.setContentsMargins(0, 0, 2, 0)
        self._layersToolBar.setMovable(False)
        self.addToolBar(self._layersToolBar)

        viewMenu = self.createPopupMenu()
        viewMenu.setTitle("View")
        viewMenu.addSeparator()
        action = viewMenu.addAction("Lock Toolbars", self.lockToolBars)
        action.setCheckable(True)
        action.setChecked(True)
        menuBar.addMenu(viewMenu)

        self.view = GlyphView(self)
        self.setGlyph(glyph)
        selectionTool = self.installTool(SelectionTool)
        selectionTool.trigger()
        self.installTool(PenTool)
        self.installTool(RulerTool)
        self.installTool(KnifeTool)
        self.installButton(RemoveOverlapButton)

        self.setCentralWidget(self.view.scrollArea())
        self.resize(900, 700)
        self.view.setFocus(True)

    # ----------
    # Menu items
    # ----------

    def glyphOffset(self, offset):
        currentGlyph = self.view.glyph()
        font = currentGlyph.font
        glyphOrder = font.glyphOrder
        # should be enforced in fontView already
        if not (glyphOrder and len(glyphOrder)):
            return
        index = glyphOrder.index(currentGlyph.name)
        newIndex = (index + offset) % len(glyphOrder)
        glyph = font[glyphOrder[newIndex]]
        self.setGlyph(glyph)

    def changeGlyph(self):
        glyph = self.view.glyph()
        newGlyph, ok = GotoDialog.getNewGlyph(self, glyph)
        if ok and newGlyph is not None:
            self.setGlyph(newGlyph)

    def layerActions(self):
        glyph = self.view.glyph()
        newLayer, action, ok = LayerActionsDialog.getLayerAndAction(
            self, glyph)
        if ok and newLayer is not None:
            # TODO: whole glyph for now, but consider selection too
            if not glyph.name in newLayer:
                newLayer.newGlyph(glyph.name)
            otherGlyph = newLayer[glyph.name]
            otherGlyph.disableNotifications()
            if action == "Swap":
                tempGlyph = TGlyph()
                otherGlyph.drawPoints(tempGlyph.getPointPen())
                tempGlyph.width = otherGlyph.width
                otherGlyph.clearContours()
            glyph.drawPoints(otherGlyph.getPointPen())
            otherGlyph.width = glyph.width
            if action != "Copy":
                glyph.disableNotifications()
                glyph.clearContours()
                if action == "Swap":
                    tempGlyph.drawPoints(glyph.getPointPen())
                    glyph.width = tempGlyph.width
                glyph.enableNotifications()
            otherGlyph.enableNotifications()

    def undo(self):
        glyph = self.view.glyph()
        glyph.undo()

    def redo(self):
        glyph = self.view.glyph()
        glyph.redo()

    def cutOutlines(self):
        pass

    def copyOutlines(self):
        glyph = self.view.glyph()
        clipboard = QApplication.clipboard()
        mimeData = QMimeData()
        copyGlyph = glyph.getRepresentation("defconQt.FilterSelection")
        mimeData.setData("application/x-defconQt-glyph-data",
                         pickle.dumps([copyGlyph.serialize(
                             blacklist=("name", "unicode")
                         )]))
        clipboard.setMimeData(mimeData)

    def pasteOutlines(self):
        glyph = self.view.glyph()
        clipboard = QApplication.clipboard()
        mimeData = clipboard.mimeData()
        if mimeData.hasFormat("application/x-defconQt-glyph-data"):
            data = pickle.loads(mimeData.data(
                "application/x-defconQt-glyph-data"))
            if len(data) == 1:
                pen = glyph.getPointPen()
                pasteGlyph = TGlyph()
                pasteGlyph.deserialize(data[0])
                # TODO: if we serialize selected state, we don't need to do
                # this
                pasteGlyph.selected = True
                pasteGlyph.drawPoints(pen)

    def selectAll(self):
        glyph = self.view.glyph()
        glyph.selected = True
        if not len(glyph):
            for component in glyph.components:
                component.selected = True

    def deselect(self):
        glyph = self.view.glyph()
        for anchor in glyph.anchors:
            anchor.selected = False
        for component in glyph.components:
            component.selected = False
        glyph.selected = False

    def lockToolBars(self):
        action = self.sender()
        movable = not action.isChecked()
        for toolBar in (
                self._toolsToolBar, self._buttonsToolBar, self._layersToolBar):
            toolBar.setMovable(movable)

    # --------------------------
    # Tools & buttons management
    # --------------------------

    def installTool(self, tool):
        # TODO: add shortcut with number
        action = self._toolsToolBar.addAction(
            QIcon(tool.iconPath), tool.name, self._setViewTool)
        action.setCheckable(True)
        action.setData(len(self._tools))
        self._toolsActionGroup.addAction(action)
        self._tools.append(tool(parent=self.view))
        return action

    def uninstallTool(self, tool):
        pass  # XXX

    def _setViewTool(self):
        action = self.sender()
        action.setChecked(True)
        index = action.data()
        self.view.currentTool = self._tools[index]

    def installButton(self, button):
        action = self._buttonsToolBar.addAction(
            QIcon(button.iconPath), button.name, self._buttonAction)
        action.setData(len(self._buttons))
        self._buttons.append(button(parent=self.view))
        return action

    def uninstallButton(self, button):
        pass  # XXX

    def _buttonAction(self):
        action = self.sender()
        index = action.data()
        button = self._buttons[index]
        button.clicked()

    # --------------------
    # Notification support
    # --------------------

    # glyph

    def _subscribeToGlyph(self, glyph):
        if glyph is not None:
            glyph.addObserver(self, "_glyphChanged", "Glyph.Changed")
            glyph.addObserver(self, "_glyphNameChanged", "Glyph.NameChanged")
            glyph.addObserver(
                self, "_glyphSelectionChanged", "Glyph.SelectionChanged")
            self._subscribeToFontAndLayerSet(glyph.font)

    def _unsubscribeFromGlyph(self, glyph):
        if glyph is not None:
            glyph.removeObserver(self, "Glyph.Changed")
            glyph.removeObserver(self, "Glyph.NameChanged")
            glyph.removeObserver(self, "Glyph.SelectionChanged")
            self._unsubscribeFromFontAndLayerSet(glyph.font)

    def _glyphChanged(self, notification):
        self.view.glyphChanged()

    def _glyphNameChanged(self, notification):
        glyph = self.view.glyph()
        self.setWindowTitle(glyph.name, glyph.font)

    def _glyphSelectionChanged(self, notification):
        self._updateSelection()
        self.view.glyphChanged()

    def _fontInfoChanged(self, notification):
        self.view.fontInfoChanged()
        glyph = self.view.glyph()
        self.setWindowTitle(glyph.name, glyph.font)

    # layers & font

    def _subscribeToFontAndLayerSet(self, font):
        """Note: called by _subscribeToGlyph."""
        if font is None:
            return
        font.info.addObserver(self, "_fontInfoChanged", "Info.Changed")
        layerSet = font.layers
        if layerSet is None:
            return
        layerSet.addObserver(self, '_layerSetLayerDeleted',
                             'LayerSet.LayerDeleted')
        for event in ('LayerSet.LayerAdded', 'LayerSet.LayerChanged',
                      'LayerSet.LayerOrderChanged'):
            layerSet.addObserver(self, '_layerSetEvents', event)

    def _unsubscribeFromFontAndLayerSet(self, font):
        """Note: called by _unsubscribeFromGlyph."""
        if font is None:
            return
        font.info.removeObserver(self, "Info.Changed")
        layerSet = font.layers
        if layerSet is None:
            return
        for event in ('LayerSet.LayerAdded', 'LayerSet.LayerChanged',
                      'LayerSet.LayerOrderChanged', 'LayerSet.LayerDeleted'):
            layerSet.removeObserver(self, event)

    def _layerSetEvents(self, notification):
        self._updateLayerBox()

    def _layerSetLayerDeleted(self, notification):
        self._layerSetEvents(notification)
        self._currentLayerBox.setCurrentIndex(0)

    # other updaters

    def _updateUndoRedo(self):
        glyph = self.view.glyph()
        undoManager = glyph.undoManager
        self._undoAction.setEnabled(glyph.canUndo())
        undoManager.canUndoChanged.connect(self._undoAction.setEnabled)
        self._redoAction.setEnabled(glyph.canRedo())
        undoManager.canRedoChanged.connect(self._redoAction.setEnabled)

    def _updateSelection(self):
        def hasSelection():
            glyph = self.view.glyph()
            for contour in glyph:
                if len(contour.selection):
                    return True
            for anchor in glyph.anchors:
                if anchor.selected:
                    return True
            for component in glyph.components:
                if component.selected:
                    return True
            return False
        self._copyAction.setEnabled(hasSelection())

    # --------------
    # Public Methods
    # --------------

    def setGlyph(self, glyph):
        currentGlyph = self.view.glyph()
        self._unsubscribeFromGlyph(currentGlyph)
        self._subscribeToGlyph(glyph)
        self.view.setGlyph(glyph)
        self._updateLayerBox()
        self._updateUndoRedo()
        self._updateSelection()
        self.setWindowTitle(glyph.name, glyph.font)

    def setDrawingAttribute(self, attr, value, layerName=None):
        self.view.setDrawingAttribute(attr, value, layerName)

    def drawingAttribute(self, attr, layerName=None):
        return self.view.drawingAttribute(attr, layerName)

    # -----------------
    # Layers management
    # -----------------

    def _layerChanged(self, newLayerIndex):
        glyph = self.view.glyph()
        layer = self._currentLayerBox.itemData(newLayerIndex)
        if layer is None:
            layer = self._makeLayer()
            if layer is None:
                # restore comboBox to active index
                layerSet = glyph.layerSet
                index = layerSet.layerOrder.index(glyph.layer.name)
                self._setLayerBoxIndex(index)
                return

        if glyph.name in layer:
            newGlyph = layer[glyph.name]
        else:
            # TODO: make sure we mimic defcon ufo3 APIs for that
            newGlyph = self._makeLayerGlyph(layer, glyph)
        self.setGlyph(newGlyph)

        # setting the layer-glyph here
        app = QApplication.instance()
        app.setCurrentGlyph(newGlyph)

    def _makeLayer(self):
        # TODO: what with duplicate names?
        glyph = self.view.glyph()
        newLayerName, ok = AddLayerDialog.getNewLayerName(self)
        if ok:
            layerSet = glyph.layerSet
            # TODO: this should return the layer
            layerSet.newLayer(newLayerName)
            return layerSet[newLayerName]
        else:
            return None

    def _makeLayerGlyph(self, layer, currentGlyph):
        glyph = layer.newGlyph(currentGlyph.name)
        glyph.width = currentGlyph.width
        glyph.template = True
        return glyph

    def _updateLayerBox(self):
        comboBox = self._currentLayerBox
        glyph = self.view.glyph()
        comboBox.blockSignals(True)
        comboBox.clear()
        for layer in glyph.layerSet:
            comboBox.addItem(layer.name, layer)
        comboBox.setCurrentText(glyph.layer.name)
        comboBox.addItem("New layer…", None)
        comboBox.blockSignals(False)

    def _setLayerBoxIndex(self, index):
        comboBox = self._currentLayerBox
        comboBox.blockSignals(True)
        comboBox.setCurrentIndex(index)
        comboBox.blockSignals(False)

    # ---------------------
    # QMainWindow functions
    # ---------------------

    def event(self, event):
        if event.type() == QEvent.WindowActivate:
            app = QApplication.instance()
            app.setCurrentGlyph(self.view.glyph())
        return super().event(event)

    def closeEvent(self, event):
        glyph = self.view.glyph()
        self._unsubscribeFromGlyph(glyph)
        event.accept()

    def setWindowTitle(self, title, font=None):
        if font is not None:
            title = "%s – %s %s" % (
                title, font.info.familyName, font.info.styleName)
        super().setWindowTitle(title)


class GlyphView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._currentTool = BaseTool()
        self._glyph = None

        # drawing attributes
        self._layerDrawingAttributes = {}
        self._fallbackDrawingAttributes = dict(
            showGlyphFill=False,
            showGlyphStroke=True,
            showGlyphOnCurvePoints=True,
            showGlyphStartPoints=True,
            showGlyphOffCurvePoints=True,
            showGlyphPointCoordinates=False,
            showGlyphAnchors=True,
            showGlyphImage=False,
            showGlyphMargins=True,
            showFontVerticalMetrics=True,
            showFontVerticalMetricsTitles=True,
            showFontPostscriptBlues=False,
            showFontPostscriptFamilyBlues=False,
        )

        # cached vertical metrics
        self._unitsPerEm = 1000
        self._descender = -250
        self._capHeight = 750
        self._ascender = 750

        # drawing data cache
        self._drawingRect = None
        self._scale = 1.0
        self._inverseScale = 0.1
        self._impliedPointSize = 1000

        # drawing calculation
        self._centerVertically = True
        self._centerHorizontally = True
        self._noPointSizePadding = 200
        self._verticalCenterYBuffer = 0

        # insert scrollArea
        self.setFocusPolicy(Qt.ClickFocus)
        self._scrollArea = QScrollArea(parent)
        self._scrollArea.resizeEvent = self.resizeEvent
        self._scrollArea.setWidget(self)

    # --------------
    # Custom Methods
    # --------------

    def _getGlyphWidthHeight(self):
        if self._glyph is None:
            return 0, 0
        bounds = self._glyph.bounds
        if bounds is not None:
            left, bottom, right, top = self._glyph.bounds
        else:
            left = right = bottom = top = 0
        left = min(0, left)
        right = max(right, self._glyph.width)
        bottom = self._descender
        top = max(self._capHeight, self._ascender,
                  self._unitsPerEm + self._descender)
        width = abs(left) + right
        height = -bottom + top
        return width, height

    # TODO: this is fit to font metrics. Add a fit to bbox facility as well.
    def _fitScale(self):
        fitHeight = self._scrollArea.viewport().height()
        _, glyphHeight = self._getGlyphWidthHeight()
        glyphHeight += self._noPointSizePadding * 2
        self.setScale(fitHeight / glyphHeight)

    def inverseScale(self):
        return self._inverseScale

    def scale(self):
        return self._scale

    def setScale(self, scale):
        self._scale = scale
        if self._scale <= 0:
            self._scale = .01
        self._inverseScale = 1.0 / self._scale
        self._impliedPointSize = self._unitsPerEm * self._scale

    def glyph(self):
        return self._glyph

    def setGlyph(self, glyph):
        self._glyph = glyph
        self._font = None
        if glyph is not None:
            font = self._font = glyph.font
            if font is not None:
                self._unitsPerEm = font.info.unitsPerEm
                if self._unitsPerEm is None:
                    self._unitsPerEm = 1000
                self._descender = font.info.descender
                if self._descender is None:
                    self._descender = -250
                self._ascender = font.info.ascender
                if self._ascender is None:
                    self._ascender = self._unitsPerEm + self._descender
                self._capHeight = font.info.capHeight
                if self._capHeight is None:
                    self._capHeight = self._ascender
            self.setScale(self._scale)
            self.adjustSize()
        self._currentTool.toolActivated()
        self.update()

    # --------------------
    # Notification Support
    # --------------------

    def glyphChanged(self):
        self.update()

    def fontInfoChanged(self):
        self.setGlyph(self._glyph)

    # ---------------
    # Display Control
    # ---------------

    def drawingAttribute(self, attr, layerName):
        if layerName is None:
            return self._fallbackDrawingAttributes.get(attr)
        d = self._layerDrawingAttributes.get(layerName, {})
        return d.get(attr)

    def setDrawingAttribute(self, attr, value, layerName):
        if layerName is None:
            self._fallbackDrawingAttributes[attr] = value
        else:
            if layerName not in self._layerDrawingAttributes:
                self._layerDrawingAttributes[layerName] = {}
            self._layerDrawingAttributes[layerName][attr] = value
        self.update()

    def showFill(self):
        return self.drawingAttribute("showGlyphFill", None)

    def setShowFill(self, value):
        self.setDrawingAttribute("showGlyphFill", value, None)

    def showStroke(self):
        return self.drawingAttribute("showGlyphStroke", None)

    def setShowStroke(self, value):
        self.setDrawingAttribute("showGlyphStroke", value, None)

    def showMetrics(self):
        return self.drawingAttribute("showGlyphMargins", None)

    def setShowMetrics(self, value):
        self.setDrawingAttribute("showGlyphMargins", value, None)
        self.setDrawingAttribute("showFontVerticalMetrics", value, None)

    def showImage(self):
        return self.drawingAttribute("showGlyphImage", None)

    def setShowImage(self, value):
        self.setDrawingAttribute("showGlyphImage", value, None)

    def showMetricsTitles(self):
        return self.drawingAttribute("showFontVerticalMetricsTitles", None)

    def setShowMetricsTitles(self, value):
        self.setDrawingAttribute("showFontVerticalMetricsTitles", value, None)

    def showOnCurvePoints(self):
        return self.drawingAttribute("showGlyphOnCurvePoints", None)

    def setShowOnCurvePoints(self, value):
        self.setDrawingAttribute("showGlyphStartPoints", value, None)
        self.setDrawingAttribute("showGlyphOnCurvePoints", value, None)

    def showOffCurvePoints(self):
        return self.drawingAttribute("showGlyphOffCurvePoints", None)

    def setShowOffCurvePoints(self, value):
        self.setDrawingAttribute("showGlyphOffCurvePoints", value, None)

    def showPointCoordinates(self):
        return self.drawingAttribute("showGlyphPointCoordinates", None)

    def setShowPointCoordinates(self, value):
        self.setDrawingAttribute("showGlyphPointCoordinates", value, None)

    def showAnchors(self):
        return self.drawingAttribute("showGlyphAnchors", None)

    def setShowAnchors(self, value):
        self.setDrawingAttribute("showGlyphAnchors", value, None)

    def showBlues(self):
        return self.drawingAttribute("showFontPostscriptBlues", None)

    def setShowBlues(self, value):
        self.setDrawingAttribute("showFontPostscriptBlues", value, None)

    def showFamilyBlues(self):
        return self.drawingAttribute("showFontPostscriptFamilyBlues", None)

    def setShowFamilyBlues(self, value):
        self.setDrawingAttribute("showFontPostscriptFamilyBlues", value, None)

    # ---------------
    # Drawing helpers
    # ---------------

    def drawImage(self, painter, glyph, layerName):
        drawing.drawGlyphImage(
            painter, glyph, self._inverseScale, self._drawingRect)

    def drawBlues(self, painter, glyph, layerName):
        drawing.drawFontPostscriptBlues(
            painter, glyph, self._inverseScale, self._drawingRect)

    def drawFamilyBlues(self, painter, glyph, layerName):
        drawing.drawFontPostscriptFamilyBlues(
            painter, glyph, self._inverseScale, self._drawingRect)

    def drawVerticalMetrics(self, painter, glyph, layerName):
        drawText = self._impliedPointSize > 175
        drawing.drawFontVerticalMetrics(
            painter, glyph, self._inverseScale, self._drawingRect,
            drawText=drawText)

    def drawMargins(self, painter, glyph, layerName):
        drawing.drawGlyphMargins(
            painter, glyph, self._inverseScale, self._drawingRect)

    def drawFillAndStroke(self, painter, glyph, layerName):
        partialAliasing = self._impliedPointSize > 175
        showFill = self.drawingAttribute("showGlyphFill", layerName)
        showStroke = self.drawingAttribute("showGlyphStroke", layerName)
        drawing.drawGlyphFillAndStroke(
            painter, glyph, self._inverseScale, self._drawingRect,
            drawFill=showFill, drawStroke=showStroke,
            partialAliasing=partialAliasing)

    def drawPoints(self, painter, glyph, layerName):
        drawStartPoints = self.drawingAttribute(
            "showGlyphStartPoints", layerName) and self._impliedPointSize > 175
        drawOnCurves = self.drawingAttribute(
            "showGlyphOnCurvePoints", layerName) and \
            self._impliedPointSize > 175
        drawOffCurves = self.drawingAttribute(
            "showGlyphOffCurvePoints", layerName) and \
            self._impliedPointSize > 175
        drawCoordinates = self.drawingAttribute(
            "showGlyphPointCoordinates", layerName) and \
            self._impliedPointSize > 250
        drawing.drawGlyphPoints(
            painter, glyph, self._inverseScale, self._drawingRect,
            drawStartPoints=drawStartPoints, drawOnCurves=drawOnCurves,
            drawOffCurves=drawOffCurves, drawCoordinates=drawCoordinates,
            backgroundColor=Qt.white)

    def drawAnchors(self, painter, glyph, layerName):
        if not self._impliedPointSize > 175:
            return
        drawing.drawGlyphAnchors(
            painter, glyph, self._inverseScale, self._drawingRect)

    # ---------------
    # QWidget methods
    # ---------------

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setFont(headerFont)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()

        # draw the background
        painter.fillRect(rect, Qt.white)
        if self._glyph is None:
            return

        # apply the overall scale
        painter.save()
        # + translate and flip
        painter.translate(0, self.height())
        painter.scale(self._scale, -self._scale)

        # move into position
        widgetWidth = self.width()
        width = self._glyph.width * self._scale
        diff = widgetWidth - width
        xOffset = round((diff / 2) * self._inverseScale)

        yOffset = self._verticalCenterYBuffer * self._inverseScale
        yOffset -= self._descender

        painter.translate(xOffset, yOffset)

        # store the current drawing rect
        w, h = self.width(), self.height()
        w *= self._inverseScale
        h *= self._inverseScale
        self._drawingRect = (-xOffset, -yOffset, w, h)

        # gather the layers
        layerSet = self._glyph.layerSet
        if layerSet is None:
            layers = [(self._glyph, None)]
        else:
            glyphName = self._glyph.name
            layers = []
            for layerName in reversed(layerSet.layerOrder):
                layer = layerSet[layerName]
                if glyphName not in layer:
                    continue
                glyph = layer[glyphName]
                if glyph == self._glyph:
                    layerName = None
                layers.append((glyph, layerName))

        for glyph, layerName in layers:
            # draw the image
            if self.drawingAttribute("showGlyphImage", layerName):
                self.drawImage(painter, glyph, layerName)
            # draw the blues
            if layerName is None and self.drawingAttribute(
                    "showFontPostscriptBlues", None):
                self.drawBlues(painter, glyph, layerName)
            if layerName is None and self.drawingAttribute(
                    "showFontPostscriptFamilyBlues", None):
                self.drawFamilyBlues(painter, glyph, layerName)
            # draw the margins
            if self.drawingAttribute("showGlyphMargins", layerName):
                self.drawMargins(painter, glyph, layerName)
            # draw the vertical metrics
            if layerName is None and self.drawingAttribute(
                    "showFontVerticalMetrics", None):
                self.drawVerticalMetrics(painter, glyph, layerName)
            # draw the glyph
            if self.drawingAttribute("showGlyphFill", layerName) or \
                    self.drawingAttribute("showGlyphStroke", layerName):
                # XXX: trying to debug an assertion failure
                try:
                    self.drawFillAndStroke(painter, glyph, layerName)
                except AssertionError as e:
                    import traceback
                    print("**********")
                    print("Internal error:", str(e))
                    print()
                    print(traceback.print_exc())
                    print()
                    for contour in self._glyph:
                        for point in contour:
                            print(point)
                        print()
                    print("**********")
                    painter.restore()
                    return
            if self.drawingAttribute("showGlyphOnCurvePoints", layerName) or \
                    self.drawingAttribute("showGlyphOffCurvePoints",
                                          layerName):
                self.drawPoints(painter, glyph, layerName)
            if self.drawingAttribute("showGlyphAnchors", layerName):
                self.drawAnchors(painter, glyph, layerName)
        self._currentTool.paint(painter)
        painter.restore()

    def scrollArea(self):
        return self._scrollArea

    def sizeHint(self):
        viewport = self._scrollArea.viewport()
        scrollWidth, scrollHeight = viewport.width(), viewport.height()
        # pick the width and height
        glyphWidth, glyphHeight = self._getGlyphWidthHeight()
        glyphWidth = glyphWidth * self._scale
        glyphHeight = glyphHeight * self._scale
        xOffset = 1000 * 2 * self._scale
        yOffset = xOffset
        width = glyphWidth + xOffset
        height = glyphHeight + yOffset
        if scrollWidth > width:
            width = scrollWidth
        if scrollHeight > height:
            height = scrollHeight
        # calculate and store the vertical centering offset
        self._verticalCenterYBuffer = (height - glyphHeight) / 2.0
        return QSize(width, height)

    def resizeEvent(self, event):
        self.adjustSize()
        event.accept()

    def showEvent(self, event):
        self._fitScale()
        self.adjustSize()
        hSB = self._scrollArea.horizontalScrollBar()
        vSB = self._scrollArea.verticalScrollBar()
        hSB.setValue((hSB.minimum() + hSB.maximum()) / 2)
        vSB.setValue((vSB.minimum() + vSB.maximum()) / 2)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            factor = pow(1.2, event.angleDelta().y() / 120.0)
            pos = event.pos()
            # compute new scrollbar position
            # http://stackoverflow.com/a/32269574/2037879
            oldScale = self._scale
            newScale = self._scale * factor
            hSB = self._scrollArea.horizontalScrollBar()
            vSB = self._scrollArea.verticalScrollBar()
            scrollBarPos = QPointF(hSB.value(), vSB.value())
            deltaToPos = (self.mapToParent(pos) - self.pos()) / oldScale
            delta = deltaToPos * (newScale - oldScale)
            # TODO: maybe put out a func that does multiply by default
            self.setScale(newScale)
            # TODO: maybe merge this in setScale
            self.adjustSize()
            self.update()
            hSB.setValue(scrollBarPos.x() + delta.x())
            vSB.setValue(scrollBarPos.y() + delta.y())
            event.accept()
        else:
            super().wheelEvent(event)

    # ------------
    # Canvas tools
    # ------------

    # current tool

    @property
    def currentTool(self):
        return self._currentTool

    @currentTool.setter
    def currentTool(self, tool):
        self._currentTool = tool
        self._currentTool.toolActivated()

    # event directing

    def mapToCanvas(self, pos):
        """
        Map *pos* from GlyphView widget to canvas coordinates.

        Note that canvas coordinates are scale-independent while widget
        coordinates are not.
        Mouse events sent to tools are in canvas coordinates.
        """
        xOffsetInv, yOffsetInv, _, _ = self._drawingRect
        x = pos.x() * self._inverseScale + xOffsetInv
        y = (pos.y() - self.height()) * (- self._inverseScale) + yOffsetInv
        return QPointF(x, y)

    def mapToWidget(self, pos):
        """
        Map *pos* from canvas to GlyphView widget coordinates.

        Note that canvas coordinates are scale-independent while widget
        coordinates are not.
        Mouse events sent to tools are in canvas coordinates.
        """
        xOffsetInv, yOffsetInv, _, _ = self._drawingRect
        x = (pos.x() - xOffsetInv) / self._inverseScale
        y = (pos.y() - yOffsetInv) / (- self._inverseScale) + self.height()
        return QPointF(x, y)

    def _redirectEvent(self, event, callback, transmuteMouseEvent=False):
        if transmuteMouseEvent:
            # construct a new event with pos in canvas coordinates
            canvasPos = self.mapToCanvas(event.localPos())
            event = QMouseEvent(
                event.type(),
                canvasPos,
                event.windowPos(),
                event.screenPos(),
                event.button(),
                event.buttons(),
                event.modifiers()
            )
        callback(event)

    def keyPressEvent(self, event):
        self._redirectEvent(event, self._currentTool.keyPressEvent)

    def keyReleaseEvent(self, event):
        self._redirectEvent(event, self._currentTool.keyReleaseEvent)

    def mousePressEvent(self, event):
        self._redirectEvent(event, self._currentTool.mousePressEvent, True)

    def mouseMoveEvent(self, event):
        self._redirectEvent(event, self._currentTool.mouseMoveEvent, True)

    def mouseReleaseEvent(self, event):
        self._redirectEvent(event, self._currentTool.mouseReleaseEvent, True)

    def mouseDoubleClickEvent(self, event):
        self._redirectEvent(
            event, self._currentTool.mouseDoubleClickEvent, True)

    # items location

    def _itemsAt(self, func, obj, justOne=True):
        """
        Go through all anchors, points and components (in this order) in the
        glyph, construct their canvas path and list items for which
        *func(path, obj)* returns True, or only return the first item if
        *justOne* is set to True.

        An item is a (point, contour) or (anchor, None) or (component, None)
        tuple. The second argument permits accessing parent contour to post
        notifications.

        Here is a sample *func* function that tests whether item with path
        *path* contains *pos*:

            def myFunction(path, pos):
                return path.contains(pos)

        This is useful to find out whether an item was clicked on canvas.
        """
        scale = self._inverseScale
        # TODO: export this from drawing or use QSettings.
        # anchor
        anchorSize = 6 * scale
        anchorHalfSize = anchorSize / 2
        # offCurve
        offWidth = 5 * scale
        offHalf = offWidth / 2.0
        # onCurve
        onWidth = 7 * scale
        onHalf = onWidth / 2.0
        # onCurve smooth
        smoothWidth = 8 * scale
        smoothHalf = smoothWidth / 2.0

        if not justOne:
            ret = dict(
                anchors=[],
                contours=[],
                points=[],
                components=[],
            )
        for anchor in reversed(self._glyph.anchors):
            path = QPainterPath()
            path.addEllipse(anchor.x - anchorHalfSize,
                            anchor.y - anchorHalfSize, anchorSize, anchorSize)
            if func(path, obj):
                if justOne:
                    return (anchor, None)
                ret["anchors"].append(anchor)
        for contour in reversed(self._glyph):
            for point in contour:
                path = QPainterPath()
                if point.segmentType is None:
                    x = point.x - offHalf
                    y = point.y - offHalf
                    path.addEllipse(x, y, offWidth, offWidth)
                elif point.smooth:
                    x = point.x - smoothHalf
                    y = point.y - smoothHalf
                    path.addEllipse(x, y, smoothWidth, smoothWidth)
                else:
                    x = point.x - onHalf
                    y = point.y - onHalf
                    path.addRect(x, y, onWidth, onWidth)
                if func(path, obj):
                    if justOne:
                        return (point, contour)
                    ret["contours"].append(contour)
                    ret["points"].append(point)
        for component in reversed(self._glyph.components):
            path = component.getRepresentation("defconQt.QPainterPath")
            if func(path, obj):
                if justOne:
                    return (component, None)
                ret["components"].append(component)
        if not justOne:
            return ret
        return None

    def itemAt(self, pos):
        """
        Find one item at *pos*.

        An item is a (point, contour) or (anchor, None) or (component, None)
        tuple.
        """
        return self.itemsAt(pos, True)

    def itemsAt(self, pos, items=False):
        """
        Find items at *pos*.
        """
        return self._itemsAt(lambda path, pos: path.contains(pos), pos, items)

    def items(self, rect):
        """
        Find items that intersect with *rect* (can be any QPainterPath).
        """
        return self._itemsAt(
            lambda path, rect: path.intersects(rect), rect, False)
