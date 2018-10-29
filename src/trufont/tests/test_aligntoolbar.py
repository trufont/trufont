# file:  test_loggingWindows.py
import sys
import logging

import wx
_rdr = wx.GraphicsRenderer.GetDefaultRenderer()
CreatePath = _rdr.CreatePath

def _bidon():
    pass

def tr(str):
    return str

def makePropertiesLayout(parent):
    
    # dc = wx.PaintDC(parent)
    # ctx = wx.GraphicsContext.Create(dc)
    sizer = wx.BoxSizer(wx.VERTICAL)
    alignmentBar = ButtonBar(parent)
    btns = []
    path = CreatePath()
    path.MoveToPoint(13.961, 13.0)
    path.AddLineToPoint(5.039, 13.0)
    path.AddCurveToPoint(4.48, 13.009, 4.012, 12.559, 4.0, 12.0)
    path.AddLineToPoint(4.0, 10.0)
    path.AddCurveToPoint(4.012, 9.441, 4.48, 8.991, 5.039, 9.0)
    path.AddLineToPoint(13.962, 9.0)
    path.AddCurveToPoint(14.521, 8.991, 14.989, 9.441, 15.001, 10.0)
    path.AddLineToPoint(15.001, 12.0)
    path.CloseSubpath()
    path.MoveToPoint(9.951, 7.0)
    path.AddLineToPoint(5.039, 7.0)
    path.AddCurveToPoint(4.48, 7.009, 4.012, 6.559, 4.0, 6.0)
    path.AddLineToPoint(4.0, 4.0)
    path.AddCurveToPoint(4.012, 3.441, 4.48, 2.991, 5.039, 3.0)
    path.AddLineToPoint(9.951, 3.0)
    path.AddCurveToPoint(10.51, 2.991, 10.978, 3.441, 10.99, 4.0)
    path.AddLineToPoint(10.99, 6.0)
    path.CloseSubpath()
    path.MoveToPoint(2.0, 0.5)
    path.AddCurveToPoint(2.0, 0.224, 1.776, 0.0, 1.5, 0.0)
    path.AddCurveToPoint(1.224, 0.0, 1.0, 0.224, 1.0, 0.5)
    path.AddLineToPoint(1.0, 15.5)
    path.AddCurveToPoint(1.0, 15.776, 1.224, 16.0, 1.5, 16.0)
    path.AddCurveToPoint(1.776, 16.0, 2.0, 15.776, 2.0, 15.5)
    path.CloseSubpath()
    btns.append(Button(path, _bidon, tr("Push selection left")))
    path = CreatePath()
    path.MoveToPoint(7.0, 3.0)
    path.AddLineToPoint(7.0, 0.5)
    path.AddCurveToPoint(7.0, 0.224, 7.224, 0.0, 7.5, 0.0)
    path.AddCurveToPoint(7.776, 0.0, 8.0, 0.224, 8.0, 0.5)
    path.AddLineToPoint(8.0, 3.0)
    path.AddLineToPoint(9.954, 3.0)
    path.AddCurveToPoint(10.514, 2.989, 10.985, 3.44, 10.999, 4.0)
    path.AddLineToPoint(10.999, 6.0)
    path.AddCurveToPoint(10.985, 6.56, 10.514, 7.011, 9.954, 7.0)
    path.AddLineToPoint(8.0, 7.0)
    path.AddLineToPoint(8.0, 9.0)
    path.AddLineToPoint(11.953, 9.0)
    path.AddCurveToPoint(12.514, 8.989, 12.985, 9.439, 13.0, 10.0)
    path.AddLineToPoint(13.0, 12.0)
    path.AddCurveToPoint(12.985, 12.563, 12.511, 13.014, 11.948, 13.0)
    path.AddLineToPoint(8.0, 13.0)
    path.AddLineToPoint(8.0, 15.5)
    path.AddCurveToPoint(8.0, 15.776, 7.776, 16.0, 7.5, 16.0)
    path.AddCurveToPoint(7.224, 16.0, 7.0, 15.776, 7.0, 15.5)
    path.AddLineToPoint(7.0, 13.0)
    path.AddLineToPoint(3.048, 13.0)
    path.AddCurveToPoint(2.487, 13.012, 2.015, 12.561, 2.0, 12.0)
    path.AddLineToPoint(2.0, 10.0)
    path.AddCurveToPoint(2.015, 9.439, 2.487, 8.988, 3.048, 9.0)
    path.AddLineToPoint(7.0, 9.0)
    path.AddLineToPoint(7.0, 7.0)
    path.AddLineToPoint(5.044, 7.0)
    path.AddCurveToPoint(4.484, 7.011, 4.013, 6.56, 3.999, 6.0)
    path.AddLineToPoint(3.999, 4.0)
    path.AddCurveToPoint(4.013, 3.44, 4.484, 2.989, 5.044, 3.0)
    path.CloseSubpath()
    btns.append(Button(path, _bidon, tr("Push selection to hz. center")))
    path = CreatePath()
    path.MoveToPoint(10.958, 13.0)
    path.AddLineToPoint(2.042, 13.0)
    path.AddCurveToPoint(1.482, 13.01, 1.013, 12.559, 1.0, 12.0)
    path.AddLineToPoint(1.0, 10.0)
    path.AddCurveToPoint(1.013, 9.441, 1.482, 8.99, 2.042, 9.0)
    path.AddLineToPoint(10.959, 9.0)
    path.AddCurveToPoint(11.518, 8.991, 11.987, 9.441, 12.0, 10.0)
    path.AddLineToPoint(12.0, 12.0)
    path.CloseSubpath()
    path.MoveToPoint(10.958, 7.0)
    path.AddLineToPoint(6.032, 7.0)
    path.AddCurveToPoint(5.472, 7.01, 5.003, 6.559, 4.99, 6.0)
    path.AddLineToPoint(4.99, 4.0)
    path.AddCurveToPoint(5.003, 3.441, 5.472, 2.99, 6.032, 3.0)
    path.AddLineToPoint(10.959, 3.0)
    path.AddCurveToPoint(11.518, 2.991, 11.987, 3.441, 12.0, 4.0)
    path.AddLineToPoint(12.0, 6.0)
    path.CloseSubpath()
    path.MoveToPoint(15.0, 0.5)
    path.AddCurveToPoint(15.0, 0.224, 14.776, 0.0, 14.5, 0.0)
    path.AddCurveToPoint(14.224, 0.0, 14.0, 0.224, 14.0, 0.5)
    path.AddLineToPoint(14.0, 15.5)
    path.AddCurveToPoint(14.0, 15.776, 14.224, 16.0, 14.5, 16.0)
    path.AddCurveToPoint(14.776, 16.0, 15.0, 15.776, 15.0, 15.5)
    path.CloseSubpath()
    btns.append(Button(path, _bidon, tr("Push selection right")))
    path = CreatePath()
    path.MoveToPoint(4.0, 3.978)
    path.AddLineToPoint(6.0, 3.978)
    path.AddCurveToPoint(6.559, 3.991, 7.009, 4.459, 7.0, 5.018)
    path.AddLineToPoint(7.0, 13.951)
    path.AddCurveToPoint(7.009, 14.51, 6.559, 14.978, 6.0, 14.991)
    path.AddLineToPoint(4.0, 14.991)
    path.AddCurveToPoint(3.441, 14.978, 2.991, 14.51, 3.0, 13.951)
    path.AddLineToPoint(3.0, 5.018)
    path.CloseSubpath()
    path.MoveToPoint(10.0, 3.993)
    path.AddLineToPoint(12.0, 3.993)
    path.AddCurveToPoint(12.559, 4.006, 13.009, 4.474, 13.0, 5.033)
    path.AddLineToPoint(13.0, 9.951)
    path.AddCurveToPoint(13.009, 10.51, 12.559, 10.978, 12.0, 10.991)
    path.AddLineToPoint(10.0, 10.991)
    path.AddCurveToPoint(9.441, 10.978, 8.991, 10.51, 9.0, 9.951)
    path.AddLineToPoint(9.0, 5.033)
    path.CloseSubpath()
    path.MoveToPoint(16.0, 1.5)
    path.AddCurveToPoint(16.0, 1.224, 15.776, 1.0, 15.5, 1.0)
    path.AddLineToPoint(0.5, 1.0)
    path.AddCurveToPoint(0.224, 1.0, 0.0, 1.224, 0.0, 1.5)
    path.AddCurveToPoint(0.0, 1.776, 0.224, 2.0, 0.5, 2.0)
    path.AddLineToPoint(15.5, 2.0)
    path.CloseSubpath()
    btns.append(Button(path, _bidon, tr("Push selection top")))
    path = CreatePath()
    path.MoveToPoint(7.0, 8.0)
    path.AddLineToPoint(7.0, 11.956)
    path.AddCurveToPoint(7.01, 12.516, 6.56, 12.986, 6.0, 13.0)
    path.AddLineToPoint(4.0, 13.0)
    path.AddCurveToPoint(3.44, 12.986, 2.99, 12.516, 3.0, 11.956)
    path.AddLineToPoint(3.0, 8.0)
    path.AddLineToPoint(0.5, 8.0)
    path.AddCurveToPoint(0.224, 8.0, 0.0, 7.776, 0.0, 7.5)
    path.AddCurveToPoint(0.0, 7.224, 0.224, 7.0, 0.5, 7.0)
    path.AddLineToPoint(3.0, 7.0)
    path.AddLineToPoint(3.0, 3.045)
    path.AddCurveToPoint(2.99, 2.485, 3.44, 2.015, 4.0, 2.0)
    path.AddLineToPoint(6.0, 2.0)
    path.AddCurveToPoint(6.56, 2.015, 7.01, 2.485, 7.0, 3.045)
    path.AddLineToPoint(7.0, 7.0)
    path.AddLineToPoint(9.0, 7.0)
    path.AddLineToPoint(9.0, 5.048)
    path.AddCurveToPoint(8.989, 4.487, 9.439, 4.015, 10.0, 4.0)
    path.AddLineToPoint(12.0, 4.0)
    path.AddCurveToPoint(12.561, 4.015, 13.011, 4.487, 13.0, 5.048)
    path.AddLineToPoint(13.0, 7.0)
    path.AddLineToPoint(15.5, 7.0)
    path.AddCurveToPoint(15.776, 7.0, 16.0, 7.224, 16.0, 7.5)
    path.AddCurveToPoint(16.0, 7.776, 15.776, 8.0, 15.5, 8.0)
    path.AddLineToPoint(13.0, 8.0)
    path.AddLineToPoint(13.0, 9.996)
    path.AddCurveToPoint(13.0, 10.0, 13.0, 10.003, 13.0, 10.007)
    path.AddCurveToPoint(13.0, 10.55, 12.554, 10.996, 12.011, 10.996)
    path.AddCurveToPoint(12.007, 10.996, 12.004, 10.996, 12.0, 10.996)
    path.AddLineToPoint(10.0, 10.996)
    path.AddCurveToPoint(9.996, 10.996, 9.993, 10.996, 9.989, 10.996)
    path.AddCurveToPoint(9.446, 10.996, 9.0, 10.55, 9.0, 10.007)
    path.AddCurveToPoint(9.0, 10.003, 9.0, 10.0, 9.0, 9.996)
    path.AddLineToPoint(9.0, 8.0)
    path.CloseSubpath()
    btns.append(Button(path, _bidon, tr("Push selection to vert. center")))
    path = CreatePath()
    path.MoveToPoint(12.0, 12.013)
    path.AddLineToPoint(10.0, 12.013)
    path.AddCurveToPoint(9.441, 12.0, 8.991, 11.532, 9.0, 10.973)
    path.AddLineToPoint(9.0, 6.055)
    path.AddCurveToPoint(8.991, 5.496, 9.441, 5.028, 10.0, 5.015)
    path.AddLineToPoint(12.0, 5.015)
    path.AddCurveToPoint(12.559, 5.028, 13.009, 5.496, 13.0, 6.055)
    path.AddLineToPoint(13.0, 10.973)
    path.CloseSubpath()
    path.MoveToPoint(6.0, 12.013)
    path.AddLineToPoint(4.0, 12.013)
    path.AddCurveToPoint(3.441, 12.0, 2.991, 11.532, 3.0, 10.973)
    path.AddLineToPoint(3.0, 2.04)
    path.AddCurveToPoint(2.991, 1.481, 3.441, 1.013, 4.0, 1.0)
    path.AddLineToPoint(6.0, 1.0)
    path.AddCurveToPoint(6.559, 1.013, 7.009, 1.481, 7.0, 2.04)
    path.AddLineToPoint(7.0, 10.973)
    path.CloseSubpath()
    path.MoveToPoint(16.0, 14.5)
    path.AddCurveToPoint(16.0, 14.224, 15.776, 14.0, 15.5, 14.0)
    path.AddLineToPoint(0.5, 14.0)
    path.AddCurveToPoint(0.224, 14.0, 0.0, 14.224, 0.0, 14.5)
    path.AddCurveToPoint(0.0, 14.776, 0.224, 15.0, 0.5, 15.0)
    path.AddLineToPoint(15.5, 15.0)
    path.CloseSubpath()
    btns.append(Button(path, _bidon, tr("Push selection to bottom")))
    alignmentBar.buttons = btns
    sizer.Add(alignmentBar, 0, wx.EXPAND)
    sizer.AddSpacer(1)
    # sizer.Add(PadControl(parent), 1, wx.EXPAND)
    return sizer


class Button:
    __slots__ = ("icon", "callback", "tooltip")  # TODO: shortcut

    def __init__(self, icon, callback, tooltip=None):
        self.icon = icon
        self.callback = callback
        self.tooltip = tooltip


class ButtonBar(wx.Window):
    """
    Buttons are tuples of (icon, callback, desc, shortcut).
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        # self.SetBackgroundColor(wx.Colour(240, 240, 240))
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetDoubleBuffered(True)

        self._buttons = []
        self._underMouseBtn = None
        self._mouseDownBtn = None

        self._logger = parent._logger


    @property
    def buttons(self):
        return self._buttons

    @buttons.setter
    def buttons(self, btns):
        self._buttons = list(btns)
        self.InvalidateBestSize()
        self.Refresh()

    @property
    def layer(self):
        return None # wx.GetTopLevelParent(self).activeLayer

    # ----------
    # wx methods
    # ----------

    def DoGetBestSize(self):
        cnt = len(self._buttons)
        pad = cnt - 1 if cnt else 0
        return wx.Size(8 + cnt * 28 + pad * 4, 36)

    def DoGetIndexForPos(self, pos):
        _, height = self.GetSize()
        if not (4 <= pos.y <= height - 5):
            return
        one = 4 + 28
        base = 4
        for i in range(len(self._buttons)):
            if base + 4 <= pos.x <= base + one:
                return i
            base += one
        return None

    def DoSetToolTip(self, index):
        if index is not None:
            if self._mouseDownBtn is not None:
                return
            btn = self._buttons[index]
            text = btn.tooltip
            # if btn.shortcut:
            #    text += f" ({btn.shortcut})"
        else:
            text = None
        self.SetToolTip(text)

    def OnLeftDown(self, event):
        self._mouseDownBtn = self._underMouseBtn
        self.DoSetToolTip(None)
        self.CaptureMouse()
        self.Refresh()
        # event.Skip()

    def OnMotion(self, event):
        index = self.DoGetIndexForPos(event.GetPosition())
        if self._underMouseBtn != index:
            self.DoSetToolTip(index)
            self._underMouseBtn = index
            self.Refresh()

    def OnLeftUp(self, event):
        self.ReleaseMouse()
        index = self._mouseDownBtn
        if index is None:
            return
        self._mouseDownBtn = None
        if self._underMouseBtn != index:
            return
        self.Refresh()
        layer = self.layer
        if layer:
            glyph = self.layer._parent
            self._logger.info("ALIGN: class {} {} -> operation {}".format(glyph.__class__.__name__ ,glyph.name, self._buttons[index].tooltip))
            self._buttons[index].callback(layer, glyph, self._buttons[index].tooltip)

            # trufont.TruFont.updateUI()

    def OnPaint(self, event):
        if graphicsContext_frompaintdc:
            self._logger.info("ButtonBar: graphicsContext_frompaintdc")
            ctx = wx.GraphicsContext.Create(wx.PaintDC(self))        
        else:
            self._logger.info("ButtonBar: graphicsContext_fromframe")
            ctx = wx.GraphicsContext.Create(self)

        ctx.SetBrush(wx.Brush(self.GetBackgroundColour()))
        ctx.DrawRectangle(0, 0, *self.GetSize())

        ctx.Translate(14, 10)
        pressedBrush = wx.Brush(wx.Colour(63, 63, 63))
        brush = wx.Brush(wx.Colour(102, 102, 102))

        for i, btn in enumerate(self._buttons):
            if i == self._mouseDownBtn == self._underMouseBtn:
                b = pressedBrush
            else:
                b = brush
            ctx.SetBrush(b)
            ctx.FillPath(btn.icon)
            ctx.Translate(32, 0)

class Frame(wx.Frame):
    def __init__(self, logger, title):
        super().__init__(None, title=title, size=(650,400))
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self._logger = logger

        try:
            propertiesSizer = makePropertiesLayout(self)
        except Exception as e:
            self._logger.error(str(e))

    def OnClose(self, event):
        dlg = wx.MessageDialog(self, 
                     "Do you really want to close this application?",
                     "Confirm Exit", wx.OK|wx.CANCEL|wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_OK:
            self.Destroy()
 

def test_toolbar(log: logging.Logger=logging.getLogger()):
    """ test a window wx with a multiline handler """
    log.info(sys.version)
    log.info("Starting .....")
    app = wx.App(redirect=True)
    win = Frame(logger, "test")
    win.Show()
    app.MainLoop()
    log.info("This is the end")

# constants
STR_FMT = '%(asctime)s - %(levelname)s : %(message)s'
DATE_FMT = '%d/%m/%Y %H:%M:%S'

if __name__ == "__main__":
    # constants
    logging.basicConfig(level=logging.DEBUG, format=STR_FMT, datefmt=DATE_FMT)
    logger = logging.getLogger()
    graphicsContext_frompaintdc = True if len(sys.argv) > 1 else False
    test_toolbar(logger)


