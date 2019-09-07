"""
The *glyphView* submodule
-----------------------------

The *glyphView* submodule provides widgets that render a Glyph_, with
various display parameters.

.. _Glyph: http://ts-defcon.readthedocs.org/en/ufo3/objects/glyph.html
"""

from PyQt5.QtCore import QEvent, QPoint, QPointF, QSize, Qt, pyqtSignal
from PyQt5.QtGui import QCursor, QPainter
from PyQt5.QtWidgets import QPinchGesture, QScrollArea, QSizePolicy, QWidget

from defconQt.tools import drawing, platformSpecific

# TODO: when the scrollArea resizes, keep the view centered

GlyphViewMinSizeForDetails = 175

UIFont = platformSpecific.otherUIFont()


class GlyphWidget(QWidget):
    pointSizeModified = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.DefaultContextMenu)
        self.setFocusPolicy(Qt.ClickFocus)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self._fitViewport = True
        self._glyph = None
        self._scrollArea = None

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
            showGlyphMetrics=True,
            showGlyphGuidelines=True,
            showGlyphImage=True,
            showFontVerticalMetrics=True,
            showFontVerticalMetricsTitles=False,
            showFontGuidelines=True,
            showFontPostscriptBlues=True,
            showFontPostscriptFamilyBlues=False,  # TODO: test appearance of this
            # combined w/ blues
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
        self._noPointSizePadding = 200
        self._verticalCenterYBuffer = 0

        self._backgroundColor = Qt.white

    # --------------
    # Custom Methods
    # --------------

    def drawingRect(self):
        return self._drawingRect

    def inverseScale(self):
        return self._inverseScale

    def pointSize(self):
        return self._impliedPointSize

    def setPointSize(self, pointSize):
        scrollArea = self._scrollArea
        newScale = pointSize / self._unitsPerEm
        if scrollArea is not None:
            # compute new scrollbar position
            hSB = scrollArea.horizontalScrollBar()
            vSB = scrollArea.verticalScrollBar()
            viewport = scrollArea.viewport()
            centerPos = QPoint(viewport.width() / 2, viewport.height() / 2)
            pos = self.mapToCanvas(self.mapFromParent(centerPos))
        self.setScale(newScale)
        if scrollArea is not None:
            pos = self.mapFromCanvas(pos)
            delta = pos - self.mapFromParent(centerPos)
            hSB.setValue(hSB.value() + delta.x())
            vSB.setValue(vSB.value() + delta.y())

    def scale(self):
        return self._scale

    def setScale(self, scale):
        self._scale = scale
        if self._scale <= 0:
            self._scale = 0.01
        self._inverseScale = 1.0 / self._scale
        self._impliedPointSize = self._unitsPerEm * self._scale
        self.adjustSize()

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
        self.update()

    def scrollArea(self):
        return self._scrollArea

    def setScrollArea(self, scrollArea):
        scrollArea.setWidget(self)
        self._scrollArea = scrollArea

    # fitting

    def centerOn(self, pos):
        """
        Centers this widget’s *scrollArea* on QPointF_ *pos*.

        .. _QPointF: http://doc.qt.io/qt-5/qpointf.html
        """
        scrollArea = self._scrollArea
        if scrollArea is None:
            return
        hSB = scrollArea.horizontalScrollBar()
        vSB = scrollArea.verticalScrollBar()
        viewport = scrollArea.viewport()
        hValue = hSB.minimum() + hSB.maximum() - (pos.x() - viewport.width() / 2)
        hSB.setValue(hValue)
        vSB.setValue(pos.y() - viewport.height() / 2)

    def _calculateDrawingRect(self):
        # calculate and store the drawing rect
        # TODO: we only need the width here
        glyphWidth = self._getGlyphWidthHeight()[0] * self._scale
        diff = self.width() - glyphWidth
        xOffset = round((diff / 2) * self._inverseScale)

        yOffset = self._verticalCenterYBuffer * self._inverseScale
        yOffset -= self._descender

        w = self.width() * self._inverseScale
        h = self.height() * self._inverseScale
        self._drawingRect = (-xOffset, -yOffset, w, h)

    def _getGlyphWidthHeight(self):
        glyph = self._glyph
        if glyph is None:
            return 0, 0
        # get the default layer width, that's what we use to draw
        # the background
        if glyph.layerSet is not None:
            glyph = glyph.layerSet.defaultLayer[glyph.name]
        bottom = self._descender
        top = max(self._capHeight, self._ascender, self._unitsPerEm + self._descender)
        width = glyph.width
        height = -bottom + top
        return width, height

    def fitScaleMetrics(self):
        """
        Scales and centers the viewport around the font’s metrics.
        """
        scrollArea = self._scrollArea
        if scrollArea:
            fitHeight = scrollArea.viewport().height()
        else:
            fitHeight = self.height()
        glyphWidth, glyphHeight = self._getGlyphWidthHeight()
        glyphHeight += self._noPointSizePadding * 2
        self.setScale(fitHeight / glyphHeight)
        self.centerOn(
            self.mapFromCanvas(
                QPointF(glyphWidth / 2, self._descender + self._unitsPerEm / 2)
            )
        )

    def fitScaleBBox(self):
        """
        Scales and centers the viewport around the *glyph*’s bounding box.
        """
        if self._glyph is None:
            return
        if self._glyph.bounds is None:
            self.fitScaleMetrics()
            return
        scrollArea = self._scrollArea
        if scrollArea:
            viewport = scrollArea.viewport()
            fitHeight = viewport.height()
            fitWidth = viewport.width()
        else:
            fitHeight = self.height()
            fitWidth = self.width()
        left, bottom, right, top = self._glyph.bounds
        glyphHeight = top - bottom
        glyphHeight += self._noPointSizePadding * 2
        glyphWidth = right - left
        glyphWidth += self._noPointSizePadding * 2
        self.setScale(min(fitHeight / glyphHeight, fitWidth / glyphWidth))
        self.centerOn(
            self.mapFromCanvas(
                QPointF(left + (right - left) / 2, bottom + (top - bottom) / 2)
            )
        )
        self.pointSizeModified.emit(self._impliedPointSize)

    def zoom(self, step, anchor="center"):
        """
        Zooms the view by *step* increments (with a scale factor of
        1.2^*step*), anchored to *anchor*:

        - QPoint_: center on that point
        - "cursor": center on the mouse cursor position
        - "center": center on the viewport
        - None: don’t anchor, i.e. stick to the viewport’s top-left.

        # TODO: improve docs from QGraphicsView descriptions.

        The default is "center".

        .. _QPoint: http://doc.qt.io/qt-5/qpoint.html
        """
        oldScale = self._scale
        newScale = self._scale * pow(1.2, step)
        scrollArea = self._scrollArea
        if newScale < 1e-2 or newScale > 1e3:
            return
        if scrollArea is not None:
            # compute new scrollbar position
            # http://stackoverflow.com/a/32269574/2037879
            hSB = scrollArea.horizontalScrollBar()
            vSB = scrollArea.verticalScrollBar()
            viewport = scrollArea.viewport()
            if isinstance(anchor, QPoint):
                pos = anchor
            elif anchor == "cursor":
                pos = self.mapFromGlobal(QCursor.pos())
            elif anchor == "center":
                pos = self.mapFromParent(
                    QPoint(viewport.width() / 2, viewport.height() / 2)
                )
            else:
                raise ValueError(f"invalid anchor value: {anchor}")
            scrollBarPos = QPointF(hSB.value(), vSB.value())
            deltaToPos = pos / oldScale
            delta = deltaToPos * (newScale - oldScale)
        self.setScale(newScale)
        self.update()
        if scrollArea is not None:
            hSB.setValue(scrollBarPos.x() + delta.x())
            vSB.setValue(scrollBarPos.y() + delta.y())

    # position mapping

    def mapFromCanvas(self, pos):
        """
        Maps *pos* from glyph canvas to this widget’s coordinates.

        Note that canvas coordinates are scale-independent while widget
        coordinates are not.
        """
        if self._drawingRect is None:
            self._calculateDrawingRect()
        xOffsetInv, yOffsetInv, _, _ = self._drawingRect
        x = (pos.x() - xOffsetInv) * self._scale
        y = (pos.y() - yOffsetInv) * (-self._scale) + self.height()
        return pos.__class__(x, y)

    def mapToCanvas(self, pos):
        """
        Maps *pos* from this widget’s to glyph canvas coordinates.

        Note that canvas coordinates are scale-independent while widget
        coordinates are not.
        """
        if self._drawingRect is None:
            self._calculateDrawingRect()
        xOffsetInv, yOffsetInv, _, _ = self._drawingRect
        x = pos.x() * self._inverseScale + xOffsetInv
        y = (pos.y() - self.height()) * (-self._inverseScale) + yOffsetInv
        return pos.__class__(x, y)

    def mapRectFromCanvas(self, rect):
        x, y, w, h = rect.getRect()
        origin = self.mapFromCanvas(QPointF(x, y))
        w *= self._scale
        h *= self._scale
        return rect.__class__(origin.x(), origin.y() - h, w, h)

    def mapRectToCanvas(self, rect):
        x, y, w, h = rect.getRect()
        origin = self.mapToCanvas(QPointF(x, y))
        w *= self._inverseScale
        h *= self._inverseScale
        return rect.__class__(origin.x(), origin.y() - h, w, h)

    # --------------------
    # Notification Support
    # --------------------

    def glyphChanged(self):
        # TODO: we could adjustSize() only when glyph width changes
        self.adjustSize()
        self.update()

    def fontChanged(self):
        self.setGlyph(self._glyph)

    # ---------------
    # Display Control
    # ---------------

    def drawingAttribute(self, attr, layerName):
        if layerName is None:
            return self._fallbackDrawingAttributes.get(attr)
        d = self._layerDrawingAttributes.get(layerName, {})
        return d.get(attr, attr == "showGlyphStroke" or None)

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

    def showGuidelines(self):
        return self.drawingAttribute("showFontGuidelines", None)

    def setShowGuidelines(self, value):
        self.setDrawingAttribute("showFontGuidelines", value, None)
        self.setDrawingAttribute("showGlyphGuidelines", value, None)

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

    def backgroundColor(self):
        return self._backgroundColor

    def setBackgroundColor(self, color):
        self._backgroundColor = color
        self.update()

    # ---------------
    # Drawing helpers
    # ---------------

    def drawBackground(self, painter):
        pass

    def drawGlyphLayer(self, painter, glyph, layerName, default=False):
        fontLayerName = None if default else layerName
        # draw the image
        if self.drawingAttribute("showGlyphImage", layerName):
            self.drawImage(painter, glyph, fontLayerName)
        # draw the blues
        if fontLayerName is None and self.drawingAttribute(
            "showFontPostscriptBlues", None
        ):
            self.drawBlues(painter, glyph, fontLayerName)
        if fontLayerName is None and self.drawingAttribute(
            "showFontPostscriptFamilyBlues", None
        ):
            self.drawFamilyBlues(painter, glyph, fontLayerName)
        # draw the metrics
        if fontLayerName is None and self.drawingAttribute("showGlyphMetrics", None):
            self.drawMetrics(painter, glyph, fontLayerName)

        layerName = None if glyph == self._glyph else layerName
        # draw the guidelines
        if (
            layerName is None
            and self.drawingAttribute("showFontGuidelines", None)
            or self.drawingAttribute("showGlyphGuidelines", None)
        ):
            self.drawGuidelines(painter, glyph, layerName)
        # draw the glyph
        if (
            self.drawingAttribute("showGlyphOnCurvePoints", layerName)
            or self.drawingAttribute("showGlyphOffCurvePoints", layerName)
            or self.drawingAttribute("showGlyphFill", layerName)
        ):
            self.drawFillAndPoints(painter, glyph, layerName)
        if self.drawingAttribute("showGlyphStroke", layerName):
            self.drawStroke(painter, glyph, layerName)
        if self.drawingAttribute("showGlyphAnchors", layerName):
            self.drawAnchors(painter, glyph, layerName)

    def drawImage(self, painter, glyph, layerName):
        drawing.drawGlyphImage(painter, glyph, self._inverseScale)

    def drawBlues(self, painter, glyph, layerName):
        drawing.drawFontPostscriptBlues(painter, glyph, self._inverseScale)

    def drawFamilyBlues(self, painter, glyph, layerName):
        drawing.drawFontPostscriptFamilyBlues(painter, glyph, self._inverseScale)

    def drawMetrics(self, painter, glyph, layerName):
        drawVMetrics = layerName is None and self.drawingAttribute(
            "showFontVerticalMetrics", None
        )
        drawText = (
            self.drawingAttribute("showFontVerticalMetricsTitles", layerName)
            and self._impliedPointSize > GlyphViewMinSizeForDetails
        )
        drawing.drawGlyphMetrics(
            painter,
            glyph,
            self._inverseScale,
            drawVMetrics=drawVMetrics,
            drawText=drawText,
        )

    def drawGuidelines(self, painter, glyph, layerName):
        drawText = self._impliedPointSize > GlyphViewMinSizeForDetails
        if self.drawingAttribute("showFontGuidelines", layerName):
            drawing.drawFontGuidelines(
                painter, glyph, self._inverseScale, self._drawingRect, drawText=drawText
            )
        if self.drawingAttribute("showGlyphGuidelines", layerName):
            drawing.drawGlyphGuidelines(
                painter, glyph, self._inverseScale, self._drawingRect, drawText=drawText
            )

    def drawFillAndPoints(self, painter, glyph, layerName):
        drawFill = self.drawingAttribute("showGlyphFill", layerName)
        drawing.drawGlyphFillAndStroke(
            painter, glyph, self._inverseScale, drawFill=drawFill, drawStroke=False
        )
        if not self._impliedPointSize > GlyphViewMinSizeForDetails:
            return
        drawStartPoints = self.drawingAttribute("showGlyphStartPoints", layerName)
        drawOnCurves = self.drawingAttribute("showGlyphOnCurvePoints", layerName)
        drawOffCurves = self.drawingAttribute("showGlyphOffCurvePoints", layerName)
        drawCoordinates = self.drawingAttribute("showGlyphPointCoordinates", layerName)
        drawing.drawGlyphPoints(
            painter,
            glyph,
            self._inverseScale,
            drawStartPoints=drawStartPoints,
            drawOnCurves=drawOnCurves,
            drawOffCurves=drawOffCurves,
            drawCoordinates=drawCoordinates,
            backgroundColor=self._backgroundColor,
        )

    def drawStroke(self, painter, glyph, layerName):
        showStroke = self.drawingAttribute("showGlyphStroke", layerName)
        drawing.drawGlyphFillAndStroke(
            painter,
            glyph,
            self._inverseScale,
            drawFill=False,
            drawComponentFill=False,
            drawStroke=showStroke,
        )

    def drawAnchors(self, painter, glyph, layerName):
        if not self._impliedPointSize > GlyphViewMinSizeForDetails:
            return
        drawing.drawGlyphAnchors(painter, glyph, self._inverseScale, self._drawingRect)

    def drawForeground(self, painter):
        pass

    # ---------------
    # QWidget methods
    # ---------------

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setFont(UIFont)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = event.rect()

        # draw the background
        painter.fillRect(rect, self._backgroundColor)
        if self._glyph is None:
            return

        # apply the overall scale
        painter.save()
        # + translate and flip
        painter.translate(0, self.height())
        painter.scale(self._scale, -self._scale)

        # move into position
        xOffsetInv, yOffsetInv, _, _ = self._drawingRect
        painter.translate(-xOffsetInv, -yOffsetInv)

        # gather the layers
        layerSet = self._glyph.layerSet
        if layerSet is None:
            layers = [(self._glyph, None, True)]
        else:
            glyphName = self._glyph.name
            layers = []
            for layerName in reversed(layerSet.layerOrder):
                layer = layerSet[layerName]
                if glyphName not in layer:
                    continue
                glyph = layer[glyphName]
                layers.append((glyph, layerName, layer == layerSet.defaultLayer))

        self.drawBackground(painter)
        for glyph, layerName, default in layers:
            self.drawGlyphLayer(painter, glyph, layerName, default)
        self.drawForeground(painter)
        painter.restore()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._calculateDrawingRect()

    def sizeHint(self):
        # pick the width and height
        glyphWidth, glyphHeight = self._getGlyphWidthHeight()
        glyphWidth = glyphWidth * self._scale
        glyphHeight = glyphHeight * self._scale
        xOffset = 1000 * 2 * self._scale
        yOffset = xOffset
        width = glyphWidth + xOffset
        height = glyphHeight + yOffset
        # calculate and store the vertical centering offset
        scrollArea = self._scrollArea
        if scrollArea:
            maxHeight = max(height, scrollArea.viewport().height())
        else:
            maxHeight = height
        self._verticalCenterYBuffer = (maxHeight - glyphHeight) / 2.0
        return QSize(width, height)

    def showEvent(self, event):
        super().showEvent(event)
        if hasattr(self, "_fitViewport"):
            self._calculateDrawingRect()
            self.fitScaleBBox()
            del self._fitViewport

    def wheelEvent(self, event):
        if event.modifiers() & platformSpecific.scaleModifier():
            step = event.angleDelta().y() / 120.0
            self.zoom(step, event.pos())
            self.pointSizeModified.emit(self._impliedPointSize)
            event.accept()
        else:
            super().wheelEvent(event)


class GlyphView(QScrollArea):
    glyphWidgetClass = GlyphWidget

    def __init__(self, parent=None):
        super().__init__(parent)
        self.grabGesture(Qt.PinchGesture)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setWidgetResizable(True)

        self._glyphWidget = self.glyphWidgetClass(self)
        self._glyphWidget.setScrollArea(self)

        self.pointSizeModified = self._glyphWidget.pointSizeModified

    # -------------
    # Notifications
    # -------------

    def _subscribeToGlyph(self, glyph):
        if glyph is not None:
            glyph.addObserver(self, "_glyphChanged", "Glyph.Changed")
            layerSet = glyph.layerSet
            if layerSet is not None:
                layerSet.addObserver(self, "_glyphChanged", "LayerSet.LayerChanged")
            font = glyph.font
            if font is not None:
                font.info.addObserver(self, "_fontChanged", "Info.Changed")

    def _unsubscribeFromGlyph(self):
        if self._glyphWidget is not None:
            glyph = self._glyphWidget.glyph()
            if glyph is not None:
                glyph.removeObserver(self, "Glyph.Changed")
                layerSet = glyph.layerSet
                if layerSet is not None:
                    layerSet.removeObserver(self, "LayerSet.LayerChanged")
                font = glyph.font
                if font is not None:
                    font.info.removeObserver(self, "Info.Changed")

    def _glyphChanged(self, notification):
        self._glyphWidget.glyphChanged()

    def _fontChanged(self, notification):
        self._glyphWidget.fontChanged()

    # --------------
    # Public Methods
    # --------------

    def pointSize(self):
        return self._glyphWidget.pointSize()

    def setPointSize(self, pointSize):
        self._glyphWidget.setPointSize(pointSize)

    def scale(self):
        return self._glyphWidget.scale()

    def setScale(self, scale):
        self._glyphWidget.setScale(scale)

    def glyph(self):
        return self._glyphWidget.glyph()

    def setGlyph(self, glyph):
        self._unsubscribeFromGlyph()
        self._subscribeToGlyph(glyph)
        self._glyphWidget.setGlyph(glyph)

    def drawingAttribute(self, attr, layerName=None):
        return self._glyphWidget.drawingAttribute(attr, layerName)

    def setDrawingAttribute(self, attr, value, layerName=None):
        self._glyphWidget.setDrawingAttribute(attr, value, layerName)

    def fitScaleBBox(self):
        self._glyphWidget.fitScaleBBox()

    def zoom(self, factor, anchor="center"):
        self._glyphWidget.zoom(factor, anchor=anchor)

    # convenience

    def showFill(self):
        return self.drawingAttribute("showGlyphFill")

    def setShowFill(self, value):
        self.setDrawingAttribute("showGlyphFill", value)

    def showStroke(self):
        return self.drawingAttribute("showGlyphStroke")

    def setShowStroke(self, value):
        self.setDrawingAttribute("showGlyphStroke", value)

    def showMetrics(self):
        return self.drawingAttribute("showGlyphMargins")

    def setShowMetrics(self, value):
        self.setDrawingAttribute("showGlyphMargins", value)
        self.setDrawingAttribute("showFontVerticalMetrics", value)
        self.setDrawingAttribute("showFontVerticalMetricsTitles", value)

    def showImage(self):
        return self.drawingAttribute("showGlyphImage")

    def setShowImage(self, value):
        self.setDrawingAttribute("showGlyphImage", value)

    def showOnCurvePoints(self):
        return self.drawingAttribute("showGlyphOnCurvePoints")

    def setShowOnCurvePoints(self, value):
        self.setDrawingAttribute("showGlyphOnCurvePoints", value)

    def showOffCurvePoints(self):
        return self.drawingAttribute("showGlyphOffCurvePoints")

    def setShowOffCurvePoints(self, value):
        self.setDrawingAttribute("showGlyphOffCurvePoints", value)

    def showPointCoordinates(self):
        return self.drawingAttribute("showGlyphPointCoordinates")

    def setShowPointCoordinates(self, value):
        self.setDrawingAttribute("showGlyphPointCoordinates", value)

    def showAnchors(self):
        return self.drawingAttribute("showGlyphAnchors")

    def setShowAnchors(self, value):
        self.setDrawingAttribute("showGlyphAnchors", value)

    def showBlues(self):
        return self.drawingAttribute("showFontPostscriptBlues")

    def setShowBlues(self, value):
        self.setDrawingAttribute("showFontPostscriptBlues", value)

    def showFamilyBlues(self):
        return self.drawingAttribute("showFontPostscriptFamilyBlues")

    def setShowFamilyBlues(self, value):
        self.setDrawingAttribute("showFontPostscriptFamilyBlues", value)

    def backgroundColor(self):
        return self._glyphWidget.backgroundColor()

    def setBackgroundColor(self, color):
        self._glyphWidget.setBackgroundColor(color)

    # ----------
    # Qt methods
    # ----------

    def event(self, event):
        if event.type() == QEvent.Gesture:
            return self.gestureEvent(event)
        return super().event(event)

    def gestureEvent(self, event):
        gesture = event.gesture(Qt.PinchGesture)
        if gesture:
            self.pinchTriggered(gesture)
            return True
        return False

    def pinchTriggered(self, gesture):
        changeFlags = gesture.changeFlags()
        if changeFlags & QPinchGesture.ScaleFactorChanged:
            self.zoom(gesture.scaleFactor() - gesture.lastScaleFactor(), "cursor")
