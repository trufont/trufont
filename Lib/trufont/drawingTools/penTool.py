from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QPainterPath
from PyQt5.QtWidgets import QApplication

from trufont.drawingTools.baseTool import BaseTool
from trufont.tools.uiMethods import moveUIPoint

_path = QPainterPath()
_path.moveTo(6.05, 22.5)
_path.lineTo(11.84, 15.59)
_path.cubicTo(11.65, 15.31, 11.47, 14.82, 11.47, 14.34)
_path.cubicTo(11.47, 12.92, 12.58, 11.9, 13.85, 11.9)
_path.cubicTo(15.21, 11.91, 16.27, 12.95, 16.27, 14.34)
_path.cubicTo(16.27, 15.58, 15.26, 16.72, 13.87, 16.72)
_path.cubicTo(13.57, 16.72, 13.19, 16.65, 12.94, 16.53)
_path.lineTo(7.16, 23.43)
_path.lineTo(7.74, 23.92)
_path.cubicTo(7.74, 23.92, 17.62, 20.39, 19.35, 18.33)
_path.cubicTo(21.25, 16.06, 21.37, 13.19, 19.67, 10.61)
_path.lineTo(22.85, 6.83)
_path.lineTo(19.67, 4.17)
_path.lineTo(16.5, 7.95)
_path.cubicTo(13.66, 6.72, 10.84, 7.32, 8.92, 9.58)
_path.cubicTo(7.27, 11.52, 5.47, 22.01, 5.47, 22.01)
_path.closeSubpath()


class PenTool(BaseTool):
    icon = _path
    name = QApplication.translate("PenTool", "Pen")
    shortcut = "P"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._shouldMoveOnCurve = False
        self._stashedOffCurve = None
        self._targetContour = None

    def toolActivated(self):
        glyph = self._glyph
        glyph.addObserver(self, "_selectionChanged", "Glyph.SelectionChanged")

    def toolDisabled(self):
        glyph = self._glyph
        glyph.removeObserver(self, "Glyph.SelectionChanged")
        self._cleanupTrailingOffcurve()
        assert not self._shouldMoveOnCurve

    # notifications

    def _selectionChanged(self, notification):
        if len(self._glyph.selection) != 1:
            self._cleanupTrailingOffcurve()

    # helpers

    def _cleanupTrailingOffcurve(self):
        for contour in self._glyph:
            if not (contour and contour.open):
                continue
            point = contour[-1]
            if point.segmentType is None:
                # TODO(meta): should we emit selection changed if deleted point
                # was selected?
                contour.removePoint(point)
                contour[-1].smooth = False

    def _getSelectedCandidatePoint(self):
        """
        If there is exactly one point selected in the glyph at the edge of an
        open contour, return said contour.

        Else return None.
        """

        candidates = set()
        shouldReverse = False
        for contour in self._glyph:
            # we're after an open contour...
            if not (len(contour) and contour.open):
                continue
            # ...with the last point selected
            sel = contour.selection
            if not len(sel) == 1:
                continue
            lastPoint = contour[-1]
            if not lastPoint.selected:
                if not contour[0].selected:
                    continue
                shouldReverse = True
            else:
                shouldReverse = False
            candidates.add(contour)
        if len(candidates) == 1:
            ret = next(iter(candidates))
            if shouldReverse:
                ret.reverse()
            return ret
        return None

    def _coerceSegmentToCurve(self, contour, pt, pos):
        contour.holdNotifications()
        index = contour.index(pt) or len(contour)
        otherPt = contour.getPoint(index - 1)
        # add an offCurve before pt
        if contour.open:
            # inverse point
            secondX = 2 * pt.x - pos.x()
            secondY = 2 * pt.y - pos.y()
            smooth = True
        else:
            # closed contour we pull the point with the mouse
            secondX = pos.x()
            secondY = pos.y()
            smooth = False
        contour.insertPoint(index, pt.__class__((secondX, secondY)))
        # add the first of two offCurves
        if self._stashedOffCurve is not None:
            offCurve, onSmooth = self._stashedOffCurve
            otherPt.smooth = index - 1 and onSmooth
            contour.insertPoint(index, offCurve)
            self._stashedOffCurve = None
        else:
            firstX = otherPt.x + round(0.35 * (pt.x - otherPt.x))
            firstY = otherPt.y + round(0.35 * (pt.y - otherPt.y))
            contour.insertPoint(index, pt.__class__((firstX, firstY)))
        # now flag pt as curve point
        pt.segmentType = "curve"
        pt.smooth = smooth
        contour.releaseHeldNotifications()

    def _updateOnCurveSmoothness(self, event):
        contour = self._targetContour
        if contour is not None:
            if len(contour) < 2:
                return
            pt = contour[-1]
            if pt.selected:
                # grab the onCurve. if not the previous point, it's the one
                # before it
                if pt.segmentType is None:
                    pt = contour[-2]
                    # this shouldn't happen, but guard whatsoever
                    if pt.segmentType is None:
                        return
                    if pt == contour[0]:
                        return
                pt.smooth = not event.modifiers() & Qt.AltModifier
                contour.dirty = True

    # events

    def keyPressEvent(self, event):
        self._updateOnCurveSmoothness(event)
        self._shouldMoveOnCurve = event.key() == Qt.Key_Space

    def keyReleaseEvent(self, event):
        self._updateOnCurveSmoothness(event)
        if event.key() == Qt.Key_Space:
            self._shouldMoveOnCurve = False

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            super().mousePressEvent(event)
            return
        self._glyph.beginUndoGroup()
        self._origin = event.localPos()
        widget = self.parent()
        candidate = self._getSelectedCandidatePoint()
        mouseItem = widget.itemAt(self._origin)
        # if we clicked on an item, see if we should join the current contour
        if isinstance(mouseItem, tuple):
            contour, index = mouseItem
            if contour == candidate and not index:
                point = contour[index]
                lastPoint = candidate[-1]
                lastPoint.selected = False
                if lastPoint.segmentType is not None:
                    point.segmentType = "line"
                else:
                    contour.removePoint(lastPoint)
                    self._stashedOffCurve = (lastPoint, contour[-1].smooth)
                    contour[-1].smooth = False
                point.segmentType = "line"
                point.selected = True
                point.smooth = False
                candidate.postNotification(notification="Contour.SelectionChanged")
                candidate.dirty = True
                self._targetContour = candidate
                return
        canvasPos = event.pos()
        x, y = canvasPos.x(), canvasPos.y()
        # otherwise, add a point to current contour if applicable
        if candidate is not None:
            contour = candidate
            lastPoint = contour[-1]
            lastPoint.selected = False
            if event.modifiers() & Qt.ShiftModifier:
                pos = self.clampToOrigin(
                    self._origin, QPointF(lastPoint.x, lastPoint.y)
                ).toPoint()
                x, y = pos.x(), pos.y()
            if not lastPoint.segmentType:
                contour.removePoint(lastPoint)
                self._stashedOffCurve = (lastPoint, contour[-1].smooth)
                contour[-1].smooth = False
            pointType = "line"
        # or create a new one
        else:
            contour = self._glyph.instantiateContour()
            self._glyph.appendContour(contour)
            pointType = "move"
        # in any case here, unselect all points (*click*) and enable new point
        self._glyph.selected = False
        contour.addPoint((x, y), pointType)
        contour[-1].selected = True
        contour.postNotification(notification="Contour.SelectionChanged")
        self._targetContour = contour

    def mouseMoveEvent(self, event):
        if not event.buttons() & Qt.LeftButton:
            super().mouseMoveEvent(event)
            return
        contour = self._targetContour
        if contour is None:
            return
        # we don't make any check here, mousePressEvent did it for us
        pos = event.pos()
        # selected point
        pt = contour[-1]
        if not contour.open:
            pt_ = contour[0]
            if pt_.selected:
                pt = pt_
        if pt.segmentType and not self._shouldMoveOnCurve:
            # don't make a curve until enough distance is reached
            widget = self.parent()
            rect = QRectF(self._origin, event.localPos())
            widgetRect = widget.mapRectFromCanvas(rect)
            if (widgetRect.bottomRight() - widgetRect.topLeft()).manhattanLength() < 10:
                return
            # go
            onSmooth = not event.modifiers() & Qt.AltModifier
            pt.selected = False
            pt.smooth = len(contour) > 1 and onSmooth
            contour.holdNotifications()
            if pt.segmentType == "line" and onSmooth:
                self._coerceSegmentToCurve(contour, pt, pos)
            elif pt.smooth and contour.open:
                # if there's a curve segment behind, we need to update the
                # offCurve's position to inverse
                if len(contour) > 1:
                    onCurveBefore = contour[-2]
                    onCurveBefore.x = 2 * pt.x - pos.x()
                    onCurveBefore.y = 2 * pt.y - pos.y()
            if contour.open:
                contour.addPoint((pos.x(), pos.y()))
            contour[-1].selected = True
            contour.postNotification(notification="Contour.SelectionChanged")
            contour.releaseHeldNotifications()
        else:
            if pt.segmentType:
                onCurve = pt
            elif contour.open:
                onCurve = contour[-2]
            else:
                onCurve = contour[0]
            if event.modifiers() & Qt.ShiftModifier:
                pos = self.clampToOrigin(
                    event.localPos(), QPointF(onCurve.x, onCurve.y)
                ).toPoint()
            if self._shouldMoveOnCurve:
                dx = pos.x() - pt.x
                dy = pos.y() - pt.y
                moveUIPoint(contour, onCurve, (dx, dy))
            else:
                pt.x = pos.x()
                pt.y = pos.y()
                if contour.open and len(contour) >= 3 and onCurve.smooth:
                    if onCurve.segmentType == "line":
                        self._coerceSegmentToCurve(contour, onCurve, pos)
                    otherSidePoint = contour[-3]
                    otherSidePoint.x = 2 * onCurve.x - pos.x()
                    otherSidePoint.y = 2 * onCurve.y - pos.y()
            contour.dirty = True

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._shouldMoveOnCurve = False
            self._stashedOffCurve = None
            self._targetContour = None
            self._glyph.endUndoGroup()
        else:
            super().mouseReleaseEvent(event)
