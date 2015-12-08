from defconQt.objects.defcon import TContour
from defconQt.tools.baseTool import BaseTool
from defconQt.util.uiMethods import moveUIPoint
from PyQt5.QtCore import Qt


class PenTool(BaseTool):
    name = "Pen"
    iconPath = ":/resources/curve.svg"

    def __init__(self, parent=None):
        super().__init__(parent)
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

    # events

    def mousePressEvent(self, event):
        canvasPos = event.localPos()
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
                candidate.dirty = True
                self._targetContour = candidate
        # otherwise, add a point to canvas
        else:
            # add to current contour if applicable
            if candidate is not None:
                contour = candidate
                lastPoint = contour[-1]
                lastPoint.selected = False
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
            # in any case, unselect all points (*click*) and enable new point
            self._glyph.selected = False
            contour.addPoint((x, y), pointType)
            contour[-1].selected = True
            self._targetContour = contour

    def mouseMoveEvent(self, event):
        canvasPos = event.localPos()
        # we don't make any check here, mousePressEvent did it for us
        contour = self._targetContour
        pt = contour[-1]
        if pt.segmentType:
            pt.selected = False
            pt.smooth = not event.modifiers() & Qt.AltModifier
            contour.disableNotifications()
            if pt.segmentType == "line":
                # remove the onCurve
                contour.removePoint(pt)
                # add the first of two offCurves
                otherPt = contour[-1]
                contour.addPoint((otherPt.x, otherPt.y))
                # add an offCurve before pt
                inverseX = 2 * pt.x - canvasPos.x()
                inverseY = 2 * pt.y - canvasPos.y()
                contour.addPoint((inverseX, inverseY))
                # now add pt back as curve point
                pt.segmentType = "curve"
                contour.insertPoint(len(self._targetContour), pt)
            contour.addPoint((canvasPos.x(), canvasPos.y()))
            contour[-1].selected = True
            contour.enableNotifications()
        else:
            dx = canvasPos.x() - pt.x
            dy = canvasPos.y() - pt.y
            if len(contour) >= 3:
                moveUIPoint(contour, pt, (dx, dy))
                otherSidePoint = contour[-3]
                moveUIPoint(contour, otherSidePoint, (-dx, -dy))
            else:
                pt.move((dx, dy))
                contour.dirty = True

    def mouseReleaseEvent(self, event):
        self._targetContour = None

    # custom painting

    def paint(self, painter):
        pass
