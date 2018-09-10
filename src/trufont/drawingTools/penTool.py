import trufont
from trufont.drawingTools.baseTool import BaseTool
from trufont.objects.misc import PointRecord, SegmentRecord
from trufont.util.canvasMorph import atOpenBoundary, breakPath, joinPaths
from trufont.util.drawing import CreatePath
from tfont.objects import Path, Point
import wx
from wx import GetTranslation as tr

_path = CreatePath()
_path.MoveToPoint(14.958, 4.56)
_path.AddLineToPoint(13.108, 2.647)
_path.AddLineToPoint(12.048, 1.547)
_path.AddCurveToPoint(11.373, 0.847, 11.283, 0.761, 10.868, 0.761)
_path.AddCurveToPoint(10.598, 0.76, 10.341, 0.873, 10.158, 1.071)
_path.AddCurveToPoint(9.808, 1.478, 9.519, 1.934, 9.3, 2.424)
_path.AddCurveToPoint(9.278, 2.471, 9.26, 2.519, 9.245, 2.569)
_path.AddCurveToPoint(9.187, 2.589, 9.13, 2.613, 9.075, 2.641)
_path.AddLineToPoint(4.158, 5.248)
_path.AddCurveToPoint(3.922, 5.374, 3.744, 5.588, 3.663, 5.843)
_path.AddLineToPoint(1.3, 13.183)
_path.AddCurveToPoint(1.176, 13.66, 1.318, 14.168, 1.67, 14.512)
_path.AddCurveToPoint(1.735, 14.579, 1.93, 14.776, 2.0, 14.838)
_path.AddCurveToPoint(2.242, 15.09, 2.576, 15.234, 2.925, 15.238)
_path.AddCurveToPoint(3.032, 15.239, 3.139, 15.221, 3.24, 15.187)
_path.AddLineToPoint(10.34, 12.74)
_path.AddCurveToPoint(10.59, 12.652, 10.796, 12.47, 10.915, 12.233)
_path.AddLineToPoint(13.45, 7.169)
_path.AddCurveToPoint(13.479, 7.111, 13.502, 7.05, 13.52, 6.988)
_path.AddCurveToPoint(13.582, 6.968, 13.643, 6.942, 13.7, 6.911)
_path.AddCurveToPoint(14.159, 6.671, 14.582, 6.37, 14.96, 6.016)
_path.AddCurveToPoint(15.348, 5.611, 15.347, 4.964, 14.958, 4.56)
_path.CloseSubpath()
_path.MoveToPoint(10.018, 11.76)
_path.AddLineToPoint(2.918, 14.207)
_path.AddLineToPoint(7.058, 9.935)
_path.AddCurveToPoint(7.507, 10.113, 8.022, 9.997, 8.353, 9.645)
_path.AddCurveToPoint(8.83, 9.15, 8.83, 8.355, 8.353, 7.86)
_path.AddCurveToPoint(8.128, 7.625, 7.816, 7.492, 7.491, 7.492)
_path.AddCurveToPoint(7.165, 7.492, 6.853, 7.625, 6.628, 7.86)
_path.AddCurveToPoint(6.279, 8.229, 6.177, 8.77, 6.368, 9.241)
_path.AddLineToPoint(2.248, 13.509)
_path.AddLineToPoint(4.613, 6.169)
_path.AddLineToPoint(9.528, 3.562)
_path.AddLineToPoint(12.553, 6.7)
_path.AddLineToPoint(10.018, 11.76)
_path.CloseSubpath()

_cursor = CreatePath()
_cursor.MoveToPoint(13.8, 20.5)
_cursor.AddLineToPoint(10.5, 17.5)
_cursor.AddLineToPoint(10.5, 16)
_cursor.AddLineToPoint(15, 7)
_cursor.AddLineToPoint(19.5, 16)
_cursor.AddLineToPoint(19.5, 17.5)
_cursor.AddLineToPoint(16.2, 20.5)
_cursor.MoveToPoint(15, 15.5)
_cursor.AddLineToPoint(15, 7)
_cursor_ = CreatePath()
_cursor_.AddRectangle(13, 20, 4, 4)
_cursor.AddEllipse(14, 15, 2, 2)

# TODO: add a bool attr to commands isBg instead of separate path
_bg_ = CreatePath()
_bg_.AddRectangle(13, 20, 4, 4)
_bg_.AddPath(_cursor)

_commands = (
    (_cursor, 230, 0),
    (_cursor_, 0, 0),
)

_plus = CreatePath()
_plus.MoveToPoint(20, 25)
_plus.AddLineToPoint(26, 25)
_plus.MoveToPoint(23, 22)
_plus.AddLineToPoint(23, 28)

_point = CreatePath()
_point.AddRectangle(21, 22, 5, 5)


class PenTool(BaseTool):
    icon = _path
    name = tr("Pen")
    shortcut = "P"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mouseItem = None
        self.origin = None
        self.shouldMoveOnCurve = False
        self.stashedOffCurve = None
        self.targetPath = None

        # TODO flush on dpi change event. need wx 3.1 and beyond...
        self._addCursor = None
        self._cursor = None
        self._pointCursor = None

    @property
    def addCursor(self):
        cursor = self._addCursor
        if cursor is None:
            suppl = ((_plus, 255, 0),)
            cursor = self._addCursor = self.makeCursor(
                _commands+suppl, 15, 8, shadowColor=255, shadowPath=_bg_)
        return cursor

    @property
    def cursor(self):
        cursor = self._cursor
        if cursor is None:
            cursor = self._cursor = self.makeCursor(
                _commands, 15, 8, shadowColor=255, shadowPath=_bg_)
        return cursor

    @property
    def pointCursor(self):
        cursor = self._pointCursor
        if cursor is None:
            bg = CreatePath()
            bg.AddPath(_bg_)
            bg.AddPath(_point)
            suppl = ((_point, 255, 0),)
            cursor = self._pointCursor = self.makeCursor(
                _commands+suppl, 15, 8, shadowColor=255, shadowPath=bg)
        return cursor

    def OnToolDisabled(self):
        # cleanup trailing offcurve
        try:
            points = self.layer.paths[-1].points
        except (AttributeError, IndexError):
            # layer might be None (no glyphs on canvas) or empty
            return
        if points[-1].type is None:
            del points[-1]
            points[-1].smooth = False
            trufont.TruFont.updateUI()

    # helpers

    def coerceSegmentToCurve(self, path, pt, pos):
        points = path.points
        index = points.index(pt)
        otherPt = points[index - 1]
        # add an offCurve before pt
        if path.open:
            # inverse point
            secondX = 2 * pt.x - pos.x
            secondY = 2 * pt.y - pos.y
            smooth = True
        else:
            # closed path we pull the point with the mouse
            secondX = pos.x
            secondY = pos.y
            smooth = False
        points.insert(index, Point(secondX, secondY))
        # add the first of two offCurves
        if self.stashedOffCurve is not None:
            offCurve, onSmooth = self.stashedOffCurve
            otherPt.smooth = index - 1 and onSmooth
            points.insert(index, offCurve)
            self.stashedOffCurve = None
        else:
            firstX = otherPt.x + round(.35 * (pt.x - otherPt.x))
            firstY = otherPt.y + round(.35 * (pt.y - otherPt.y))
            points.insert(index, Point(firstX, firstY))
        # now flag pt as curve point
        pt.type = "curve"
        pt.smooth = smooth

    def selectedPoint(self):
        selection = self.layer.selection
        if len(selection) == 1:
            elem = next(iter(selection))
            if isinstance(elem, Point):
                return elem

    def updateOnCurveSmoothness(self, value):
        path = self.targetPath
        if path is not None:
            points = path.points
            if len(points) < 2:
                return
            point = points[-1]
            if point.selected:
                if point.type is None:
                    point = points[-2]
                    if point.type is None:
                        return
                    if point == points[0]:
                        return
                point.smooth = value
                trufont.TruFont.updateUI()

    # events

    def OnKeyDown(self, event):
        key = event.GetKeyCode()
        if key == wx.WXK_ALT:
            self.updateOnCurveSmoothness(False)
        elif key == wx.WXK_SPACE and self.targetPath is not None:
            self.shouldMoveOnCurve = True
        else:
            super().OnKeyDown(event)

    def OnKeyUp(self, event):
        key = event.GetKeyCode()
        if key == wx.WXK_ALT:
            self.updateOnCurveSmoothness(True)
        elif key == wx.WXK_SPACE and self.targetPath is not None:
            self.shouldMoveOnCurve = False
        else:
            super().OnKeyUp(event)

    def OnMouseDown(self, event):
        if not event.LeftDown():
            super().OnMouseDown(event)
            return
        canvas = self.canvas
        canvas.SetFocus()
        layer = self.layer
        if layer is None:
            return
        #self.layer.beginUndoGroup()
        self.origin = pos = event.GetCanvasPosition()
        mouseItem = self.mouseItem
        selPoint = self.selectedPoint()
        # if we click an on curve, join it at boundaries or break the path
        if isinstance(mouseItem, PointRecord):
            mousePoint = mouseItem.point
            mousePath = mousePoint.path
            if atOpenBoundary(mousePoint):
                if selPoint and selPoint is not mousePoint and atOpenBoundary(
                        selPoint):
                    selPath = selPoint.path
                    selPoints = selPath.points
                    if selPoint.type is None:
                        del selPoints[-1]
                        lastOn = selPoints[-1]
                        self.stashedOffCurve = (selPoint, lastOn.smooth)
                        lastOn.smooth = False
                    joinPaths(selPath, selPoints[0] is selPoint,
                              mousePath, mousePath.points[0] is mousePoint)
                    self.targetPath = selPath
            else:
                # the api could even just be the point...
                breakPath(mousePath, mousePath.points.index(mousePoint))
            if selPoint:
                selPoint.selected = False
            mousePoint.selected = True
        elif isinstance(mouseItem, SegmentRecord):
            # sucks that we gotta reproject (canvas.segmentAt does it already),
            # save projection tValue in the SegmentRecord?
            _, _, t = mouseItem.segment.projectPoint(pos.x, pos.y)
            segment = mouseItem.segments.splitSegment(mouseItem.index, t)
            layer.clearSelection()
            segment.onCurve.selected = True
        else:
            x, y = pos.x, pos.y
            # otherwise, add a point to current path if applicable
            if selPoint and atOpenBoundary(selPoint):
                path = selPoint.path
                points = path.points
                lastPoint = points[-1]
                lastPoint.selected = False
                if lastPoint.type is None:
                    del points[-1]
                    lastOn = points[-1]
                    self.stashedOffCurve = (lastPoint, lastOn.smooth)
                    lastOn.smooth = False
                    # for shift origin, always use an onCurve
                    lastPoint = lastOn
                if event.ShiftDown():
                    pos = self.clampToOrigin(
                        pos, wx.RealPoint(lastPoint.x, lastPoint.y))
                    x, y = pos.x, pos.y
                pointType = "line"
            # or create a new one
            else:
                path = Path()
                points = path.points
                layer.paths.append(path)
                pointType = "move"
            # in any case, unselect all points (*click*) and enable new point
            layer.clearSelection()
            point = Point(x, y, pointType)
            point.selected = True
            points.append(point)
            self.targetPath = path
        trufont.TruFont.updateUI()

    def OnMotion(self, event):
        canvas = self.canvas
        pos = event.GetCanvasPosition()
        if not event.LeftIsDown():
            if event.Dragging():
                super().OnMotion(event)
            else:
                item = canvas.itemAt(pos)
                if item.__class__ is PointRecord and \
                        item.point.type is not None:
                    self.mouseItem = item
                    canvas.SetCursor(self.pointCursor)
                else:
                    item = canvas.segmentAt(pos)
                    if item.__class__ is SegmentRecord:
                        self.mouseItem = item
                        canvas.SetCursor(self.addCursor)
                    else:
                        self.mouseItem = None
                        canvas.SetCursor(self.cursor)
            return
        path = self.targetPath
        if path is None:
            return
        points = path.points
        # selected point
        pt = points[-1]
        if not path.open:
            if pt.type == "curve":
                pt_ = points[-2]
                if pt_.selected:
                    pt = pt_
        if pt.type is not None and not self.shouldMoveOnCurve:
            # don't make a curve until enough distance is reached
            diff = wx.RealPoint(
                event.GetPosition()) - canvas.canvasToClient(self.origin)
            if abs(diff.x) < wx.SYS_DRAG_X and abs(diff.y) < wx.SYS_DRAG_Y:
                return
            onSmooth = not event.AltDown()
            pt.selected = False
            pt.smooth = len(points) > 1 and onSmooth

            if pt.type == "line" and onSmooth:
                self.coerceSegmentToCurve(path, pt, pos)
            elif pt.smooth and path.open:
                # if there's a curve segment behind, we need to update the
                # offCurve's position to inverse
                if len(points) > 1:
                    onCurveBefore = points[-2]
                    onCurveBefore.x = 2 * pt.x - pos.x
                    onCurveBefore.y = 2 * pt.y - pos.y
            if path.open:
                point = Point(pos.x, pos.y)
                point.selected = True
                points.append(point)
            else:
                pt.selected = False
                points[-2].selected = True
        else:
            if pt.type is not None:
                onCurveIndex = -1
                onCurve = pt
            elif path.open:
                onCurveIndex = -2
                onCurve = points[onCurveIndex]
            else:
                onCurveIndex = -1
                onCurve = points[onCurveIndex]
            if event.ShiftDown():
                pos = self.clampToOrigin(
                    pos, wx.RealPoint(onCurve.x, onCurve.y))
            if self.shouldMoveOnCurve:
                dx = pos.x - pt.x
                dy = pos.y - pt.y
                onCurve.x += dx
                onCurve.y += dy
                if len(points) >= 3:
                    prev = points[onCurveIndex-1]
                    if prev.type is None:
                        prev.x += dx
                        prev.y += dy
                next_ = points[onCurveIndex+1]
                if next_.type is None:
                    next_.x += dx
                    next_.y += dy
            else:
                pt.x = pos.x
                pt.y = pos.y
                if path.open and len(points) >= 3 and onCurve.smooth:
                    if onCurve.type == "line":
                        self.coerceSegmentToCurve(path, onCurve, pos)
                    otherSidePoint = points[-3]
                    otherSidePoint.x = 2 * onCurve.x - pos.x
                    otherSidePoint.y = 2 * onCurve.y - pos.y
        trufont.TruFont.updateUI()

    def OnMouseUp(self, event):
        if event.LeftUp():
            self.origin = None
            self.shouldMoveOnCurve = False
            self.stashedOffCurve = None
            self.targetPath = None
            #self.layer.endUndoGroup()
        else:
            super().OnMouseUp(event)
