import trufont
from trufont.objects.layoutManager import LayoutManager
from trufont.objects.textCursor import TextCursor
from trufont.util import drawing, platformSpecific
import wx
import wx.lib.newevent

# TODO: forbid scrolling past scene boundary

__all__ = ("GlyphContextView",)

MinSizeForDetails = 175
MinSizeForGuidelines = 100
MinSizeForGrid = 10000

OptionsChangedEvent, EVT_OPTIONS_CHANGED = wx.lib.newevent.NewEvent()
PointSizeChangedEvent, EVT_PT_SIZE_CHANGED = wx.lib.newevent.NewEvent()
TextChangedEvent, EVT_TEXT_CHANGED = wx.lib.newevent.NewEvent()

# maybe clientToCanvas etc. and scrollBy could be capitalized back, idk


class GlyphContextView(wx.Window):
    OPTIONS_CHANGED = EVT_OPTIONS_CHANGED
    PT_SIZE_CHANGED = EVT_PT_SIZE_CHANGED
    TEXT_CHANGED = EVT_TEXT_CHANGED

    def __init__(self, parent, font):
        super().__init__(parent, style=wx.FULL_REPAINT_ON_RESIZE | wx.WANTS_CHARS)
        self.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.SetBackgroundColour(wx.WHITE)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetDoubleBuffered(True)

        self._font = font
        self._textBuffer = []
        self._textCursor = TextCursor(self, self._textBuffer)

        self._offset = wx.RealPoint()
        self._scale = 1.0
        # try to remove these two
        self._inverseScale = 0.1
        self._pointSize = 1000

        self._applyKerning = True
        self._direction = "ltr"
        self._features = {}
        self._layerOverrides = {}
        self._layoutManager = LayoutManager(self)

        self._fitViewport = True

    @property
    def activeLayer(self):
        return self._layoutManager.activeLayer

    @activeLayer.setter
    def activeLayer(self, layer):
        # XXX still need to shift indices when the text changes
        index = self._layoutManager.activeIndex
        if layer is layer.glyph.layerForMaster(None):
            if index not in self._layerOverrides:
                return
            del self._layerOverrides[index]
        else:
            self._layerOverrides[index] = layer
        self.applyOptionsChange()
        trufont.TruFont.updateUI()

    @property
    def applyKerning(self):
        return self._applyKerning

    @applyKerning.setter
    def applyKerning(self, value):
        self._applyKerning = value
        self.applyOptionsChange()

    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, value):
        self._direction = value
        self.applyOptionsChange()

    @property
    def inverseScale(self):
        return self._inverseScale

    @property
    def pointSize(self):
        return self._pointSize

    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, value):
        if value <= 0:
            value = .01
        if value == self._scale:
            return
        self._scale = value
        self._inverseScale = 1.0 / value
        self._pointSize = sz = round(self._font.unitsPerEm * value)
        wx.PostEvent(self, PointSizeChangedEvent(pointSize=sz))
        self.Refresh()

    @property
    def text(self):
        return self._textCursor.text()

    @text.setter
    def text(self, text):
        self._textCursor.setText(text)

    @property
    def textCursor(self):
        return self._textCursor

    def drawingAttribute(self, attr):
        return trufont.TruFont.settings[attr]

    def ensureCaretVisible(self):
        # TODO also scroll vertically
        manager = self._layoutManager
        xPos = self._offset.x + manager.caretPosition * self._scale
        if xPos < 0:
            self._offset.x -= xPos - 28
        else:
            w, _ = self.GetClientSize()
            if xPos > w:
                self._offset.x -= xPos - w + 28
            else:
                return
        self.Refresh()

    def moveTextCursorTo(self, point, lOffset=False):
        manager = self._layoutManager
        textCursor = self.textCursor
        index = manager.indexAt(
            (point.x - self._offset.x) * self._inverseScale, lOffset
        )
        if index is not None:
            textCursor.setPosition(index)

    # events

    def applyCursorChange(self):
        self._layoutManager.clearPosition()
        self.ensureCaretVisible()
        self.Refresh()

    def applyOptionsChange(self):
        self._layoutManager.clear()
        evt = OptionsChangedEvent()
        evt.SetEventObject(self)
        wx.PostEvent(self, evt)
        self.ensureCaretVisible()
        self.Refresh()

    def applyTextChange(self):
        self._layoutManager.clear()
        evt = TextChangedEvent()
        evt.SetEventObject(self)
        wx.PostEvent(self, evt)
        self.ensureCaretVisible()
        self.Refresh()

    # fitting

    def fitMetrics(self):
        master = self._font.selectedMaster
        ascender = master.ascender
        height = -master.descender + ascender
        fitWidth, fitHeight = self.GetSize()
        # 40% padding around layer box
        inflatedHeight = round(height * 1.4)
        self.scale = fitHeight / inflatedHeight

        manager = self._layoutManager
        activeIndex = manager.activeIndex
        activeWidth = 600
        otherWidth = 0
        for idx, otherLayer in enumerate(manager.layers):
            if idx == activeIndex:
                activeLayer = otherLayer
                activeWidth = otherLayer.width
                break
            otherWidth += otherLayer.width
        scale = self._scale
        dx = .5 * (fitWidth - activeWidth * scale) - otherWidth * scale
        dy = .5 * (fitHeight - height * scale) + ascender * scale
        self._offset = wx.RealPoint(dx, dy)
        self.Refresh()

    def scrollBy(self, point):
        self._offset += wx.RealPoint(point)
        self.Refresh()

    def zoom(self, newScale, anchor="center"):
        oldScale = self._scale
        if newScale < 1e-2 or newScale > 1e3:
            return
        # compute new position
        # http://stackoverflow.com/a/32269574/2037879
        if isinstance(anchor, wx.Point):
            pos = anchor
        elif anchor == "cursor":
            pos = self.ScreenToClient(wx.GetMousePosition())
        elif anchor == "center":
            width, height = self.GetSize()
            pos = wx.Point(.5 * width, .5 * height)
        else:
            raise ValueError(f"invalid anchor value: {anchor!r}")
        xDeltaToPos = pos.x / oldScale - self._offset.x / oldScale
        yDeltaToPos = pos.y / oldScale - self._offset.y / oldScale
        xDelta = xDeltaToPos * (newScale - oldScale)
        yDelta = yDeltaToPos * (newScale - oldScale)
        self.scale = newScale
        self._offset -= wx.RealPoint(xDelta, yDelta)

    # position mapping

    def canvasToClient(self, pos, index=None):
        manager = self._layoutManager
        if index is None:
            index = manager.activeIndex
        offset = self._offset
        x, y = pos.x, pos.y
        for idx, _, xOff, yOff, xAdv, yAdv in manager.records:
            if idx == index:
                x += xOff
                y += yOff
                break
            x += xAdv
            y += yAdv
        x = x * self._scale + offset.x
        y = y * -self._scale + offset.y
        return wx.RealPoint(x, y)

    def clientToCanvas(self, pos, index=None):  # XXX: just take x and y?
        manager = self._layoutManager
        if index is None:
            index = manager.activeIndex
        offset = self._offset
        x = (pos.x - offset.x) * self._inverseScale
        y = (offset.y - pos.y) * self._inverseScale
        for idx, _, xOff, yOff, xAdv, yAdv in manager.records:
            if idx == index:
                x -= xOff
                y -= yOff
                break
            x -= xAdv
            y -= yAdv
        return wx.RealPoint(x, y)

    def canvasRectToClient(self, rect):  # XXX: wx.Rect only takes integers
        x, y, w, h = rect.Get()
        origin = self.canvasToClient(wx.RealPoint(x, y))
        w *= self._scale
        h *= self._scale
        return rect.__class__(origin.x, origin.y - h, w, h)

    def clientRectToCanvas(self, rect):
        x, y, w, h = rect.Get()
        origin = self.clientToCanvas(wx.RealPoint(x, y))
        w *= self._inverseScale
        h *= self._inverseScale
        return rect.__class__(origin.x, origin.y - h, w, h)

    # -------------
    # Drawing funcs
    # -------------

    def drawBackground(self, ctx, layer):
        scale = self._inverseScale
        showMetrics = self.drawingAttribute("showMetrics")
        if showMetrics:
            if self._pointSize > MinSizeForGrid:
                viewportRect = (
                    self.clientRectToCanvas(wx.Rect(self.GetSize())).Inflate(2, 2).Get()
                )
                drawing.drawGrid(ctx, scale, viewportRect)
        if layer is None:
            return
        if showMetrics:
            drawing.drawLayerMetrics(ctx, layer, scale)
        if self.drawingAttribute("showFill"):
            fillColor = wx.Colour(*self.drawingAttribute("fillColor"))
            ctx.SetBrush(wx.Brush(fillColor))
            ctx.FillPath(layer.closedGraphicsPath, wx.WINDING_RULE)

    def drawForeground(self, ctx, layer):
        glyph = layer._parent
        scale = self._inverseScale

        # layers
        if self.drawingAttribute("showBackground"):
            strokeColor = self.drawingAttribute("backgroundStrokeColor")
            pen = wx.Pen(strokeColor, scale)
            ctx.SetPen(pen)
            for otherLayer in glyph.layers:
                if not otherLayer.visible or otherLayer is layer:
                    continue
                # image
                # drawing.drawLayerImage(ctx, otherLayer, self._inverseScale)
                # stroke
                color = otherLayer.color
                if color:
                    ctx.SetPen(wx.Pen(wx.Colour(*color), scale))
                ctx.StrokePath(otherLayer.closedComponentsGraphicsPath)
                ctx.StrokePath(otherLayer.openComponentsGraphicsPath)
                ctx.StrokePath(otherLayer.closedGraphicsPath)
                ctx.StrokePath(otherLayer.openGraphicsPath)
                # TODO: draw points, more control?
                if color:
                    ctx.SetPen(pen)
        # image
        # drawing.drawLayerImage(ctx, layer, self._inverseScale)
        # guidelines
        if self._pointSize > MinSizeForGuidelines and self.drawingAttribute(
            "showGuidelines"
        ):
            viewportRect = (
                self.clientRectToCanvas(wx.Rect(self.GetSize())).Inflate(2, 2).Get()
            )
            drawing.drawLayerGuidelines(ctx, layer, self._inverseScale, viewportRect)
        # layer
        if layer:
            # components
            fillColor = wx.Colour(*self.drawingAttribute("componentFillColor"))
            drawing.drawLayerComponents(ctx, layer, scale, fillColor=fillColor)
            # fill
            # drawn in the background
            # selection
            if self._pointSize > MinSizeForDetails and self.drawingAttribute(
                "showSelection"
            ):
                selectionColor = wx.Colour(*self.drawingAttribute("selectionColor"))
                ctx.SetPen(wx.Pen(selectionColor, 3.5 * scale))
                for path in layer.selectedPaths:
                    ctx.StrokePath(path.graphicsPath)
            # points
            if self._pointSize > MinSizeForDetails and self.drawingAttribute(
                "showPoints"
            ):
                backgroundColor = self.GetBackgroundColour()
                if self.drawingAttribute("showCoordinates"):
                    coordinatesColor = None
                else:
                    coordinatesColor = wx.NullColour
                drawing.drawLayerPoints(
                    ctx,
                    layer,
                    scale,
                    backgroundColor=backgroundColor,
                    coordinatesColor=coordinatesColor,
                )
            # stroke
            # if we show fill but not stroke, we still stroke open paths
            showStroke = self.drawingAttribute("showStroke")
            if showStroke or self.drawingAttribute("showFill"):
                strokeColor = wx.Colour(*self.drawingAttribute("strokeColor"))
                ctx.SetPen(wx.Pen(strokeColor, scale))
                if showStroke:
                    ctx.StrokePath(layer.closedGraphicsPath)
                ctx.StrokePath(layer.openGraphicsPath)
            if self._pointSize > MinSizeForDetails and self.drawingAttribute(
                "showSelectionBounds"
            ):
                drawing.drawLayerSelectionBounds(ctx, layer, scale)
        else:
            drawing.drawLayerTemplate(ctx, layer, scale)
        # anchors
        if (
            layer.anchors
            and self._pointSize > MinSizeForDetails
            and self.drawingAttribute("showAnchors")
        ):
            drawing.drawLayerAnchors(ctx, layer, scale)

    # ----------
    # wx methods
    # ----------

    def DoGetBestSize(self):
        return wx.Size(900, 900)

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.SetBrush(wx.WHITE_BRUSH)
        dc.Clear()
        ctx = wx.GraphicsContext.Create(dc)
        ctx.GetDC = lambda: dc
        ctx.GetFont = self.GetFont
        ctx.SetFont(self.GetFont(), wx.BLACK)

        # move into the canvas origin
        offset = wx.Point(self._offset)
        scale = self._scale
        ctx.Translate(offset.x, offset.y)
        ctx.Scale(scale, -scale)

        drawTextCursor = self.drawingAttribute("showTextCursor")
        inverseScale = self._inverseScale
        manager = self._layoutManager
        layers = manager.layers
        if not layers:
            if drawTextCursor:
                drawing.drawCaret(ctx, inverseScale, self._font)
            self.drawBackground(ctx, None)
            del ctx.GetDC
            del ctx.GetFont
            return

        activeIndex = manager.activeIndex
        caretIndex = manager.caretIndex + 1  # adjust to not have to shift
        drawTextMetrics = self._pointSize > MinSizeForDetails and self.drawingAttribute(
            "showTextMetrics"
        )
        # draw cursor + active background
        ctx.PushState()
        for idx, layer, xOff, yOff, xAdv, yAdv in manager.records:
            if drawTextMetrics:
                drawing.drawLayerTextMetrics(ctx, layer, inverseScale)
            if drawTextCursor and idx == caretIndex:
                drawing.drawCaret(ctx, inverseScale, self._font)
                drawTextCursor = False
            if idx == activeIndex:
                ctx.PushState()
                ctx.Translate(xOff, yOff)
                activeTransform = ctx.GetTransform()
                self.drawBackground(ctx, layer)
                ctx.PopState()
                activeLayer = layer
            ctx.Translate(xAdv, yAdv)
        if drawTextCursor:
            drawing.drawCaret(ctx, inverseScale, self._font)
        ctx.PopState()
        # draw inactive
        ctx.PushState()
        ctx.SetBrush(wx.BLACK_BRUSH)
        ctx.SetPen(wx.BLACK_PEN)
        for idx, layer, xOff, yOff, xAdv, yAdv in manager.records:
            if idx != activeIndex:
                ctx.PushState()
                ctx.Translate(xOff, yOff)
                if layer:
                    ctx.FillPath(layer.closedComponentsGraphicsPath, wx.WINDING_RULE)
                    ctx.StrokePath(layer.openComponentsGraphicsPath)
                    ctx.FillPath(layer.closedGraphicsPath, wx.WINDING_RULE)
                    ctx.StrokePath(layer.openGraphicsPath)
                else:
                    drawing.drawLayerTemplate(ctx, layer, scale)
                ctx.PopState()
            ctx.Translate(xAdv, yAdv)
        ctx.PopState()
        # draw active foreground
        ctx.PushState()
        ctx.SetTransform(activeTransform)
        self.drawForeground(ctx, activeLayer)
        ctx.PopState()

        del ctx.GetDC
        del ctx.GetFont

    def OnMouseWheel(self, event):
        modifiers = event.GetModifiers()
        hz = event.GetWheelAxis() == wx.MOUSE_WHEEL_HORIZONTAL
        steps = int(event.GetWheelRotation() / event.GetWheelDelta())
        if modifiers & platformSpecific.scaleModifier():
            newScale = self._scale * pow(1.2, steps)
            self.zoom(newScale, anchor=event.GetPosition())
        else:
            dx, dy = 0, steps * event.GetLinesPerAction() * 8
            if hz or modifiers & wx.MOD_ALT:
                dx, dy = dy, dx
                if hz:
                    dx = -dx
            self._offset += wx.RealPoint(dx, dy)
            self.Refresh()

    def OnSize(self, event):
        size = event.GetSize()
        if hasattr(self, "_offset") and hasattr(self, "_cachedSize"):
            delta = self._cachedSize - size
            offset = self._offset
            offset.x -= .5 * delta.width
            offset.y -= .5 * delta.height
        self._cachedSize = size
        if hasattr(self, "_fitViewport"):
            self.fitMetrics()
            del self._fitViewport
        event.Skip()
