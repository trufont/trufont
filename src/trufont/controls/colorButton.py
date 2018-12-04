import wx
import logging

ColorModifiedEvent, EVT_COLOR_MODIFIED = wx.lib.newevent.NewEvent()


class ColorButton(wx.Window):
    """
    TODO: kbd focus and focus ring
    """

    COLOR_MODIFIED = EVT_COLOR_MODIFIED

    def __init__(self, parent):
        super().__init__(parent)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.SetBackgroundColour(wx.WHITE)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetDoubleBuffered(True)

        self._color = None

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, color):
        self._color = color
        self.Refresh()

    # ----------
    # wx methods
    # ----------

    def DoGetBestSize(self):
        return wx.Size(28, 16)

    @staticmethod
    def DoPickColor(parent, color):
        dialog = wx.ColourDialog(parent)
        data = dialog.GetColourData()
        # TODO: use SetChooseAlpha(True) in wx 3.1
        data.SetChooseFull(True)
        data.SetColour(color)
        ret = dialog.ShowModal()
        if ret == wx.ID_OK:
            return dialog.GetColourData().GetColour()
        return None

    @staticmethod
    def DoDraw(parent, dc, rect, color):
        logging.debug("COLORBUTTON: DoDraw")
        wx.RendererNative.Get().DrawTextCtrl(
            parent,
            dc,
            rect
            # wx.CONTROL_FOCUSED
        )

        dc.SetPen(wx.TRANSPARENT_PEN)
        rect = wx.Rect(rect)
        rect.Deflate(2, 2)

        opaque = color is not None and color.Alpha() == wx.ALPHA_OPAQUE
        if not opaque:
            dc.SetBrush(wx.Brush(wx.Colour(214, 214, 214)))
            dc.SetClippingRegion(rect)
            cRect = wx.Rect(rect)
            cRect.SetSize(wx.Size(6, 6))
            dc.DrawRectangle(cRect)
            cRect.Offset(6, 6)
            dc.DrawRectangle(cRect)
            cRect.Offset(6, -6)
            dc.DrawRectangle(cRect)
            cRect.Offset(6, 6)
            dc.DrawRectangle(cRect)
            cRect.Offset(-12, -6)
            dc.SetBrush(wx.Brush(wx.Colour(170, 170, 170)))
            dc.DrawRectangle(cRect)
            cRect.Offset(-6, 6)
            dc.DrawRectangle(cRect)
            cRect.Offset(18, -6)
            dc.DrawRectangle(cRect)
            cRect.Offset(-6, 6)
            dc.DrawRectangle(cRect)
            dc.DestroyClippingRegion()
        if color is not None:
            dc.SetBrush(wx.Brush(wx.Colour(color)))
            dc.DrawRectangle(rect)

    def OnLeftDown(self, event):
        color = self.DoPickColor(self._color)
        if color is not None:
            self._color = color
            wx.PostEvent(self, ColorModifiedEvent(color=self._color))
            self.Refresh()

    def OnPaint(self, event):
        logging.debug("COLORBUTTON: onPaint")
        dc = wx.GraphicsContext.Create(wx.PaintDC(self))

        self.DoDraw(dc, wx.Rect(0, 0, 28, 16), self._color)
