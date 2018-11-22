import trufont
from trufont.util import platformSpecific
from trufont.util.drawing import CreatePath
from trufont.util.canvasDelete import deleteUILayerSelection
from trufont.util.canvasMove import moveFromKeysUILayerSelection
from trufont.objects.undoredomgr import Action
from tfont.objects import Point
import wx
from wx import GetTranslation as tr

TRANSLATE_CURSOR = platformSpecific.translateCursor()


class BaseTool(object):
    icon = CreatePath()
    name = tr("Tool")
    shortcut = None
    grabKeyboard = False

    def __init__(self, canvas=None):
        self.canvas = canvas
        self.preparedUndo = False

    @property
    def cursor(self):
        return wx.Cursor(wx.CURSOR_ARROW)

    @property
    def font(self):
        return self.canvas._font

    @property
    def layer(self):
        return self.canvas._layoutManager.activeLayer

    def drawingAttribute(self, attr):
        return None

    # helper functions

    def clampToOrigin(self, pos, origin):
        """Projects the point |pos| onto the closest axis.
        Returns the projected position."""
        deltaX = pos.x - origin.x
        deltaY = pos.y - origin.y
        # go into the first quadrant to simplify our study
        aDeltaX = abs(deltaX)
        aDeltaY = abs(deltaY)
        if aDeltaY >= aDeltaX:
            pos.x = origin.x
        else:
            pos.y = origin.y
        return pos

    def makeCursor(self, cmds, x, y, shadowColor=0, shadowPath=None, shadowRadius=1):
        canvas = self.canvas
        w = wx.SystemSettings.GetMetric(wx.SYS_CURSOR_X, canvas)
        h = wx.SystemSettings.GetMetric(wx.SYS_CURSOR_Y, canvas)
        if w == -1 or h == -1:
            w = h = 32
        # NOTE: size is 32 (or 64) on Windows, -1 on OSX, 24 on GNU
        # TODO: we should probably call GetContentScaleFactor instead
        s = 2 if w > 32 else 0

        bitmap = wx.Bitmap.FromRGBA(w, h)
        dc = wx.MemoryDC()
        dc.SelectObject(bitmap)
        # draw the shadow
        if shadowPath is not None:
            ctx = wx.GraphicsContext.Create(dc)
            if s > 1:
                ctx.Scale(s, s)
            ctx.PushState()
            ctx.Translate(1, 1)
            ctx.SetBrush(
                wx.Brush(wx.Colour(shadowColor, shadowColor, shadowColor, 200))
            )
            ctx.DrawPath(shadowPath, wx.WINDING_RULE)
            ctx.PopState()
            dc.SelectObject(wx.NullBitmap)
            image = bitmap.ConvertToImage()
            bitmap = wx.Bitmap.FromRGBA(w, h)
            dc.SelectObject(bitmap)
            dc.DrawBitmap(wx.Bitmap(image.Blur(shadowRadius)), 0, 0, True)
        # draw the cursor
        ctx = wx.GraphicsContext.Create(dc)
        if s > 1:
            ctx.Scale(s, s)
        for path, f, s in cmds:
            ctx.SetBrush(wx.Brush(wx.Colour(f, f, f)))
            ctx.SetPen(wx.Pen(wx.Colour(s, s, s)))
            ctx.DrawPath(path, wx.WINDING_RULE)
        dc.SelectObject(wx.NullBitmap)
        image = bitmap.ConvertToImage()
        image.SetOption(wx.IMAGE_OPTION_CUR_HOTSPOT_X, x)
        image.SetOption(wx.IMAGE_OPTION_CUR_HOTSPOT_Y, y)
        return wx.Cursor(image)

    # events

    def OnContextMenu(self, event):
        event.Skip()

    def OnChar(self, event):
        event.Skip()

    def prepareUndo(self, group_name: str="unknown"):
        """A local function to ask the layer to prepare for undo but doing so
        only once if prepareUndo() is called several time during event handling.
        Also layer.endUndoGroup() will be called once, and only if prepareUndo()
        was called."""
        if not self.preparedUndo and self.layer:
            self.layer.beginUndoGroup(group_name)
            self.preparedUndo = True

    def performUndo(self, operation:str, group_name: str="unknown"):
        if self.preparedUndo and self.layer:
            self.layer._parent.get_undoredo().append_action(Action(operation, *self.layer.endUndoGroup(group_name)))
            self.preparedUndo = False

    # we oughta eat the modifiers down/up events in baseTool to stop the
    # system from using them
    def OnKeyDown(self, event):
        if event.IsKeyInCategory(wx.WXK_CATEGORY_ARROW):
            key = event.GetKeyCode()
            dx, dy = 0, 0
            if key == wx.WXK_LEFT:
                dx = -1
            elif key == wx.WXK_UP:
                dy = 1
            elif key == wx.WXK_RIGHT:
                dx = 1
            elif key == wx.WXK_DOWN:
                dy = -1
            if event.ShiftDown():
                dx *= 10
                dy *= 10
                if event.ControlDown():
                    dx *= 10
                    dy *= 10
            if event.GetModifiers() == platformSpecific.combinedModifiers():
                option = "nudge"
            elif event.AltDown():
                option = "slide"
            else:
                option = None
            # prepare undo
            moveFromKeysUILayerSelection(self.layer, dx, dy, option=option)
        elif event.IsKeyInCategory(wx.WXK_CATEGORY_CUT):
            deleteUILayerSelection(self.layer, breakPaths=event.AltDown())
        elif event.GetKeyCode() == wx.WXK_TAB:
            # Changes only the selection
            # TODO: make this undo-able (in particular the current
            # layer.selection may contain many things, not just one point)
            layer = self.layer
            point = None
            for sel in layer.selection: # find any selected point
                if isinstance(sel, Point):
                    point = sel
            if point is not None:
                # select next or previous point
                # typical case where point.nextPoint/point.prevPoint
                # would make a lot of sense
                path = point.path
                points = path.points
                index = points.index(point)
                if event.ShiftDown():
                    newPoint = points[index - 1]
                else:
                    ptIndex = (index + 1) % len(points)
                    newPoint = points[ptIndex]
                layer.clearSelection()
                newPoint.selected = True
        elif event.GetKeyCode() == wx.WXK_RETURN:
            self.prepareUndo()
            # FIXME: can't we directly access the indices of the selected points?
            for path in self.layer.paths:
                points = path.points
                for index, point in enumerate(points):
                    if point.type is None or not point.selected:
                        continue
                    if (points[index - 1].type is not None) and \
                        (points[(index+1)%len(points)].type is not None):
                        continue
                    point.smooth = not point.smooth
            self.performUndo("Toggle smooth")
        else:
            event.Skip()
            return
        trufont.TruFont.updateUI()

    def OnKeyUp(self, event):
        event.Skip()

    def OnMouseDown(self, event):
        if event.MiddleDown():
            self._panOrigin = event.GetPosition()
            # TODO: glyphCanvasView should reset cursor on evt_leave
            # and call OnToolDisabled
            self.canvas.SetCursor(wx.Cursor(TRANSLATE_CURSOR))
        else:
            event.Skip()

    def OnMotion(self, event):
        if hasattr(self, "_panOrigin"):
            pos = event.GetPosition()
            self.canvas.scrollBy(pos - self._panOrigin)
            self._panOrigin = pos
        else:
            event.Skip()

    def OnMouseUp(self, event):
        # TODO: this should be done in OnToolDisabled in addition to
        # here for the EVT_LEAVE case
        if hasattr(self, "_panOrigin"):
            self.canvas.SetCursor(self.cursor)
            del self._panOrigin
        else:
            event.Skip()

    def OnMouseDClick(self, event):
        if event.LeftDClick():
            self.canvas.moveTextCursorTo(event.GetPosition())
        else:
            event.Skip()

    # custom events

    def OnPaint(self, ctx, index):
        pass

    def OnPaintForeground(self, ctx, index):
        pass

    def OnToolActivated(self):
        pass

    def OnToolDisabled(self):
        pass
