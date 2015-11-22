from defconQt.glyphCollectionView import headerFont
# XXX: drawingTools sound too much like canvas tools
from defconQt.util import drawingTools
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class MainGVWindow(QMainWindow):
    def __init__(self, glyph, parent=None):
        super().__init__(parent)
        self.view = GlyphView(self)
        self.view.setGlyph(glyph)
        self.setCentralWidget(self.view.scrollArea())
        self.resize(800, 700)


class GlyphView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._glyph = None

        # drawing attributes
        self._layerDrawingAttributes = {}
        self._fallbackDrawingAttributes = dict(
            showGlyphFill=True,
            showGlyphStroke=True,
            showGlyphOnCurvePoints=True,
            showGlyphStartPoints=True,
            showGlyphOffCurvePoints=True, #
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
        top = max(self._capHeight, self._ascender, self._unitsPerEm + self._descender)
        width = abs(left) + right
        height = -bottom + top
        return width, height

    def _fitScale(self):
        fitHeight = self._scrollArea.viewport().height()
        _, glyphHeight = self._getGlyphWidthHeight()
        glyphHeight += self._noPointSizePadding * 2
        self.setScale(fitHeight / glyphHeight)

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
            font = self._font = glyph.getParent()
            if font is not None:
                self._unitsPerEm = font.info.unitsPerEm
                self._descender = font.info.descender
                self._xHeight = font.info.xHeight
                self._ascender = font.info.ascender
                self._capHeight = font.info.capHeight
            self.setScale(self._scale)
            self.adjustSize()
            #self.recalculateFrame()
        self.update()

    # --------------------
    # Notification Support
    # --------------------

    def glyphChanged(self):
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
    # QWidget methods
    # ---------------

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setFont(headerFont)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()

        # draw the background
        painter.fillRect(rect, Qt.white)#self._backgroundColor)
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
        justInCaseBuffer = 1 * self._inverseScale
        xOffset += justInCaseBuffer
        yOffset += justInCaseBuffer
        w += justInCaseBuffer * 2
        h += justInCaseBuffer * 2
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
            if layerName is None and self.drawingAttribute("showFontPostscriptBlues", None):
                self.drawBlues(painter, glyph, layerName)
            if layerName is None and self.drawingAttribute("showFontPostscriptFamilyBlues", None):
                self.drawFamilyBlues(painter, glyph, layerName)
            # draw the margins
            if self.drawingAttribute("showGlyphMargins", layerName):
                self.drawMargins(painter, glyph, layerName)
            # draw the vertical metrics
            if layerName is None and self.drawingAttribute("showFontVerticalMetrics", None):
                self.drawVerticalMetrics(painter, glyph, layerName)
            # draw the glyph
            if self.drawingAttribute("showGlyphFill", layerName) or self.drawingAttribute("showGlyphStroke", layerName):
                self.drawFillAndStroke(painter, glyph, layerName)
            if self.drawingAttribute("showGlyphOnCurvePoints", layerName) or self.drawingAttribute("showGlyphOffCurvePoints", layerName):
                self.drawPoints(painter, glyph, layerName)
            if self.drawingAttribute("showGlyphAnchors", layerName):
                self.drawAnchors(painter, glyph, layerName)
        painter.restore()

    def drawImage(self, painter, glyph, layerName):
        drawingTools.drawGlyphImage(
            painter, glyph, self._inverseScale, self._drawingRect)

    def drawBlues(self, painter, glyph, layerName):
        drawingTools.drawFontPostscriptBlues(
            painter, glyph, self._inverseScale, self._drawingRect)

    def drawFamilyBlues(self, painter, glyph, layerName):
        drawingTools.drawFontPostscriptFamilyBlues(
            painter, glyph, self._inverseScale, self._drawingRect)

    def drawVerticalMetrics(self, painter, glyph, layerName):
        drawingTools.drawFontVerticalMetrics(
            painter, glyph, self._inverseScale, self._drawingRect)

    def drawMargins(self, painter, glyph, layerName):
        drawingTools.drawGlyphMargins(
            painter, glyph, self._inverseScale, self._drawingRect)

    def drawFillAndStroke(self, painter, glyph, layerName):
        showFill = self.drawingAttribute("showGlyphFill", layerName)
        showStroke = self.drawingAttribute("showGlyphStroke", layerName)
        drawingTools.drawGlyphFillAndStroke(
            painter, glyph, self._inverseScale, self._drawingRect,
            drawFill=showFill, drawStroke=showStroke)

    def drawPoints(self, painter, glyph, layerName):
        drawStartPoints = self.drawingAttribute(
            "showGlyphStartPoints", layerName) and self._impliedPointSize > 175
        drawOnCurves = self.drawingAttribute(
            "showGlyphOnCurvePoints", layerName) and self._impliedPointSize > 175
        drawOffCurves = self.drawingAttribute(
            "showGlyphOffCurvePoints", layerName) and self._impliedPointSize > 175
        drawCoordinates = self.drawingAttribute(
            "showGlyphPointCoordinates", layerName) and self._impliedPointSize > 250
        drawingTools.drawGlyphPoints(
            painter, glyph, self._inverseScale, self._drawingRect,
            drawStartPoints=drawStartPoints, drawOnCurves=drawOnCurves,
            drawOffCurves=drawOffCurves, drawCoordinates=drawCoordinates,
            backgroundColor=Qt.white)

    def drawAnchors(self, painter, glyph, layerName):
        drawText = self._impliedPointSize > 50
        drawingTools.drawGlyphAnchors(
            painter, glyph, self._inverseScale, self._drawingRect,
            drawText=drawText)#, backgroundColor=self._backgroundColor)

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
        print("resize!")
        self.adjustSize()
        event.accept()

    def _showEvent(self, event):
        print("showtime!")
        self._fitScale()
        self.adjustSize()
        # TODO: switch to QRect?
        #if self._drawingRect is not None:
        xC, yC = self.width() / 2, self.height() / 2
        #xM, yM = self._glyph.width / 2
        self._scrollArea.ensureVisible(xC, yC)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            factor = pow(1.2, event.angleDelta().y() / 120.0)
            # TODO: anchor on scale
            # TODO: maybe put out a func that does multiply by default
            self.setScale(self._scale * factor)
            # TODO: maybe merge this in setScale
            self.adjustSize()
            self.update()
            event.accept()
        else:
            super().wheelEvent(event)
