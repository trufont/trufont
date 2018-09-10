from trufont.controls.featureDropdown import FeatureDropdown
from trufont.controls.spinCtrl import SpinCtrl
import wx
from wx import GetTranslation as tr

# tbh all custom ids (here and fontWindow) should be taken to a data file
ID_ZOOM_IN = wx.NewId()
ID_ZOOM_OUT = wx.NewId()

ZoomModifiedEvent, EVT_ZOOM_MODIFIED = wx.lib.newevent.NewEvent()


class GlyphStatusBar(wx.Panel):
    # this ctrl should redraw on UpdateUI since the feature dropdown might
    # enable/disable
    ZOOM_MODIFIED = EVT_ZOOM_MODIFIED

    def __init__(self, parent, canvas):
        super().__init__(parent)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.SetBackgroundColour(wx.WHITE)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetDoubleBuffered(True)
        self.SetForegroundColour(wx.Colour(37, 37, 37))

        self._canvas = canvas
        self._mouseDownElem = None
        self._underMouseElem = None

        ctrl = self._dropdown = FeatureDropdown(self)
        ctrl.SetPosition(wx.Point(6, 0))
        ctrl.SetSize(ctrl.GetBestSize())
        ctrl.Bind(ctrl.FEATURE_MODIFIED, self.OnFeatureModified)

        ctrl = self._ptSizeCtrl = SpinCtrl(
            self, style=wx.TE_CENTRE | wx.NO_BORDER)
        ctrl.SetForegroundColour(self.GetForegroundColour())
        ctrl.SetToolTip(tr("Zoom"))
        ctrl.number = canvas.pointSize
        ctrl.suffix = " pt"
        ctrlHeight = ctrl.GetSize()[1]
        ctrl.SetSize(wx.Size(56, ctrlHeight))
        ctrl.Bind(ctrl.NUMBER_MODIFIED, self.OnPointSizeModified)

        canvas.Bind(canvas.OPTIONS_CHANGED, self._canvasOptionsChanged)
        canvas.Bind(canvas.PT_SIZE_CHANGED, self._canvasSizeChanged)
        self._dropdown.features = self._canvas._features

    @property
    def _engine(self):
        return self._canvas._font.engine

    def _canvasOptionsChanged(self, event):
        self._dropdown.features = self._canvas._features
        self.Refresh()

    def _canvasSizeChanged(self, event):
        self._ptSizeCtrl.number = event.pointSize

    # ----------
    # wx methods
    # ----------

    def DoGetBestSize(self):
        return wx.Size(280, 25)

    def DoGetIndexForPos(self, pos):
        if pos.x < 0 or pos.y < 0:
            return
        width, height = self.GetSize()
        if pos.y >= height:
            return
        if width - 8 > pos.x >= width - 31:
            return 0
        elif width - 87 > pos.x >= width - 110:
            return 1
        elif width - 120 > pos.x >= width - 144:
            return 2
        elif width - 146 > pos.x >= width - 170:
            return 3
        elif width - 172 > pos.x >= width - 196:
            return 4
        return None

    def DoSetToolTip(self, index):
        if index == 2:
            text = tr("Right-to-Left")
        elif index == 3:
            text = tr("Left-to-Right")
        elif index == 4:
            text = tr("Kerning")
        else:
            text = None
        self.SetToolTip(text)

    def OnFeatureModified(self, event):
        # XXX needs more encapsulation!
        self._canvas._features[event.feat] = event.value
        self._canvas.applyOptionsChange()

    def OnLeftDown(self, event):
        index = self.DoGetIndexForPos(event.GetPosition())
        if index is not None:
            self._mouseDownElem = self._underMouseElem = index
            self.CaptureMouse()
            self.Refresh()

    def OnMotion(self, event):
        index = self.DoGetIndexForPos(event.GetPosition())
        if self._underMouseElem != index:
            self.DoSetToolTip(index)
            self._underMouseElem = index
            self.Refresh()

    def OnLeftUp(self, event):
        e = self._mouseDownElem
        if e is not None:
            self.ReleaseMouse()
        if e is not None and e == self._underMouseElem:
            canvas = self._canvas
            if e < 2:
                evt = ZoomModifiedEvent()
                evt.SetId(ID_ZOOM_OUT if e else ID_ZOOM_IN)
                wx.PostEvent(self, evt)
            elif e == 2:
                canvas.direction = "rtl"
            elif e == 3:
                canvas.direction = "ltr"
            elif e == 4:
                canvas.applyKerning = not canvas.applyKerning
        self._mouseDownElem = None
        if self._underMouseElem is not None:
            self._underMouseElem = None
            self.Refresh()

    def OnPaint(self, event):
        ctx = wx.GraphicsContext.Create(self)
        ctx.SetFont(self.GetFont(), self.GetForegroundColour())
        canvas = self._canvas
        width, _ = self.GetSize()

        selectedBrush = wx.Brush(wx.Colour(29, 127, 204))
        brush = wx.Brush(wx.Colour(102, 102, 102))

        ctx.SetBrush(wx.Brush(self.GetBackgroundColour()))
        ctx.DrawRectangle(0, 0, *self.GetSize())

        ctx.Translate(width - 31, 0)
        if self._mouseDownElem == self._underMouseElem == 0:
            ctx.SetBrush(wx.Brush(wx.Colour(210, 210, 210)))
            ctx.DrawRectangle(0, 0, 23, 25)
        ctx.SetBrush(wx.NullBrush)
        ctx.SetPen(wx.Pen(wx.Colour(123, 123, 123)))
        ctx.StrokeLine(11, 6.5, 11, 17.5)
        ctx.StrokeLine(5.5, 12, 16.5, 12)

        ctx.Translate(-79, 0)
        if self._mouseDownElem == self._underMouseElem == 1:
            ctx.SetBrush(wx.Brush(wx.Colour(210, 210, 210)))
            ctx.SetPen(wx.NullPen)
            ctx.DrawRectangle(0, 0, 23, 25)
        ctx.SetBrush(wx.NullBrush)
        ctx.SetPen(wx.Pen(wx.Colour(123, 123, 123)))
        ctx.StrokeLine(5.5, 12, 16.5, 12)

        path = ctx.CreatePath()
        path.MoveToPoint(13.5, 10.0)
        path.AddLineToPoint(2.5, 10.0)
        path.AddCurveToPoint(2.226, 10.0, 2.0, 9.774, 2.0, 9.5)
        path.AddCurveToPoint(2.0, 9.226, 2.226, 9.0, 2.5, 9.0)
        path.AddLineToPoint(13.5, 9.0)
        path.AddCurveToPoint(13.774, 9.0, 14.0, 9.226, 14.0, 9.5)
        path.AddCurveToPoint(14.0, 9.774, 13.774, 10.0, 13.5, 10.0)
        path.MoveToPoint(13.5, 7.0)
        path.AddLineToPoint(6.5, 7.0)
        path.AddCurveToPoint(6.226, 7.0, 6.0, 6.774, 6.0, 6.5)
        path.AddCurveToPoint(6.0, 6.226, 6.226, 6.0, 6.5, 6.0)
        path.AddLineToPoint(13.5, 6.0)
        path.AddCurveToPoint(13.774, 6.0, 14.0, 6.226, 14.0, 6.5)
        path.AddCurveToPoint(14.0, 6.774, 13.774, 7.0, 13.5, 7.0)
        path.MoveToPoint(13.5, 4.0)
        path.AddLineToPoint(2.5, 4.0)
        path.AddCurveToPoint(2.226, 4.0, 2.0, 3.774, 2.0, 3.5)
        path.AddCurveToPoint(2.0, 3.226, 2.226, 3.0, 2.5, 3.0)
        path.AddLineToPoint(13.5, 3.0)
        path.AddCurveToPoint(13.774, 3.0, 14.0, 3.226, 14.0, 3.5)
        path.AddCurveToPoint(14.0, 3.774, 13.774, 4.0, 13.5, 4.0)
        path.MoveToPoint(6.5, 12.0)
        path.AddLineToPoint(13.5, 12.0)
        path.AddCurveToPoint(13.774, 12.0, 14.0, 12.226, 14.0, 12.5)
        path.AddCurveToPoint(14.0, 12.774, 13.774, 13.0, 13.5, 13.0)
        path.AddLineToPoint(6.5, 13.0)
        path.AddCurveToPoint(6.226, 13.0, 6.0, 12.774, 6.0, 12.5)
        path.AddCurveToPoint(6.0, 12.226, 6.226, 12.0, 6.5, 12.0)
        ctx.Translate(-30, 5)
        if canvas and (canvas.direction == "rtl") ^ (
                self._mouseDownElem == self._underMouseElem == 2):
            ctx.SetBrush(selectedBrush)
        else:
            ctx.SetBrush(brush)
        ctx.SetPen(wx.NullPen)
        ctx.DrawPath(path)

        path = ctx.CreatePath()
        path.MoveToPoint(13.5, 4.0)
        path.AddLineToPoint(2.5, 4.0)
        path.AddCurveToPoint(2.226, 4.0, 2.0, 3.774, 2.0, 3.5)
        path.AddCurveToPoint(2.0, 3.226, 2.226, 3.0, 2.5, 3.0)
        path.AddLineToPoint(13.5, 3.0)
        path.AddCurveToPoint(13.774, 3.0, 14.0, 3.226, 14.0, 3.5)
        path.AddCurveToPoint(14.0, 3.774, 13.774, 4.0, 13.5, 4.0)
        path.MoveToPoint(2.5, 6.0)
        path.AddLineToPoint(9.5, 6.0)
        path.AddCurveToPoint(9.774, 6.0, 10.0, 6.226, 10.0, 6.5)
        path.AddCurveToPoint(10.0, 6.774, 9.774, 7.0, 9.5, 7.0)
        path.AddLineToPoint(2.5, 7.0)
        path.AddCurveToPoint(2.226, 7.0, 2.0, 6.774, 2.0, 6.5)
        path.AddCurveToPoint(2.0, 6.226, 2.226, 6.0, 2.5, 6.0)
        path.MoveToPoint(2.5, 9.0)
        path.AddLineToPoint(13.5, 9.0)
        path.AddCurveToPoint(13.774, 9.0, 14.0, 9.226, 14.0, 9.5)
        path.AddCurveToPoint(14.0, 9.774, 13.774, 10.0, 13.5, 10.0)
        path.AddLineToPoint(2.5, 10.0)
        path.AddCurveToPoint(2.226, 10.0, 2.0, 9.774, 2.0, 9.5)
        path.AddCurveToPoint(2.0, 9.226, 2.226, 9.0, 2.5, 9.0)
        path.MoveToPoint(2.5, 12.0)
        path.AddLineToPoint(9.5, 12.0)
        path.AddCurveToPoint(9.774, 12.0, 10.0, 12.226, 10.0, 12.5)
        path.AddCurveToPoint(10.0, 12.774, 9.774, 13.0, 9.5, 13.0)
        path.AddLineToPoint(2.5, 13.0)
        path.AddCurveToPoint(2.226, 13.0, 2.0, 12.774, 2.0, 12.5)
        path.AddCurveToPoint(2.0, 12.226, 2.226, 12.0, 2.5, 12.0)
        ctx.Translate(-26, 0)
        if canvas and (canvas.direction == "ltr") ^ (
                self._mouseDownElem == self._underMouseElem == 3):
            ctx.SetBrush(selectedBrush)
        else:
            ctx.SetBrush(brush)
        ctx.DrawPath(path)

        path = ctx.CreatePath()
        path.MoveToPoint(12.0, 6.5)
        path.AddLineToPoint(11.342, 5.835)
        path.AddLineToPoint(12.859, 4.0)
        path.AddLineToPoint(3.141, 4.0)
        path.AddLineToPoint(4.641, 5.9)
        path.AddLineToPoint(4.0, 6.5)
        path.AddLineToPoint(1.5, 3.516)
        path.AddLineToPoint(4.0, 0.5)
        path.AddLineToPoint(4.658, 1.165)
        path.AddLineToPoint(3.141, 3.0)
        path.AddLineToPoint(12.859, 3.0)
        path.AddLineToPoint(11.359, 1.1)
        path.AddLineToPoint(12.0, 0.5)
        path.AddLineToPoint(14.5, 3.484)
        path.CloseSubpath()
        path.MoveToPoint(7.175, 6.07)
        path.AddCurveToPoint(7.175, 6.069, 7.175, 6.067, 7.175, 6.066)
        path.AddCurveToPoint(7.175, 6.03, 7.205, 6.0, 7.241, 6.0)
        path.AddLineToPoint(8.617, 6.0)
        path.AddCurveToPoint(8.673, 6.0, 8.687, 6.013, 8.701, 6.07)
        path.AddLineToPoint(11.491, 13.905)
        path.AddCurveToPoint(11.519, 13.961, 11.505, 14.005, 11.435, 14.005)
        path.AddLineToPoint(10.371, 14.005)
        path.AddCurveToPoint(10.324, 14.005, 10.28, 13.978, 10.259, 13.936)
        path.AddLineToPoint(9.737, 12.009)
        path.AddLineToPoint(6.137, 12.009)
        path.AddLineToPoint(5.626, 13.919)
        path.AddCurveToPoint(5.618, 13.972, 5.568, 14.01, 5.514, 14.003)
        path.AddLineToPoint(4.562, 14.003)
        path.AddCurveToPoint(4.492, 14.003, 4.462, 13.961, 4.478, 13.892)
        path.AddLineToPoint(7.078, 6.643)
        path.AddCurveToPoint(7.148, 6.46, 7.181, 6.266, 7.175, 6.07)
        path.CloseSubpath()
        path.MoveToPoint(9.415, 11.014)
        path.AddCurveToPoint(9.107, 10.103, 8.272, 7.904, 8.006, 6.951)
        path.AddLineToPoint(7.992, 6.951)
        path.AddCurveToPoint(7.754, 7.851, 6.992, 9.474, 6.456, 11.014)
        path.CloseSubpath()
        ctx.Translate(-26, 0)
        if canvas and canvas.applyKerning ^ (
                self._mouseDownElem == self._underMouseElem == 4):
            ctx.SetBrush(selectedBrush)
        else:
            ctx.SetBrush(brush)
        ctx.DrawPath(path)

    def OnPointSizeModified(self, event):
        # maybe canvas.font should be a property?
        self._canvas.zoom(event.number / self._canvas._font.unitsPerEm)

    def OnSize(self, event):
        w = event.GetSize().GetWidth()
        ctrlHeight = self._ptSizeCtrl.GetSize()[1]
        h = int(.5 * (25 - ctrlHeight))
        self._ptSizeCtrl.SetPosition(wx.Point(w - 87, h))
        self._dropdown.Refresh()
