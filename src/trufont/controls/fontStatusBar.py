from trufont.controls.featureDropdown import FeatureDropdown
from trufont.controls.spinCtrl import SpinCtrl
import wx
from wx import GetTranslation as tr


class FontStatusBar(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.SetBackgroundColour(wx.WHITE)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetDoubleBuffered(True)
        self.SetForegroundColour(wx.Colour(37, 37, 37))

        self._selectionText = ""
        self._titleText = ""
        self._titleWidth = None

    # ----------
    # wx methods
    # ----------

    def DoGetBestSize(self):
        return wx.Size(280, 25)

    # XXX this should take an event / initial value from font ctor arg?
    def OnCountChanged(self, value):
        self._titleText = tr("%d glyphs") % value
        self.Refresh()

    # XXX this should take an event
    def OnSelectionChanged(self, value):
        if not value:
            text = wx.EmptyString
        else:
            text = tr("%d selected") % value
        self._selectionText = text
        self.Refresh()

    def OnPaint(self, event):
        ctx = wx.GraphicsContext.Create(self)
        ctx.SetFont(self.GetFont(), self.GetForegroundColour())

        ctx.SetBrush(wx.Brush(self.GetBackgroundColour()))
        ctx.DrawRectangle(0, 0, *self.GetSize())

        text = self._titleText
        if not text:
            return
        ctx.Translate(14, 4)
        ctx.DrawText(text, 0, 0)

        text = self._selectionText
        if not text:
            return
        width = self._titleWidth
        if width is None:
            width = self._titleWidth = 12 + ctx.GetTextExtent("00000 glyphs")[0]
        ctx.Translate(width, 0)
        ctx.DrawText(text, 0, 0)
