import trufont
from trufont.drawingTools.baseTool import BaseTool
from trufont.util.drawing import CreatePath
import wx
from wx import GetTranslation as tr

import trufont.objects.undoredomgr as undoredomgr

_path = CreatePath()
_path.MoveToPoint(1.0, 0.975)
_path.AddLineToPoint(1.468, 0.3)
_path.AddLineToPoint(10.276, 8.909)
_path.AddLineToPoint(8.036, 11.149)
_path.AddLineToPoint(5.436, 10.52)
_path.CloseSubpath()
_path.MoveToPoint(9.0, 11.694)
_path.AddLineToPoint(11.041, 9.653)
_path.AddLineToPoint(14.701, 13.229)
_path.AddLineToPoint(12.417, 15.5)
_path.AddLineToPoint(8.995, 11.694)
_path.CloseSubpath()

_cpath1 = CreatePath()
_cpath1.MoveToPoint(14.4, 8.4)
_cpath1.AddLineToPoint(18.6, 3.6)
_cpath1.AddLineToPoint(22.6, 5.7)
_cpath1.AddLineToPoint(16.7, 10.7)
_cpath1.CloseSubpath()
_cpath2 = CreatePath()
_cpath2.MoveToPoint(5.0, 19.0)
_cpath2.AddLineToPoint(12.5, 10.5)
_cpath2.AddLineToPoint(14.0, 10.5)
_cpath2.AddLineToPoint(15.5, 12.0)
_cpath2.AddLineToPoint(15.5, 14.5)
_cpath2.CloseSubpath()

_commands = ((_cpath1, 0, 0), (_cpath2, 230, 0))

class KnifeTool(BaseTool):
    icon = _path
    name = tr("Knife")
    shortcut = "E"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.origin = None
        self.points = None

    @property
    def cursor(self):
        return self.makeCursor(_commands, 4, 20, shadowPath=_cpath2)

    # events

    def OnMouseDown(self, event):
        if event.LeftDown():
            self.origin = event.GetCanvasPosition()
            self.canvas.SetFocus()
        else:
            super().OnMouseDown(event)

    def OnMotion(self, event):
        if event.LeftIsDown():
            origin = self.origin
            pos = event.GetCanvasPosition()
            if origin is None:
                self.origin = pos
                return
            layer = self.layer
            if event.ShiftDown():
                pos = self.clampToOrigin(pos, origin)
            if layer is None:
                self.points = [(origin.x, origin.y), (pos.x, pos.y)]
            else:
                self.points = self.layer.intersectLine(origin.x, origin.y, pos.x, pos.y)
            self.canvas.Refresh()
        else:
            super().OnMotion(event)

    @undoredomgr.layer_decorate_undoredo((lambda *args, **kwargs: args[0].layer), 
                                         operation="Knife cut something",
                                         paths=True, guidelines=False, components=False, anchors=False)
    def OnMouseUpLeftUp(self, event):
        """ make thios method to be sure that the super().OnMouseUp() call do not 
        bloc process of wx msgs  """
        points = self.points
        if points: #  is not None:
            layer = self.layer
            if layer: # is not None:
                origin = self.origin
                layer.clearSelection()
                layer.sliceLine(origin.x, origin.y, *points[-1])
                trufont.TruFont.updateUI()
            else:
                self.canvas.Refresh()
        self.origin = self.points = None

    def OnMouseUp(self, event):
        if event.LeftUp():
            self.OnMouseUpLeftUp(event)
        else:
            super().OnMouseUp(event)


    # custom painting

    def OnPaint(self, ctx, index):
        points = self.points
        if points is None:
            return
        canvas = self.canvas
        p1 = points[0]
        p2 = points[-1]
        halfSize = 3 * canvas.inverseScale
        size = 2 * halfSize
        color = wx.Colour(60, 60, 60, 120)

        ctx.SetBrush(wx.Brush(color))
        ctx.SetPen(wx.Pen(color))
        ctx.StrokeLine(*p1, *p2)
        path = ctx.CreatePath()
        for point in points:
            if point is p1 or point is p2:
                continue
            x, y = point
            x -= halfSize
            y -= halfSize
            path.AddEllipse(x, y, size, size)
        ctx.FillPath(path, wx.WINDING_RULE)
