from math import copysign
from tfont.objects import Path, Point, Layer
import trufont
from trufont.drawingTools.baseTool import BaseTool
from trufont.util.drawing import CreatePath
import wx
from wx import GetTranslation as tr

import trufont.objects.undoredomgr as undoredomgr



_path = CreatePath()
_path.MoveToPoint(5.831, 11.829)
_path.AddCurveToPoint(2.903, 11.708, 0.565, 9.219, 0.565, 6.167)
_path.AddCurveToPoint(0.565, 3.037, 3.022, 0.5, 6.054, 0.5)
_path.AddCurveToPoint(9.012, 0.5, 11.423, 2.916, 11.538, 5.94)
_path.AddLineToPoint(14.166, 5.94)
_path.AddCurveToPoint(14.71, 5.94, 15.153, 6.384, 15.153, 6.927)
_path.AddLineToPoint(15.153, 14.379)
_path.AddCurveToPoint(15.153, 14.922, 14.71, 15.363, 14.166, 15.363)
_path.AddLineToPoint(6.817, 15.363)
_path.AddCurveToPoint(6.274, 15.363, 5.831, 14.92, 5.831, 14.376)
_path.CloseSubpath()
_path.MoveToPoint(13.98, 7.113)
_path.AddLineToPoint(7.003, 7.113)
_path.AddLineToPoint(7.003, 14.19)
_path.AddLineToPoint(13.98, 14.19)
_path.CloseSubpath()
_path.MoveToPoint(10.337, 5.94)
_path.AddCurveToPoint(10.224, 3.582, 8.346, 1.7, 6.054, 1.7)
_path.AddCurveToPoint(3.689, 1.7, 1.765, 3.704, 1.765, 6.167)
_path.AddCurveToPoint(1.765, 8.552, 3.569, 10.506, 5.831, 10.627)
_path.AddLineToPoint(5.831, 6.927)
_path.AddCurveToPoint(5.831, 6.384, 6.274, 5.94, 6.817, 5.94)
_path.CloseSubpath()



#-------------------------
# Used by undoredo decorator
#-------------------------
def mouseup_expand_params(obj, *args):
    """ use by decorator to get three params aselif 
    layer, undoredomgr and operation """
    if obj.drawRectangle:
        operation =  "Draw rectangle"
    elif obj.originAtCenter:
        operation = "Draw Circle"
    else:
        operation = "Draw ellipsis"

    return obj.layer, operation 
#-------------------------

class ShapesTool(BaseTool):
    icon = _path
    name = tr("Shapes")
    shortcut = "S"

    def __init__(self, parent=None):
        super().__init__(parent)

        self.origin = None
        self.anchor = None

        self.drawRectangle = False
        self.linkAxes = False
        self.originAtCenter = False
        self.shouldMoveOrigin = False

    @property
    def cursor(self):
        return wx.Cursor(wx.CURSOR_CROSS)

    @property
    def points(self):
        try:
            x1, y1 = self.origin.Get()
            x2, y2 = self.anchor.Get()
        except AttributeError:
            pass
        else:
            if self.linkAxes:
                dx, dy = x2 - x1, y2 - y1
                if abs(dx) > abs(dy):
                    y2 = y1 + copysign(dx, dy)
                else:
                    x2 = x1 + copysign(dy, dx)
            if self.originAtCenter:
                x1, y1 = 2 * x1 - x2, 2 * y1 - y2
            if x1 > x2:
                x1, x2 = x2, x1
            if y1 > y2:
                y1, y2 = y2, y1
            return x1, y1, x2, y2

    # events

    def OnKeyDown(self, event):
        key = event.GetKeyCode()
        update = self.origin
        if key == wx.WXK_ALT:
            self.drawRectangle = True
        elif key == wx.WXK_SHIFT:
            self.linkAxes = True
        elif key == wx.WXK_CONTROL:
            self.originAtCenter = True
        elif key == wx.WXK_SPACE and update:
            self.shouldMoveOrigin = True
        elif key == wx.WXK_ESCAPE:
            self.origin = self.anchor = None
        else:
            super().OnKeyDown(event)
            return
        if update:
            self.canvas.Refresh()

    def OnKeyUp(self, event):
        key = event.GetKeyCode()
        if key == wx.WXK_ALT:
            self.drawRectangle = False
        elif key == wx.WXK_SHIFT:
            self.linkAxes = False
        elif key == wx.WXK_CONTROL:
            self.originAtCenter = False
        elif key == wx.WXK_SPACE:
            self.shouldMoveOrigin = False
        else:
            super().OnKeyUp(event)
            return
        if self.origin:
            self.canvas.Refresh()

    def OnMouseDown(self, event):
        if event.LeftDown():
            layer = self.layer
            if layer is None:
                return
            self.origin = event.GetCanvasPosition()
            layer.clearSelection()
        else:
            super().OnMouseDown(event)

    def OnMotion(self, event):
        if event.LeftIsDown():
            if self.origin:
                if self.shouldMoveOrigin:
                    self.origin += event.GetCanvasPosition() - self.anchor
                self.anchor = event.GetCanvasPosition()
                self.canvas.Refresh()
        else:
            super().OnMotion(event)

    @undoredomgr.layer_decorate_undoredo(mouseup_expand_params, 
                                         paths=True, guidelines=False, components=False, anchors=False)
    def OnMouseUpLeftUp(self, event):
        """ make thios method to be sure that the super().OnMouseUp() call do not 
        bloc process of wx msgs  """
        points = self.points
        if points:
            x1, y1, x2, y2 = points
            if self.drawRectangle:
                path = Path(
                    [
                        Point(x1, y1, "line"),
                        Point(x2, y1, "line"),
                        Point(x2, y2, "line"),
                        Point(x1, y2, "line"),
                    ]
                )
            else:
                dx, dy = x2 - x1, y2 - y1
                path = Path(
                    [
                        Point(x1 + .225 * dx, y2),
                        Point(x1, y1 + .775 * dy),
                        Point(x1, y1 + .5 * dy, "curve", smooth=True),
                        Point(x1, y1 + .225 * dy),
                        Point(x1 + .225 * dx, y1),
                        Point(x1 + .5 * dx, y1, "curve", smooth=True),
                        Point(x1 + .775 * dx, y1),
                        Point(x2, y1 + .225 * dy),
                        Point(x2, y1 + .5 * dy, "curve", smooth=True),
                        Point(x2, y1 + .775 * dy),
                        Point(x1 + .775 * dx, y2),
                        Point(x1 + .5 * dx, y2, "curve", smooth=True),
                    ]
                )
            self.layer.paths.append(path)
            path.selected = True
            trufont.TruFont.updateUI()
        self.origin = self.anchor = None

    def OnMouseUp(self, event):
        if event.LeftUp():
            self.OnMouseUpLeftUp(event)
        else:
            super().OnMouseUp(event)

    def OnPaintForeground(self, ctx, index):
        points = self.points
        if not points:
            return
        x1, y1, x2, y2 = points
        ctx.SetBrush(wx.NullBrush)
        # it would be nice to be able to directly request a pen from the canvas
        canvas = self.canvas
        strokeColor = wx.Colour(*trufont.TruFont.settings["strokeColor"])
        ctx.SetPen(wx.Pen(strokeColor, canvas.inverseScale))
        if self.drawRectangle:
            ctx_Draw = ctx.DrawRectangle
        else:
            ctx_Draw = ctx.DrawEllipse
        ctx_Draw(x1, y1, x2 - x1, y2 - y1)
