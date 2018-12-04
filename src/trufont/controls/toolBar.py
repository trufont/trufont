import wx
from trufont.controls.glyphContextView import GlyphContextView
from trufont.drawingTools import (
    SelectionTool,
    PenTool,
    RulerTool,
    KnifeTool,
    ShapesTool,
    TextTool,
)

color = wx.Colour(102, 102, 102)
selectedColor = wx.Colour(20, 146, 230)

# TODO: can this and the putting into the class be done thru a decorator?
ToolModifiedEvent, EVT_TOOL_MODIFIED = wx.lib.newevent.NewEvent()


# interim solution, this should be handled by the Application
def drawingTools():
    return [SelectionTool, PenTool, KnifeTool, RulerTool, ShapesTool, TextTool]


class ToolBar(wx.Window):
    """
    TODO: allow all orientations
    """

    TOOL_MODIFIED = EVT_TOOL_MODIFIED

    def __init__(self, parent):
        super().__init__(parent)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        # self.SetBackgroundColor(wx.Colour(240, 240, 240))
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetDoubleBuffered(True)

        self._currentTool = 0
        self._tools = []
        self._underMouseTool = None
        self._mouseDownTool = None

    def currentTool(self):
        return self._tools[self._currentTool]

    def setCurrentTool(self, tool):
        if isinstance(tool, type):
            ok = False
            for idx, tool_ in enumerate(self._tools):
                if isinstance(tool_, tool):
                    self._currentTool = idx
                    ok = True
                    break
            if not ok:
                raise ValueError(f"no instance of {tool!r} found")
        elif tool.__class__ is int:
            if tool < 0:
                tool = tool % len(self._tools)
            self._currentTool = tool
        else:
            self._currentTool = self._tools.index(tool)
        self.Refresh()

    def tools(self):
        return self._tools

    def setTools(self, tools):
        self._tools = list(tools)
        self._currentTool = 0
        self.InvalidateBestSize()
        self.Refresh()

    # ----------
    # wx methods
    # ----------

    def DoGetBestSize(self):
        cnt = len(self._tools)
        pad = cnt - 1 if cnt else 0
        return wx.Size(42, 12 + cnt * 32 + pad * 4)

    def DoGetIndexForPos(self, pos):
        width, _ = self.GetSize()
        if not (5 <= pos.x <= width - 6):
            return
        one = 4 + 32
        base = 2
        for i in range(self.DoGetToolsSize()):
            if base + 4 <= pos.y <= base + one:
                return i
            base += one
        return None

    def DoGetToolsSize(self):
        return len(self._tools)

    def DoProcessCharHook(self, event):
        if not event.GetModifiers():
            char = chr(event.GetUnicodeKey())
            size = self.DoGetToolsSize()
            for i, tool in enumerate(self._tools):
                if i >= size:
                    break
                if char == tool.shortcut:
                    if self._currentTool != i:
                        self._currentTool = i
                        wx.PostEvent(
                            self, ToolModifiedEvent(tool=self._tools[self._currentTool])
                        )
                        self.Refresh()
                    return
        event.Skip()

    def DoSetToolTip(self, index):
        if index is not None:
            if self._mouseDownTool is not None:
                return
            tool = self._tools[index]
            text = tool.name
            if tool.shortcut:
                text += f" ({tool.shortcut})"
        else:
            text = None
        self.SetToolTip(text)

    def OnLeftDown(self, event):
        self._mouseDownTool = self._underMouseTool
        self.DoSetToolTip(None)
        self.CaptureMouse()
        self.Refresh()

    def OnMotion(self, event):
        index = self.DoGetIndexForPos(event.GetPosition())
        if self._underMouseTool != index:
            self.DoSetToolTip(index)
            self._underMouseTool = index
            self.Refresh()

    def OnLeftUp(self, event):
        self.ReleaseMouse()
        if self._mouseDownTool is None:
            return
        if self._underMouseTool == self._mouseDownTool:
            if self._mouseDownTool != self._currentTool:
                self._currentTool = self._mouseDownTool
                wx.PostEvent(
                    self, ToolModifiedEvent(tool=self._tools[self._currentTool])
                )
            self.Refresh()
        self.DoSetToolTip(self._mouseDownTool)
        self._mouseDownTool = None

    def OnPaint(self, event):
        # ctx = wx.GraphicsContext.Create(self)
        ctx = wx.GraphicsContext.Create(wx.PaintDC(self))

        ctx.SetBrush(wx.Brush(self.GetBackgroundColour()))
        ctx.DrawRectangle(0, 0, *self.GetSize())

        ctx.Translate(13, 14)
        selectedBrush = wx.Brush(selectedColor)
        brush = wx.Brush(color)

        size = self.DoGetToolsSize()
        for i, tool in enumerate(self._tools):
            if i >= size:
                break
            if (i == self._currentTool) ^ (
                i == self._mouseDownTool == self._underMouseTool
            ):
                b = selectedBrush
            else:
                b = brush
            ctx.SetBrush(b)
            ctx.FillPath(tool.icon)
            ctx.Translate(0, 16 + 20)


class FontToolBar(ToolBar):
    def __init__(self, parent):
        super().__init__(parent)
        self.__ctrl = None
        self.__previousTool = 0
        self.__shadow = True
        self.setTools([t() for t in drawingTools()])

        self.Bind(self.TOOL_MODIFIED, self.__toolModified)

    # tool mgmt

    def parentControl(self):
        return self.__ctrl

    def setParentControl(self, ctrl):
        self.__ctrl = ctrl
        isCanvas = isinstance(ctrl, GlyphContextView)
        self.__shadow = not isCanvas
        if isCanvas:
            ctrl.setCurrentTool(self.currentTool())
        else:
            self.__previousTool = self._currentTool = 0
        self.Refresh()

    def __toolModified(self, event):
        if self.__ctrl is not None:
            priorTool = self.__ctrl.currentTool()
            ok = self.__ctrl.setCurrentTool(event.tool)
            if ok:
                if priorTool.grabKeyboard:
                    self.__previousTool = 0
                else:
                    p = self._tools.index(priorTool)
                    if self._currentTool != p:
                        self.__previousTool = p
            else:
                # reverting the change... we might just stop sending events
                # then, this whole logic feels too complicated and piecewise
                # -- or make an actual third party controller object
                p = self._tools.index(priorTool)
                self._currentTool = p
                self.Refresh()

    def resetCurrentTool(self):
        self._currentTool = 0
        wx.PostEvent(self, ToolModifiedEvent(tool=self._tools[self._currentTool]))
        self.Refresh()

    def DoGetToolsSize(self):
        return 1 if self.__shadow else len(self._tools)

    # previous tool (for kbd grabbers)

    def setTools(self, tools):
        super().setTools(tools)
        self.__previousTool = 0

    def DoProcessCharHook(self, event):
        t = self._tools[self._currentTool]
        if t.grabKeyboard:
            if not event.GetModifiers():
                key = event.GetKeyCode()
                if key == wx.WXK_ESCAPE:
                    self._currentTool = self.__previousTool
                    wx.PostEvent(
                        self, ToolModifiedEvent(tool=self._tools[self._currentTool])
                    )
                    self.Refresh()
                    return
            event.Skip()
        else:
            super().DoProcessCharHook(event)
