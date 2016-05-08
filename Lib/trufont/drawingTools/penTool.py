from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtWidgets import QApplication
from trufont.drawingTools.baseTool import BaseTool
from trufont.objects.defcon import TContour
from trufont.tools.uiMethods import moveUIPoint


class PenTool(BaseTool):
    name = QApplication.translate("PenTool", "Pen")
    iconPath = ":curve.svg"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._shouldMoveOnCurve = False
        self._targetContour = None

    # helpers

    def _getSelectedCandidatePoint(self):
        """
        If there is exactly one point selected in the glyph at the edge of an
        open contour, return said contour.

        Else return None.
        """

        candidates = set()
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
                continue
            candidates.add(contour)
        if len(candidates) == 1:
            return next(iter(candidates))
        return None

    def _coerceSegmentToCurve(self, contour, pt, pos):
        contour.holdNotifications()
        index = contour.index(pt)
        otherPt = contour.getPoint(index - 1)
        # add an offCurve before pt
        inverseX = 2 * pt.x - pos.x()
        inverseY = 2 * pt.y - pos.y()
        contour.insertPoint(index, pt.__class__((inverseX, inverseY)))
        # add the first of two offCurves
        contour.insertPoint(index, pt.__class__((otherPt.x, otherPt.y)))
        # now flag pt as curve point
        pt.segmentType = "curve"
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
        self._origin = canvasPos = event.localPos()
        x, y = canvasPos.x(), canvasPos.y()
        widget = self.parent()
        candidate = self._getSelectedCandidatePoint()
        itemTuple = widget.itemAt(canvasPos)
        self._glyph.prepareUndo()
        # if we clicked on an item, see if we should join the current contour
        if itemTuple is not None:
            item, parent = itemTuple
            if parent and parent == candidate and not parent.index(item):
                lastPoint = candidate[-1]
                lastPoint.selected = False
                if lastPoint.segmentType:
                    item.segmentType = "line"
                else:
                    candidate.addPoint((item.x, item.y))
                    item.segmentType = "curve"
                item.selected = True
                item.smooth = False
                candidate.dirty = True
                self._targetContour = candidate
                return
        # otherwise, add a point to current contour if applicable
        if candidate is not None:
            contour = candidate
            lastPoint = contour[-1]
            lastPoint.selected = False
            if event.modifiers() & Qt.ShiftModifier:
                pos = self.clampToOrigin(
                    canvasPos, QPointF(lastPoint.x, lastPoint.y))
                x, y = pos.x(), pos.y()
            if lastPoint.segmentType:
                pointType = "line"
            else:
                pointType = "curve"
                contour.addPoint((x, y))
        # or create a new one
        else:
            contour = TContour()
            self._glyph.appendContour(contour)
            pointType = "move"
        # in any case here, unselect all points (*click*) and enable new point
        self._glyph.selected = False
        contour.addPoint((x, y), pointType)
        contour[-1].selected = True
        self._targetContour = contour

    def mouseMoveEvent(self, event):
        contour = self._targetContour
        if contour is None:
            return
        # we don't make any check here, mousePressEvent did it for us
        pos = event.localPos()
        pt = contour[-1]
        if pt.segmentType and not self._shouldMoveOnCurve:
            # don't make a curve until enough distance is reached
            widget = self.parent()
            rect = QRectF(self._origin, pos)
            widgetRect = widget.mapRectFromCanvas(rect)
            if (widgetRect.bottomRight() - widgetRect.topLeft(
                    )).manhattanLength() < 10:
                return
            # go
            pt.selected = False
            pt.smooth = not event.modifiers() & Qt.AltModifier
            contour.holdNotifications()
            # TODO: defer this if Alt is pressed
            if not contour.open:
                # pt is the last point before contour start
                if pt.segmentType:
                    contour.addPoint((pt.x, pt.y))
                startPt = contour[0]
                startPt.segmentType = "curve"
            elif pt.smooth:
                if pt.segmentType == "line":
                    self._coerceSegmentToCurve(contour, pt, pos)
                else:
                    # if there's a curve segment behind, we need to update the
                    # offCurve's position to inverse
                    if len(contour) > 1:
                        onCurveBefore = contour[-2]
                        onCurveBefore.x = 2 * pt.x - pos.x()
                        onCurveBefore.y = 2 * pt.y - pos.y()
            contour.addPoint((pos.x(), pos.y()))
            contour[-1].selected = True
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
                    pos, QPointF(onCurve.x, onCurve.y))
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
        self._targetContour = None
