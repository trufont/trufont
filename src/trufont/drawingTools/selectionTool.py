import math
import trufont

# from trufont.controls.layerDialogs import AddComponentDialog, RenameDialog
from trufont.drawingTools.baseTool import BaseTool
from trufont.objects.misc import GuidelineSegment, PointRecord, SegmentRecord
from trufont.objects.undoredomgr import Action
from trufont.util import platformSpecific
from trufont.util.canvasMorph import atOpenBoundary, joinPaths
from trufont.util.canvasMove import moveUILayerSelection, rotateUIPointAroundRefLine
from trufont.util.drawing import CreatePath
from tfont.objects import Anchor, Component, Guideline, Layer, Point
import wx
from wx import GetTranslation as tr

import trufont.util.deco4class as deco4class
import trufont.objects.undoredomgr as undoredomgr

# The icon for the tool's button
_path = CreatePath()
_path.MoveToPoint(3.018, 1.167)
_path.AddLineToPoint(3.0, 15.0)
_path.AddCurveToPoint(3.0, 15.79, 3.356, 15.9, 3.91, 15.35)
_path.AddLineToPoint(7.35, 11.962)
_path.AddCurveToPoint(7.652, 11.634, 8.073, 11.44, 8.519, 11.422)
_path.AddLineToPoint(13.29, 11.422)
_path.AddCurveToPoint(14.04, 11.422, 14.242, 10.946, 13.69, 10.392)
_path.AddLineToPoint(3.97, 0.822)
_path.AddCurveToPoint(3.43, 0.261, 3.018, 0.428, 3.018, 1.167)
_path.AddLineToPoint(3.018, 1.167)
_path.AddLineToPoint(3.018, 1.167)
_path.CloseSubpath()

# The tool's mouse cursor
_cursor = CreatePath()
_cursor.MoveToPoint(6, 4)
_cursor.AddLineToPoint(6, 19)
_cursor.AddLineToPoint(9.5, 15.45)
_cursor.AddLineToPoint(12.2, 21.55)
_cursor.AddLineToPoint(14.75, 20.75)
_cursor.AddLineToPoint(12.2, 15)
_cursor.AddLineToPoint(16.75, 15)
_cursor.CloseSubpath()

_commands = ((_cursor, 255, 25),)

_point = CreatePath()
_point.AddRectangle(19, 19, 5, 5)

#-------------------------
# Used by undoredo decorator
#-------------------------
def selectionTool_expand_params(obj, *args, **kwargs):
    return obj.layer 
#-------------------------

# @deco4class.decorator_classfunc()
class SelectionTool(BaseTool):
    icon = _path
    name = tr("Selection")
    shortcut = "V"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.origin = None
        self.mouseItem = None
        self.oldPath = None
        self.oldSelection = set()
        self.rubberBandRect = None

        self.preparedUndo = False

        # TODO flush on dpi change event. need wx 3.1 and beyond...
        self._cursor = None
        self._pointCursor = None

    @property
    def cursor(self):
        cursor = self._cursor
        if cursor is None:
            cursor = self._cursor = self.makeCursor(_commands, 6, 4)
        return cursor

    @property
    def pointCursor(self):
        cursor = self._pointCursor
        if cursor is None:
            suppl = ((_point, 255, 90),)
            cursor = self._pointCursor = self.makeCursor(
                _commands + suppl, 6, 4, shadowColor=255, shadowPath=_point
            )
        return cursor

    # helpers
    @undoredomgr.layer_decorate_undoredo(selectionTool_expand_params, operation="Create anchor", 
                                         paths=False, guidelines=False, components=False, anchors=True)
    def createAnchor(self, *_):
        pos = self._cachedPos
        self.layer.anchors["new anchor"] = Anchor(pos.x, pos.y)
        trufont.TruFont.updateUI()

    @undoredomgr.layer_decorate_undoredo(selectionTool_expand_params, operation="Create component", 
                                         paths=False, guidelines=False, components=True, anchors=False)
    def createComponent(self, *_):
        raise NotImplementedError
        layer = self.layer
        newGlyph, ok = AddComponentDialog.getNewGlyph(self.canvas, layer)
        if ok and newGlyph is not None:
            layer.components.append(Component(newGlyph.name))
            trufont.TruFont.updateUI()

    @undoredomgr.layer_decorate_undoredo(selectionTool_expand_params, operation="Create guideline", 
                                     paths=False, guidelines=True, components=False, anchors=False)
    def createGuideline(self, *_):
        pos = self._cachedPos
        self.layer.guidelines.append(Guideline(pos.x, pos.y, 0))
        trufont.TruFont.updateUI()

    @undoredomgr.layer_decorate_undoredo(selectionTool_expand_params, operation="Decompose component", 
                                     paths=False, guidelines=False, components=True, anchors=False)
    def decomposeComponent(self, *_):
        item = self.mouseItem
        item.decompose()
        trufont.TruFont.updateUI()

    @undoredomgr.layer_decorate_undoredo(selectionTool_expand_params, operation="Lock component", 
                                     paths=False, guidelines=False, components=True, anchors=False)
    def lockComponent(self, *_):
        raise NotImplementedError

    @undoredomgr.layer_decorate_undoredo(selectionTool_expand_params, operation="Lock guideline", 
                                     paths=False, guidelines=True, components=False, anchors=False)
    def lockGuideline(self, *_):
        raise NotImplementedError

    @undoredomgr.layer_decorate_undoredo(selectionTool_expand_params, operation="Toggle guideline", 
                                     paths=False, guidelines=True, components=False, anchors=False)
    def toggleGuideline(self, *_):
        item = self.mouseItem
        parent = item._parent
        parent.guidelines.remove(item)
        if parent.__class__ is Layer:
            master = parent.master
            master.guidelines.append(item)
        else:
            self.layer.guidelines.append(item)
        trufont.TruFont.updateUI()

    def maybeJoinPath(self, pos):
        item = self.mouseItem
        if not (item.__class__ is PointRecord and atOpenBoundary(item.point)):
            return
        item_ = self.canvas.itemAt(pos, skipElement=item.point)
        if not (item_.__class__ is PointRecord and atOpenBoundary(item_.point)):
            return
        # joinPaths is decorated
        joinPaths(item.path, not item.index, item_.path, not item_.index, True)
        trufont.TruFont.updateUI()

    def renameItem(self, item):
        raise NotImplementedError

    @undoredomgr.layer_decorate_undoredo(selectionTool_expand_params, operation="Reverse path", 
                                         paths=True, guidelines=False, components=False, anchors=False)
    def reverse(self, *_):
        target = self._targetPath
        if target is not None:
            target.reverse()
        else:
            layer = self.layer
            selectedPaths = set()
            for elem in layer.selection:
                if elem.__class__ is Point:
                    selectedPaths.add(elem._parent)
            target = selectedPaths or layer.paths
            for path in target:
                path.reverse()
        trufont.TruFont.updateUI()

    @undoredomgr.layer_decorate_undoredo(selectionTool_expand_params, operation="Set start point", 
                                         paths=True, guidelines=False, components=False, anchors=False)
    def setStartPoint(self, *_):
        item = self.mouseItem
        item.path.setStartPoint(item.index)
        trufont.TruFont.updateUI()

    # events

    def OnContextMenu(self, event):
        canvas = self.canvas
        menu = wx.Menu()
        item = self.mouseItem
        self._targetPath = None
        if item is not None:
            cls = item.__class__
            if cls is PointRecord:
                self._targetPath = item.path
                if item.point.type is not None:
                    canvas.Bind(
                        wx.EVT_MENU,
                        self.setStartPoint,
                        menu.Append(wx.ID_ANY, tr("Set Start Point")),
                    )
            elif cls is Component:
                canvas.Bind(
                    wx.EVT_MENU,
                    self.decomposeComponent,
                    menu.Append(wx.ID_ANY, tr("Decompose")),
                )
                canvas.Bind(
                    wx.EVT_MENU,
                    self.lockComponent,
                    menu.Append(wx.ID_ANY, tr("Lock Component")),
                )
            elif cls is Guideline:
                if item._parent.__class__ is Layer:
                    text = tr("Make Global Guideline")
                else:
                    text = tr("Make Local Guideline")
                canvas.Bind(
                    wx.EVT_MENU, self.toggleGuideline, menu.Append(wx.ID_ANY, text)
                )
                canvas.Bind(
                    wx.EVT_MENU,
                    self.lockGuideline,
                    menu.Append(wx.ID_ANY, tr("Lock Guideline")),
                )
        if self.layer:
            if self._targetPath is not None:
                reverseText = tr("Reverse Path")
            else:
                if any(e.__class__ is Point for e in self.layer.selection):
                    reverseText = tr("Reverse Selected Paths")
                else:
                    reverseText = tr("Reverse All Paths")
            canvas.Bind(wx.EVT_MENU, self.reverse, menu.Append(wx.ID_ANY, reverseText))
            menu.AppendSeparator()
        canvas.Bind(
            wx.EVT_MENU,
            self.createComponent,
            menu.Append(wx.ID_ANY, tr("Add Component…")),
        )
        canvas.Bind(
            wx.EVT_MENU, self.createAnchor, menu.Append(wx.ID_ANY, tr("Add Anchor"))
        )
        canvas.Bind(
            wx.EVT_MENU,
            self.createGuideline,
            menu.Append(wx.ID_ANY, tr("Add Guideline")),
        )
        self._cachedPos = event.GetCanvasPosition()
        canvas.PopupMenu(menu)
        del self._cachedPos
        del self._targetPath
        # query pos again, mouse has moved
        self.mouseItem = item = canvas.itemAt(event.GetCanvasPosition())
        if item is not None:
            canvas.SetCursor(self.pointCursor)
        else:
            canvas.SetCursor(self.cursor)

    def prepareUndo(self):
        """A local function to ask the layer to prepare for undo but doing so
        only once if prepareUndo() is called several time during event handling.
        Also layer.endUndoGroup() will be called once, and only if prepareUndo()
        was called."""
        if not self.preparedUndo:
            self.layer.beginUndoGroup()
            self.preparedUndo = True

    def OnMouseDown(self, event):
        if not event.LeftDown():
            super().OnMouseDown(event)
            return
        canvas = self.canvas
        layer = self.layer
        self.origin = pos = event.GetCanvasPosition()
        item = self.mouseItem
        if item is not None:
            cls = item.__class__
            if cls is Component:
                self.deltaToComponent = pos - wx.RealPoint(*item.origin)
            elif cls is PointRecord:
                item = item.point
            elif cls is SegmentRecord:
                # mouseDClick may be followed by mouseDown w/o mouseUp
                return
            if event.ControlDown():
                item.selected = not item.selected
            else:
                if not item.selected:
                    layer.clearSelection()
                    item.selected = True
        else:
            self.mouseItem = item = canvas.segmentAt(pos)
            handleSelection = False
            if item.__class__ is SegmentRecord:
                firstPoint = item.points[0]
                self.deltaToSegment = pos - wx.RealPoint(firstPoint.x, firstPoint.y)
                if event.AltDown() and item.segment.type != "curve":
                    item.segment.addOffCurves()
                handleSelection = not item.segment.selected
            elif item is None:
                handleSelection = layer is not None
            if handleSelection:
                if event.ControlDown():
                    self.oldSelection = {
                        elem for elem in layer.selection if elem.__class__ is Point
                    }
                else:
                    layer.clearSelection()
        if self.mouseItem is not None:
            self.oldPath = (layer.closedGraphicsPath, layer.openGraphicsPath)
        else:
            x, y = pos.Get()
            self.rubberBandRect = x, y, x, y
        canvas.Refresh()
        canvas.SetFocus()

    def OnMotion(self, event):
        canvas = self.canvas
        pos = event.GetCanvasPosition()
        if not event.LeftIsDown():
            if event.Dragging():
                super().OnMotion(event)
            else:
                self.mouseItem = item = canvas.itemAt(pos)
                if item is not None:
                    canvas.SetCursor(self.pointCursor)
                else:
                    canvas.SetCursor(self.cursor)
            return
        if self.origin is None:
            return
        pos = event.GetCanvasPosition()
        item = self.mouseItem
        layer = self.layer
        if item is not None:
            cls = item.__class__
            if cls is GuidelineSegment:
                item = item.guideline
                angle = math.atan2(pos.y - item.y, pos.x - item.x)
                item.angle = math.degrees(angle)
                trufont.TruFont.updateUI()
                return
            if event.ShiftDown():
                # we clamp to the mouseDownPos, unless we have a
                # single offCurve in which case we clamp it against
                # its parent
                onPoint = False
                if (
                    cls is PointRecord
                    and item.point.type is None
                    and len(layer.selection) == 1
                ):
                    points, index = item.points, item.index
                    point = points[index]
                    otherPoint = points[index - 1]
                    if otherPoint.type is None:
                        otherIndex = index + 1
                        # tbh bin modulo might just be faster than this fuss
                        len_points = len(points)
                        if otherIndex >= len_points:
                            otherIndex -= len_points
                        otherPoint = points[otherIndex]
                    if otherPoint.type is not None:
                        pos = self.clampToOrigin(
                            pos, wx.RealPoint(otherPoint.x, otherPoint.y)
                        )
                        onPoint = True
                if not onPoint:
                    pos = self.clampToOrigin(pos, self.origin)
            # this could be a property, itemPos (firstPoint.x + ds) or item.x
            if cls is Component:
                dc = self.deltaToComponent
                ox, oy = item.origin
                dx = pos.x - (ox + dc.x)
                dy = pos.y - (oy + dc.y)
            elif cls is SegmentRecord:
                ds = self.deltaToSegment
                firstPoint = item.points[0]
                dx = pos.x - (firstPoint.x + ds.x)
                dy = pos.y - (firstPoint.y + ds.y)
            else:
                if cls is PointRecord:
                    item = item.point
                dx = pos.x - item.x
                dy = pos.y - item.y
            if event.GetModifiers() == platformSpecific.combinedModifiers():
                option = "nudge"
            elif event.AltDown():
                option = "slide"
            else:
                option = None
            self.prepareUndo()
            moveUILayerSelection(layer, dx, dy, option=option)
        else:
            x2, y2 = pos.Get()
            rubberBandRect = self.rubberBandRect
            if rubberBandRect is None:
                self.rubberBandRect = x2, y2, x2, y2
                return
            x1, y1, *_ = rubberBandRect
            self.rubberBandRect = x1, y1, x2, y2
            if layer is not None:
                if x1 > x2:
                    x1, x2 = x2, x1
                if y1 > y2:
                    y1, y2 = y2, y1
                points = set()
                for path in layer.paths:
                    for point in path.points:
                        if x1 <= point.x <= x2 and y1 <= point.y <= y2:
                            points.add(point)
                if event.ControlDown():
                    points ^= self.oldSelection
                skipOffCurve = event.AltDown()
                for path in layer.paths:
                    for point in path.points:
                        if skipOffCurve and point.type is None:
                            continue
                        point.selected = point in points
        trufont.TruFont.updateUI()

    def OnMouseUp(self, event):
        if event.LeftUp():
            self.maybeJoinPath(event.GetCanvasPosition())
            self.mouseItem = None
            self.oldPath = None
            self.oldSelection = set()
            self.rubberBandRect = None
            if self.preparedUndo:
                self.preparedUndo = False
                layer = self.layer
                layer._parent.get_undoredo().append_action(Action("Move selection", *layer.endUndoGroup()))
            self.canvas.Refresh()
            trufont.TruFont.updateUI()
        else:
            super().OnMouseUp(event)

    def OnMouseDClick(self, event):
        if not event.LeftIsDown():
            super().OnMouseDClick(event)
            return
        canvas = self.canvas
        pos = event.GetCanvasPosition()
        self.mouseItem = item = canvas.itemAt(pos)
        # self.layer.beginUndoGroup()
        if item is not None:
            cls = item.__class__
            if cls is PointRecord:
                path = item.path
                points = path._points
                index = item.index
                point = points[index]
                if point.type is not None:
                    value = not point.smooth
                    if value:
                        if atOpenBoundary(point):
                            return
                        # we could add a method points.siblings(index)
                        len_points = len(points)
                        prev = points[index - 1]
                        nextIndex = index + 1
                        if nextIndex >= len_points:
                            nextIndex -= len_points
                        next_ = points[nextIndex]
                        offCount = (prev.type is None) + (next_.type is None)
                        if not offCount:
                            return
                        elif offCount == 1:
                            offS, onS = prev, next_
                            if onS.type is None:
                                offS, onS = onS, offS
                            rotateUIPointAroundRefLine(
                                onS.x, onS.y, point.x, point.y, offS
                            )
                    point.smooth = value
                    # tbh I feel updateUI could just always be called for tools
                    trufont.TruFont.updateUI()
            elif cls is Anchor:
                self.renameItem(item)
            elif cls is Component:
                self.canvas.textCursor.insertGlyph(item.glyph)
        else:
            self.mouseItem = item = canvas.segmentAt(pos)
            if item.__class__ is SegmentRecord:
                path = item.path
                path.selected = not path.selected
                trufont.TruFont.updateUI()
            else:
                canvas.moveTextCursorTo(event.GetPosition())
        # don't perform move events on double click
        self.origin = None

    # custom painting

    def OnPaint(self, ctx, index):
        path = self.oldPath
        if path is not None:
            scale = self.canvas.inverseScale
            color = trufont.TruFont.settings["backgroundStrokeColor"]
            ctx.SetPen(wx.Pen(color, scale))
            path1, path2 = path
            ctx.StrokePath(path1)
            ctx.StrokePath(path2)
        rect = self.rubberBandRect
        if rect is None:
            return
        color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT)
        r, g, b, a = color.Get()
        color.Set(r, g, b, int(.2 * a))
        ctx.SetBrush(wx.Brush(color))
        ctx.SetPen(wx.NullPen)
        x1, y1, x2, y2 = rect
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1
        w, h = x2 - x1, y2 - y1
        ctx.DrawRectangle(x1, y1, w, h)
