import itertools
import math
from trufont.drawingTools.baseTool import BaseTool
from trufont.objects.misc import PointRecord
from trufont.util import bezierMath, drawing
from trufont.util.drawing import CreateMatrix, CreatePath
import wx
from wx import GetTranslation as tr

_path = CreatePath()
_path.MoveToPoint(0.5, 3.5)
_path.AddLineToPoint(12.5, 15.5)
_path.AddLineToPoint(15.5, 12.5)
_path.AddLineToPoint(14.25, 11.25)
_path.AddLineToPoint(13.242, 12.242)
_path.AddLineToPoint(12.5, 11.5)
_path.AddLineToPoint(13.5, 10.5)
_path.AddLineToPoint(12.5, 9.5)
_path.AddLineToPoint(10.75, 11.25)
_path.AddLineToPoint(10.0, 10.5)
_path.AddLineToPoint(11.75, 8.75)
_path.AddLineToPoint(10.75, 7.75)
_path.AddLineToPoint(9.75, 8.75)
_path.AddLineToPoint(9.0, 8.0)
_path.AddLineToPoint(10.0, 7.0)
_path.AddLineToPoint(9.0, 6.0)
_path.AddLineToPoint(7.25, 7.75)
_path.AddLineToPoint(6.5, 7.0)
_path.AddLineToPoint(8.25, 5.25)
_path.AddLineToPoint(7.25, 4.25)
_path.AddLineToPoint(6.25, 5.25)
_path.AddLineToPoint(5.5, 4.5)
_path.AddLineToPoint(6.5, 3.5)
_path.AddLineToPoint(5.5, 2.5)
_path.AddLineToPoint(3.758, 4.25)
_path.AddLineToPoint(3.0, 3.5)
_path.AddLineToPoint(4.75, 1.75)
_path.AddLineToPoint(3.5, 0.5)
_path.CloseSubpath()
_path.Transform(CreateMatrix(tx=.2))

_cbgpath = CreatePath()
_cbgpath.MoveToPoint(7.5, 17.0)
_cbgpath.AddLineToPoint(17.0, 7.5)
_cbgpath.AddLineToPoint(20.5, 11.0)
_cbgpath.AddLineToPoint(11.0, 20.5)
_cbgpath.CloseSubpath()

_cpath = CreatePath()
_cpath.MoveToPoint(8, 4.5)
_cpath.AddLineToPoint(8, 11.5)
_cpath.MoveToPoint(4.5, 8)
_cpath.AddLineToPoint(11.5, 8)
_cpath.MoveToPoint(7.5, 17.0)
_cpath.AddLineToPoint(17.0, 7.5)
_cpath.AddLineToPoint(20.5, 11.0)
_cpath.AddLineToPoint(11.0, 20.5)
_cpath.CloseSubpath()
_cpath.MoveToPoint(16.5, 12.0)
_cpath.AddLineToPoint(14.5, 10.0)
_cpath.CloseSubpath()
_cpath.MoveToPoint(12.0, 16.5)
_cpath.AddLineToPoint(10.0, 14.5)
_cpath.MoveToPoint(14.75, 14.75)
_cpath.AddLineToPoint(12.25, 12.25)

_commands = (
    (_cpath, 255, 0),
)


def pairwise(iterable):
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


class RulerTool(BaseTool):
    icon = _path
    name = tr("Ruler")
    shortcut = "R"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.origin = None
        self.points = None

    @property
    def cursor(self):
        return self.makeCursor(_commands, 8.5, 9.5, shadowPath=_cbgpath)

    def drawingAttribute(self, attr):
        if attr == "showCoordinates":
            return True
        return None

    # maybe we could just refresh in the base impl or in the widget
    def OnToolActivated(self):
        # show coordinates
        self.canvas.Refresh()

    def OnToolDisabled(self):
        self.origin = self.points = None
        self.canvas.Refresh()

    # custom method

    def magnetPos(self, pos):
        mouseItem = self.canvas.itemAt(pos)
        if isinstance(mouseItem, PointRecord):
            point = mouseItem.point
            pos.x = point.x
            pos.y = point.y
        return pos

    # events

    def OnMouseDown(self, event):
        if event.LeftDown():
            # TODO: I think GetCanvasPosition is in order here.
            # also make sure it's floating point precision.
            self.origin = self.magnetPos(event.GetCanvasPosition())
            self.canvas.SetFocus()
        else:
            super().OnMouseDown(event)

    def OnMotion(self, event):
        if event.LeftIsDown():
            origin = self.origin
            pos = self.magnetPos(event.GetCanvasPosition())
            if origin is None:
                self.origin = pos
                return
            layer = self.layer
            # magnet done before clamping to axis
            if event.ShiftDown():
                pos = self.clampToOrigin(pos, origin)
            if event.AltDown() or layer is None:
                self.points = [(origin.x, origin.y), (pos.x, pos.y)]
            else:
                self.points = layer.intersectLine(
                    origin.x, origin.y, pos.x, pos.y)
            self.canvas.Refresh()
        else:
            super().OnMotion(event)

    def OnMouseUp(self, event):
        if event.LeftUp():
            # double click calls release twice
            if self.origin is None:
                return
            self.origin = self.points = None
            self.canvas.Refresh()
        else:
            super().OnMouseUp(event)

    # custom painting

    def OnPaint(self, ctx, index):
        points = self.points
        if points is None:
            return
        canvas = self.canvas
        p1x, p1y = points[0]
        p2x, p2y = points[-1]
        scale = canvas.inverseScale
        halfSize = 4 * scale
        size = 2 * halfSize
        color = wx.Colour(255, 111, 146, 170)

        # line
        ctx.SetPen(wx.Pen(color, scale))
        ctx.StrokeLine(p1x, p1y, p2x, p2y)
        # ellipses
        path = ctx.CreatePath()
        for x, y in points:
            x -= halfSize
            y -= halfSize
            path.AddEllipse(x, y, size, size)
        ctx.SetBrush(wx.Brush(color))
        ctx.FillPath(path, wx.WINDING_RULE)
        # text
        font = ctx.GetFont()
        font.SetPixelSize(wx.Size(0, 11))
        ctx.SetFont(font, wx.Colour(37, 37, 37))
        xAlign = yAlign = "center"
        # TODO spell out distance and drawText
        for (x1, y1), (x2, y2) in pairwise(points):
            # we could calc the length from the t values and total len
            length = round(bezierMath.distance(x1, y1, x2, y2), 1)
            if length:
                x, y = .5 * (x1 + x2), .5 * (y1 + y2)
                drawing.drawTextAtPoint(
                    ctx, str(length), x, y, scale, xAlign, yAlign)
        angleText = "%sº" % round(
            math.degrees(math.atan2(p2y - p1y, p2x - p1x)), 1)
        xAlign, yAlign = "left", "top"
        px = size
        if p2x < p1x:
            xAlign = "right"
            px = -px
        drawing.drawTextAtPoint(
            ctx, angleText, p2x + px, p2y + size, scale,
            xAlign, yAlign)
