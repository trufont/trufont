from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtWidgets import QApplication
from trufont.drawingTools.baseTool import BaseTool
from trufont.tools.uiMethods import moveUIPoint


class PenTool(BaseTool):
    name = QApplication.translate("PenTool", "Pen")
    iconPath = ":curve.svg"

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
            firstX = otherPt.x + round(.35 * (pt.x - otherPt.x))
            firstY = otherPt.y + round(.35 * (pt.y - otherPt.y))
            contour.insertPoint(index, pt.__class__((firstX, firstY)))
        # now flag pt as curve point
        pt.segmentType = "curve"
        pt.smooth = smooth
        contour.releaseHeldNotifications()

    def _updateOnCurveSmoothness(self, event):
        if self._targetContour is not None:
            if len(self._targetContour) < 2:
                return
            pt = self._targetContour[-1]
            if pt.selected:
                onCurve = self._targetContour[-2]
                onCurve.smooth = not event.modifiers() & Qt.AltModifier
                self._targetContour.dirty = True

    # events

    def keyPressEvent(self, event):
        self._updateOnCurveSmoothness(event)
        self._shouldMoveOnCurve = event.key() == Qt.Key_Space

    def keyReleaseEvent(self, event):
        self._updateOnCurveSmoothness(event)
        if event.key() == Qt.Key_Space:
            self._shouldMoveOnCurve = False

    def mousePressEvent(self, event):
        self._origin = event.localPos()
        widget = self.parent()
        candidate = self._getSelectedCandidatePoint()
        itemTuple = widget.itemAt(self._origin)
        self._glyph.prepareUndo()
        # if we clicked on an item, see if we should join the current contour
        if itemTuple is not None:
            item, parent = itemTuple
            if parent and parent == candidate and not parent.index(item):
                lastPoint = candidate[-1]
                lastPoint.selected = False
                if lastPoint.segmentType is not None:
                    item.segmentType = "line"
                else:
                    parent.removePoint(lastPoint)
                    self._stashedOffCurve = (lastPoint, parent[-1].smooth)
                    parent[-1].smooth = False
                item.segmentType = "line"
                item.selected = True
                item.smooth = False
                candidate.postNotification(
                    notification="Contour.SelectionChanged")
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
                    self._origin, QPointF(lastPoint.x, lastPoint.y)).toPoint()
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
        contour.postNotification(
            notification="Contour.SelectionChanged")
        self._targetContour = contour

    def mouseMoveEvent(self, event):
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
            if (widgetRect.bottomRight() - widgetRect.topLeft(
                    )).manhattanLength() < 10:
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
            contour.postNotification(
                notification="Contour.SelectionChanged")
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
                    event.localPos(), QPointF(onCurve.x, onCurve.y)).toPoint()
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
        self._shouldMoveOnCurve = False
        self._stashedOffCurve = None
        self._targetContour = None
