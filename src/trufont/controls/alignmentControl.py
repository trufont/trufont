import wx


class AlignmentControl(wx.Window):
    def __init__(self, parent):
        super().__init__(parent)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetDoubleBuffered(True)

        self._alignment = 4

    @property
    def alignment(self):
        return self._alignment

    @alignment.setter
    def alignment(self, value):
        self._alignment = value
        self.Refresh()

    @property
    def layer(self):
        return wx.GetTopLevelParent(self).activeLayer

    @property
    def origin(self):
        layer = self.layer
        bounds = layer.selectionBounds or layer.bounds
        if bounds is None:
            return 0, 0
        l, b, r, t = bounds
        alignment = self._alignment
        xFactor = .5 * (alignment % 3)
        yFactor = .5 * (2 - alignment // 3)
        return l + (r - l) * xFactor, b + (t - b) * yFactor

    # ----------
    # wx methods
    # ----------

    def DoGetBestSize(self):
        return wx.Size(25, 25)

    def OnLeftDown(self, event):
        pos = event.GetPosition()
        rect = wx.Rect(-1, -1, 9, 9)
        for i in range(9):
            rect.SetLeft(i % 3 * 9)
            rect.SetTop(i // 3 * 9)
            if rect.Contains(pos):
                self._alignment = i
                self.Refresh()
                return

    def OnPaint(self, event):
        # ctx = wx.GraphicsContext.Create(self)
        ctx = wx.GraphicsContext.Create(wx.PaintDC(self))

        backgroundBrush = wx.Brush(self.GetBackgroundColour())
        valueBrush = wx.Brush(wx.Colour(102, 102, 102))

        ctx.SetBrush(backgroundBrush)
        ctx.DrawRectangle(0, 0, *self.GetSize())

        ctx.SetPen(wx.Pen(wx.Colour(204, 204, 204)))
        ctx.DrawRectangle(4, 4, 16, 16)

        ctx.SetPen(wx.Pen(wx.Colour(102, 102, 102)))
        ctx.Translate(2, 2)
        for i in range(9):
            value = i == self._alignment
            if value:
                ctx.SetBrush(valueBrush)
            ctx.DrawRoundedRectangle(i % 3 * 8, i // 3 * 8, 4, 4, 1)
            if value:
                ctx.SetBrush(backgroundBrush)
