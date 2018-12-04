import trufont
from trufont.controls.colorButton import ColorButton
from trufont.util.drawing import CreatePath
import wx
from wx import GetTranslation as tr

cellHeight = 28

cross = CreatePath()
cross.MoveToPoint(7.999, 6.586)
cross.AddLineToPoint(10.475, 4.11)
cross.AddCurveToPoint(10.863, 3.723, 11.501, 3.723, 11.889, 4.11)
cross.AddCurveToPoint(12.277, 4.498, 12.277, 5.137, 11.889, 5.525)
cross.AddLineToPoint(9.414, 8.0)
cross.AddLineToPoint(11.889, 10.475)
cross.AddCurveToPoint(12.277, 10.863, 12.277, 11.501, 11.889, 11.889)
cross.AddCurveToPoint(11.501, 12.277, 10.862, 12.277, 10.474, 11.889)
cross.AddLineToPoint(7.999, 9.414)
cross.AddLineToPoint(5.525, 11.889)
cross.AddCurveToPoint(5.137, 12.277, 4.499, 12.277, 4.111, 11.889)
cross.AddCurveToPoint(3.723, 11.501, 3.723, 10.862, 4.111, 10.474)
cross.AddLineToPoint(6.585, 8.0)
cross.AddLineToPoint(4.11, 5.525)
cross.AddCurveToPoint(3.723, 5.137, 3.723, 4.499, 4.11, 4.111)
cross.AddCurveToPoint(4.498, 3.723, 5.137, 3.723, 5.525, 4.111)
cross.CloseSubpath()

path = CreatePath()
path.MoveToPoint(8.0, 4.25)
path.AddCurveToPoint(4.063, 4.25, 2.0, 7.517, 2.0, 8.031)
path.AddCurveToPoint(2.0, 8.545, 4.063, 11.711, 8.0, 11.711)
path.AddCurveToPoint(11.937, 11.711, 14.0, 8.543, 14.0, 8.031)
path.AddCurveToPoint(14.0, 7.519, 11.936, 4.25, 8.0, 4.25)
path.MoveToPoint(8.0, 10.844)
path.AddCurveToPoint(6.528, 10.817, 5.331, 9.598, 5.331, 8.125)
path.AddCurveToPoint(5.331, 8.094, 5.332, 8.062, 5.333, 8.031)
path.AddCurveToPoint(5.276, 6.509, 6.479, 5.209, 8.0, 5.148)
path.AddCurveToPoint(9.521, 5.209, 10.724, 6.509, 10.667, 8.031)
path.AddCurveToPoint(10.668, 8.062, 10.669, 8.094, 10.669, 8.125)
path.AddCurveToPoint(10.669, 9.598, 9.472, 10.817, 8.0, 10.844)
path.AddEllipse(6.65, 6.65, 2.7, 2.8)


class LayersView(wx.Window):
    """
    TODO: Add a min width and clip layer name text
    """

    def __init__(self, parent, font):
        super().__init__(parent)  # , style=wx.FULL_REPAINT_ON_RESIZE
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeave)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftDClick)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetDoubleBuffered(True)

        self._font = font
        self._textCtrl = None
        self._underMouseLayer = None
        self._fontWindow = wx.GetTopLevelParent(self)

        trufont.TruFont.addObserver("updateUI", self)

    @property
    def _activeLayer(self):
        return self._fontWindow.activeLayer

    @_activeLayer.setter
    def _activeLayer(self, value):
        self._fontWindow.activeLayer = value

    @property
    def _layers(self):
        activeLayer = self._fontWindow.activeLayer
        if activeLayer is None:
            return []
        return activeLayer._parent.layers

    def _layerNameModified(self, event):
        self._renamedLayer.name = self._textCtrl.GetValue()
        self._textCtrl.Hide()
        trufont.TruFont.updateUI()
        del self._renamedLayer

    def _setLocation(self, event):
        ...

    def _setMasterLayer(self, event):
        layers = self._layers
        layer = layers[self._hoverLayer]
        glyph = layer._parent
        otherLayer = glyph.layerForMaster(layer.masterName)
        name, visible = layer.name, layer.visible
        layer.name = ""
        otherLayer.name = name
        layer.visible = False
        otherLayer.visible = visible
        trufont.TruFont.updateUI()

    # ----------
    # wx methods
    # ----------

    def DoEditLayerName(self, index, layer):
        if layer.masterLayer:
            return
        # TODO: do filter (out-of-control) clicks and Esc as exit signals
        # during editing
        # wx.App.AddFilter(KeyEventFilter)
        if self._textCtrl is None:
            self._textCtrl = wx.TextCtrl(self)
            _, h = self._textCtrl.GetSize()
            self._textCtrl.SetSize(wx.Size(110, h))
            self._textCtrl.Bind(wx.EVT_TEXT_ENTER, self._layerNameModified)
            self._textCtrl.Bind(wx.EVT_KILL_FOCUS, self._layerNameModified)
        else:
            self._textCtrl.Show()
        self._renamedLayer = layer
        _, h = self._textCtrl.GetSize()
        self._textCtrl.SetPosition(wx.Point(36, 14 + 28 * index - int(.5 * h)))
        self._textCtrl.SetValue(layer.name)
        self._textCtrl.SelectAll()
        self._textCtrl.SetFocus()

    def DoGetBestSize(self):
        # TODO: compute width according to elements
        # height = 100
        return wx.Size(204, cellHeight * len(self._layers))

    def OnContextMenu(self, event):
        self._hoverLayer = hoverLayer = self._underMouseLayer
        layer = self._layers[hoverLayer]
        if layer.masterLayer:
            return
        menu = wx.Menu()
        self.Bind(
            wx.EVT_MENU,
            self._setMasterLayer,
            menu.Append(wx.ID_ANY, tr("Use as Master")),
        )
        item = menu.Append(wx.ID_ANY, tr("Set Location…"))
        item.Enabled = False
        self.Bind(wx.EVT_MENU, self._setLocation, item)
        self.PopupMenu(menu)
        del self._hoverLayer

    def OnLeave(self, event):
        self._underMouseLayer = None
        self.Refresh()

    def OnLeftDown(self, event):
        pos = event.GetPosition()
        width, _ = self.GetSize()
        layers = self._layers
        rect = wx.Rect(12, 6, 16, 16)
        fullRect = wx.Rect(0, 0, width, 28)
        for i, layer in enumerate(layers):
            if rect.Contains(pos):
                # TODO we can even more color picker to simple click
                return
            rect.SetLeft(width - 26)
            if rect.Contains(pos):
                layer.visible = not layer.visible
                trufont.TruFont.updateUI()
                return
            if not layer.masterLayer:
                rect.Offset(-24, 0)
                if rect.Contains(pos):
                    print("del")
                    return
                rect.Offset(24, 0)
            if fullRect.Contains(pos):
                self._activeLayer = layer
                return
            rect.Offset(0, 28)
            fullRect.Offset(0, 28)
            rect.SetLeft(12)

    def OnLeftDClick(self, event):
        pos = event.GetPosition()
        # ctx = wx.GraphicsContext.Create(self)
        ctx = wx.GraphicsContext.Create(wx.PaintDC(self))
        ctx.SetFont(self.GetFont(), self.GetForegroundColour())
        rect = wx.Rect(12, 6, 16, 16)
        for i, layer in enumerate(self._layers):
            if rect.Contains(pos):
                color = ColorButton.DoPickColor(self, wx.Colour(layer.color))
                if color is not None:
                    layer.color = color.Get()
                    trufont.TruFont.updateUI()
                return
            rect.Offset(36, 0)
            rect.SetWidth(ctx.GetTextExtent(layer.name)[0])
            if rect.Contains(pos):
                self.DoEditLayerName(i, layer)
                return
            rect.Offset(-36, 28)
            rect.SetWidth(16)
        # fallback to simple click
        self.OnLeftDown(event)

    def OnMotion(self, event):
        pos = event.GetPosition()
        index = pos.y // cellHeight
        if self._underMouseLayer != index:
            self._underMouseLayer = index
            self.Refresh()

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.SetBrush(wx.Brush(self.GetBackgroundColour()))
        dc.Clear()

        activeLayer = self._activeLayer
        if activeLayer is None:
            return
        layers = self._layers

        ctx = wx.GraphicsContext.Create(dc)
        ctx.SetFont(self.GetFont(), wx.Colour(63, 63, 63))
        width, height = self.GetSize()

        for idx, layer in enumerate(layers):
            hover = idx == self._underMouseLayer
            # background
            # TODO: add way to figure out if layer is current
            if hover or layer is activeLayer:
                if hover:
                    color = wx.Colour(232, 232, 232)
                else:
                    color = wx.Colour(225, 225, 225)
                ctx.SetBrush(wx.Brush(color))
                ctx.DrawRectangle(0, 0, width, cellHeight)
            # lhs
            ctx.PushState()
            ctx.Translate(12, 6)
            color = layer.color
            masterLayer = layer.masterLayer
            origin = ctx.GetTransform().Get()[-2:]
            if color is not None or hover or masterLayer:
                if color is not None:
                    color = wx.Colour(color)
                ColorButton.DoDraw(self, dc, wx.Rect(*origin, 16, 16), color)
            ctx.Translate(24, 0)
            if not masterLayer:
                ctx.Translate(10, 0)
            ctx.DrawText(layer.name, 0, 0)
            ctx.PopState()
            # rhs
            ctx.PushState()
            ctx.Translate(width - 26, 6)
            if hover or layer.visible:
                if layer.visible:
                    color = wx.Colour(102, 102, 102)
                else:
                    color = wx.Colour(170, 170, 170)
                ctx.SetBrush(wx.Brush(color))
                ctx.FillPath(path)
            ctx.Translate(-24, 0)
            if hover and not masterLayer:
                ctx.SetBrush(wx.Brush(wx.Colour(170, 170, 170)))
                ctx.FillPath(cross)
            ctx.PopState()
            ctx.Translate(0, cellHeight)
