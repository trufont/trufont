from trufont.util.drawing import CreateMeasuringContext
import wx
import wx.lib.newevent
from wx import GetTranslation as tr

FeatureModifiedEvent, EVT_FEATURE_MODIFIED = wx.lib.newevent.NewEvent()

_title = tr("Features")


class FeatureDropdown(wx.Window):
    FEATURE_MODIFIED = EVT_FEATURE_MODIFIED

    def __init__(self, parent):
        super().__init__(parent)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.SetBackgroundColour(wx.WHITE)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetDoubleBuffered(True)

        self._features = dict()
        self._pressed = False

        self._popup = FeaturePopup(self)

    @property
    def features(self):
        return self._features

    @features.setter
    def features(self, features):
        self._features = features
        self.Refresh()

    @property
    def pressed(self):
        return self._pressed

    @pressed.setter
    def pressed(self, value):
        if value == self._pressed:
            return
        self._pressed = value
        self.Refresh()
        if self._pressed:
            self.DoPickFeatures()
        else:
            if self._popup is not None:
                self._popup.Dismiss()

    # ----------
    # wx methods
    # ----------

    def DoEnd(self):
        if self._pressed:
            self._pressed = False
            self.Refresh()

    def DoGetBestSize(self):
        ctx = CreateMeasuringContext()
        ctx.SetFont(self.GetFont(), self.GetForegroundColour())
        textWidth, _ = ctx.GetTextExtent(_title)
        return wx.Size(31 + textWidth, 25)

    def DoPickFeatures(self):
        popup = self._popup
        popup.features = self._features

        size = popup.GetBestSize()
        origin = self.ClientToScreen(wx.Point(0, -size.y))
        popup.SetPosition(origin)
        size.SetWidth(self.GetBestSize().GetWidth())
        popup.SetSize(size)
        popup.OnDismiss = lambda *_: self.DoEnd()
        popup.Popup(self)

    def OnLeftDown(self, event):
        if not self._features:
            return
        self.pressed = not self._pressed

    def OnPaint(self, event):
        ctx = wx.GraphicsContext.Create(self)
        if self._pressed:
            backgroundColor = self._popup.GetBackgroundColour()
        else:
            backgroundColor = self.GetBackgroundColour()
        ctx.SetBrush(wx.Brush(backgroundColor))
        ctx.DrawRectangle(0, 0, *self.GetSize())

        if self._features:
            color = wx.Colour(37, 37, 37)
        else:
            color = wx.Colour(132, 132, 132)
        ctx.SetFont(self.GetFont(), color)
        ctx.Translate(8, 4)
        ctx.DrawText(_title, 0, 0)

        path = ctx.CreatePath()
        path.MoveToPoint(5, 7.5)
        path.AddLineToPoint(11, 7.5)
        path.AddLineToPoint(8, 11)
        path.CloseSubpath()
        textWidth, _ = ctx.GetTextExtent(_title)
        ctx.Translate(textWidth + 3, 0)
        ctx.SetBrush(wx.Brush(color))
        ctx.DrawPath(path)


class FeaturePopup(wx.PopupTransientWindow):

    def __init__(self, parent):
        super().__init__(parent)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.SetBackgroundColour(wx.Colour(235, 235, 235))
        self.SetForegroundColour(wx.Colour(37, 37, 37))
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetDoubleBuffered(True)

        self._features = []
        self._featureList = []

        self._underMouseFeat = None

    @property
    def features(self):
        return self._features

    @features.setter
    def features(self, features):
        self._features = features
        self._featureList = sorted(self._features.keys())
        self.Refresh()

    # ----------
    # wx methods
    # ----------

    def DoGetBestSize(self):
        height = 13 + 24 * len(self._featureList)
        # TODO: the width is really the width of feature dropdown
        # touch area, which is dependent on fontMetrics
        return wx.Size(76, height)

    def DoGetIndexForPos(self, pos):
        width, _ = self.GetSize()
        if pos.x < 0 or pos.x >= width:
            return None
        if pos.y < 6:
            return None
        for i in range(len(self._featureList)):
            if pos.y < 6 + 24 * (i + 1):
                return i
        return None

    def OnLeftDown(self, event):
        index = self.DoGetIndexForPos(event.GetPosition())
        if index is not None:
            feat = self._featureList[index]
            value = not self._features[feat]
            wx.PostEvent(self.GetParent(), FeatureModifiedEvent(
                feat=feat, value=value))
            self.Refresh()

    def OnMotion(self, event):
        index = self.DoGetIndexForPos(event.GetPosition())
        if index != self._underMouseFeat:
            self._underMouseFeat = index
            self.Refresh()

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        dc.SetBrush(wx.Brush(self.GetBackgroundColour()))
        dc.Clear()
        ctx = wx.GraphicsContext.Create(dc)
        ctx.SetFont(self.GetFont(), self.GetForegroundColour())
        rdr = wx.RendererNative.Get()
        width, height = self.GetSize()

        ctx.SetPen(wx.Pen(wx.Colour(212, 212, 212)))
        ctx.StrokeLine(0, height - 1, width - 1, height - 1)

        ctx.Translate(0, 6)
        ctx.SetBrush(wx.Brush(wx.Colour(220, 220, 220)))
        ctx.SetPen(wx.NullPen)
        for i, feat in enumerate(self._featureList):
            if self._underMouseFeat == i:
                ctx.DrawRectangle(0, 0, width, 24)
            ox, oy = ctx.GetTransform().Get()[-2:]
            origin = wx.Point(ox + 8, oy + 6)
            value = self._features[feat] * wx.CONTROL_CHECKED
            # TODO: checkbox size is OS dependent
            rdr.DrawCheckBox(
                self, dc, wx.Rect(origin, wx.Size(13, 13)), value)
            ctx.DrawText(feat, 28, 4)
            ctx.Translate(0, 24)
