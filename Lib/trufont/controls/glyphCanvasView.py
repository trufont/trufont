from PyQt5.QtCore import QBuffer, QByteArray, QIODevice, QPoint, QRectF, Qt
from PyQt5.QtGui import (
    QContextMenuEvent, QImage, QImageReader, QMouseEvent, QPainterPath,
    QPainterPathStroker, QTransform)
from PyQt5.QtWidgets import QApplication
from defconQt.controls.glyphView import (
    GlyphView, GlyphViewMinSizeForDetails, GlyphWidget)
from trufont.drawingTools.baseTool import BaseTool
from trufont.objects import settings
from trufont.tools import drawing, errorReports
from trufont.tools.uiMethods import UIGlyphGuidelines
import os

GlyphViewMinSizeForGrid = 10000


class GlyphCanvasWidget(GlyphWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setAcceptDrops(True)
        self._currentTool = BaseTool()
        self._currentToolActivated = False
        self._mouseDown = False
        self._preview = False

        # inbound notifications
        app = QApplication.instance()
        app.dispatcher.addObserver(self, "_needsUpdate", "glyphViewUpdate")
        app.dispatcher.addObserver(
            self, "_preferencesChanged", "preferencesChanged")

        self.readSettings()

    def readSettings(self):
        drawingAttributes = settings.drawingAttributes()
        for attr, value in drawingAttributes.items():
            self.setDrawingAttribute(attr, value, None)

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

    def _preferencesChanged(self, notification):
        self.readSettings()

    # ---------------
    # Drawing helpers
    # ---------------

    def drawingAttribute(self, attr, layerName):
        toolOverride = self._currentTool.drawingAttribute(attr, layerName)
        if toolOverride is not None:
            return toolOverride
        return super().drawingAttribute(attr, layerName)

    def drawBackground(self, painter):
        app = QApplication.instance()
        data = dict(
            widget=self,
            painter=painter,
        )
        app.postNotification("glyphViewDrawBackground", data)
        self._currentTool.paintBackground(painter)

    def drawGlyphLayer(self, painter, glyph, layerName, default=False):
        if self._preview:
            layerName = None if glyph == self._glyph else layerName
            if layerName is None:
                self.drawFillAndStroke(painter, glyph, layerName)
        else:
            super().drawGlyphLayer(painter, glyph, layerName, default)

    def drawMetrics(self, painter, glyph, layerName):
        # TODO: should this have its own parameter?
        if self._impliedPointSize > GlyphViewMinSizeForGrid:
            drawingRect = self._drawingRect
            if self._scrollArea is not None:
                # culling
                drawingRect = self.mapRectToCanvas(QRectF(
                    self.mapFromParent(QPoint(0, 0)),
                    self.mapFromParent(QPoint(
                        self.parent().width(), self.parent().height()))
                )).getRect()
            drawing.drawGrid(painter, self._inverseScale, drawingRect)
        super().drawMetrics(painter, glyph, layerName)

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

    def drawPoints(self, painter, glyph, layerName):
        if not self._impliedPointSize > GlyphViewMinSizeForDetails:
            return
        # XXX: those won't be drawn if points are hidden
        drawFill = self.drawingAttribute("showGlyphFill", layerName)
        drawSelection = not self._preview and layerName is None
        drawing.drawGlyphFillAndStroke(
            painter, glyph, self._inverseScale, self._drawingRect,
            drawFill=drawFill, drawSelection=drawSelection, drawStroke=False)
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
            drawOffCurves=drawOffCurves, drawCoordinates=drawCoordinates,
            backgroundColor=self._backgroundColor)

    def drawFillAndStroke(self, painter, glyph, layerName):
        drawDetails = self._impliedPointSize > GlyphViewMinSizeForDetails
        if self._preview:
            contourFillColor = componentFillColor = Qt.black
            showFill = showComponentsFill = True
            showStroke = False
        else:
            contourFillColor = componentFillColor = None
            showFill = showComponentsFill = False
            showStroke = self.drawingAttribute("showGlyphStroke", layerName)
        drawing.drawGlyphFillAndStroke(
            painter, glyph, self._inverseScale, self._drawingRect,
            componentFillColor=componentFillColor,
            contourFillColor=contourFillColor,
            drawFill=showFill, drawSelection=False, drawStroke=showStroke,
            drawComponentsFill=showComponentsFill, partialAliasing=drawDetails)

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

    def showEvent(self, event):
        super().showEvent(event)
        self._setCurrentToolEnabled(True)

    def hideEvent(self, event):
        super().hideEvent(event)
        self._setCurrentToolEnabled(False)
        self._preview = False

    def closeEvent(self, event):
        super().closeEvent(event)
        if event.isAccepted():
            self._setCurrentToolEnabled(False)
            app = QApplication.instance()
            app.dispatcher.removeObserver(self, "glyphViewUpdate")
            app.dispatcher.removeObserver(self, "parametersChanged")

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

    def contextMenuEvent(self, event):
        self._redirectEvent(event, self._currentTool.contextMenuEvent, True)
        app = QApplication.instance()
        data = dict(
            event=event,
            widget=self,
        )
        app.postNotification("glyphViewContextMenu", data)

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

    def _setCurrentToolEnabled(self, value):
        if self._currentToolActivated == value:
            return
        if value != self.isVisible():
            return
        self._currentToolActivated = value
        if value:
            self._currentTool.toolActivated()
        else:
            self._currentTool.toolDisabled()

    def currentTool(self):
        return self._currentTool

    def setCurrentTool(self, tool):
        if self._mouseDown:
            return False
        self._setCurrentToolEnabled(False)
        self._currentTool = tool
        self.setCursor(tool.cursor)
        self._setCurrentToolEnabled(True)
        return True

    def _redirectEvent(self, event, callback, transmute=False):
        if self._preview:
            return
        # construct a new event with pos in canvas coordinates
        if transmute:
            if isinstance(event, QContextMenuEvent):
                canvasPos = self.mapToCanvas(event.pos())
                event = event.__class__(
                    event.reason(),
                    canvasPos,
                    event.globalPos(),
                    event.modifiers()
                )
                event.localPos = lambda: canvasPos
            elif isinstance(event, QMouseEvent):
                canvasPos = self.mapToCanvas(event.localPos())
                event = event.__class__(
                    event.type(),
                    canvasPos,
                    event.windowPos(),
                    event.screenPos(),
                    event.button(),
                    event.buttons(),
                    event.modifiers()
                )
            else:
                raise ValueError("cannot transmute event: {}".format(event))
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
        # XXX: outdated
        # anchor
        anchorSize = 7 * scale
        anchorHalfSize = anchorSize / 2
        # offCurve
        offSize = 5 * scale
        offHalf = offSize / 2
        offStrokeWidth = 2.5 * scale
        # onCurve
        onSize = 6.5 * scale
        onHalf = onSize / 2
        onStrokeWidth = 1.5 * scale
        # onCurve smooth
        smoothSize = 8 * scale
        smoothHalf = smoothSize / 2
        # guideline pt
        guidelineStrokeWidth = 1 * scale

        if not justOne:
            ret = dict(
                anchors=[],
                points=[],
                components=[],
                guidelines=[],
                image=None,
            )
        if not self.drawingAttribute("showGlyphOnCurvePoints", None):
            if not justOne:
                return ret
            return None
        # anchors
        for anchor in reversed(self._glyph.anchors):
            path = QPainterPath()
            path.addEllipse(anchor.x - anchorHalfSize,
                            anchor.y - anchorHalfSize, anchorSize, anchorSize)
            if func(path, obj):
                if justOne:
                    return anchor
                ret["anchors"].append(anchor)
        # points
        for contour in reversed(self._glyph):
            for index, point in enumerate(contour):
                path = QPainterPath()
                if point.segmentType is None:
                    x = point.x - offHalf
                    y = point.y - offHalf
                    path.addEllipse(x, y, offSize, offSize)
                    strokeWidth = offStrokeWidth
                else:
                    if point.smooth:
                        x = point.x - smoothHalf
                        y = point.y - smoothHalf
                        path.addEllipse(x, y, smoothSize, smoothSize)
                    else:
                        x = point.x - onHalf
                        y = point.y - onHalf
                        path.addRect(x, y, onSize, onSize)
                    strokeWidth = onStrokeWidth
                path = _shapeFromPath(path, strokeWidth)
                if func(path, obj):
                    if justOne:
                        return (contour, index)
                    ret["points"].append((contour, index))
        # components
        for component in reversed(self._glyph.components):
            path = component.getRepresentation("TruFont.QPainterPath")
            if func(path, obj):
                if justOne:
                    return component
                ret["components"].append(component)
        # guideline
        for guideline in UIGlyphGuidelines(self._glyph):
            if None not in (guideline.x, guideline.y):
                # point
                x = guideline.x - smoothHalf
                y = guideline.y - smoothHalf
                path = QPainterPath()
                path.addEllipse(x, y, smoothSize, smoothSize)
                path = _shapeFromPath(path, guidelineStrokeWidth)
                if func(path, obj):
                    if justOne:
                        return guideline
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
                    return image
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

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
