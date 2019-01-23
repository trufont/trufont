import math
import trufont
from trufont.controls.glyphContextView import GlyphContextView
from trufont.drawingTools.baseTool import BaseTool
from trufont.drawingTools.previewTool import PreviewTool
from trufont.objects.misc import GuidelineSegment, PointRecord, SegmentRecord
from trufont.util import bezierMath
from tfont.objects import Guideline
import wx
import wx.lib.newevent

import trufont.util.deco4class as deco4class

ToolModifiedEvent, EVT_TOOL_MODIFIED = wx.lib.newevent.NewEvent()


def GetCanvasPosition(event):
    canvas = event.GetEventObject()
    return canvas.clientToCanvas(canvas.ScreenToClient(wx.GetMousePosition()))


wx.ContextMenuEvent.GetCanvasPosition = GetCanvasPosition


def GetCanvasPosition(event):
    return event.GetEventObject().clientToCanvas(event.GetPosition())


wx.MouseEvent.GetCanvasPosition = GetCanvasPosition

# @deco4class.decorator_classfunc('OnMotion', 'OnPaint', "drawBackground", "drawForeground")
class GlyphCanvasView(GlyphContextView):
    TOOL_MODIFIED = EVT_TOOL_MODIFIED

    def __init__(self, parent, font):
        super().__init__(parent, font)
        self.Bind(wx.EVT_CHAR, self.OnChar)
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnMouseDClick)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnMouseDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnMouseUp)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_MOUSE_CAPTURE_LOST, self.OnMouseCaptureLost)
        # multiplex
        self.Bind(wx.EVT_MIDDLE_DOWN, self.OnMouseDown)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnMouseDown)
        self.Bind(wx.EVT_MIDDLE_UP, self.OnMouseUp)
        self.Bind(wx.EVT_RIGHT_UP, self.OnMouseUp)
        self.Bind(wx.EVT_MIDDLE_DCLICK, self.OnMouseDClick)
        self.Bind(wx.EVT_RIGHT_DCLICK, self.OnMouseDClick)
        #
        self._currentTool = BaseTool(self)
        self._currentToolActivated = False
        self._mouseDown = 0

        # XXX: drawing settings

        trufont.TruFont.addObserver("updateUI", self)

    def drawingAttribute(self, attr):
        # idea: pass default value as arg
        toolOverride = self._currentTool.drawingAttribute(attr)
        if toolOverride is not None:
            return toolOverride
        return trufont.TruFont.settings[attr]

    def OnUpdateUI(self):
        manager = self._layoutManager
        manager.clear()
        manager.updateFeatures()
        self.Refresh()

    # ---------------
    # Drawing helpers
    # ---------------

    def drawBackground(self, ctx, index):
        super().drawBackground(ctx, index)
        for observer in trufont.TruFont._observers["drawBackground"]:
            observer._drawBackgroundCallback(self, ctx, index)
        # could just be OnPaintBackground for consistency w observer...
        self._currentTool.OnPaint(ctx, index)

    def drawForeground(self, ctx, index):
        super().drawForeground(ctx, index)
        for observer in trufont.TruFont._observers["drawForeground"]:
            observer._drawForegroundCallback(self, ctx, index)
        self._currentTool.OnPaintForeground(ctx, index)

    # ----------
    # wx methods
    # ----------

    def OnChar(self, event):
        self._currentTool.OnChar(event)

    def OnContextMenu(self, event):
        self._currentTool.OnContextMenu(event)

    def OnKeyDown(self, event):
        tool = self._currentTool
        tool.OnKeyDown(event)
        if (
            event.GetKeyCode() == wx.WXK_SPACE
            and not tool.grabKeyboard
            and event.GetSkipped()
        ):
            if not isinstance(tool, PreviewTool):
                self.__priorTool = self._currentTool
                self._currentTool = PreviewTool(self)
                self.Refresh()

    def OnKeyUp(self, event):
        tool = self._currentTool
        tool.OnKeyUp(event)
        if (
            event.GetKeyCode() == wx.WXK_SPACE
            and not tool.grabKeyboard
            and event.GetSkipped()
        ):
            self._currentTool = self.__priorTool
            del self.__priorTool
            self.Refresh()

    def OnMouseCaptureLost(self, event):
        # why we need a mouseDown guard:
        # - when clicking a glyph cell this ctrl will show in mouse down state
        #   (which wasn't registered by it)
        # - if mouse capture is lost, we need to ignore any eventual mouse
        #   mouse event
        self._mouseDown = 0

    def OnMouseDown(self, event):
        if not self._mouseDown:
            self.CaptureMouse()
        self._mouseDown += 1
        self._currentTool.OnMouseDown(event)

    def OnMotion(self, event):
        if not self._mouseDown and event.Dragging():
            return
        self._currentTool.OnMotion(event)

    def OnMouseUp(self, event):
        if not self._mouseDown:
            return
        self._currentTool.OnMouseUp(event)
        self._mouseDown -= 1
        if not self._mouseDown:
            self.ReleaseMouse()

    def OnMouseDClick(self, event):
        self._currentTool.OnMouseDClick(event)

    # XXX: drag n drop

    # ------------
    # Canvas tools
    # ------------

    # current tool

    def _setCurrentToolEnabled(self, value):
        if self._currentToolActivated == value:
            return
        self._currentToolActivated = value
        if value:
            self._currentTool.OnToolActivated()
        else:
            self._currentTool.OnToolDisabled()

    def currentTool(self):
        return self._currentTool

    def setCurrentTool(self, tool):
        if self._mouseDown:
            return False
        self._setCurrentToolEnabled(False)
        self._currentTool = tool
        tool.canvas = self
        self.SetCursor(tool.cursor)
        self._setCurrentToolEnabled(True)
        return True

    # items location

    def itemAt(self, pos, skipElement=None):
        """
        Go through all anchors, points, components, guidelines (in this order)
        in the glyph and return the object that's under mouse (a PointRecord in
        case of a point), or None.
        """
        layer = self._layoutManager.activeLayer
        if layer is None:
            return
        x, y = pos.x, pos.y
        halfSize = 4 * self._inverseScale
        mHalfSize = -halfSize
        # anchors
        for anchor in layer._anchors.values():
            if (
                mHalfSize <= anchor.x - x <= halfSize
                and mHalfSize <= anchor.y - y <= halfSize
            ):
                return anchor
        # points
        for path in layer._paths:
            for index, point in enumerate(path._points):
                if point is skipElement:
                    continue
                if (
                    mHalfSize <= point.x - x <= halfSize
                    and mHalfSize <= point.y - y <= halfSize
                ):
                    return PointRecord(point, index)
        # components
        wr = wx.WINDING_RULE
        for component in layer._components:
            if component.closedGraphicsPath.Contains(x, y, wr):
                return component
        # guidelines
        master = layer.master
        if master is not None:
            guidelines = layer._guidelines + master._guidelines
        else:
            guidelines = layer._guidelines
        for guideline in guidelines:
            if (
                mHalfSize <= guideline.x - x <= halfSize
                and mHalfSize <= guideline.y - y <= halfSize
            ):
                return guideline

    def segmentAt(self, pos):
        layer = self._layoutManager.activeLayer
        if layer is None:
            return
        scale = self._inverseScale
        x, y = pos.x, pos.y
        maxSqDist = 9 + scale * (6 + scale)
        for path in layer.paths:
            segments = path.segments
            for index, segment in enumerate(segments):
                projection = segment.projectPoint(x, y)
                if projection is not None:
                    px, py, _ = projection
                    dx = px - x
                    dy = py - y
                    if dx * dx + dy * dy <= maxSqDist:
                        return SegmentRecord(segments, index)
        selection = layer.selection
        # check if we have exactly one guideline selected
        if len(selection) == 1:
            guideline = next(iter(selection))
            if guideline.__class__ is not Guideline:
                return
        else:
            master = layer.master
            if master is None:
                return
            guidelines = filter(lambda g: g.selected, master.guidelines)
            guideline = next(guidelines, None)
            if guideline is None or next(guidelines, None) is not None:
                return
        # end of the check of exactly one guideline selected
        if guideline.selected:
            dl = sum(self.GetClientSize()) * self._inverseScale
            gx, gy = guideline.x, guideline.y
            angle = math.radians(guideline.angle)
            ax = math.cos(angle)
            ay = math.sin(angle)
            projection = bezierMath.lineProjection(
                gx - ax * dl, gy - ay * dl, gx + ax * dl, gy + ay * dl, x, y
            )
            if projection is not None:
                px, py, _ = projection
                dx = px - x
                dy = py - y
                if dx * dx + dy * dy <= maxSqDist:
                    return GuidelineSegment(guideline)
        else:
            print("This should never happen:")
