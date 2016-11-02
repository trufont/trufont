from defconQt.controls.glyphView import (
    GlyphView, GlyphViewMinSizeForDetails, GlyphWidget)
from defconQt.windows.baseWindows import BaseMainWindow
from trufont.controls.glyphDialogs import (
    AddLayerDialog, FindDialog, LayerActionsDialog)
from trufont.drawingTools.baseTool import BaseTool
from trufont.drawingTools.removeOverlapButton import RemoveOverlapButton
from trufont.objects import settings
from trufont.objects.menu import Entries
from trufont.tools import drawing, errorReports
from trufont.tools.uiMethods import deleteUISelection, UIGlyphGuidelines
from PyQt5.QtCore import (
    QBuffer, QByteArray, QEvent, QIODevice, QMimeData, QRectF,
    QSize, Qt)
from PyQt5.QtGui import (
    QIcon, QImage, QImageReader, QKeySequence, QMouseEvent, QPainterPath,
    QPainterPathStroker, QTransform)
from PyQt5.QtWidgets import (
    QApplication, QComboBox, QSizePolicy, QToolBar, QWidget)
import os
import pickle


class GlyphWindow(BaseMainWindow):

    def __init__(self, glyph, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setUnifiedTitleAndToolBarOnMac(True)

        self.view = GlyphCanvasView(self)
        # create tools and buttons toolBars
        self._tools = []
        self._toolsToolBar = QToolBar(self.tr("Tools"), self)
        self._toolsToolBar.setMovable(False)
        self._buttons = []
        self._buttonsToolBar = QToolBar(self.tr("Buttons"), self)
        self._buttonsToolBar.setMovable(False)
        self.addToolBar(self._toolsToolBar)
        self.addToolBar(self._buttonsToolBar)

        # http://www.setnode.com/blog/right-aligning-a-button-in-a-qtoolbar/
        self._layersToolBar = QToolBar(self.tr("Layers"), self)
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

        self.setGlyph(glyph)
        app = QApplication.instance()
        tools = app.drawingTools()
        for index, tool in enumerate(tools):
            action = self.installTool(tool)
            if not index:
                action.trigger()
        app.dispatcher.addObserver(
            self, "_drawingToolRegistered", "drawingToolRegistered")
        # TODO: drawingToolUnregistered
        self.installButton(RemoveOverlapButton)

        self.setCentralWidget(self.view)
        self.view.setFocus(True)

        self.readSettings()

    def readSettings(self):
        geometry = settings.glyphWindowGeometry()
        if geometry:
            self.restoreGeometry(geometry)

    def writeSettings(self):
        # TODO: save current tool?
        settings.setGlyphWindowGeometry(self.saveGeometry())

    def setupMenu(self, menuBar):
        fileMenu = menuBar.fetchMenu(Entries.File)
        fontWindow = self.parent()
        if fontWindow is not None:
            fileMenu.fetchAction(Entries.File_Save, fontWindow.saveFile)
            fileMenu.fetchAction(Entries.File_Save_As, fontWindow.saveFileAs)
        fileMenu.fetchAction(Entries.File_Close, self.close)
        if fontWindow is not None:
            fileMenu.fetchAction(Entries.File_Reload, fontWindow.reloadFile)

        editMenu = menuBar.fetchMenu(Entries.Edit)
        self._undoAction = editMenu.fetchAction(Entries.Edit_Undo, self.undo)
        self._redoAction = editMenu.fetchAction(Entries.Edit_Redo, self.redo)
        editMenu.addSeparator()
        cutAction = editMenu.fetchAction(Entries.Edit_Cut, self.cutOutlines)
        copyAction = editMenu.fetchAction(Entries.Edit_Copy, self.copyOutlines)
        self._selectActions = (cutAction, copyAction)
        editMenu.fetchAction(Entries.Edit_Paste, self.pasteOutlines)
        editMenu.fetchAction(Entries.Edit_Select_All, self.selectAll)
        editMenu.fetchAction(Entries.Edit_Find, self.changeGlyph)
        # TODO: sort this out
        # editMenu.fetchAction(self.tr("&Deselect"), self.deselect, "Ctrl+D")

        # glyphMenu = menuBar.fetchMenu(self.tr("&Glyph"))
        # self._layerAction = glyphMenu.fetchAction(
        #     self.tr("&Layer Actions…"), self.layerActions, "L")

        viewMenu = menuBar.fetchMenu(Entries.View)
        viewMenu.fetchAction(Entries.View_Zoom_In, lambda: self.view.zoom(1))
        viewMenu.fetchAction(Entries.View_Zoom_Out, lambda: self.view.zoom(-1))
        viewMenu.fetchAction(Entries.View_Reset_Zoom, self.view.fitScaleBBox)
        viewMenu.addSeparator()
        viewMenu.fetchAction(
            Entries.View_Next_Glyph, lambda: self.glyphOffset(1))
        viewMenu.fetchAction(
            Entries.View_Previous_Glyph, lambda: self.glyphOffset(-1))

        self._updateUndoRedo()

    # ----------
    # Menu items
    # ----------

    def saveFile(self):
        glyph = self.view.glyph()
        font = glyph.font
        if None not in (font, font.path):
            font.save()

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
        newGlyph, ok = FindDialog.getNewGlyph(self, glyph)
        if ok and newGlyph is not None:
            self.setGlyph(newGlyph)

    def layerActions(self):
        glyph = self.view.glyph()
        newLayer, action, ok = LayerActionsDialog.getLayerAndAction(
            self, glyph)
        if ok and newLayer is not None:
            # TODO: whole glyph for now, but consider selection too
            if glyph.name not in newLayer:
                newLayer.newGlyph(glyph.name)
            otherGlyph = newLayer[glyph.name]
            otherGlyph.holdNotifications()
            if action == "Swap":
                tempGlyph = glyph.__class__()
                otherGlyph.drawPoints(tempGlyph.getPointPen())
                tempGlyph.width = otherGlyph.width
                otherGlyph.clearContours()
            glyph.drawPoints(otherGlyph.getPointPen())
            otherGlyph.width = glyph.width
            if action != "Copy":
                glyph.holdNotifications()
                glyph.clearContours()
                if action == "Swap":
                    tempGlyph.drawPoints(glyph.getPointPen())
                    glyph.width = tempGlyph.width
                glyph.releaseHeldNotifications()
            otherGlyph.releaseHeldNotifications()

    def undo(self):
        glyph = self.view.glyph()
        glyph.undo()

    def redo(self):
        glyph = self.view.glyph()
        glyph.redo()

    def cutOutlines(self):
        glyph = self.view.glyph()
        self.copyOutlines()
        deleteUISelection(glyph)

    def copyOutlines(self):
        glyph = self.view.glyph()
        clipboard = QApplication.clipboard()
        mimeData = QMimeData()
        copyGlyph = glyph.getRepresentation("TruFont.FilterSelection")
        mimeData.setData("application/x-trufont-glyph-data",
                         pickle.dumps([copyGlyph.serialize(
                             blacklist=("name", "unicode")
                         )]))
        clipboard.setMimeData(mimeData)

    def pasteOutlines(self):
        glyph = self.view.glyph()
        clipboard = QApplication.clipboard()
        mimeData = clipboard.mimeData()
        if mimeData.hasFormat("application/x-trufont-glyph-data"):
            data = pickle.loads(mimeData.data(
                "application/x-trufont-glyph-data"))
            if len(data) == 1:
                pen = glyph.getPointPen()
                pasteGlyph = glyph.__class__()
                pasteGlyph.deserialize(data[0])
                # TODO: if we serialize selected state, we don't need to do
                # this
                pasteGlyph.selected = True
                if len(pasteGlyph) or len(pasteGlyph.components) or \
                        len(pasteGlyph.anchors):
                    glyph.prepareUndo()
                    pasteGlyph.drawPoints(pen)

    def selectAll(self):
        glyph = self.view.glyph()
        if glyph.selected:
            for anchor in glyph.anchors:
                anchor.selected = True
            for component in glyph.components:
                component.selected = True
        else:
            glyph.selected = True

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
        action = self._toolsToolBar.addAction(
            QIcon(tool.iconPath), tool.name, self._setViewTool)
        action.setCheckable(True)
        num = len(self._tools)
        action.setData(num)
        action.setShortcut(QKeySequence(str(num + 1)))
        self._tools.append(tool(parent=self.view.widget()))
        return action

    def uninstallTool(self, tool):
        pass  # XXX

    def _setViewTool(self):
        action = self.sender()
        index = action.data()
        newTool = self._tools[index]
        if newTool == self.view.currentTool():
            action.setChecked(True)
            return
        ok = self.view.setCurrentTool(newTool)
        # if view did change tool, disable them all and enable the one we want
        # otherwise, just disable the tool that was clicked.
        # previously we used QActionGroup to have exclusive buttons, but doing
        # it manually allows us to NAK a button change.
        if ok:
            for act in self._toolsToolBar.actions():
                act.setChecked(False)
        action.setChecked(ok)

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

    # -------------
    # Notifications
    # -------------

    # app

    def _drawingToolRegistered(self, notification):
        tool = notification.data["tool"]
        self.installTool(tool)

    # glyph

    def _subscribeToGlyph(self, glyph):
        if glyph is not None:
            glyph.addObserver(self, "_glyphNameChanged", "Glyph.NameChanged")
            glyph.addObserver(
                self, "_glyphSelectionChanged", "Glyph.SelectionChanged")
            undoManager = glyph.undoManager
            undoManager.canUndoChanged.connect(self._setUndoEnabled)
            undoManager.canRedoChanged.connect(self._setRedoEnabled)
            self._subscribeToFontAndLayerSet(glyph.font)

    def _unsubscribeFromGlyph(self, glyph):
        if glyph is not None:
            glyph.removeObserver(self, "Glyph.NameChanged")
            glyph.removeObserver(self, "Glyph.SelectionChanged")
            undoManager = glyph.undoManager
            undoManager.canUndoChanged.disconnect(self._setUndoEnabled)
            undoManager.canRedoChanged.disconnect(self._setRedoEnabled)
            self._unsubscribeFromFontAndLayerSet(glyph.font)

    def _glyphNameChanged(self, notification):
        glyph = self.view.glyph()
        self.setWindowTitle(glyph.name, glyph.font)

    def _glyphSelectionChanged(self, notification):
        self._updateSelection()

    # layers & font

    def _subscribeToFontAndLayerSet(self, font):
        """Note: called by _subscribeToGlyph."""
        if font is None:
            return
        font.info.addObserver(self, "_fontInfoChanged", "Info.Changed")
        layerSet = font.layers
        if layerSet is None:
            return
        layerSet.addObserver(
            self, '_layerSetLayerDeleted', 'LayerSet.LayerDeleted')
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

    def _fontInfoChanged(self, notification):
        glyph = self.view.glyph()
        self.setWindowTitle(glyph.name, glyph.font)

    def _layerSetEvents(self, notification):
        self._updateLayerControls()

    def _layerSetLayerDeleted(self, notification):
        self._layerSetEvents(notification)
        self._currentLayerBox.setCurrentIndex(0)

    # other updaters

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

        if not hasattr(self, "_selectActions"):
            return
        hasSelection = hasSelection()
        for action in self._selectActions:
            action.setEnabled(hasSelection)

    def _updateUndoRedo(self):
        glyph = self.view.glyph()
        self._setUndoEnabled(glyph.canUndo())
        self._setRedoEnabled(glyph.canRedo())

    def _setUndoEnabled(self, value):
        if not hasattr(self, "_undoAction"):
            return
        self._undoAction.setEnabled(value)

    def _setRedoEnabled(self, value):
        if not hasattr(self, "_redoAction"):
            return
        self._redoAction.setEnabled(value)

    # --------------
    # Public Methods
    # --------------

    def setGlyph(self, glyph):
        currentGlyph = self.view.glyph()
        self._unsubscribeFromGlyph(currentGlyph)
        self.view.setGlyph(glyph)
        self._subscribeToGlyph(glyph)
        self._updateLayerControls()
        self._updateUndoRedo()
        self._updateSelection()
        self.setWindowTitle(glyph.name, glyph.font)
        # setting the layer-glyph here
        app = QApplication.instance()
        app.setCurrentGlyph(glyph)

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

    def _makeLayer(self):
        # TODO: what with duplicate names?
        glyph = self.view.glyph()
        newLayerName, color, ok = AddLayerDialog.getNewLayerNameAndColor(self)
        if ok:
            layerSet = glyph.layerSet
            layer = layerSet.newLayer(newLayerName)
            layer.color = color
            return layer
        return None

    def _makeLayerGlyph(self, layer, currentGlyph):
        glyph = layer.newGlyph(currentGlyph.name)
        glyph.width = currentGlyph.width
        glyph.template = True
        return glyph

    def _updateLayerControls(self):
        comboBox = self._currentLayerBox
        glyph = self.view.glyph()
        comboBox.blockSignals(True)
        comboBox.clear()
        for layer in glyph.layerSet:
            comboBox.addItem(layer.name, layer)
        comboBox.setCurrentText(glyph.layer.name)
        comboBox.addItem(self.tr("New layer…"), None)
        comboBox.blockSignals(False)
        if not hasattr(self, "_layerAction"):
            return
        self._layerAction.setEnabled(len(glyph.layerSet) > 1)

    def _setLayerBoxIndex(self, index):
        comboBox = self._currentLayerBox
        comboBox.blockSignals(True)
        comboBox.setCurrentIndex(index)
        comboBox.blockSignals(False)

    # ---------------------
    # QMainWindow functions
    # ---------------------

    def sizeHint(self):
        return QSize(1100, 750)

    def moveEvent(self, event):
        self.writeSettings()

    resizeEvent = moveEvent

    def event(self, event):
        if event.type() == QEvent.WindowActivate:
            app = QApplication.instance()
            app.setCurrentGlyph(self.view.glyph())
        return super().event(event)

    def showEvent(self, event):
        app = QApplication.instance()
        data = dict(window=self)
        app.postNotification("glyphWindowWillOpen", data)
        super().showEvent(event)
        app.postNotification("glyphWindowOpened", data)

    def closeEvent(self, event):
        super().closeEvent(event)
        if event.isAccepted():
            app = QApplication.instance()
            app.dispatcher.removeObserver(self, "drawingToolRegistered")
            data = dict(window=self)
            app.postNotification("glyphWindowWillClose", data)
            glyph = self.view.glyph()
            self._unsubscribeFromGlyph(glyph)
            self.view.closeEvent(event)

    def setWindowTitle(self, title, font=None):
        if font is not None:
            title = "%s – %s %s" % (
                title, font.info.familyName, font.info.styleName)
        super().setWindowTitle(title)


class GlyphCanvasWidget(GlyphWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAcceptDrops(True)
        self._currentTool = BaseTool()
        self._mouseDown = False
        self._preview = False

        # inbound notification
        app = QApplication.instance()
        app.dispatcher.addObserver(self, "_needsUpdate", "glyphViewUpdate")

    # --------------
    # Custom Methods
    # --------------

    def setGlyph(self, glyph):
        app = QApplication.instance()
        app.postNotification("glyphViewGlyphWillChange")
        self._currentTool.toolDisabled()
        super().setGlyph(glyph)
        self._currentTool.toolActivated()
        app.postNotification("glyphViewGlyphChanged")

    # --------------------
    # Notifications
    # --------------------

    def _needsUpdate(self, notification):
        self.update()

    # ---------------
    # Drawing helpers
    # ---------------

    def drawingAttribute(self, attr, layerName):
        # TODO: work more on a sound model for this
        if attr == "showGlyphStroke":
            return True
        else:
            return super().drawingAttribute(attr, layerName)

    def drawBackground(self, painter):
        app = QApplication.instance()
        data = dict(
            widget=self,
            painter=painter,
        )
        app.postNotification("glyphViewDrawBackground", data)

    def drawGlyphLayer(self, painter, glyph, layerName):
        if self._preview:
            if layerName is None:
                self.drawFillAndStroke(painter, glyph, layerName)
        else:
            super().drawGlyphLayer(painter, glyph, layerName)

    def drawGuidelines(self, painter, glyph, layerName):
        drawText = self._impliedPointSize > GlyphViewMinSizeForDetails
        if self.drawingAttribute("showFontGuidelines", layerName):
            drawing.drawFontGuidelines(
                painter, glyph, self._inverseScale, self._drawingRect,
                drawText=drawText)
        if self.drawingAttribute("showGlyphGuidelines", layerName):
            drawing.drawGlyphGuidelines(
                painter, glyph, self._inverseScale, self._drawingRect,
                drawText=drawText)

    def drawFillAndStroke(self, painter, glyph, layerName):
        if self._preview:
            contourFillColor = componentFillColor = Qt.black
            drawSelection = False
            showFill = True
            showStroke = False
        else:
            contourFillColor = componentFillColor = None
            drawSelection = layerName is None
            showFill = self.drawingAttribute("showGlyphFill", layerName)
            showStroke = self.drawingAttribute("showGlyphStroke", layerName)
        drawing.drawGlyphFillAndStroke(
            painter, glyph, self._inverseScale, self._drawingRect,
            componentFillColor=componentFillColor,
            contourFillColor=contourFillColor, drawFill=showFill,
            drawSelection=drawSelection, drawStroke=showStroke)

    def drawPoints(self, painter, glyph, layerName):
        if not self._impliedPointSize > GlyphViewMinSizeForDetails:
            return
        drawStartPoints = self.drawingAttribute(
            "showGlyphStartPoints", layerName)
        drawOnCurves = self.drawingAttribute(
            "showGlyphOnCurvePoints", layerName)
        drawOffCurves = self.drawingAttribute(
            "showGlyphOffCurvePoints", layerName)
        drawCoordinates = self.drawingAttribute(
            "showGlyphPointCoordinates", layerName)
        drawing.drawGlyphPoints(
            painter, glyph, self._inverseScale, self._drawingRect,
            drawStartPoints=drawStartPoints, drawOnCurves=drawOnCurves,
            drawOffCurves=drawOffCurves, drawCoordinates=drawCoordinates)

    def drawAnchors(self, painter, glyph, layerName):
        if not self._impliedPointSize > GlyphViewMinSizeForDetails:
            return
        drawing.drawGlyphAnchors(
            painter, glyph, self._inverseScale, self._drawingRect)

    def drawForeground(self, painter):
        app = QApplication.instance()
        data = dict(
            widget=self,
            painter=painter,
        )
        app.postNotification("glyphViewDrawForeground", data)
        self._currentTool.paint(painter)

    # ---------------
    # QWidget methods
    # ---------------

    def closeEvent(self, event):
        super().closeEvent(event)
        if event.isAccepted():
            self._currentTool.toolDisabled()
            app = QApplication.instance()
            app.dispatcher.removeObserver(self, "glyphViewUpdate")

    def dragEnterEvent(self, event):
        mimeData = event.mimeData()
        if mimeData.hasUrls():
            url = mimeData.urls()[0]
            if url.isLocalFile():
                path = url.toLocalFile()
                ext = os.path.splitext(path)[1][1:]
                if ext.lower() in QImageReader.supportedImageFormats():
                    event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dropEvent(self, event):
        mimeData = event.mimeData()
        if mimeData.hasUrls():
            paths = mimeData.urls()
            # pick just one image
            path = paths[0].toLocalFile()
            fileName = os.path.basename(path)
            with open(path, "rb") as imgFile:
                data = imgFile.read()
            ext = os.path.splitext(path)[1][1:]
            # TODO: make sure we cleanup properly when replacing an image with
            # another
            if ext.lower() != "png":
                # convert
                img = QImage(path)
                data = QByteArray()
                buffer = QBuffer(data)
                buffer.open(QIODevice.WriteOnly)
                img.save(buffer, 'PNG')
                # format
                data = bytearray(data)
                fileName = "%s.png" % os.path.splitext(fileName)[0]
            imageSet = self._glyph.font.images
            try:
                imageSet[fileName] = data
            except Exception as e:
                errorReports.showCriticalException(e)
                return
            image = self._glyph.instantiateImage()
            image.fileName = fileName
            event.setAccepted(True)
        else:
            super().dropEvent(event)

    def keyPressEvent(self, event):
        if not event.isAutoRepeat() and event.key() == Qt.Key_Space:
            if not self._mouseDown:
                self._preview = True
                self.update()
        self._redirectEvent(event, self._currentTool.keyPressEvent)
        app = QApplication.instance()
        data = dict(
            event=event,
            widget=self,
        )
        app.postNotification("glyphViewKeyPress", data)

    def keyReleaseEvent(self, event):
        if not event.isAutoRepeat() and event.key() == Qt.Key_Space:
            self._preview = False
            self.update()
        self._redirectEvent(event, self._currentTool.keyReleaseEvent)
        app = QApplication.instance()
        data = dict(
            event=event,
            widget=self,
        )
        app.postNotification("glyphViewKeyRelease", data)

    def mousePressEvent(self, event):
        self._mouseDown = True
        self._redirectEvent(event, self._currentTool.mousePressEvent, True)
        app = QApplication.instance()
        data = dict(
            event=event,
            widget=self,
        )
        app.postNotification("glyphViewMousePress", data)

    def mouseMoveEvent(self, event):
        self._redirectEvent(event, self._currentTool.mouseMoveEvent, True)
        app = QApplication.instance()
        data = dict(
            event=event,
            widget=self,
        )
        app.postNotification("glyphViewMouseMove", data)

    def mouseReleaseEvent(self, event):
        self._redirectEvent(event, self._currentTool.mouseReleaseEvent, True)
        app = QApplication.instance()
        data = dict(
            event=event,
            widget=self,
        )
        app.postNotification("glyphViewMouseRelease", data)
        self._mouseDown = False

    def mouseDoubleClickEvent(self, event):
        self._redirectEvent(
            event, self._currentTool.mouseDoubleClickEvent, True)
        app = QApplication.instance()
        data = dict(
            event=event,
            widget=self,
        )
        app.postNotification("glyphViewMouseDoubleClick", data)

    # ------------
    # Canvas tools
    # ------------

    # current tool

    def currentTool(self):
        return self._currentTool

    def setCurrentTool(self, tool):
        if self._mouseDown:
            return False
        self._currentTool.toolDisabled()
        self._currentTool = tool
        self._currentTool.toolActivated()
        return True

    def _redirectEvent(self, event, callback, transmuteMouseEvent=False):
        if self._preview:
            return
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
        offHalf = offWidth / 2
        offStrokeWidth = 3 * scale
        # onCurve
        onWidth = 7 * scale
        onHalf = onWidth / 2
        onStrokeWidth = 1.5 * scale
        # onCurve smooth
        smoothWidth = 8 * scale
        smoothHalf = smoothWidth / 2
        # guideline pt
        guidelineStrokeWidth = 1 * scale

        if not justOne:
            ret = dict(
                anchors=[],
                contours=[],
                points=[],
                components=[],
                guidelines=[],
                image=None,
            )
        # anchors
        for anchor in reversed(self._glyph.anchors):
            path = QPainterPath()
            path.addEllipse(anchor.x - anchorHalfSize,
                            anchor.y - anchorHalfSize, anchorSize, anchorSize)
            if func(path, obj):
                if justOne:
                    return (anchor, None)
                ret["anchors"].append(anchor)
        # points
        for contour in reversed(self._glyph):
            for point in contour:
                path = QPainterPath()
                if point.segmentType is None:
                    x = point.x - offHalf
                    y = point.y - offHalf
                    path.addEllipse(x, y, offWidth, offWidth)
                    strokeWidth = offStrokeWidth
                else:
                    if point.smooth:
                        x = point.x - smoothHalf
                        y = point.y - smoothHalf
                        path.addEllipse(x, y, smoothWidth, smoothWidth)
                    else:
                        x = point.x - onHalf
                        y = point.y - onHalf
                        path.addRect(x, y, onWidth, onWidth)
                    strokeWidth = onStrokeWidth
                path = _shapeFromPath(path, strokeWidth)
                if func(path, obj):
                    if justOne:
                        return (point, contour)
                    ret["contours"].append(contour)
                    ret["points"].append(point)
        # components
        for component in reversed(self._glyph.components):
            path = component.getRepresentation("TruFont.QPainterPath")
            if func(path, obj):
                if justOne:
                    return (component, None)
                ret["components"].append(component)
        # guideline
        for guideline in UIGlyphGuidelines(self._glyph):
            if None not in (guideline.x, guideline.y):
                # point
                x = guideline.x - smoothHalf
                y = guideline.y - smoothHalf
                path = QPainterPath()
                path.addEllipse(x, y, smoothWidth, smoothWidth)
                path = _shapeFromPath(path, guidelineStrokeWidth)
                if func(path, obj):
                    if justOne:
                        return (guideline, None)
                    ret["guidelines"].append(guideline)
                # TODO: catch line if selected
        # image
        image = self._glyph.image
        pixmap = image.getRepresentation("defconQt.QPixmap")
        if pixmap is not None:
            path = QPainterPath()
            transform = QTransform(*image.transformation)
            rect = transform.mapRect(QRectF(pixmap.rect()))
            path.addRect(*rect.getCoords())
            if func(path, obj):
                if justOne:
                    return (image, None)
                ret["image"] = image
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


class GlyphCanvasView(GlyphView):
    glyphWidgetClass = GlyphCanvasWidget

    # -------------
    # Notifications
    # -------------

    def _subscribeToGlyph(self, glyph):
        if glyph is not None:
            glyph.addObserver(
                self, "_glyphSelectionChanged", "Glyph.SelectionChanged")
            super()._subscribeToGlyph(glyph)

    def _unsubscribeFromGlyph(self):
        if self._glyphWidget is not None:
            glyph = self._glyphWidget.glyph()
            if glyph is not None:
                super()._unsubscribeFromGlyph()
                glyph.removeObserver(self, "Glyph.SelectionChanged")

    def _glyphSelectionChanged(self, notification):
        self._glyphWidget.glyphChanged()

    # ------------
    # Canvas tools
    # ------------

    def currentTool(self):
        return self._glyphWidget.currentTool()

    def setCurrentTool(self, tool):
        return self._glyphWidget.setCurrentTool(tool)

    def itemAt(self, pos):
        return self._glyphWidget.itemAt(pos)

    def itemsAt(self, pos, items=False):
        return self._glyphWidget.itemsAt(pos, items)

    def items(self, rect):
        return self._glyphWidget.items(rect)

    def setFocus(self, value):
        super().setFocus(value)
        self._glyphWidget.setFocus(value)

    # ----------
    # Qt methods
    # ----------

    def closeEvent(self, event):
        super().closeEvent(event)
        if event.isAccepted():
            self._glyphWidget.closeEvent(event)


def _shapeFromPath(path, width):
    if path.isEmpty():
        return path
    ps = QPainterPathStroker()
    ps.setWidth(width)
    p = ps.createStroke(path)
    p.addPath(path)
    return p
