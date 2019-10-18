from PyQt5.QtCore import QEvent, QPoint, QPointF, QSize, Qt, pyqtSignal
from PyQt5.QtGui import QCursor, QPainter
from PyQt5.QtWidgets import QApplication, QWidget

from defconQt.controls.glyphView import GlyphViewMinSizeForDetails, UIFont
from defconQt.tools import drawing, platformSpecific

# TODO: forbid scrolling past scene boundary

_noPointSizePadding = 200


class GlyphFlags:
    __slots__ = ["_isActiveGlyph", "_isActiveLayer"]

    def __init__(self, isActiveGlyph, isActiveLayer=True):
        self._isActiveGlyph = isActiveGlyph
        self._isActiveLayer = isActiveLayer

    def __repr__(self):
        return "<{} isActiveGlyph: {} isActiveLayer: {}>".format(
            self.__class__.__name__, self.isActiveGlyph, self.isActiveLayer
        )

    @property
    def isActiveGlyph(self):
        return self._isActiveGlyph

    @property
    def isActiveLayer(self):
        return self._isActiveLayer


class GlyphContextView(QWidget):
    activeGlyphChanged = pyqtSignal()
    pointSizeModified = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.DefaultContextMenu)
        self.setFocusPolicy(Qt.ClickFocus)
        self.grabGesture(Qt.PanGesture)
        self.grabGesture(Qt.PinchGesture)
        self._drawingOffset = QPoint()
        self._fitViewport = True
        self._glyphRecords = []
        self._glyphRecordsRects = {}
        self._activeIndex = 0

        # drawing attributes
        self._defaultDrawingAttributes = dict(
            showGlyphFill=False,
            showGlyphStroke=True,
            showGlyphComponentFill=True,
            showGlyphComponentStroke=False,
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
            showFontPostscriptFamilyBlues=False,  # TODO: test appearance of
            # this combined w/ blues
        )

        # cached vertical metrics
        self._unitsPerEm = 1000
        self._descender = -250
        self._capHeight = 750
        self._ascender = 750

        # drawing data cache
        self._scale = 1.0
        self._inverseScale = 0.1
        self._impliedPointSize = 1000

        self._backgroundColor = Qt.white

    @property
    def _glyph(self):
        if not self._glyphRecords:
            return None
        return self._glyphRecords[self._activeIndex].glyph

    # -------------
    # Notifications
    # -------------

    def _subscribeToGlyphs(self, glyphRecords):
        handledGlyphs = set()
        handledFonts = set()
        for glyphRecord in glyphRecords:
            glyph = glyphRecord.glyph
            if glyph in handledGlyphs:
                continue
            handledGlyphs.add(glyph)
            glyph.addObserver(self, "_glyphChanged", "Glyph.Changed")
            font = glyph.font
            if font is None:
                continue
            if font in handledFonts:
                continue
            handledFonts.add(font)
            font.info.addObserver(self, "_fontChanged", "Info.Changed")

    def _unsubscribeFromGlyphs(self):
        handledGlyphs = set()
        handledFonts = set()
        glyphRecords = self.glyphRecords()
        for glyphRecord in glyphRecords:
            glyph = glyphRecord.glyph
            if glyph in handledGlyphs:
                continue
            handledGlyphs.add(glyph)
            glyph.removeObserver(self, "Glyph.Changed")
            font = glyph.font
            if font is None:
                continue
            if font in handledFonts:
                continue
            handledFonts.add(font)
            font.info.removeObserver(self, "Info.Changed")

    def _glyphChanged(self, notification):
        self.update()

    def _fontChanged(self, notification):
        self.setGlyphRecords(self.glyphRecords())

    # --------------
    # Custom Methods
    # --------------

    def activeGlyph(self):
        return self._glyph

    def setActiveGlyph(self, glyph):
        glyphs = list(self.glyphs())
        glyphs[self._activeIndex] = glyph
        self.setGlyphs(glyphs)

    def activeIndex(self):
        return self._activeIndex

    def setActiveIndex(self, value):
        if value == self._activeIndex:
            return
        self._activeIndex = value
        self.activeGlyphChanged.emit()
        self.update()

    def glyphForIndex(self, index):
        if not self._glyphRecords:
            return None
        return self._glyphRecords[index].glyph

    def indexForPoint(self, point):
        if not self._glyphRecordsRects:
            return None
        for rect, recordIndex in self._glyphRecordsRects.items():
            # we don't bound the height here
            x, _, w, _ = rect
            if point.x() >= x and point.x() <= x + w:
                return recordIndex
        return None

    def originForIndex(self, index=None):
        if index is None:
            index = self._activeIndex
        ret = QPointF(self._drawingOffset)
        for glyphIndex, glyphRecord in enumerate(self._glyphRecords):
            if glyphIndex == index:
                xO, yO = glyphRecord.xOffset, glyphRecord.yOffset
                ret += QPointF(xO * self._scale, yO * self._scale)
                break
            xA = glyphRecord.xAdvance
            yA = glyphRecord.yAdvance
            ret += QPointF(xA * self._scale, yA * self._scale)
        return ret

    def inverseScale(self):
        return self._inverseScale

    def pointSize(self):
        return self._impliedPointSize

    def setPointSize(self, pointSize):
        scale = pointSize / self._unitsPerEm
        self.setScale(scale)

    def scale(self):
        return self._scale

    def setScale(self, scale):
        self._scale = scale
        if self._scale <= 0:
            self._scale = 0.01
        self._inverseScale = 1.0 / self._scale
        self._impliedPointSize = self._unitsPerEm * self._scale
        self.update()

    def glyphRecords(self):
        return self._glyphRecords

    def setGlyphRecords(self, glyphRecords):
        self._unsubscribeFromGlyphs()
        self._glyphRecords = glyphRecords
        self._font = None
        # XXX: for now, we assume all glyphs come from
        # the same font
        if self._glyphRecords:
            font = self._font = self._glyphRecords[0].glyph.font
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
            if self._activeIndex >= len(self._glyphRecords):
                self._activeIndex = len(self._glyphRecords) - 1
        else:
            self._activeIndex = 0
        self._subscribeToGlyphs(glyphRecords)
        self.activeGlyphChanged.emit()
        self.update()

    def glyphs(self):
        for glyphRecord in self._glyphRecords:
            yield glyphRecord.glyph

    def setGlyphs(self, glyphs):
        glyphRecords = []
        for index, glyph in enumerate(glyphs):
            glyphRecord = GlyphRecord()
            glyphRecord.glyph = glyph
            glyphRecord.cluster = index
            #
            w, h = glyph.width, glyph.height
            layerSet = glyph.layerSet
            if layerSet is not None:
                layer = layerSet.defaultLayer
                if glyph.name in layer:
                    layerGlyph = layer[glyph.name]
                    w, h = layerGlyph.width, layerGlyph.height
            glyphRecord.xAdvance = w
            glyphRecord.yAdvance = h
            #
            glyphRecords.append(glyphRecord)
        self.setGlyphRecords(glyphRecords)

    # fitting

    def fitScaleMetrics(self):
        """
        Scales and centers the viewport around the font’s metrics.
        """
        fitHeight = self.height()
        fitWidth = self.width()
        glyph = self._glyph
        bottom, top = self.verticalBounds()
        height = -bottom + top
        self.setScale(fitHeight / height)
        otherWidth = 0
        for glyph_ in self.glyphs():
            if glyph_ == glyph:
                break
            otherWidth += glyph_.width
        dx = 0.5 * (fitWidth - glyph.width * self._scale) - otherWidth * self._scale
        dy = 0.5 * (fitHeight - height * self._scale) + top * self._scale
        # TODO: round?
        self._drawingOffset = QPoint(dx, dy)
        self.pointSizeModified.emit(self._impliedPointSize)

    def fitScaleBBox(self):
        """
        Scales and centers the viewport around the *glyph*’s bounding box.
        """
        glyph = self.activeGlyph()
        if glyph is None:
            return
        if glyph.bounds is None:
            self.fitScaleMetrics()
            return
        fitHeight = self.height()
        fitWidth = self.width()
        left, bottom, right, top = glyph.bounds
        glyphHeight = top - bottom
        glyphHeightPad = glyphHeight + _noPointSizePadding * 2
        glyphWidth = right - left
        glyphWidthPad = glyphWidth + _noPointSizePadding * 2
        self.setScale(min(fitHeight / glyphHeightPad, fitWidth / glyphWidthPad))
        otherWidth = 0
        for glyph_ in self.glyphs():
            if glyph_ == glyph:
                break
            otherWidth += glyph_.width
        dx = (
            0.5 * (fitWidth - glyphWidth * self._scale)
            - (otherWidth + left) * self._scale
        )
        dy = 0.5 * (fitHeight - glyphHeight * self._scale) + top * self._scale
        # TODO: round?
        self._drawingOffset = QPoint(dx, dy)
        self.pointSizeModified.emit(self._impliedPointSize)

    def scrollBy(self, point):
        self._drawingOffset += point
        self.update()

    def verticalBounds(self):
        bottom = self._descender
        top = max(self._capHeight, self._ascender, self._unitsPerEm + self._descender)
        return bottom, top

    def zoom(self, newScale, anchor="center"):
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
        if newScale < 1e-2 or newScale > 1e3:
            return
        # compute new position
        # http://stackoverflow.com/a/32269574/2037879
        if isinstance(anchor, QPoint):
            pos = anchor
        elif anchor == "cursor":
            pos = self.mapFromGlobal(QCursor.pos())
        elif anchor == "center":
            pos = QPoint(0.5 * self.width(), 0.5 * self.height())
        else:
            raise ValueError(f"invalid anchor value: {anchor}")
        deltaToPos = pos / oldScale - self._drawingOffset / oldScale
        delta = deltaToPos * (newScale - oldScale)
        self.setScale(newScale)
        self._drawingOffset -= delta

    # position mapping

    def mapFromCanvas(self, pos, index=None):
        """
        Maps *pos* from glyph canvas to this widget’s coordinates.

        Note that canvas coordinates are scale-independent while widget
        coordinates are not.
        """
        if index is None:
            index = self._activeIndex
        offset = self._drawingOffset
        x, y = pos.x(), pos.y()
        for glyphIndex, glyphRecord in enumerate(self._glyphRecords):
            if glyphIndex == index:
                x += glyphRecord.xOffset
                y += glyphRecord.yOffset
                break
            x += glyphRecord.xAdvance
            y += glyphRecord.yAdvance
        x = x * self._scale + offset.x()
        y = y * -self._scale + offset.y()
        return pos.__class__(x, y)

    def mapToCanvas(self, pos, index=None):
        """
        Maps *pos* from this widget’s to glyph canvas coordinates.

        Note that canvas coordinates are scale-independent while widget
        coordinates are not.
        """
        if index is None:
            index = self._activeIndex
        offset = self._drawingOffset
        x = (pos.x() - offset.x()) * self._inverseScale
        y = (offset.y() - pos.y()) * self._inverseScale
        for glyphIndex, glyphRecord in enumerate(self._glyphRecords):
            if glyphIndex == index:
                x -= glyphRecord.xOffset
                y -= glyphRecord.yOffset
                break
            x -= glyphRecord.xAdvance
            y -= glyphRecord.yAdvance
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

    # ---------------
    # Display Control
    # ---------------

    def drawingAttribute(self, attr, flags):
        if flags.isActiveGlyph != flags.isActiveLayer:
            if not flags.isActiveGlyph and attr == "showGlyphComponentStroke":
                return True
            return attr == "showGlyphStroke"
        elif not flags.isActiveGlyph:
            return False
        return self._defaultDrawingAttributes.get(attr)

    def drawingColor(self, attr, flags):
        if attr == "contourFillColor":
            return Qt.black
        return None

    # defaults

    def defaultDrawingAttribute(self, attr):
        return self._defaultDrawingAttributes.get(attr)

    def setDefaultDrawingAttribute(self, attr, value):
        self._defaultDrawingAttributes[attr] = value
        self.update()

    def showFill(self):
        return self.defaultDrawingAttribute("showGlyphFill")

    def setShowFill(self, value):
        self.setDefaultDrawingAttribute("showGlyphFill", value)

    def showStroke(self):
        return self.defaultDrawingAttribute("showGlyphStroke")

    def setShowStroke(self, value):
        self.setDefaultDrawingAttribute("showGlyphStroke", value)

    def showMetrics(self):
        return self.defaultDrawingAttribute("showGlyphMargins")

    def setShowMetrics(self, value):
        self.setDefaultDrawingAttribute("showGlyphMargins", value)
        self.setDefaultDrawingAttribute("showFontVerticalMetrics", value)

    def showImage(self):
        return self.defaultDrawingAttribute("showGlyphImage")

    def setShowImage(self, value):
        self.setDefaultDrawingAttribute("showGlyphImage", value)

    def showMetricsTitles(self):
        return self.defaultDrawingAttribute("showFontVerticalMetricsTitles")

    def setShowMetricsTitles(self, value):
        self.setDefaultDrawingAttribute("showFontVerticalMetricsTitles", value)

    def showGuidelines(self):
        return self.defaultDrawingAttribute("showFontGuidelines")

    def setShowGuidelines(self, value):
        self.setDefaultDrawingAttribute("showFontGuidelines", value)
        self.setDefaultDrawingAttribute("showGlyphGuidelines", value)

    def showOnCurvePoints(self):
        return self.defaultDrawingAttribute("showGlyphOnCurvePoints")

    def setShowOnCurvePoints(self, value):
        self.setDefaultDrawingAttribute("showGlyphStartPoints", value)
        self.setDefaultDrawingAttribute("showGlyphOnCurvePoints", value)

    def showOffCurvePoints(self):
        return self.defaultDrawingAttribute("showGlyphOffCurvePoints")

    def setShowOffCurvePoints(self, value):
        self.setDefaultDrawingAttribute("showGlyphOffCurvePoints", value)

    def showPointCoordinates(self):
        return self.defaultDrawingAttribute("showGlyphPointCoordinates")

    def setShowPointCoordinates(self, value):
        self.setDefaultDrawingAttribute("showGlyphPointCoordinates", value)

    def showAnchors(self):
        return self.defaultDrawingAttribute("showGlyphAnchors")

    def setShowAnchors(self, value):
        self.setDefaultDrawingAttribute("showGlyphAnchors", value)

    def showBlues(self):
        return self.defaultDrawingAttribute("showFontPostscriptBlues")

    def setShowBlues(self, value):
        self.setDefaultDrawingAttribute("showFontPostscriptBlues", value)

    def showFamilyBlues(self):
        return self.defaultDrawingAttribute("showFontPostscriptFamilyBlues")

    def setShowFamilyBlues(self, value):
        self.setDefaultDrawingAttribute("showFontPostscriptFamilyBlues", value)

    def backgroundColor(self):
        return self._backgroundColor

    def setBackgroundColor(self, color):
        self._backgroundColor = color
        self.update()

    # ---------------
    # Drawing helpers
    # ---------------

    def drawGlyphBackground(self, painter, glyph, flags):
        if flags.isActiveLayer:
            # draw the blues
            if self.drawingAttribute("showFontPostscriptBlues", flags):
                self.drawBlues(painter, glyph, flags)
            if self.drawingAttribute("showFontPostscriptFamilyBlues", flags):
                self.drawFamilyBlues(painter, glyph, flags)
            # draw the metrics
            if self.drawingAttribute("showGlyphMetrics", flags):
                self.drawMetrics(painter, glyph, flags)

    def drawBackground(self, painter, index):
        pass

    def drawGlyphLayer(self, painter, glyph, flags):
        # draw the image
        if self.drawingAttribute("showGlyphImage", flags):
            self.drawImage(painter, glyph, flags)
        # draw the guidelines
        if (
            flags.isActiveLayer
            and self.drawingAttribute("showFontGuidelines", flags)
            or self.drawingAttribute("showGlyphGuidelines", flags)
        ):
            self.drawGuidelines(painter, glyph, flags)
        # draw the glyph
        if (
            self.drawingAttribute("showGlyphOnCurvePoints", flags)
            or self.drawingAttribute("showGlyphFill", flags)
            or self.drawingAttribute("showGlyphComponentFill", flags)
        ):
            self.drawFillAndPoints(painter, glyph, flags)
        if self.drawingAttribute("showGlyphStroke", flags) or self.drawingAttribute(
            "showGlyphComponentStroke", flags
        ):
            self.drawStroke(painter, glyph, flags)
        if self.drawingAttribute("showGlyphAnchors", flags):
            self.drawAnchors(painter, glyph, flags)

    def drawForeground(self, painter, index):
        pass

    # drawing primitives

    def drawBlues(self, painter, glyph, flags):
        drawing.drawFontPostscriptBlues(painter, glyph, self._inverseScale)

    def drawFamilyBlues(self, painter, glyph, flags):
        drawing.drawFontPostscriptFamilyBlues(painter, glyph, self._inverseScale)

    def drawMetrics(self, painter, glyph, flags):
        drawVMetrics = flags.isActiveLayer and self.drawingAttribute(
            "showFontVerticalMetrics", flags
        )
        drawText = (
            self.drawingAttribute("showFontVerticalMetricsTitles", flags)
            and self._impliedPointSize > GlyphViewMinSizeForDetails
        )
        drawing.drawGlyphMetrics(
            painter,
            glyph,
            self._inverseScale,
            drawVMetrics=drawVMetrics,
            drawText=drawText,
        )

    def drawImage(self, painter, glyph, flags):
        drawing.drawGlyphImage(painter, glyph, self._inverseScale)

    def drawGuidelines(self, painter, glyph, flags):
        drawText = self._impliedPointSize > GlyphViewMinSizeForDetails
        viewportRect = self.mapRectToCanvas(self.rect()).getRect()
        if self.drawingAttribute("showFontGuidelines", flags):
            drawing.drawFontGuidelines(
                painter, glyph, self._inverseScale, viewportRect, drawText=drawText
            )
        if self.drawingAttribute("showGlyphGuidelines", flags):
            drawing.drawGlyphGuidelines(
                painter, glyph, self._inverseScale, viewportRect, drawText=drawText
            )

    def drawFillAndPoints(self, painter, glyph, flags):
        drawFill = self.drawingAttribute("showGlyphFill", flags)
        drawComponentFill = self.drawingAttribute("showGlyphComponentFill", flags)
        drawing.drawGlyphFillAndStroke(
            painter,
            glyph,
            self._inverseScale,
            drawFill=drawFill,
            drawComponentFill=drawComponentFill,
            drawStroke=False,
        )
        if not self._impliedPointSize > GlyphViewMinSizeForDetails:
            return
        drawStartPoints = self.drawingAttribute("showGlyphStartPoints", flags)
        drawOnCurves = self.drawingAttribute("showGlyphOnCurvePoints", flags)
        drawOffCurves = self.drawingAttribute("showGlyphOffCurvePoints", flags)
        drawCoordinates = self.drawingAttribute("showGlyphPointCoordinates", flags)
        drawing.drawGlyphPoints(
            painter,
            glyph,
            self._inverseScale,
            drawOnCurves=drawOnCurves,
            drawOffCurves=drawOffCurves,
            drawStartPoints=drawStartPoints,
            drawCoordinates=drawCoordinates,
            backgroundColor=self._backgroundColor,
        )

    def drawStroke(self, painter, glyph, flags):
        drawStroke = self.drawingAttribute("showGlyphStroke", flags)
        drawComponentStroke = self.drawingAttribute("showGlyphComponentStroke", flags)
        drawing.drawGlyphFillAndStroke(
            painter,
            glyph,
            self._inverseScale,
            drawFill=False,
            drawComponentsFill=False,
            drawStroke=drawStroke,
            drawComponentStroke=drawComponentStroke,
        )

    def drawAnchors(self, painter, glyph, flags):
        if not self._impliedPointSize > GlyphViewMinSizeForDetails:
            return
        drawing.drawGlyphAnchors(painter, glyph, self._inverseScale)

    # ---------------
    # QWidget methods
    # ---------------

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setFont(UIFont)
        painter.setRenderHint(QPainter.Antialiasing)

        # draw the background
        self._glyphRecordsRects = {}
        painter.fillRect(event.rect(), self._backgroundColor)
        if not self._glyphRecords:
            return

        # move into the canvas origin
        offset = self._drawingOffset
        painter.translate(offset)
        painter.scale(self._scale, -self._scale)

        left = offset.x()
        top = offset.y() - self._ascender * self._scale
        height = self._unitsPerEm * self._scale
        painter.save()
        for recordIndex, glyphRecord in enumerate(self._glyphRecords):
            active = recordIndex == self._activeIndex
            xO = glyphRecord.xOffset
            yO = glyphRecord.yOffset
            xA = glyphRecord.xAdvance
            yA = glyphRecord.yAdvance
            # store the glyph rect
            top -= yO * self._scale
            glyphHeight = height + yA * self._scale
            glyphLeft = left + xO * self._scale
            glyphWidth = xA * self._scale
            rect = (glyphLeft, top, glyphWidth, glyphHeight)
            self._glyphRecordsRects[rect] = recordIndex
            # handle placement
            if xO or yO:
                painter.translate(xO, yO)
            # draw the background
            painter.save()
            foreGlyph = glyphRecord.glyph
            foreGlyph = foreGlyph.font[foreGlyph.name]
            self.drawGlyphBackground(painter, foreGlyph, GlyphFlags(active))
            self.drawBackground(painter, recordIndex)
            painter.restore()
            # shift for the next glyph
            painter.translate(xA - xO, yA - yO)
            left += glyphWidth
        painter.restore()

        for recordIndex, glyphRecord in enumerate(self._glyphRecords):
            glyph = glyphRecord.glyph
            xO = glyphRecord.xOffset
            yO = glyphRecord.yOffset
            xA = glyphRecord.xAdvance
            yA = glyphRecord.yAdvance
            # gather the crowd
            layerSet = glyph.layerSet
            if layerSet is None:
                layers = [(glyph, GlyphFlags(True))]
            else:
                layers = []
                for layerName in reversed(layerSet.layerOrder):
                    layer = layerSet[layerName]
                    if glyph.name in layer:
                        layerGlyph = layer[glyph.name]
                        layerFlags = GlyphFlags(
                            recordIndex == self._activeIndex, layerGlyph == glyph
                        )
                        layers.append((layerGlyph, layerFlags))
            # handle placement
            if xO or yO:
                painter.translate(xO, yO)
            # draw layers and foreground
            painter.save()
            for layerGlyph, layerFlags in layers:
                self.drawGlyphLayer(painter, layerGlyph, layerFlags)
            self.drawForeground(painter, recordIndex)
            painter.restore()
            # shift for the next glyph
            painter.translate(xA - xO, yA - yO)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not hasattr(self, "_drawingOffset"):
            return
        delta = 0.5 * (event.oldSize() - event.size())
        offset = self._drawingOffset
        offset.setX(offset.x() - delta.width())
        offset.setY(offset.y() - delta.height())

    def minimumSizeHint(self):
        return QSize(400, 400)

    def sizeHint(self):
        return QSize(900, 900)

    def showEvent(self, event):
        super().showEvent(event)
        if hasattr(self, "_fitViewport"):
            self.fitScaleBBox()
            del self._fitViewport

    def event(self, event):
        if event.type() == QEvent.Gesture:
            # Handle pan gestures
            panGesture = event.gesture(Qt.PanGesture)
            if panGesture:
                self._drawingOffset += panGesture.delta()

            # Handle pinch gestures
            pinchGesture = event.gesture(Qt.PinchGesture)
            if pinchGesture:
                newScale = self._scale * pinchGesture.scaleFactor()
                self.zoom(newScale, "cursor")
                self.pointSizeModified.emit(self._impliedPointSize)

            return True
        return super().event(event)

    def wheelEvent(self, event):
        if event.modifiers() & platformSpecific.scaleModifier():
            step = event.angleDelta().y() / 120.0
            newScale = self._scale * pow(1.2, step)
            self.zoom(newScale, event.pos())
            self.pointSizeModified.emit(self._impliedPointSize)
        else:
            delta = event.pixelDelta()
            if delta.isNull():
                delta = event.angleDelta()
                dx = delta.x() / 120 * QApplication.wheelScrollLines() * 8
                dy = delta.y() / 120 * QApplication.wheelScrollLines() * 8
                delta = QPoint(dx, dy)
            self._drawingOffset += delta
            self.update()
        event.accept()


class GlyphRecord:
    __slots__ = ["glyph", "cluster", "xOffset", "yOffset", "xAdvance", "yAdvance"]

    def __init__(self):
        self.glyph = None
        self.cluster = 0
        self.xOffset = 0
        self.yOffset = 0
        self.xAdvance = 0
        self.yAdvance = 0

    def __repr__(self):
        return "<GlyphRecord {}={}@{},{}+{}>".format(
            self.glyph.name, self.cluster, self.xAdvance, self.xOffset, self.yOffset
        )
