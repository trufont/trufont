from trufont.util.drawing import CreateMeasuringContext
import wx
from wx import GetTranslation as tr

TabChangedEvent, EVT_TAB_CHANGED = wx.lib.newevent.NewEvent()
TabRemovedEvent, EVT_TAB_REMOVED = wx.lib.newevent.NewEvent()


def masterTitle(font):
    return font.selectedMaster.name


class TabBar(wx.Window):
    TAB_CHANGED = EVT_TAB_CHANGED
    TAB_REMOVED = EVT_TAB_REMOVED

    def __init__(self, parent):
        super().__init__(parent)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        # self.Bind(wx.EVT_MOTION, self.OnMotion)
        # self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        # self.SetBackgroundColor(wx.Colour(240, 240, 240))
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetDoubleBuffered(True)

        self._currentTab = 0
        self._tabs = []
        self._tabsRanges = {}

    def addTab(self, name, parent=None):
        index = len(self._tabs)
        self._tabs.append(name)
        self.setCurrentTab(index)
        self.InvalidateBestSize()
        self.Refresh()
        return index

    def count(self):
        return len(self._tabs)

    def currentTab(self):
        return self._currentTab

    def setCurrentTab(self, value):
        if value < 0:
            value = value % len(self._tabs)
        if self._currentTab == value:
            return
        self._currentTab = value
        wx.PostEvent(self, TabChangedEvent(index=self._currentTab))
        self.Refresh()

    def removeTab(self, index):
        del self._tabs[index]
        currentTab = self._currentTab
        if currentTab > 0:
            self.setCurrentTab(currentTab - 1)
        self.InvalidateBestSize()
        wx.PostEvent(self, TabRemovedEvent(index=index))
        self.Refresh()

    def setTabName(self, index, name):
        self._tabs[index] = name
        self.InvalidateBestSize()
        self.Refresh()

    # ----------
    # wx methods
    # ----------

    def DoGetBestSize(self):
        ctx = CreateMeasuringContext()
        ctx.SetFont(self.GetFont(), self.GetForegroundColour())
        if not self._tabs:
            width = 16
        else:
            width = 8
            for name in self._tabs:
                width += ctx.GetTextExtent(name)[0] + 12
            width -= 4
        return wx.Size(width, 37)

    def DoGetTabColor(self, index):
        if index == self._currentTab:
            color = wx.Colour(63, 63, 63)
        else:
            color = wx.Colour(142, 142, 142)
        return color

    def OnLeftDown(self, event):
        pos = event.GetPosition()
        for recordIndex, (x, w) in self._tabsRanges.items():
            if x <= pos.x <= x + w:
                self.setCurrentTab(recordIndex)

    def OnPaint(self, event):
        self._tabsRanges = {}
        ctx = wx.GraphicsContext.Create(self)
        font = self.GetFont()
        ctx.SetFont(font, wx.BLACK)

        width, height = self.GetSize()
        ctx.SetBrush(wx.Brush(self.GetBackgroundColour()))
        ctx.DrawRectangle(0, 0, width, height)
        ctx.SetBrush(wx.Brush(wx.Colour(212, 212, 212)))
        ctx.DrawRectangle(0, height - 1, width, 1)

        # text metrics
        _, h, d, _ = ctx.GetFullTextExtent("x")
        ascent = h - d

        ctx.Translate(14, 10)
        ctx.SetPen(wx.Pen(wx.Colour(63, 63, 63)))
        left = 6
        for i, name in enumerate(self._tabs):
            color = self.DoGetTabColor(i)
            ctx.SetFont(font, color)
            ctx.DrawText(name, 0, 0)
            width = round(ctx.GetTextExtent(name)[0])
            self._tabsRanges[i] = (left, width + 16)
            if i == self._currentTab:
                ctx.PushState()
                ctx.Translate(0, height - 11)
                ctx.DrawRectangle(0, 0, width, 1)
                ctx.PopState()
            ctx.Translate(width, 0)
            if False and i:
                ctx.PushState()
                ctx.Translate(6, ascent - 9)
                ctx.StrokeLine(0, 0, 8, 8)
                ctx.StrokeLine(0, 8, 8, 0)
                ctx.PopState()
            ctx.Translate(24, 0)
            left += width + 24


class FontTabBar(TabBar):
    def __init__(self, parent, font):
        super().__init__(parent)
        self._contents = [font]
        self._empty = tr("Tab")

        self.addTab(masterTitle(font))

    def _canvasTextChanged(self, event):
        canvas = event.GetEventObject()
        try:
            index = self._contents.index(canvas)
        except ValueError:
            return
        self.setTabName(index, canvas.text or self._empty)

    def addCanvasTab(self, canvas):
        self._contents.append(canvas)
        self.addTab(canvas.text or self._empty)
        canvas.Bind(canvas.TEXT_CHANGED, self._canvasTextChanged)

    def removeCanvasTab(self, canvas):
        index = self._contents.index(canvas)
        self.removeTab(index)
        canvas.Unbind(canvas.TEXT_CHANGED, canvas)
        del self._contents[index]

    # ----------
    # wx methods
    # ----------

    def DoGetTabColor(self, index):
        if not index and index != self._currentTab:
            return wx.Colour(102, 102, 102)
        return super().DoGetTabColor(index)
